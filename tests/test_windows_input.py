"""Cross-platform injected tests for the private Windows console backend."""

from __future__ import annotations

import ctypes
from dataclasses import dataclass, field
from io import UnsupportedOperation
import sys

import pytest

from thebitlab_tui import Key, KeyEvent
from thebitlab_tui import terminal
from thebitlab_tui import _windows_input as windows_input
from thebitlab_tui._windows_decoder import _WindowsKeyRecord
from thebitlab_tui._windows_input import (
    _ENABLE_PROCESSED_INPUT,
    _INPUT_RECORD,
    _KEY_EVENT,
    _KEY_EVENT_RECORD,
    _READ_BATCH_SIZE,
    _WAIT_OBJECT_0,
    _WAIT_TIMEOUT,
    _Kernel32Bindings,
    _NotConsoleError,
    _WindowsInputBackend,
    _WindowsOps,
    _default_ops,
)


class FakeStream:
    """Expose one deterministic CRT file descriptor."""

    def fileno(self) -> int:
        """Return the injected standard-input descriptor."""

        return 7


@dataclass
class Harness:
    """Provide deterministic handle, mode, wait, record, and clock operations."""

    mode: int = _ENABLE_PROCESSED_INPUT
    now: float = 10.0
    waits: list[int | BaseException] = field(default_factory=list)
    batches: list[list[_WindowsKeyRecord | None] | BaseException] = field(
        default_factory=list
    )
    wait_calls: list[int] = field(default_factory=list)
    capacities: list[int] = field(default_factory=list)
    descriptor_calls: list[int] = field(default_factory=list)

    def ops(self) -> _WindowsOps:
        """Build one injected operation bundle."""

        return _WindowsOps(
            stream=FakeStream(),  # type: ignore[arg-type]
            get_osfhandle=self.get_osfhandle,
            get_console_mode=lambda handle: self.mode,
            wait=self.wait,
            read_records=self.read_records,
            monotonic=lambda: self.now,
        )

    def get_osfhandle(self, descriptor: int) -> int:
        """Record the CRT descriptor and return a borrowed handle."""

        self.descriptor_calls.append(descriptor)
        return 99

    def wait(self, handle: int, milliseconds: int) -> int:
        """Return one injected wait result and record its timeout."""

        self.wait_calls.append(milliseconds)
        result = self.waits.pop(0) if self.waits else _WAIT_TIMEOUT
        if isinstance(result, BaseException):
            raise result
        if result == _WAIT_TIMEOUT and milliseconds:
            self.now += milliseconds / 1000.0
        return result

    def read_records(
        self, handle: int, capacity: int
    ) -> list[_WindowsKeyRecord | None]:
        """Return one injected bounded input-record batch."""

        self.capacities.append(capacity)
        result = self.batches.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


def key(character: str = "x") -> _WindowsKeyRecord:
    """Create one printable key-down record for backend tests."""

    return _WindowsKeyRecord(
        key_down=True,
        repeat_count=1,
        virtual_key=ord(character.upper()),
        unicode_unit=ord(character),
        control_state=0,
    )


def active_backend(harness: Harness) -> _WindowsInputBackend:
    """Create and activate one injected backend."""

    backend = _WindowsInputBackend(0.05, ops=harness.ops())
    backend.activate()
    return backend


def test_fixed_width_win32_abi_is_host_independent() -> None:
    assert ctypes.sizeof(_KEY_EVENT_RECORD) == 16
    assert _KEY_EVENT_RECORD.KeyDown.offset == 0
    assert _KEY_EVENT_RECORD.RepeatCount.offset == 4
    assert _KEY_EVENT_RECORD.VirtualKeyCode.offset == 6
    assert _KEY_EVENT_RECORD.VirtualScanCode.offset == 8
    assert _KEY_EVENT_RECORD.UnicodeUnit.offset == 10
    assert _KEY_EVENT_RECORD.ControlKeyState.offset == 12
    assert ctypes.sizeof(_INPUT_RECORD) == 20
    assert _INPUT_RECORD.EventType.offset == 0
    assert _INPUT_RECORD.Event.offset == 4


def test_activation_uses_crt_handle_and_requires_processed_console() -> None:
    harness = Harness()
    backend = active_backend(harness)
    assert harness.descriptor_calls == [7]
    backend.restore()
    with pytest.raises(RuntimeError, match="not active"):
        backend.read(None)

    disabled = Harness(mode=0)
    with pytest.raises(UnsupportedOperation, match="processed input"):
        _WindowsInputBackend(0.05, ops=disabled.ops()).activate()


def test_platform_factory_selects_windows_backend_lazily(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = Harness()
    monkeypatch.setattr(terminal.sys, "platform", "win32")
    monkeypatch.setattr(
        "thebitlab_tui._windows_input._default_ops", harness.ops
    )

    backend = terminal._create_backend(0.05)

    assert isinstance(backend, _WindowsInputBackend)
    assert harness.descriptor_calls == []


def test_non_console_and_unusable_descriptor_are_rejected() -> None:
    harness = Harness()
    ops = harness.ops()
    backend = _WindowsInputBackend(
        0.05,
        ops=_WindowsOps(
            stream=ops.stream,
            get_osfhandle=ops.get_osfhandle,
            get_console_mode=lambda handle: (_ for _ in ()).throw(
                _NotConsoleError("not console")
            ),
            wait=ops.wait,
            read_records=ops.read_records,
            monotonic=ops.monotonic,
        ),
    )
    with pytest.raises(UnsupportedOperation, match="not a Windows console"):
        backend.activate()

    class MissingDescriptor:
        pass

    missing_ops = _WindowsOps(
        stream=MissingDescriptor(),  # type: ignore[arg-type]
        get_osfhandle=ops.get_osfhandle,
        get_console_mode=ops.get_console_mode,
        wait=ops.wait,
        read_records=ops.read_records,
        monotonic=ops.monotonic,
    )
    with pytest.raises(UnsupportedOperation, match="no usable"):
        _WindowsInputBackend(0.05, ops=missing_ops).activate()


def test_zero_deadline_polls_once_and_returns_queued_event() -> None:
    harness = Harness(waits=[_WAIT_OBJECT_0], batches=[[key()]])
    backend = active_backend(harness)
    assert backend.read(10.0) == KeyEvent(Key.CHARACTER, "x")
    assert harness.wait_calls == [0]
    assert harness.capacities == [_READ_BATCH_SIZE]


def test_expired_deadline_stops_after_one_ignored_batch() -> None:
    harness = Harness(waits=[_WAIT_OBJECT_0], batches=[[None]])
    backend = active_backend(harness)
    assert backend.read(10.0) is None
    assert harness.wait_calls == [0]


def test_partial_surrogate_drains_one_more_ready_batch() -> None:
    high = _WindowsKeyRecord(True, 1, 0, 0xD83D, 0)
    low = _WindowsKeyRecord(True, 1, 0, 0xDE00, 0)
    harness = Harness(
        waits=[_WAIT_OBJECT_0, _WAIT_OBJECT_0], batches=[[high], [low]]
    )
    backend = active_backend(harness)
    assert backend.read(10.0) == KeyEvent(Key.CHARACTER, "😀")
    assert harness.wait_calls == [0, 0]


def test_partial_surrogate_cannot_starve_an_expired_deadline() -> None:
    high = _WindowsKeyRecord(True, 1, 0, 0xD83D, 0)
    sentinel = AssertionError("partial input was over-drained")
    harness = Harness(
        waits=[_WAIT_OBJECT_0, _WAIT_OBJECT_0, _WAIT_OBJECT_0],
        batches=[[high], [None], sentinel],
    )
    backend = active_backend(harness)
    assert backend.read(10.0) is None
    assert harness.batches == [sentinel]
    assert harness.wait_calls == [0, 0]


def test_unbounded_waits_are_sliced_and_keyboard_interrupt_propagates() -> None:
    harness = Harness(waits=[_WAIT_TIMEOUT, KeyboardInterrupt()])
    backend = active_backend(harness)
    with pytest.raises(KeyboardInterrupt):
        backend.read(None)
    assert harness.wait_calls == [50, 50]


def test_finite_wait_uses_remaining_ceiling_without_restarting_deadline() -> None:
    harness = Harness(waits=[_WAIT_TIMEOUT, _WAIT_TIMEOUT])
    backend = active_backend(harness)
    assert backend.read(10.051) is None
    assert harness.wait_calls == [50, 1]


@pytest.mark.parametrize("failure", [OSError("wait failed"), SystemExit(2)])
def test_wait_failures_and_control_flow_propagate(failure: BaseException) -> None:
    harness = Harness(waits=[failure])
    backend = active_backend(harness)
    with pytest.raises(type(failure)):
        backend.read(10.1)


def test_read_failure_zero_batch_and_unexpected_wait_are_errors() -> None:
    failed = Harness(waits=[_WAIT_OBJECT_0], batches=[OSError("read failed")])
    with pytest.raises(OSError, match="read failed"):
        active_backend(failed).read(10.1)

    empty = Harness(waits=[_WAIT_OBJECT_0], batches=[[]])
    with pytest.raises(OSError, match="no records"):
        active_backend(empty).read(10.1)

    unexpected = Harness(waits=[0x80])
    with pytest.raises(OSError, match="unexpected"):
        active_backend(unexpected).read(10.1)


def test_non_key_record_does_not_reset_finite_deadline() -> None:
    harness = Harness(waits=[_WAIT_OBJECT_0], batches=[[None]])
    backend = active_backend(harness)
    assert backend.read(10.0) is None


class FakeFunction:
    """Callable that accepts ctypes prototype attributes."""

    def __init__(self, result: int = 1) -> None:
        self.result = result
        self.argtypes: list[object] | None = None
        self.restype: object | None = None

    def __call__(self, *args: object) -> int:
        return self.result


class FakeKernel32:
    """Expose only the approved minimal kernel32 functions."""

    def __init__(self) -> None:
        self.GetConsoleMode = FakeFunction()
        self.WaitForSingleObject = FakeFunction(_WAIT_TIMEOUT)
        self.ReadConsoleInputW = FakeFunction()


def test_kernel32_bindings_declare_only_fixed_width_signatures() -> None:
    library = FakeKernel32()
    _Kernel32Bindings(library)  # type: ignore[arg-type]
    assert library.GetConsoleMode.restype is ctypes.c_int32
    assert library.WaitForSingleObject.restype is ctypes.c_uint32
    assert library.ReadConsoleInputW.restype is ctypes.c_int32
    assert len(library.GetConsoleMode.argtypes or []) == 2
    assert len(library.WaitForSingleObject.argtypes or []) == 2
    assert len(library.ReadConsoleInputW.argtypes or []) == 4


@pytest.mark.parametrize(
    ("operation", "expected"),
    [
        ("mode", "GetConsoleMode"),
        ("wait", "WaitForSingleObject"),
        ("read", "ReadConsoleInputW"),
    ],
)
def test_kernel32_binding_failures_preserve_last_error(
    monkeypatch: pytest.MonkeyPatch, operation: str, expected: str
) -> None:
    library = FakeKernel32()
    if operation == "mode":
        library.GetConsoleMode.result = 0
    elif operation == "wait":
        library.WaitForSingleObject.result = windows_input._WAIT_FAILED
    else:
        library.ReadConsoleInputW.result = 0
    monkeypatch.setattr(windows_input, "_last_error", lambda: 123)
    bindings = _Kernel32Bindings(library)  # type: ignore[arg-type]

    with pytest.raises(OSError) as caught:
        if operation == "mode":
            bindings.get_console_mode(99)
        elif operation == "wait":
            bindings.wait(99, 0)
        else:
            bindings.read_records(99, 1)

    assert expected in str(caught.value) or getattr(caught.value, "winerror", None) == 123


def test_invalid_handle_mode_failure_is_a_console_capability_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    library = FakeKernel32()
    library.GetConsoleMode.result = 0
    monkeypatch.setattr(
        windows_input, "_last_error", lambda: windows_input._ERROR_INVALID_HANDLE
    )

    with pytest.raises(_NotConsoleError):
        _Kernel32Bindings(library).get_console_mode(99)  # type: ignore[arg-type]


def test_kernel32_record_buffer_translates_key_and_non_key_records() -> None:
    class RecordRead(FakeFunction):
        def __call__(
            self,
            handle: object,
            records: object,
            capacity: object,
            count: object,
        ) -> int:
            records[0].EventType = _KEY_EVENT  # type: ignore[index,union-attr]
            raw = records[0].Event.KeyEvent  # type: ignore[index,union-attr]
            raw.KeyDown = 1
            raw.RepeatCount = 2
            raw.VirtualKeyCode = ord("X")
            raw.UnicodeUnit = ord("x")
            raw.ControlKeyState = 0x10
            records[1].EventType = 0x0004  # type: ignore[index,union-attr]
            ctypes.cast(count, ctypes.POINTER(ctypes.c_uint32)).contents.value = 2
            return 1

    library = FakeKernel32()
    library.ReadConsoleInputW = RecordRead()
    bindings = _Kernel32Bindings(library)  # type: ignore[arg-type]
    assert bindings.read_records(99, 4) == [
        _WindowsKeyRecord(True, 2, ord("X"), ord("x"), 0x10),
        None,
    ]


@pytest.mark.skipif(sys.platform != "win32", reason="real Win32 console smoke only")
def test_real_windows_console_policy_smoke() -> None:
    """Activate a real console without requiring CI standard input to be interactive."""

    ops = _default_ops()
    backend = _WindowsInputBackend(0.05, ops=ops)
    try:
        descriptor = ops.stream.fileno()
        handle = int(ops.get_osfhandle(descriptor))
        before = ops.get_console_mode(handle)
    except (AttributeError, OSError, ValueError):
        with pytest.raises(UnsupportedOperation):
            backend.activate()
        return

    backend.activate()
    assert ops.get_console_mode(handle) == before
    backend.restore()
    assert ops.get_console_mode(handle) == before

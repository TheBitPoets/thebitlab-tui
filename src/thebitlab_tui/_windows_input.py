"""Private Windows console backend with fixed-width ``ctypes`` bindings."""

from __future__ import annotations

import ctypes
import math
import sys
from collections.abc import Callable
from dataclasses import dataclass
from io import UnsupportedOperation
from typing import BinaryIO, Protocol

from ._windows_decoder import _WindowsKeyRecord, _WindowsRecordDecoder
from .events import KeyEvent


_BOOL = ctypes.c_int32
_WORD = ctypes.c_uint16
_DWORD = ctypes.c_uint32
_WCHAR = ctypes.c_uint16
_HANDLE = ctypes.c_void_p

_KEY_EVENT = 0x0001
_ENABLE_PROCESSED_INPUT = 0x0001
_WAIT_OBJECT_0 = 0x00000000
_WAIT_TIMEOUT = 0x00000102
_WAIT_FAILED = 0xFFFFFFFF
_INVALID_HANDLE_VALUE = -1
_ERROR_INVALID_HANDLE = 6
_WAIT_SLICE_MS = 50
_READ_BATCH_SIZE = 64
_PARTIAL_DRAIN_BATCH_LIMIT = 16


class _KEY_EVENT_RECORD(ctypes.Structure):
    """Fixed-width representation of the Win32 ``KEY_EVENT_RECORD`` ABI."""

    _fields_ = [
        ("KeyDown", _BOOL),
        ("RepeatCount", _WORD),
        ("VirtualKeyCode", _WORD),
        ("VirtualScanCode", _WORD),
        ("UnicodeUnit", _WCHAR),
        ("ControlKeyState", _DWORD),
    ]


class _INPUT_EVENT_UNION(ctypes.Union):
    """Largest Win32 input-record payload needed to preserve union alignment."""

    _fields_ = [("KeyEvent", _KEY_EVENT_RECORD), ("Raw", ctypes.c_ubyte * 16)]


class _INPUT_RECORD(ctypes.Structure):
    """Fixed-width representation of the Win32 ``INPUT_RECORD`` ABI."""

    _fields_ = [("EventType", _WORD), ("Event", _INPUT_EVENT_UNION)]


class _Kernel32Like(Protocol):
    """Structural type for the three injected kernel32 functions."""

    GetConsoleMode: object
    WaitForSingleObject: object
    ReadConsoleInputW: object


class _NotConsoleError(OSError):
    """Mark ``GetConsoleMode`` failure caused by a non-console handle."""


def _last_error() -> int:
    """Return the thread-local Win32 last-error value when available."""

    reader = getattr(ctypes, "get_last_error", None)
    return 0 if reader is None else int(reader())


def _os_error(operation: str, code: int | None = None) -> OSError:
    """Create an ``OSError`` without importing Windows-only helpers eagerly."""

    error_code = _last_error() if code is None else code
    win_error = getattr(ctypes, "WinError", None)
    if win_error is not None and error_code:
        return win_error(error_code)
    return OSError(error_code, f"{operation} failed")


class _Kernel32Bindings:
    """Typed wrappers around the minimal kernel32 console input API."""

    def __init__(self, library: _Kernel32Like) -> None:
        self._get_console_mode = library.GetConsoleMode
        self._get_console_mode.argtypes = [_HANDLE, ctypes.POINTER(_DWORD)]
        self._get_console_mode.restype = _BOOL
        self._wait = library.WaitForSingleObject
        self._wait.argtypes = [_HANDLE, _DWORD]
        self._wait.restype = _DWORD
        self._read = library.ReadConsoleInputW
        self._read.argtypes = [
            _HANDLE,
            ctypes.POINTER(_INPUT_RECORD),
            _DWORD,
            ctypes.POINTER(_DWORD),
        ]
        self._read.restype = _BOOL

    def get_console_mode(self, handle: int) -> int:
        """Return console mode or raise for a failed capability probe."""

        mode = _DWORD()
        if not self._get_console_mode(_HANDLE(handle), ctypes.byref(mode)):
            code = _last_error()
            if code == _ERROR_INVALID_HANDLE:
                raise _NotConsoleError(code, "standard input is not a console")
            raise _os_error("GetConsoleMode", code)
        return int(mode.value)

    def wait(self, handle: int, milliseconds: int) -> int:
        """Wait for console input and preserve the raw documented result."""

        result = int(self._wait(_HANDLE(handle), _DWORD(milliseconds)))
        if result == _WAIT_FAILED:
            raise _os_error("WaitForSingleObject")
        return result

    def read_records(
        self, handle: int, capacity: int
    ) -> list[_WindowsKeyRecord | None]:
        """Read a bounded batch; ``None`` represents a non-key input record."""

        records = (_INPUT_RECORD * capacity)()
        count = _DWORD()
        if not self._read(
            _HANDLE(handle), records, _DWORD(capacity), ctypes.byref(count)
        ):
            raise _os_error("ReadConsoleInputW")
        if count.value == 0:
            raise OSError("ReadConsoleInputW returned no records")
        converted: list[_WindowsKeyRecord | None] = []
        for raw in records[: count.value]:
            if raw.EventType != _KEY_EVENT:
                converted.append(None)
                continue
            key = raw.Event.KeyEvent
            converted.append(
                _WindowsKeyRecord(
                    key_down=bool(key.KeyDown),
                    repeat_count=int(key.RepeatCount),
                    virtual_key=int(key.VirtualKeyCode),
                    unicode_unit=int(key.UnicodeUnit),
                    control_state=int(key.ControlKeyState),
                )
            )
        return converted


@dataclass(frozen=True, slots=True)
class _WindowsOps:
    """Injectable stream, handle, console, wait, record-read, and clock operations."""

    stream: BinaryIO
    get_osfhandle: Callable[[int], int]
    get_console_mode: Callable[[int], int]
    wait: Callable[[int, int], int]
    read_records: Callable[[int, int], list[_WindowsKeyRecord | None]]
    monotonic: Callable[[], float]


def _default_ops() -> _WindowsOps:
    """Load CRT and kernel32 bindings only after Windows platform selection."""

    import msvcrt
    import time

    library = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
    bindings = _Kernel32Bindings(library)
    return _WindowsOps(
        stream=sys.stdin,  # type: ignore[arg-type]
        get_osfhandle=msvcrt.get_osfhandle,
        get_console_mode=bindings.get_console_mode,
        wait=bindings.wait,
        read_records=bindings.read_records,
        monotonic=time.monotonic,
    )


class _WindowsInputBackend:
    """Read normalized events from one borrowed Windows console input handle."""

    def __init__(self, escape_timeout: float, *, ops: _WindowsOps | None = None) -> None:
        del escape_timeout
        self._ops = _default_ops() if ops is None else ops
        self._handle: int | None = None
        self._decoder = _WindowsRecordDecoder()

    def activate(self) -> None:
        """Borrow standard input and require processed console input without mutation."""

        try:
            descriptor = self._ops.stream.fileno()
            handle = int(self._ops.get_osfhandle(descriptor))
        except (AttributeError, OSError, ValueError) as error:
            raise UnsupportedOperation(
                "standard input has no usable Windows console handle"
            ) from error
        if handle in (0, _INVALID_HANDLE_VALUE):
            raise UnsupportedOperation("standard input has no usable Windows console handle")
        try:
            mode = self._ops.get_console_mode(handle)
        except _NotConsoleError as error:
            raise UnsupportedOperation("standard input is not a Windows console") from error
        if not mode & _ENABLE_PROCESSED_INPUT:
            raise UnsupportedOperation("Windows console processed input must be enabled")
        self._handle = handle

    def read(self, deadline: float | None) -> KeyEvent | None:
        """Return one event before an absolute deadline using bounded Win32 waits."""

        if self._handle is None:
            raise RuntimeError("Windows backend is not active")
        poll_before_deadline = True
        drain_partial = False
        partial_drain_batches = 0
        while True:
            event = self._decoder.pop()
            if event is not None:
                return event
            now = self._ops.monotonic()
            if (
                not poll_before_deadline
                and not drain_partial
                and deadline is not None
                and now >= deadline
            ):
                return None
            milliseconds = self._wait_milliseconds(deadline, now)
            result = self._ops.wait(self._handle, milliseconds)
            using_partial_drain = drain_partial
            poll_before_deadline = False
            drain_partial = False
            if result == _WAIT_TIMEOUT:
                continue
            if result != _WAIT_OBJECT_0:
                raise OSError(f"unexpected WaitForSingleObject result: {result:#x}")
            records = self._ops.read_records(self._handle, _READ_BATCH_SIZE)
            if not records:
                raise OSError("ReadConsoleInputW returned no records")
            for record in records:
                if record is not None:
                    self._decoder.feed(record)
            if using_partial_drain:
                partial_drain_batches += 1
            drain_partial = (
                self._decoder.has_partial
                and partial_drain_batches < _PARTIAL_DRAIN_BATCH_LIMIT
            )

    def restore(self) -> None:
        """Release private lifecycle state without closing or mutating the borrowed handle."""

        self._handle = None

    @staticmethod
    def _wait_milliseconds(deadline: float | None, now: float) -> int:
        """Convert the remaining absolute deadline into one bounded DWORD wait."""

        if deadline is None:
            return _WAIT_SLICE_MS
        remaining = deadline - now
        if remaining <= 0:
            return 0
        bounded = min(remaining, _WAIT_SLICE_MS / 1000.0)
        return max(1, math.ceil(bounded * 1000.0))

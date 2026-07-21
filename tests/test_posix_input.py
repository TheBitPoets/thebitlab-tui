"""Injected-operation tests for the private POSIX input backend."""

from __future__ import annotations

import copy
import sys
from dataclasses import dataclass, field
from io import UnsupportedOperation

import pytest

from thebitlab_tui import Key, KeyEvent, KeyReader
from thebitlab_tui import terminal
from thebitlab_tui._posix_input import _PosixInputBackend, _PosixOps


class FakeStream:
    encoding = "utf-8"

    def fileno(self) -> int:
        return 7


@dataclass
class Harness:
    """Supply deterministic termios, readiness, read, and clock operations."""

    tty: bool = True
    attributes: list[object] = field(
        default_factory=lambda: [1, 2, 3, 0b1111, 5, 6, [b"a", b"b", b"c", b"d"]]
    )
    ready: list[bool | BaseException] = field(default_factory=list)
    reads: list[bytes | BaseException] = field(default_factory=list)
    now: float = 10.0
    set_errors: list[BaseException | None] = field(default_factory=list)
    set_calls: list[tuple[int, int, list[object]]] = field(default_factory=list)
    timeouts: list[float | None] = field(default_factory=list)
    select_interrupt_advance: float = 0.0
    read_interrupt_advance: float = 0.0

    def ops(self, *, stream: FakeStream | None = None) -> _PosixOps:
        return _PosixOps(
            stream=FakeStream() if stream is None else stream,  # type: ignore[arg-type]
            isatty=lambda fd: self.tty,
            tcgetattr=lambda fd: copy.deepcopy(self.attributes),
            tcsetattr=self.tcsetattr,
            select=self.select,
            read=self.read,
            monotonic=lambda: self.now,
            tcsanow=99,
            echo=0b0001,
            icanon=0b0010,
            vmin=0,
            vtime=1,
        )

    def tcsetattr(self, fd: int, when: int, attributes: list[object]) -> None:
        self.set_calls.append((fd, when, copy.deepcopy(attributes)))
        if self.set_errors:
            error = self.set_errors.pop(0)
            if error is not None:
                raise error

    def select(
        self,
        read: list[int],
        write: list[int],
        errors: list[int],
        timeout: float | None,
    ) -> tuple[list[int], list[int], list[int]]:
        self.timeouts.append(timeout)
        result = self.ready.pop(0) if self.ready else False
        if isinstance(result, BaseException):
            self.now += self.select_interrupt_advance
            raise result
        if timeout is not None and not result:
            self.now += timeout
        return ([7] if result else [], [], [])

    def read(self, fd: int, size: int) -> bytes:
        result = self.reads.pop(0)
        if isinstance(result, BaseException):
            self.now += self.read_interrupt_advance
            raise result
        return result


def test_activation_applies_conservative_cbreak_and_restores_exactly() -> None:
    harness = Harness()
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    original = copy.deepcopy(harness.attributes)

    backend.activate()
    active = harness.set_calls[0]
    assert active[0:2] == (7, 99)
    changed = active[2]
    assert changed[:3] == original[:3]
    assert changed[3] == original[3] & ~0b0011
    assert changed[4:6] == original[4:6]
    assert changed[6] == [1, 0, b"c", b"d"]
    assert original == harness.attributes

    backend.restore()
    assert harness.set_calls[1] == (7, 99, original)


def test_non_tty_is_rejected_before_snapshot_or_mutation() -> None:
    harness = Harness(tty=False)
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    with pytest.raises(UnsupportedOperation, match="not an interactive TTY"):
        backend.activate()
    assert harness.set_calls == []


def test_setup_failure_compensates_and_preserves_primary_error() -> None:
    harness = Harness(set_errors=[OSError("setup"), OSError("restore")])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    with pytest.raises(OSError, match="setup") as caught:
        backend.activate()
    assert len(harness.set_calls) == 2
    if sys.version_info >= (3, 11):
        assert "restore" in caught.value.__notes__[0]


def test_restore_failure_retains_snapshot_for_retry() -> None:
    harness = Harness(set_errors=[None, OSError("restore"), None])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    with pytest.raises(OSError, match="restore"):
        backend.restore()
    backend.restore()
    assert len(harness.set_calls) == 3


def test_read_returns_one_event_and_latches_eof() -> None:
    harness = Harness(ready=[True, True], reads=[b"xy", b""])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(None) == KeyEvent(Key.CHARACTER, "x")
    assert backend.read(None) == KeyEvent(Key.CHARACTER, "y")
    with pytest.raises(EOFError):
        backend.read(None)
    with pytest.raises(EOFError):
        backend.read(None)


def test_partial_text_is_discarded_when_eof_is_latched() -> None:
    harness = Harness(ready=[True, True], reads=[b"\xc3", b""])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    with pytest.raises(EOFError):
        backend.read(None)
    with pytest.raises(EOFError):
        backend.read(None)


def test_unbounded_read_passes_no_timeout_to_select() -> None:
    harness = Harness(ready=[True], reads=[b"x"])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(None) == KeyEvent(Key.CHARACTER, "x")
    assert harness.timeouts == [None]


def test_zero_deadline_drains_ready_arrow_before_expiring() -> None:
    harness = Harness(
        ready=[True, True, True], reads=[b"\x1b", b"[", b"A"]
    )
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.0) == KeyEvent(Key.UP)
    assert harness.timeouts == [0.0, 0.0, 0.0]


def test_zero_deadline_drains_ready_multibyte_character() -> None:
    harness = Harness(ready=[True, True], reads=[b"\xc3", b"\xa0"])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.0) == KeyEvent(Key.CHARACTER, "à")
    assert harness.timeouts == [0.0, 0.0]


def test_expired_deadline_does_not_drain_ignored_input_forever() -> None:
    sentinel = AssertionError("ignored input was over-drained")
    harness = Harness(ready=[True, True], reads=[b"\x00", sentinel])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.0) is None
    assert harness.reads == [sentinel]
    assert harness.timeouts == [0.0]


def test_interrupted_initial_poll_does_not_restart_expired_deadline() -> None:
    sentinel = AssertionError("deadline was restarted after interruption")
    harness = Harness(ready=[InterruptedError(), True], reads=[sentinel])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.0) is None
    assert harness.reads == [sentinel]
    assert harness.timeouts == [0.0]


def test_outer_deadline_returns_none_and_preserves_pending_escape() -> None:
    harness = Harness(ready=[True, False, False], reads=[b"\x1b"])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.01) is None
    assert backend.read(10.05) == KeyEvent(Key.ESCAPE)


def test_expired_escape_precedes_newly_ready_text_on_later_read() -> None:
    harness = Harness(ready=[True, False, True], reads=[b"\x1b", b"x"])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.01) is None
    harness.now = 11.0
    assert backend.read(11.0) == KeyEvent(Key.ESCAPE)
    assert backend.read(11.0) == KeyEvent(Key.CHARACTER, "x")


def test_select_interruption_cannot_bypass_escape_expiry() -> None:
    harness = Harness(ready=[True, False], reads=[b"\x1b"])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.01) is None

    harness.now = 10.04
    harness.select_interrupt_advance = 0.02
    harness.ready.extend([InterruptedError(), True])
    harness.reads.append(b"x")
    assert backend.read(11.0) == KeyEvent(Key.ESCAPE)
    assert backend.read(11.0) == KeyEvent(Key.CHARACTER, "x")


def test_ready_continuation_survives_repeated_interruptions() -> None:
    harness = Harness(ready=[True, False], reads=[b"\x1b"])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.01) is None

    harness.now = 10.04
    harness.read_interrupt_advance = 0.02
    harness.ready.extend([True, InterruptedError(), True])
    harness.reads.extend([InterruptedError(), b"[A"])
    assert backend.read(11.0) == KeyEvent(Key.UP)


def test_interrupted_select_and_read_do_not_reset_deadline() -> None:
    harness = Harness(
        ready=[InterruptedError(), True, False],
        reads=[InterruptedError(), b"x"],
    )
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    assert backend.read(10.1) is None
    assert harness.timeouts[0] == pytest.approx(0.1)
    assert harness.timeouts[1] == pytest.approx(0.1)


@pytest.mark.parametrize("failure_at", ["select", "read"])
def test_operating_system_read_failures_propagate(failure_at: str) -> None:
    if failure_at == "select":
        harness = Harness(ready=[OSError("select failed")])
    else:
        harness = Harness(ready=[True], reads=[OSError("read failed")])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    backend.activate()
    with pytest.raises(OSError, match=f"{failure_at} failed"):
        backend.read(10.1)


@pytest.mark.parametrize("body_error", [RuntimeError("body"), KeyboardInterrupt()])
def test_public_reader_restores_posix_state_after_body_control_flow(
    monkeypatch: pytest.MonkeyPatch, body_error: BaseException
) -> None:
    harness = Harness()
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    monkeypatch.setattr(terminal, "_create_backend", lambda escape_timeout: backend)
    with pytest.raises(type(body_error)):
        with KeyReader():
            raise body_error
    assert harness.set_calls[-1][2] == harness.attributes


def test_public_reader_selects_injected_posix_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    harness = Harness(ready=[True], reads=[b"x"])
    backend = _PosixInputBackend(0.05, ops=harness.ops())
    monkeypatch.setattr(terminal, "_create_backend", lambda escape_timeout: backend)
    with KeyReader() as reader:
        assert reader.read(0) == KeyEvent(Key.CHARACTER, "x")
    assert len(harness.set_calls) == 2


def test_unsupported_platform_factory_stays_lazy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(terminal.sys, "platform", "win32")
    with pytest.raises(UnsupportedOperation, match="not implemented for this platform"):
        KeyReader().__enter__()

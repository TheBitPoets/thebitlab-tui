"""Deterministic tests for the shared :class:`KeyReader` facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from io import UnsupportedOperation
import inspect
import sys

import pytest

from thebitlab_tui import Key, KeyEvent, KeyReader
from thebitlab_tui import terminal
from thebitlab_tui._input import _EventQueue


@dataclass
class FakeBackend:
    """Record facade calls while returning injected events and errors."""

    events: list[KeyEvent | None | BaseException] = field(default_factory=list)
    activation_error: BaseException | None = None
    restore_error: BaseException | None = None
    activated: int = 0
    restored: int = 0
    deadlines: list[float | None] = field(default_factory=list)

    def activate(self) -> None:
        self.activated += 1
        if self.activation_error is not None:
            raise self.activation_error

    def read(self, deadline: float | None) -> KeyEvent | None:
        self.deadlines.append(deadline)
        if not self.events:
            return None
        result = self.events.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result

    def restore(self) -> None:
        self.restored += 1
        if self.restore_error is not None:
            raise self.restore_error


def install_backend(monkeypatch: pytest.MonkeyPatch, backend: FakeBackend) -> None:
    """Install one fake backend without adding a public injection API."""

    monkeypatch.setattr(terminal, "_create_backend", lambda escape_timeout: backend)


def test_public_signatures_match_the_approved_contract() -> None:
    constructor = inspect.signature(KeyReader).parameters
    assert tuple(constructor) == ("escape_timeout",)
    assert constructor["escape_timeout"].kind is inspect.Parameter.KEYWORD_ONLY
    assert constructor["escape_timeout"].default == 0.05

    enter = inspect.signature(KeyReader.__enter__).parameters
    assert tuple(enter) == ("self",)

    read = inspect.signature(KeyReader.read).parameters
    assert tuple(read) == ("self", "timeout")
    assert read["timeout"].default is None

    exit_parameters = inspect.signature(KeyReader.__exit__).parameters
    assert tuple(exit_parameters) == ("self", "exc_type", "exc", "traceback")


def test_private_event_queue_preserves_order_and_one_event_per_pop() -> None:
    queue = _EventQueue()
    first = KeyEvent(Key.UP)
    second = KeyEvent(Key.CHARACTER, "x")
    third = KeyEvent(Key.TAB)

    assert queue.pop() is None
    queue.push(first)
    queue.extend([second, third])
    assert queue.pop() == first
    assert queue.pop() == second
    assert queue.pop() == third
    assert queue.pop() is None


@pytest.mark.parametrize("value", [0.05, 1, 0.0001])
def test_escape_timeout_accepts_positive_finite_values(value: float) -> None:
    KeyReader(escape_timeout=value)


@pytest.mark.parametrize(
    "value",
    [
        0,
        -0.1,
        float("inf"),
        -float("inf"),
        float("nan"),
        pytest.param(10**10000, id="overflowing-int"),
    ],
)
def test_escape_timeout_rejects_non_positive_or_non_finite_values(value: float) -> None:
    with pytest.raises(ValueError, match="escape_timeout must be positive and finite"):
        KeyReader(escape_timeout=value)


def test_construction_has_no_backend_side_effect(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(escape_timeout: float) -> FakeBackend:
        raise AssertionError(f"unexpected activation for {escape_timeout}")

    monkeypatch.setattr(terminal, "_create_backend", fail_if_called)
    KeyReader()


def test_context_identity_lifecycle_and_fifo_order(monkeypatch: pytest.MonkeyPatch) -> None:
    first = KeyEvent(Key.UP)
    second = KeyEvent(Key.CHARACTER, "x")
    backend = FakeBackend(events=[first, second, None])
    install_backend(monkeypatch, backend)

    reader = KeyReader()
    with pytest.raises(RuntimeError, match="not active"):
        reader.read()

    with reader as entered:
        assert entered is reader
        with pytest.raises(RuntimeError, match="single-use"):
            reader.__enter__()
        assert reader.read() == first
        assert reader.read() == second
        assert reader.read() is None

    assert backend.activated == 1
    assert backend.restored == 1
    with pytest.raises(RuntimeError, match="not active"):
        reader.read()
    with pytest.raises(RuntimeError, match="single-use"):
        reader.__enter__()


@pytest.mark.parametrize("timeout", [None, 0, 0.25])
def test_read_passes_one_absolute_deadline(
    monkeypatch: pytest.MonkeyPatch, timeout: float | None
) -> None:
    backend = FakeBackend()
    install_backend(monkeypatch, backend)
    clock_calls = iter([100.0])
    monkeypatch.setattr(terminal.time, "monotonic", lambda: next(clock_calls))

    with KeyReader() as reader:
        assert reader.read(timeout) is None

    assert backend.deadlines == [None if timeout is None else 100.0 + timeout]


@pytest.mark.parametrize(
    "timeout",
    [
        -0.1,
        float("inf"),
        -float("inf"),
        float("nan"),
        pytest.param(10**10000, id="overflowing-int"),
    ],
)
def test_read_rejects_invalid_timeout(
    monkeypatch: pytest.MonkeyPatch, timeout: float
) -> None:
    backend = FakeBackend()
    install_backend(monkeypatch, backend)

    with KeyReader() as reader:
        with pytest.raises(ValueError, match="timeout must be non-negative and finite"):
            reader.read(timeout)
    assert backend.deadlines == []


def test_zero_deadline_still_delegates_to_buffered_backend(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = KeyEvent(Key.ENTER)
    backend = FakeBackend(events=[event])
    install_backend(monkeypatch, backend)
    monkeypatch.setattr(terminal.time, "monotonic", lambda: 25.0)

    with KeyReader() as reader:
        assert reader.read(0) == event
    assert backend.deadlines == [25.0]


def test_failed_activation_consumes_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = FakeBackend(activation_error=OSError("activation failed"))
    install_backend(monkeypatch, backend)
    reader = KeyReader()

    with pytest.raises(OSError, match="activation failed"):
        reader.__enter__()
    with pytest.raises(RuntimeError, match="single-use"):
        reader.__enter__()
    with pytest.raises(RuntimeError, match="not active"):
        reader.read()


def test_body_exception_is_not_suppressed(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = FakeBackend()
    install_backend(monkeypatch, backend)

    with pytest.raises(LookupError, match="body failed"):
        with KeyReader():
            raise LookupError("body failed")
    assert backend.restored == 1


def test_normal_restore_failure_propagates(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = FakeBackend(restore_error=OSError("restore failed"))
    install_backend(monkeypatch, backend)
    reader = KeyReader()

    with pytest.raises(OSError, match="restore failed"):
        with reader:
            pass
    with pytest.raises(RuntimeError, match="single-use"):
        reader.__enter__()


def test_body_error_remains_primary_when_restore_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = FakeBackend(restore_error=OSError("restore failed"))
    install_backend(monkeypatch, backend)

    with pytest.raises(ValueError, match="body failed") as caught:
        with KeyReader():
            raise ValueError("body failed")
    if sys.version_info >= (3, 11):
        assert caught.value.__notes__ == [
            "terminal restoration also failed: OSError('restore failed')"
        ]


@pytest.mark.parametrize("restore_error", [KeyboardInterrupt(), SystemExit(2)])
def test_control_flow_from_restore_is_not_suppressed_by_body_error(
    monkeypatch: pytest.MonkeyPatch, restore_error: BaseException
) -> None:
    backend = FakeBackend(restore_error=restore_error)
    install_backend(monkeypatch, backend)

    with pytest.raises(type(restore_error)):
        with KeyReader():
            raise ValueError("body failed")


@pytest.mark.parametrize("restore_error", [KeyboardInterrupt(), SystemExit(2)])
def test_control_flow_from_restore_propagates_on_normal_exit(
    monkeypatch: pytest.MonkeyPatch, restore_error: BaseException
) -> None:
    backend = FakeBackend(restore_error=restore_error)
    install_backend(monkeypatch, backend)

    with pytest.raises(type(restore_error)):
        with KeyReader():
            pass


@pytest.mark.parametrize(
    "error",
    [EOFError("eof"), OSError("read failed"), KeyboardInterrupt(), SystemExit(2)],
)
def test_read_errors_propagate_and_context_restores(
    monkeypatch: pytest.MonkeyPatch, error: BaseException
) -> None:
    backend = FakeBackend(events=[error])
    install_backend(monkeypatch, backend)

    with pytest.raises(type(error)):
        with KeyReader() as reader:
            reader.read()
    assert backend.restored == 1


def test_backend_factory_is_lazy_and_unavailable_until_platform_slice() -> None:
    reader = KeyReader()
    with pytest.raises(UnsupportedOperation, match="not implemented yet"):
        reader.__enter__()
    with pytest.raises(RuntimeError, match="single-use"):
        reader.__enter__()

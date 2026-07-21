"""Thin, optional terminal policy helpers; no event loop or drawing."""

from __future__ import annotations

import os
import shutil
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import Enum, auto
from io import UnsupportedOperation
from math import isfinite
from types import TracebackType
from typing import TextIO

try:  # Python 3.10 is useful for local development; the supported runtime starts at Python 3.11.
    from typing import Self
except ImportError:  # pragma: no cover - exercised only below the supported runtime
    from typing import TypeVar

    Self = TypeVar("Self")

from ._input import _InputBackend
from .events import KeyEvent


class _ReaderState(Enum):
    """Private lifecycle states for :class:`KeyReader`."""

    NEW = auto()
    ACTIVE = auto()
    EXITED = auto()


def _create_backend(escape_timeout: float) -> _InputBackend:
    """Create the platform backend when its bounded implementation slice lands."""

    del escape_timeout
    raise UnsupportedOperation("terminal input backends are not implemented yet")


def _validate_duration(value: float, *, positive: bool, name: str) -> float:
    """Return a finite duration or raise the public timeout error."""

    qualifier = "positive and finite" if positive else "non-negative and finite"
    try:
        duration = float(value)
    except OverflowError:
        raise ValueError(f"{name} must be {qualifier}") from None
    if not isfinite(duration) or duration < 0 or (positive and duration == 0):
        raise ValueError(f"{name} must be {qualifier}")
    return duration


class KeyReader:
    """Read normalized terminal keys through a single-use context manager.

    Args:
        escape_timeout: Positive finite ambiguity window, in seconds, used by platform decoders.

    Raises:
        ValueError: If ``escape_timeout`` cannot represent a positive finite duration, including
            zero, negative, infinite, NaN, and overflow-sized values.

    Construction validates scalar arguments but does not inspect or mutate a terminal.  Entering
    selects and activates a private platform backend.  The POSIX and Windows backends are delivered
    by later Phase 3 slices; until then, entering raises ``io.UnsupportedOperation``.

    Instances are neither reusable nor thread-safe.  The application owns its event loop, commands,
    resize handling, state updates, and redraws.
    """

    def __init__(self, *, escape_timeout: float = 0.05) -> None:
        self._escape_timeout = _validate_duration(
            escape_timeout, positive=True, name="escape_timeout"
        )
        self._state = _ReaderState.NEW
        self._backend: _InputBackend | None = None

    def __enter__(self) -> Self:
        """Activate input and return this exact facade instance.

        Raises:
            RuntimeError: If this reader has already entered or attempted activation.
            UnsupportedOperation: If no backend supports the current input environment.
            OSError: If backend activation fails.
        """

        if self._state is not _ReaderState.NEW:
            raise RuntimeError("KeyReader instances are single-use")

        # Mark the instance consumed before any operation that can fail.  A failed setup attempt is
        # permanently exited, matching the restoration boundary promised by the public contract.
        self._state = _ReaderState.EXITED
        backend = _create_backend(self._escape_timeout)
        self._backend = backend
        backend.activate()
        self._state = _ReaderState.ACTIVE
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        """Restore backend state without suppressing an exception from the context body.

        If restoration also fails while another exception is active, the active exception remains
        primary and receives a note describing the restoration failure.  A restoration failure on
        normal exit propagates normally.
        """

        del exc_type, traceback
        if self._state is not _ReaderState.ACTIVE or self._backend is None:
            raise RuntimeError("KeyReader is not active")

        backend = self._backend
        self._state = _ReaderState.EXITED
        try:
            backend.restore()
        except OSError as restore_error:
            if exc is None:
                raise
            if hasattr(exc, "add_note"):
                exc.add_note(f"terminal restoration also failed: {restore_error!r}")
        return False

    def read(self, timeout: float | None = None) -> KeyEvent | None:
        """Return at most one normalized key before a total deadline.

        Args:
            timeout: ``None`` to wait, zero to poll, or a positive finite number of seconds.

        Returns:
            One event, or ``None`` when no complete supported event is available by the deadline.

        Raises:
            RuntimeError: If the reader is not inside its active context.
            ValueError: If ``timeout`` is negative, infinite, or NaN.
            EOFError: If a future POSIX backend reaches end of input.
            OSError: If a backend readiness or read operation fails.
        """

        if self._state is not _ReaderState.ACTIVE or self._backend is None:
            raise RuntimeError("KeyReader is not active")

        deadline: float | None = None
        if timeout is not None:
            duration = _validate_duration(timeout, positive=False, name="timeout")
            deadline = time.monotonic() + duration
        return self._backend.read(deadline)


@dataclass(frozen=True, slots=True)
class TerminalSize:
    """Current terminal width and height in cells.

    Args:
        width: Number of columns, clamped to at least one by :func:`get_terminal_size`.
        height: Number of rows, clamped to at least one by :func:`get_terminal_size`.
    """

    width: int
    height: int


def get_terminal_size(fallback: tuple[int, int] = (80, 24)) -> TerminalSize:
    """Read the terminal size and clamp both dimensions to at least one.

    Args:
        fallback: Width and height used when the OS cannot report a terminal size.
    """

    size = shutil.get_terminal_size(fallback)
    return TerminalSize(max(1, size.columns), max(1, size.lines))


class ResizeWatcher:
    """Detect size changes by polling an injectable size reader.

    Args:
        reader: Injectable size reader used by :meth:`poll`.

    The first :meth:`poll` returns the initial size; unchanged subsequent polls return ``None``.
    """

    def __init__(self, reader: Callable[[], TerminalSize] = get_terminal_size) -> None:
        self._reader = reader
        self._last: TerminalSize | None = None

    def poll(self) -> TerminalSize | None:
        """Return the new size when it differs from the preceding poll."""

        current = self._reader()
        if current == self._last:
            return None
        self._last = current
        return current


def supports_color(
    *,
    no_color: bool = False,
    stream: TextIO | None = None,
    environ: Mapping[str, str] | None = None,
    platform: str | None = None,
) -> bool:
    """Apply a conservative ANSI policy on Linux and Windows.

    Args:
        no_color: Explicitly disable ANSI output.
        stream: Output stream used for the TTY check; defaults to standard output.
        environ: Injectable environment mapping; defaults to ``os.environ``.
        platform: Injectable platform name; defaults to ``sys.platform``.

    Returns:
        ``True`` only when ANSI output is allowed and plausibly supported.
    """

    if no_color:
        return False
    env = os.environ if environ is None else environ
    if "NO_COLOR" in env:
        return False
    output = sys.stdout if stream is None else stream
    if not output.isatty():
        return False
    current_platform = sys.platform if platform is None else platform
    if current_platform == "win32":
        return any(key in env for key in ("WT_SESSION", "ANSICON", "TERM_PROGRAM"))
    return env.get("TERM") != "dumb"

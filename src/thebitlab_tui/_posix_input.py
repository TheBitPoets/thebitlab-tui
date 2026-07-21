"""Private POSIX TTY backend with injectable operating-system operations."""

from __future__ import annotations

import copy
import sys
from collections.abc import Callable
from dataclasses import dataclass
from io import UnsupportedOperation
from typing import Any, BinaryIO

from ._posix_decoder import _PosixDecoder, _validated_codec
from .events import KeyEvent


@dataclass(frozen=True, slots=True)
class _PosixOps:
    """Injected POSIX operations and termios constants."""

    stream: BinaryIO
    isatty: Callable[[int], bool]
    tcgetattr: Callable[[int], list[Any]]
    tcsetattr: Callable[[int, int, list[Any]], None]
    select: Callable[
        [list[int], list[int], list[int], float | None],
        tuple[list[int], list[int], list[int]],
    ]
    read: Callable[[int, int], bytes]
    monotonic: Callable[[], float]
    tcsanow: int
    echo: int
    icanon: int
    vmin: int
    vtime: int


def _default_ops() -> _PosixOps:
    """Load POSIX-only modules lazily after platform selection."""

    import os
    import select
    import termios
    import time

    return _PosixOps(
        stream=sys.stdin,  # type: ignore[arg-type]
        isatty=os.isatty,
        tcgetattr=termios.tcgetattr,
        tcsetattr=termios.tcsetattr,
        select=select.select,
        read=os.read,
        monotonic=time.monotonic,
        tcsanow=termios.TCSANOW,
        echo=termios.ECHO,
        icanon=termios.ICANON,
        vmin=termios.VMIN,
        vtime=termios.VTIME,
    )


class _PosixInputBackend:
    """Read normalized events from one borrowed interactive POSIX descriptor."""

    def __init__(self, escape_timeout: float, *, ops: _PosixOps | None = None) -> None:
        self._escape_timeout = escape_timeout
        self._ops = _default_ops() if ops is None else ops
        self._fd: int | None = None
        self._saved: list[Any] | None = None
        self._decoder: _PosixDecoder | None = None
        self._eof = False

    def activate(self) -> None:
        """Validate input, snapshot attributes, and enter conservative cbreak mode."""

        try:
            fd = self._ops.stream.fileno()
        except (AttributeError, OSError, ValueError) as error:
            raise UnsupportedOperation(
                "standard input has no usable descriptor"
            ) from error
        if not self._ops.isatty(fd):
            raise UnsupportedOperation("standard input is not an interactive TTY")

        encoding = _validated_codec(getattr(self._ops.stream, "encoding", None))
        decoder = _PosixDecoder(encoding, self._escape_timeout)
        saved = copy.deepcopy(self._ops.tcgetattr(fd))
        changed = copy.deepcopy(saved)
        changed[3] &= ~(self._ops.echo | self._ops.icanon)
        changed[6][self._ops.vmin] = 1
        changed[6][self._ops.vtime] = 0

        self._fd = fd
        self._saved = saved
        self._decoder = decoder
        try:
            self._ops.tcsetattr(fd, self._ops.tcsanow, changed)
        except BaseException as activation_error:
            try:
                self._ops.tcsetattr(fd, self._ops.tcsanow, saved)
            except OSError as restore_error:
                if hasattr(activation_error, "add_note"):
                    activation_error.add_note(
                        f"terminal restoration also failed: {restore_error!r}"
                    )
            else:
                self._saved = None
            raise

    def read(self, deadline: float | None) -> KeyEvent | None:
        """Return one event before an absolute caller or Escape deadline."""

        if self._fd is None or self._decoder is None:
            raise RuntimeError("POSIX backend is not active")
        poll_before_deadline = True
        drain_before_expiry = False
        while True:
            event = self._decoder.pop()
            if event is not None:
                return event
            if self._eof:
                raise EOFError("terminal input reached EOF")

            now = self._ops.monotonic()
            escape_deadline = self._decoder.escape_deadline
            if (
                not drain_before_expiry
                and escape_deadline is not None
                and now >= escape_deadline
            ):
                self._decoder.expire(now)
                event = self._decoder.pop()
                if event is not None:
                    return event
            if (
                not poll_before_deadline
                and not drain_before_expiry
                and deadline is not None
                and now >= deadline
            ):
                return None
            effective = self._earliest(deadline, escape_deadline)
            timeout = None if effective is None else max(0.0, effective - now)
            try:
                ready, _, _ = self._ops.select([self._fd], [], [], timeout)
            except InterruptedError:
                continue
            poll_before_deadline = False
            drain_before_expiry = False

            if ready:
                try:
                    data = self._ops.read(self._fd, 4096)
                except InterruptedError:
                    drain_before_expiry = True
                    continue
                if not data:
                    self._eof = True
                    self._decoder.discard_partial()
                    event = self._decoder.pop()
                    if event is not None:
                        return event
                    raise EOFError("terminal input reached EOF")
                self._decoder.feed(data, self._ops.monotonic())
                drain_before_expiry = self._decoder.has_partial
                continue

            now = self._ops.monotonic()
            if escape_deadline is not None and now >= escape_deadline:
                self._decoder.expire(now)
                event = self._decoder.pop()
                if event is not None:
                    return event
            if deadline is not None and now >= deadline:
                return None

    def restore(self) -> None:
        """Restore the exact saved attributes; retain them when restoration fails."""

        if self._fd is None or self._saved is None:
            return
        self._ops.tcsetattr(self._fd, self._ops.tcsanow, self._saved)
        self._saved = None

    @staticmethod
    def _earliest(first: float | None, second: float | None) -> float | None:
        if first is None:
            return second
        if second is None:
            return first
        return min(first, second)

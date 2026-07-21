"""Private contracts shared by terminal input backends.

This module deliberately exposes no public API.  Platform implementations use the structural
backend contract while :class:`thebitlab_tui.terminal.KeyReader` owns lifecycle and deadlines.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from typing import Protocol

from .events import KeyEvent


class _InputBackend(Protocol):
    """Structural contract implemented by private platform input backends."""

    def activate(self) -> None:
        """Acquire backend state and prepare input without returning an event.

        A backend that fails after changing caller-owned state must attempt its own compensating
        restoration.  The activation error remains primary and a restoration ``OSError`` is added
        as a note.  The facade cannot safely infer whether activation reached that point.
        """

    def read(self, deadline: float | None) -> KeyEvent | None:
        """Return at most one event before an absolute monotonic deadline."""

    def restore(self) -> None:
        """Restore every piece of caller-owned state changed by :meth:`activate`."""


class _EventQueue:
    """Small FIFO used by private decoders when one input unit yields later events."""

    def __init__(self) -> None:
        self._events: deque[KeyEvent] = deque()

    def push(self, event: KeyEvent) -> None:
        """Append one normalized event."""

        self._events.append(event)

    def extend(self, events: Iterable[KeyEvent]) -> None:
        """Append normalized events in source order."""

        self._events.extend(events)

    def pop(self) -> KeyEvent | None:
        """Remove the oldest event, or return ``None`` when empty."""

        if not self._events:
            return None
        return self._events.popleft()

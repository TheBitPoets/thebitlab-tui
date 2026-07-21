"""Pure console-record decoding for the private Windows input backend.

The module deliberately contains no ``ctypes`` or operating-system calls.  A
platform backend translates ``KEY_EVENT_RECORD`` values into the small private
record below, while this decoder owns normalization, UTF-16 state, repeats,
and event ordering.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from .events import Key, KeyEvent


_RIGHT_ALT_PRESSED = 0x0001
_LEFT_ALT_PRESSED = 0x0002
_RIGHT_CTRL_PRESSED = 0x0004
_LEFT_CTRL_PRESSED = 0x0008
_SHIFT_PRESSED = 0x0010

_VK_TAB = 0x09
_VK_RETURN = 0x0D
_VK_ESCAPE = 0x1B
_VK_LEFT = 0x25
_VK_UP = 0x26
_VK_RIGHT = 0x27
_VK_DOWN = 0x28
_VK_A = 0x41
_VK_C = 0x43
_VK_Z = 0x5A

_SEMANTIC_VIRTUAL_KEYS = {
    _VK_TAB: Key.TAB,
    _VK_RETURN: Key.ENTER,
    _VK_ESCAPE: Key.ESCAPE,
    _VK_LEFT: Key.LEFT,
    _VK_UP: Key.UP,
    _VK_RIGHT: Key.RIGHT,
    _VK_DOWN: Key.DOWN,
}

_SEMANTIC_TEXT_UNITS = {
    0x09: Key.TAB,
    0x0A: Key.ENTER,
    0x0D: Key.ENTER,
    0x1B: Key.ESCAPE,
}


@dataclass(frozen=True, slots=True)
class _WindowsKeyRecord:
    """Platform-independent fields copied from one ``KEY_EVENT_RECORD``.

    Args:
        key_down: Whether this is a key-down record.
        repeat_count: Number of identical logical events represented by the
            record.  Zero is malformed and is consumed.
        virtual_key: Win32 virtual-key code.
        unicode_unit: One unsigned UTF-16 code unit from ``UnicodeChar``.
        control_state: Raw ``dwControlKeyState`` flags.
    """

    key_down: bool
    repeat_count: int
    virtual_key: int
    unicode_unit: int
    control_state: int = 0


@dataclass(frozen=True, slots=True)
class _Modifiers:
    """Relevant modifier flags derived exactly from a console record."""

    ctrl: bool
    alt: bool
    shift: bool


@dataclass(slots=True)
class _EventRun:
    """One normalized event and its unexpanded remaining repeat count."""

    event: KeyEvent
    remaining: int


@dataclass(frozen=True, slots=True)
class _PendingHighSurrogate:
    """High-surrogate state retained until the next logical key-down unit."""

    unit: int
    modifiers: _Modifiers
    repeat_count: int


class _WindowsRecordDecoder:
    """Normalize private Windows key records without performing console I/O.

    The decoder returns at most one event from :meth:`pop`.  Positive repeat
    counts remain compressed as private runs.  A high UTF-16 surrogate remains
    pending across calls and ignored records; only a matching low surrogate
    with identical relevant modifiers and repeat count completes it.
    """

    def __init__(self) -> None:
        self._runs: deque[_EventRun] = deque()
        self._pending_high: _PendingHighSurrogate | None = None

    @property
    def has_partial(self) -> bool:
        """Return whether a high surrogate is waiting for its low half."""

        return self._pending_high is not None

    def feed(self, record: _WindowsKeyRecord) -> None:
        """Consume one translated key record and retain normalized events.

        Key-up records are ignored without disturbing a pending high
        surrogate. A malformed zero-repeat key-down discards partial text.
        Semantic virtual keys take priority; other positive key-down records
        complete, replace, or discard the pending surrogate deterministically.
        """

        if not record.key_down:
            return
        if record.repeat_count <= 0:
            self._pending_high = None
            return
        if not 0 <= record.unicode_unit <= 0xFFFF:
            self._pending_high = None
            return

        modifiers = self._modifiers(record.control_state)
        unit = record.unicode_unit

        handled, semantic_event = self._semantic_event(record, modifiers)
        if handled:
            self._pending_high = None
            if semantic_event is not None:
                self._runs.append(_EventRun(semantic_event, record.repeat_count))
            return

        if self._pending_high is not None:
            pending = self._pending_high
            self._pending_high = None
            if (
                self._is_low_surrogate(unit)
                and record.repeat_count == pending.repeat_count
                and modifiers == pending.modifiers
            ):
                scalar = chr(
                    0x10000
                    + ((pending.unit - 0xD800) << 10)
                    + (unit - 0xDC00)
                )
                self._queue_character(
                    scalar, pending.modifiers, pending.repeat_count
                )
                return
            if self._is_low_surrogate(unit):
                return

        if self._is_high_surrogate(unit):
            self._pending_high = _PendingHighSurrogate(
                unit, modifiers, record.repeat_count
            )
            return
        if self._is_low_surrogate(unit):
            return

        event = self._text_event(record, modifiers)
        if event is not None:
            self._runs.append(_EventRun(event, record.repeat_count))

    def pop(self) -> KeyEvent | None:
        """Return one event from the oldest run, or ``None`` when empty."""

        if not self._runs:
            return None
        run = self._runs[0]
        event = run.event
        run.remaining -= 1
        if run.remaining == 0:
            self._runs.popleft()
        return event

    def _semantic_event(
        self, record: _WindowsKeyRecord, modifiers: _Modifiers
    ) -> tuple[bool, KeyEvent | None]:
        unit = record.unicode_unit
        virtual_key = record.virtual_key

        if (
            modifiers.ctrl
            and virtual_key == _VK_C
            and unit in (0x00, 0x03, ord("c"), ord("C"))
        ):
            return True, None

        semantic = _SEMANTIC_VIRTUAL_KEYS.get(virtual_key)
        if semantic is not None:
            return True, self._event(semantic, modifiers)

        if virtual_key == 0:
            semantic = _SEMANTIC_TEXT_UNITS.get(unit)
            if semantic is not None:
                return True, self._event(semantic, modifiers)
        return False, None

    def _text_event(
        self, record: _WindowsKeyRecord, modifiers: _Modifiers
    ) -> KeyEvent | None:
        unit = record.unicode_unit
        virtual_key = record.virtual_key

        if unit != 0:
            character = chr(unit)
            if character.isprintable():
                return self._character_event(character, modifiers)

        if modifiers.ctrl and _VK_A <= virtual_key <= _VK_Z:
            expected_control = virtual_key - _VK_A + 1
            if unit in (0, expected_control):
                return self._character_event(
                    chr(ord("a") + virtual_key - _VK_A), modifiers
                )
        return None

    def _queue_character(
        self, character: str, modifiers: _Modifiers, repeat_count: int
    ) -> None:
        if character.isprintable():
            self._runs.append(
                _EventRun(
                    self._character_event(character, modifiers), repeat_count
                )
            )

    @staticmethod
    def _event(key: Key, modifiers: _Modifiers) -> KeyEvent:
        return KeyEvent(
            key,
            ctrl=modifiers.ctrl,
            alt=modifiers.alt,
            shift=modifiers.shift,
        )

    @staticmethod
    def _character_event(character: str, modifiers: _Modifiers) -> KeyEvent:
        return KeyEvent(
            Key.CHARACTER,
            character,
            ctrl=modifiers.ctrl,
            alt=modifiers.alt,
            shift=modifiers.shift,
        )

    @staticmethod
    def _modifiers(control_state: int) -> _Modifiers:
        return _Modifiers(
            ctrl=bool(
                control_state & (_LEFT_CTRL_PRESSED | _RIGHT_CTRL_PRESSED)
            ),
            alt=bool(control_state & (_LEFT_ALT_PRESSED | _RIGHT_ALT_PRESSED)),
            shift=bool(control_state & _SHIFT_PRESSED),
        )

    @staticmethod
    def _is_high_surrogate(unit: int) -> bool:
        return 0xD800 <= unit <= 0xDBFF

    @staticmethod
    def _is_low_surrogate(unit: int) -> bool:
        return 0xDC00 <= unit <= 0xDFFF

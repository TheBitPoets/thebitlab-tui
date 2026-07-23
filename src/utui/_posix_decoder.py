"""Pure byte decoding for the private POSIX terminal input backend."""

from __future__ import annotations

import codecs
from enum import Enum, auto
from io import UnsupportedOperation

from ._input import _EventQueue
from .events import Key, KeyEvent


_ARROWS = {
    ord("A"): Key.UP,
    ord("B"): Key.DOWN,
    ord("C"): Key.RIGHT,
    ord("D"): Key.LEFT,
}


def _validated_codec(encoding: str | None) -> str:
    """Return an ASCII-compatible codec name without mutating terminal state."""

    selected = encoding or "utf-8"
    info = codecs.lookup(selected)
    for value in range(0x80):
        try:
            decoder = info.incrementaldecoder(errors="strict")
            initial_state = decoder.getstate()
            text = decoder.decode(bytes((value,)), final=False)
            decoded_state = decoder.getstate()
            tail = decoder.decode(b"", final=True)
        except (AttributeError, TypeError, UnicodeError, ValueError) as error:
            raise UnsupportedOperation(
                "terminal input encoding must preserve ASCII bytes"
            ) from error
        if text != chr(value) or decoded_state != initial_state or tail != "":
            raise UnsupportedOperation(
                "terminal input encoding must preserve ASCII bytes"
            )
    return info.name


class _State(Enum):
    NORMAL = auto()
    ESCAPE = auto()
    CSI_PARAMETERS = auto()
    CSI_INTERMEDIATES = auto()
    SS3 = auto()
    ALT_TEXT = auto()


class _PosixDecoder:
    """Decode POSIX bytes deterministically without performing I/O."""

    def __init__(
        self, encoding: str, escape_timeout: float, *, control_limit: int = 64
    ) -> None:
        if control_limit < 3:
            raise ValueError("control_limit must be at least three")
        self._encoding = _validated_codec(encoding)
        self._decoder_factory = codecs.getincrementaldecoder(self._encoding)
        self._text_decoder = self._decoder_factory(errors="strict")
        self._alt_decoder = self._decoder_factory(errors="strict")
        self._escape_timeout = escape_timeout
        self._control_limit = control_limit
        self._state = _State.NORMAL
        self._escape_deadline: float | None = None
        self._control = bytearray()
        self._events = _EventQueue()

    @property
    def escape_deadline(self) -> float | None:
        """Return the active Escape ambiguity deadline, if any."""

        return self._escape_deadline

    @property
    def has_partial(self) -> bool:
        """Return whether more bytes can complete the current logical input unit."""

        return self._state is not _State.NORMAL or self._decoder_pending(
            self._text_decoder
        )

    def pop(self) -> KeyEvent | None:
        """Return the oldest complete event."""

        return self._events.pop()

    def feed(self, data: bytes, now: float) -> None:
        """Consume bytes; deadline expiry remains the backend's responsibility."""

        for value in data:
            self._feed_byte(value, now)

    def expire(self, now: float) -> None:
        """Resolve an Escape-related fragment whose grace period has elapsed."""

        if self._escape_deadline is None or now < self._escape_deadline:
            return
        if self._state is _State.ESCAPE:
            self._events.push(KeyEvent(Key.ESCAPE))
        self._reset_escape_state()

    def discard_partial(self) -> None:
        """Discard incomplete text and Escape fragments, retaining queued events."""

        self._text_decoder.reset()
        self._alt_decoder.reset()
        self._reset_escape_state()

    def _feed_byte(self, value: int, now: float) -> None:
        if self._state is _State.NORMAL:
            self._feed_normal(value, now)
        elif self._state is _State.ESCAPE:
            self._feed_escape(value, now)
        elif self._state in (_State.CSI_PARAMETERS, _State.CSI_INTERMEDIATES):
            self._feed_csi(value)
        elif self._state is _State.SS3:
            self._feed_ss3(value)
        else:
            self._feed_alt(value, now)

    def _feed_normal(self, value: int, now: float) -> None:
        if self._decoder_pending(self._text_decoder):
            text, suffix, _ = self._decode(self._text_decoder, value)
            self._emit_text(text)
            for replay in suffix:
                self._feed_normal(replay, now)
            return

        if value == 0x1B:
            self._start_escape(now)
        elif value in (0x0A, 0x0D):
            self._events.push(KeyEvent(Key.ENTER))
        elif value == 0x09:
            self._events.push(KeyEvent(Key.TAB))
        elif value == 0x03:
            return
        elif 0x01 <= value <= 0x1A:
            self._events.push(
                KeyEvent(Key.CHARACTER, chr(ord("a") + value - 1), ctrl=True)
            )
        elif value < 0x20 or value == 0x7F:
            return
        else:
            text, suffix, _ = self._decode(self._text_decoder, value)
            self._emit_text(text)
            for replay in suffix:
                self._feed_normal(replay, now)

    def _feed_escape(self, value: int, now: float) -> None:
        if value == ord("["):
            self._state = _State.CSI_PARAMETERS
            self._control = bytearray((0x1B, value))
        elif value == ord("O"):
            self._state = _State.SS3
            self._control = bytearray((0x1B, value))
        elif value == 0x1B:
            self._events.push(KeyEvent(Key.ESCAPE))
            self._start_escape(now)
        elif value in (0x09, 0x0A, 0x0D):
            self._events.push(KeyEvent(Key.ESCAPE))
            self._reset_escape_state()
            self._feed_normal(value, now)
        elif value < 0x20 or value == 0x7F:
            self._reset_escape_state()
        else:
            self._state = _State.ALT_TEXT
            self._alt_decoder.reset()
            self._feed_alt(value, now)

    def _feed_alt(self, value: int, now: float) -> None:
        text, suffix, malformed = self._decode(self._alt_decoder, value)
        if text:
            first, *remaining = text
            if self._supported_scalar(first):
                self._events.push(KeyEvent(Key.CHARACTER, first, alt=True))
            self._reset_escape_state()
            for scalar in remaining:
                if self._supported_scalar(scalar):
                    self._events.push(KeyEvent(Key.CHARACTER, scalar))
        elif malformed:
            self._reset_escape_state()
            for replay in suffix:
                self._feed_normal(replay, now)

    def _feed_csi(self, value: int) -> None:
        self._control.append(value)
        if len(self._control) > self._control_limit:
            self._reset_escape_state()
            return

        if self._state is _State.CSI_PARAMETERS:
            if 0x30 <= value <= 0x3F:
                return
            if 0x20 <= value <= 0x2F:
                self._state = _State.CSI_INTERMEDIATES
                return
            if 0x40 <= value <= 0x7E:
                if len(self._control) == 3 and value in _ARROWS:
                    self._events.push(KeyEvent(_ARROWS[value]))
                self._reset_escape_state()
                return
        elif 0x20 <= value <= 0x2F:
            return
        elif 0x40 <= value <= 0x7E:
            self._reset_escape_state()
            return
        self._reset_escape_state()

    def _feed_ss3(self, value: int) -> None:
        self._control.append(value)
        if 0x40 <= value <= 0x7E and value in _ARROWS:
            self._events.push(KeyEvent(_ARROWS[value]))
        self._reset_escape_state()

    def _start_escape(self, now: float) -> None:
        self._state = _State.ESCAPE
        self._escape_deadline = now + self._escape_timeout
        self._control = bytearray((0x1B,))
        self._alt_decoder.reset()

    def _reset_escape_state(self) -> None:
        self._state = _State.NORMAL
        self._escape_deadline = None
        self._control.clear()
        self._alt_decoder.reset()

    @staticmethod
    def _decoder_pending(decoder: object) -> bool:
        state = decoder.getstate()  # type: ignore[attr-defined]
        return bool(state[0]) if isinstance(state, tuple) else bool(state)

    @staticmethod
    def _decode(decoder: object, value: int) -> tuple[str, bytes, bool]:
        try:
            text = decoder.decode(  # type: ignore[attr-defined]
                bytes((value,)), final=False
            )
            return text, b"", False
        except UnicodeDecodeError as error:
            decoder.reset()  # type: ignore[attr-defined]
            return "", error.object[error.end :], True

    def _emit_text(self, text: str) -> None:
        for scalar in text:
            if self._supported_scalar(scalar):
                self._events.push(KeyEvent(Key.CHARACTER, scalar))

    @staticmethod
    def _supported_scalar(value: str) -> bool:
        codepoint = ord(value)
        return not 0xD800 <= codepoint <= 0xDFFF and value.isprintable()

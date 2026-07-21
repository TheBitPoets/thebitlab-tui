"""Pure cross-platform tests for the private POSIX byte decoder."""

from __future__ import annotations

import codecs
from io import UnsupportedOperation
from types import SimpleNamespace

import pytest

from thebitlab_tui import Key, KeyEvent
from thebitlab_tui._posix_decoder import _PosixDecoder, _validated_codec


def drain(decoder: _PosixDecoder) -> list[KeyEvent]:
    events: list[KeyEvent] = []
    while (event := decoder.pop()) is not None:
        events.append(event)
    return events


def decode(data: bytes, *, encoding: str = "utf-8") -> list[KeyEvent]:
    decoder = _PosixDecoder(encoding, 0.05)
    decoder.feed(data, 1.0)
    return drain(decoder)


@pytest.mark.parametrize(
    ("data", "event"),
    [
        (b"\r", KeyEvent(Key.ENTER)),
        (b"\n", KeyEvent(Key.ENTER)),
        (b"\t", KeyEvent(Key.TAB)),
        (b" ", KeyEvent(Key.CHARACTER, " ")),
        (b"x", KeyEvent(Key.CHARACTER, "x")),
        (b"\x01", KeyEvent(Key.CHARACTER, "a", ctrl=True)),
        (b"\x1a", KeyEvent(Key.CHARACTER, "z", ctrl=True)),
    ],
)
def test_semantic_and_character_mappings(data: bytes, event: KeyEvent) -> None:
    assert decode(data) == [event]


def test_ctrl_c_and_unsupported_controls_are_consumed() -> None:
    assert decode(b"\x00\x03\x1c\x7f") == []


def test_printable_unicode_and_replacement_scalar_are_preserved() -> None:
    text = "à\u0301�"
    assert decode(text.encode()) == [KeyEvent(Key.CHARACTER, char) for char in text]


def test_non_printable_unicode_is_ignored() -> None:
    assert decode("\u200b".encode()) == []


def test_malformed_text_does_not_manufacture_replacement_and_replays_suffix() -> None:
    assert decode(b"\xc3(x") == [
        KeyEvent(Key.CHARACTER, "("),
        KeyEvent(Key.CHARACTER, "x"),
    ]


@pytest.mark.parametrize("split", range(1, 4))
def test_multibyte_text_is_chunk_invariant(split: int) -> None:
    data = "€x".encode()
    decoder = _PosixDecoder("utf-8", 0.05)
    decoder.feed(data[:split], 0.0)
    decoder.feed(data[split:], 0.0)
    assert drain(decoder) == [
        KeyEvent(Key.CHARACTER, "€"),
        KeyEvent(Key.CHARACTER, "x"),
    ]


@pytest.mark.parametrize(
    ("sequence", "key"),
    [
        (b"\x1b[A", Key.UP),
        (b"\x1b[B", Key.DOWN),
        (b"\x1b[C", Key.RIGHT),
        (b"\x1b[D", Key.LEFT),
        (b"\x1bOA", Key.UP),
        (b"\x1bOB", Key.DOWN),
        (b"\x1bOC", Key.RIGHT),
        (b"\x1bOD", Key.LEFT),
    ],
)
def test_csi_and_ss3_arrows(sequence: bytes, key: Key) -> None:
    assert decode(sequence) == [KeyEvent(key)]


@pytest.mark.parametrize(
    ("sequence", "key"),
    [
        (b"\x1b[A", Key.UP),
        (b"\x1b[B", Key.DOWN),
        (b"\x1b[C", Key.RIGHT),
        (b"\x1b[D", Key.LEFT),
        (b"\x1bOA", Key.UP),
        (b"\x1bOB", Key.DOWN),
        (b"\x1bOC", Key.RIGHT),
        (b"\x1bOD", Key.LEFT),
    ],
)
def test_arrow_sequences_are_chunk_invariant(sequence: bytes, key: Key) -> None:
    for split in range(1, len(sequence)):
        decoder = _PosixDecoder("utf-8", 0.05)
        decoder.feed(sequence[:split], 0.0)
        decoder.feed(sequence[split:], 0.01)
        assert drain(decoder) == [KeyEvent(key)]


@pytest.mark.parametrize("sequence", [b"\x1b[1A", b"\x1b[ A", b"\x1bOP", b"\x1b[~"])
def test_complete_unsupported_sequences_are_consumed(sequence: bytes) -> None:
    assert decode(sequence + b"x") == [KeyEvent(Key.CHARACTER, "x")]


@pytest.mark.parametrize(
    "sequence",
    [b"\x1b[1A", b"\x1b[ A", b"\x1bOP", b"\x1b[\x10", b"\x1bO\x10"],
)
def test_unsupported_and_malformed_sequences_are_chunk_invariant(
    sequence: bytes,
) -> None:
    for split in range(1, len(sequence)):
        decoder = _PosixDecoder("utf-8", 0.05)
        decoder.feed(sequence[:split], 0.0)
        decoder.feed(sequence[split:] + b"x", 0.01)
        assert drain(decoder) == [KeyEvent(Key.CHARACTER, "x")]


def test_ss3_has_an_exact_three_byte_grammar() -> None:
    assert decode(b"\x1bO\x10x") == [KeyEvent(Key.CHARACTER, "x")]


def test_malformed_control_consumes_crossing_byte_and_preserves_following() -> None:
    assert decode(b"\x1b[\x10x") == [KeyEvent(Key.CHARACTER, "x")]


@pytest.mark.parametrize("sequence", [b"\x1b[0Ax", b"\x1b[00Ax", b"\x1b[000?x"])
def test_csi_private_bound_is_chunk_invariant(sequence: bytes) -> None:
    for split in range(1, len(sequence)):
        decoder = _PosixDecoder("utf-8", 0.05, control_limit=5)
        decoder.feed(sequence[:split], 0.0)
        decoder.feed(sequence[split:], 0.01)
        assert drain(decoder) == [KeyEvent(Key.CHARACTER, "x")]


def test_lone_escape_waits_for_grace_period() -> None:
    decoder = _PosixDecoder("utf-8", 0.05)
    decoder.feed(b"\x1b", 10.0)
    decoder.expire(10.049)
    assert drain(decoder) == []
    decoder.expire(10.05)
    assert drain(decoder) == [KeyEvent(Key.ESCAPE)]


def test_alt_text_reserved_prefixes_and_repeated_escape() -> None:
    alt = _PosixDecoder("utf-8", 0.05)
    alt.feed(b"\x1b" + "à".encode(), 1.0)
    assert drain(alt) == [KeyEvent(Key.CHARACTER, "à", alt=True)]

    repeated = _PosixDecoder("utf-8", 0.05)
    repeated.feed(b"\x1b\x1b", 1.0)
    assert drain(repeated) == [KeyEvent(Key.ESCAPE)]
    repeated.expire(1.05)
    assert drain(repeated) == [KeyEvent(Key.ESCAPE)]

    for prefix in (b"\x1b[", b"\x1bO"):
        reserved = _PosixDecoder("utf-8", 0.05)
        reserved.feed(prefix, 1.0)
        reserved.expire(1.05)
        assert drain(reserved) == []


def test_escape_before_semantic_control_is_replayed_in_order() -> None:
    assert decode(b"\x1b\t") == [KeyEvent(Key.ESCAPE), KeyEvent(Key.TAB)]


def test_incomplete_alt_multibyte_is_discarded_at_escape_deadline() -> None:
    decoder = _PosixDecoder("utf-8", 0.05)
    decoder.feed(b"\x1b\xc3", 1.0)
    decoder.expire(1.05)
    assert drain(decoder) == []


def test_malformed_alt_replays_valid_suffix_with_current_timestamp() -> None:
    decoder = _PosixDecoder("utf-8", 0.05)
    decoder.feed(b"\x1b\xc3\x1b", 4.0)
    decoder.expire(4.049)
    assert drain(decoder) == []
    decoder.expire(4.05)
    assert drain(decoder) == [KeyEvent(Key.ESCAPE)]


def test_codec_validation() -> None:
    assert _validated_codec(None) == "utf-8"
    assert _validated_codec("") == "utf-8"
    assert _validated_codec("UTF-8") == "utf-8"
    with pytest.raises(LookupError):
        _validated_codec("not-a-real-codec")
    with pytest.raises(UnsupportedOperation, match="preserve ASCII"):
        _validated_codec("utf-16")


def test_codec_validation_rejects_incremental_state_and_missing_decoder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StatefulDecoder(codecs.IncrementalDecoder):
        def decode(self, data: bytes, final: bool = False) -> str:
            self.buffer = data
            return data.decode("ascii")

        def getstate(self) -> tuple[bytes, int]:
            return (getattr(self, "buffer", b""), 0)

    monkeypatch.setattr(
        codecs,
        "lookup",
        lambda name: SimpleNamespace(incrementaldecoder=StatefulDecoder),
    )
    with pytest.raises(UnsupportedOperation, match="preserve ASCII"):
        _validated_codec("stateful-test")

    monkeypatch.setattr(
        codecs,
        "lookup",
        lambda name: SimpleNamespace(incrementaldecoder=None),
    )
    with pytest.raises(UnsupportedOperation, match="preserve ASCII"):
        _validated_codec("missing-decoder-test")


def test_discard_partial_keeps_complete_events_only() -> None:
    decoder = _PosixDecoder("utf-8", 0.05)
    decoder.feed(b"x\xc3", 0.0)
    decoder.discard_partial()
    assert drain(decoder) == [KeyEvent(Key.CHARACTER, "x")]

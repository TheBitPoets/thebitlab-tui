"""Deterministic cross-platform tests for the private Windows decoder."""

from __future__ import annotations

import pytest

from utui import Key, KeyEvent
from utui._windows_decoder import (
    _LEFT_ALT_PRESSED,
    _LEFT_CTRL_PRESSED,
    _RIGHT_ALT_PRESSED,
    _RIGHT_CTRL_PRESSED,
    _SHIFT_PRESSED,
    _WindowsKeyRecord,
    _WindowsRecordDecoder,
)


def record(
    *,
    virtual_key: int = 0,
    unicode_unit: int = 0,
    control_state: int = 0,
    repeat_count: int = 1,
    key_down: bool = True,
) -> _WindowsKeyRecord:
    """Build one concise private record fixture."""

    return _WindowsKeyRecord(
        key_down=key_down,
        repeat_count=repeat_count,
        virtual_key=virtual_key,
        unicode_unit=unicode_unit,
        control_state=control_state,
    )


def drain(decoder: _WindowsRecordDecoder) -> list[KeyEvent]:
    """Return every complete event retained by a decoder."""

    events: list[KeyEvent] = []
    while (event := decoder.pop()) is not None:
        events.append(event)
    return events


@pytest.mark.parametrize(
    ("virtual_key", "key"),
    [
        (0x25, Key.LEFT),
        (0x26, Key.UP),
        (0x27, Key.RIGHT),
        (0x28, Key.DOWN),
        (0x0D, Key.ENTER),
        (0x1B, Key.ESCAPE),
        (0x09, Key.TAB),
    ],
)
def test_semantic_virtual_keys_take_priority(
    virtual_key: int, key: Key
) -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(
        record(
            virtual_key=virtual_key,
            unicode_unit=ord("x"),
            control_state=_LEFT_CTRL_PRESSED | _RIGHT_ALT_PRESSED,
        )
    )
    assert drain(decoder) == [KeyEvent(key, ctrl=True, alt=True)]


@pytest.mark.parametrize("virtual_key", [0x26, 0x0D, 0x09])
@pytest.mark.parametrize("unicode_unit", [0xD83D, 0xDE00])
def test_semantic_virtual_keys_take_priority_over_surrogate_units(
    virtual_key: int, unicode_unit: int
) -> None:
    expected = {0x26: Key.UP, 0x0D: Key.ENTER, 0x09: Key.TAB}[virtual_key]
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=0xD83D))
    decoder.feed(record(virtual_key=virtual_key, unicode_unit=unicode_unit))

    assert drain(decoder) == [KeyEvent(expected)]
    assert not decoder.has_partial


@pytest.mark.parametrize(
    ("unicode_unit", "key"),
    [(0x0D, Key.ENTER), (0x0A, Key.ENTER), (0x09, Key.TAB), (0x1B, Key.ESCAPE)],
)
def test_virtual_key_zero_maps_semantic_text_controls(
    unicode_unit: int, key: Key
) -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=unicode_unit, control_state=_SHIFT_PRESSED))
    assert drain(decoder) == [KeyEvent(key, shift=True)]


def test_printable_text_preserves_reported_modifiers_and_altgr() -> None:
    decoder = _WindowsRecordDecoder()
    state = _LEFT_CTRL_PRESSED | _RIGHT_ALT_PRESSED | _SHIFT_PRESSED
    decoder.feed(record(virtual_key=0x45, unicode_unit=ord("€"), control_state=state))
    decoder.feed(record(virtual_key=0x41, unicode_unit=ord("A")))
    assert drain(decoder) == [
        KeyEvent(Key.CHARACTER, "€", ctrl=True, alt=True, shift=True),
        KeyEvent(Key.CHARACTER, "A"),
    ]


@pytest.mark.parametrize("character", ["à", "́", "�", " "])
def test_printable_bmp_scalars_are_preserved(character: str) -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=ord(character)))
    assert drain(decoder) == [KeyEvent(Key.CHARACTER, character)]


@pytest.mark.parametrize("unicode_unit", [0, 0x01, 0x7F, 0x80, 0x200B])
def test_non_printable_units_are_consumed(unicode_unit: int) -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=unicode_unit))
    assert drain(decoder) == []


@pytest.mark.parametrize("virtual_key", range(0x41, 0x5B))
def test_ctrl_letters_derive_lowercase_from_nul_or_matching_c0(
    virtual_key: int,
) -> None:
    expected = chr(ord("a") + virtual_key - 0x41)
    units = (0, virtual_key - 0x41 + 1)
    for unit in units:
        decoder = _WindowsRecordDecoder()
        decoder.feed(
            record(
                virtual_key=virtual_key,
                unicode_unit=unit,
                control_state=_RIGHT_CTRL_PRESSED,
            )
        )
        expected_events = (
            []
            if virtual_key == 0x43
            else [KeyEvent(Key.CHARACTER, expected, ctrl=True)]
        )
        assert drain(decoder) == expected_events


@pytest.mark.parametrize("unicode_unit", [0, 0x03, ord("c"), ord("C")])
def test_synthetic_ctrl_c_is_always_consumed(unicode_unit: int) -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(
        record(
            virtual_key=0x43,
            unicode_unit=unicode_unit,
            control_state=_LEFT_CTRL_PRESSED | _RIGHT_ALT_PRESSED,
        )
    )
    assert drain(decoder) == []


def test_distinct_printable_ctrl_c_virtual_key_remains_text() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(
        record(
            virtual_key=0x43,
            unicode_unit=ord("©"),
            control_state=_LEFT_CTRL_PRESSED | _RIGHT_ALT_PRESSED,
        )
    )
    assert drain(decoder) == [
        KeyEvent(Key.CHARACTER, "©", ctrl=True, alt=True)
    ]


def test_physical_ctrl_i_and_m_remain_characters_not_semantic_keys() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(virtual_key=0x49, unicode_unit=0x09, control_state=0x0004))
    decoder.feed(record(virtual_key=0x4D, unicode_unit=0x0D, control_state=0x0004))
    assert drain(decoder) == [
        KeyEvent(Key.CHARACTER, "i", ctrl=True),
        KeyEvent(Key.CHARACTER, "m", ctrl=True),
    ]


def test_lock_and_enhanced_bits_do_not_become_modifiers() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=ord("x"), control_state=0x0020 | 0x0040 | 0x0080 | 0x0100))
    assert drain(decoder) == [KeyEvent(Key.CHARACTER, "x")]


def test_key_up_zero_repeat_and_unsupported_records_are_ignored() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(virtual_key=0x70, key_down=False))
    decoder.feed(record(virtual_key=0x70, repeat_count=0))
    decoder.feed(record(virtual_key=0x70))
    assert drain(decoder) == []


def test_repeats_remain_ordered_and_are_returned_one_at_a_time() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=ord("x"), repeat_count=3))
    decoder.feed(record(virtual_key=0x26, repeat_count=2))
    assert [decoder.pop() for _ in range(6)] == [
        KeyEvent(Key.CHARACTER, "x"),
        KeyEvent(Key.CHARACTER, "x"),
        KeyEvent(Key.CHARACTER, "x"),
        KeyEvent(Key.UP),
        KeyEvent(Key.UP),
        None,
    ]


def test_large_repeat_is_retained_as_one_private_run() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=ord("x"), repeat_count=0xFFFF))
    assert len(decoder._runs) == 1
    assert decoder.pop() == KeyEvent(Key.CHARACTER, "x")
    assert decoder._runs[0].remaining == 0xFFFE


def test_matching_surrogate_pair_emits_supplementary_scalar_run() -> None:
    decoder = _WindowsRecordDecoder()
    modifiers = _LEFT_ALT_PRESSED | _SHIFT_PRESSED
    decoder.feed(
        record(unicode_unit=0xD83D, repeat_count=2, control_state=modifiers)
    )
    assert decoder.has_partial
    assert decoder.pop() is None
    decoder.feed(
        record(unicode_unit=0xDE42, repeat_count=2, control_state=modifiers)
    )
    assert not decoder.has_partial
    expected = KeyEvent(Key.CHARACTER, chr(0x1F642), alt=True, shift=True)
    assert drain(decoder) == [expected, expected]


@pytest.mark.parametrize(
    "low",
    [
        record(unicode_unit=0xDE42, repeat_count=1, control_state=_LEFT_ALT_PRESSED),
        record(unicode_unit=0xDE42, repeat_count=2, control_state=_RIGHT_CTRL_PRESSED),
    ],
)
def test_surrogate_mismatch_discards_both_halves(low: _WindowsKeyRecord) -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(
        record(unicode_unit=0xD83D, repeat_count=2, control_state=_LEFT_ALT_PRESSED)
    )
    decoder.feed(low)
    assert not decoder.has_partial
    assert drain(decoder) == []


def test_lone_low_is_consumed_and_non_low_replaces_pending_high() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=0xDE42))
    decoder.feed(record(unicode_unit=0xD83D))
    decoder.feed(record(unicode_unit=ord("x")))
    assert not decoder.has_partial
    assert drain(decoder) == [KeyEvent(Key.CHARACTER, "x")]


def test_second_high_replaces_first_and_can_complete() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=0xD800))
    decoder.feed(record(unicode_unit=0xD83D))
    decoder.feed(record(unicode_unit=0xDE42))
    assert drain(decoder) == [KeyEvent(Key.CHARACTER, chr(0x1F642))]


def test_key_up_record_does_not_break_pending_surrogate() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=0xD83D))
    decoder.feed(record(unicode_unit=0xD83D, key_down=False))
    assert decoder.has_partial
    decoder.feed(record(unicode_unit=0xDE42))
    assert drain(decoder) == [KeyEvent(Key.CHARACTER, chr(0x1F642))]


@pytest.mark.parametrize("unicode_unit", [0xDE42, ord("x"), 0xD800])
def test_zero_repeat_key_down_discards_pending_surrogate(
    unicode_unit: int,
) -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=0xD83D))
    decoder.feed(record(unicode_unit=unicode_unit, repeat_count=0))
    decoder.feed(record(unicode_unit=0xDE42))

    assert not decoder.has_partial
    assert drain(decoder) == []


def test_invalid_injected_utf16_unit_discards_pending_state() -> None:
    decoder = _WindowsRecordDecoder()
    decoder.feed(record(unicode_unit=0xD83D))
    decoder.feed(record(unicode_unit=0x110000))
    assert not decoder.has_partial
    assert drain(decoder) == []

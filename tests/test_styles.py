import pytest

from thebitlab_tui import Style, strip_ansi, truncate, visible_width


def test_color_mode_adds_ansi_without_changing_visible_width() -> None:
    rendered = Style(bold=True, foreground="green").apply("ready", color=True)
    assert rendered.startswith("\x1b[")
    assert rendered.endswith("\x1b[0m")
    assert visible_width(rendered) == 5
    assert strip_ansi(rendered) == "ready"


def test_no_color_returns_plain_text() -> None:
    assert Style(bold=True, foreground="red").apply("error", color=False) == "error"


def test_ansi_is_excluded_from_width_and_truncation() -> None:
    styled = "\x1b[31mabcdef\x1b[0m"
    assert visible_width(styled) == 6
    assert truncate(styled, 5) == "ab..."


def test_unknown_color_is_rejected() -> None:
    with pytest.raises(ValueError):
        Style(foreground="orange")


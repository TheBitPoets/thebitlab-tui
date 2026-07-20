import pytest

from thebitlab_tui import Label, Panel, Style, render_lines, visible_width


def test_label_alignment_wrapping_and_truncation() -> None:
    assert render_lines(Label("abcdef"), 5, 1) == ["ab..."]
    assert render_lines(Label("x", align="center"), 5, 1) == ["  x  "]
    assert render_lines(Label("one two", wrap=True), 4, 2) == ["one ", "two "]


def test_label_ignores_input_ansi_for_geometry() -> None:
    label = Label("\x1b[31mabcdef\x1b[0m", wrap=True)
    assert render_lines(label, 5, 2) == ["abcde", "f    "]


def test_panel_with_title_snapshot() -> None:
    panel = Panel("hello", title="Info")
    assert render_lines(panel, 12, 4) == [
        "+ Info ----+",
        "|hello     |",
        "|          |",
        "+----------+",
    ]


def test_collapsed_panel_snapshot() -> None:
    panel = Panel("hidden", title="Info", collapsed=True)
    assert render_lines(panel, 14, 5) == [
        "+ [+] Info --+",
        "|            |",
        "+------------+",
        "              ",
        "              ",
    ]


def test_focused_panel_is_visible_without_color() -> None:
    lines = render_lines(Panel("body", title="Active", focused=True), 14, 3)
    assert lines[0] == "+ > Active --+"


def test_panel_color_keeps_borders_aligned() -> None:
    panel = Panel("body", title="Active", focused=True, focus_style=Style(foreground="cyan"))
    lines = render_lines(panel, 14, 3, color=True)
    assert all(visible_width(line) == 14 for line in lines)
    assert "\x1b[" in lines[0]


def test_partially_clipped_panel_does_not_grow_a_new_border() -> None:
    from thebitlab_tui import Canvas, Rect

    canvas = Canvas(8, 3)
    Panel("body", title="Title").draw(canvas, Rect(-2, 0, 10, 3))
    assert canvas.lines() == ["Title -+", "ody    |", "-------+"]


def test_borderless_panel_reserves_title_row() -> None:
    assert render_lines(Panel("body", title="Title", border=False), 10, 2) == [
        "Title     ",
        "body      ",
    ]


@pytest.mark.parametrize(
    ("width", "expected"),
    [
        (3, "+>+"),
        (4, "+> +"),
        (5, "+ > +"),
        (6, "+ >  +"),
        (7, "+ > . +"),
        (8, "+ > .. +"),
    ],
)
def test_focus_marker_survives_narrow_widths(width: int, expected: str) -> None:
    assert render_lines(Panel("", title="Active", focused=True), width, 3)[0] == expected


@pytest.mark.parametrize(
    ("width", "expected"),
    [
        (5, "+ + +"),
        (6, "+ +  +"),
        (7, "+ [+] +"),
        (8, "+ [+]  +"),
    ],
)
def test_collapsed_marker_survives_narrow_widths(width: int, expected: str) -> None:
    assert render_lines(Panel("", title="Active", collapsed=True), width, 3)[0] == expected


@pytest.mark.parametrize(
    ("width", "expected"),
    [
        (0, ""),
        (1, "|"),
        (2, "++"),
        (3, "+>+"),
        (4, "+>++"),
        (5, "+>+ +"),
        (6, "+ >+ +"),
        (7, "+ >+  +"),
        (8, "+ >[+] +"),
    ],
)
def test_focused_collapsed_panel_preserves_both_states_when_space_allows(
    width: int,
    expected: str,
) -> None:
    # Widths below three have no interior header cell, so no marker can fit.
    panel = Panel("", title="Active", focused=True, collapsed=True)
    assert render_lines(panel, width, 3)[0] == expected


@pytest.mark.parametrize(
    ("width", "expected"),
    [(0, ""), (1, ">"), (2, ">+"), (3, ">+ "), (4, ">[+]"), (5, ">[+] ")],
)
def test_borderless_focused_collapsed_panel_preserves_state(
    width: int,
    expected: str,
) -> None:
    panel = Panel("", title="Active", focused=True, collapsed=True, border=False)
    assert render_lines(panel, width, 1)[0] == expected

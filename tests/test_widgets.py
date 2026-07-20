from thebitlab_tui import Label, Panel, Style, render_lines, visible_width


def test_label_alignment_wrapping_and_truncation() -> None:
    assert render_lines(Label("abcdef"), 5, 1) == ["ab..."]
    assert render_lines(Label("x", align="center"), 5, 1) == ["  x  "]
    assert render_lines(Label("one two", wrap=True), 4, 2) == ["one ", "two "]


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

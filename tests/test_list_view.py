"""Snapshots and public contracts for :class:`thebitlab_tui.ListView`."""

from __future__ import annotations

import inspect

import pytest

import thebitlab_tui
from thebitlab_tui import (
    Canvas,
    Column,
    Label,
    ListView,
    Panel,
    Rect,
    Row,
    Style,
    render_lines,
    strip_ansi,
    visible_width,
)


def test_list_view_focused_and_unfocused_snapshots() -> None:
    items = ["Alpha", "Beta", "Gamma"]
    assert render_lines(ListView(items, active_index=1), 8, 3) == [
        "  Alpha ",
        "* Beta  ",
        "  Gamma ",
    ]
    assert render_lines(ListView(items, active_index=1, focused=True), 8, 3) == [
        "  Alpha ",
        "> Beta  ",
        "  Gamma ",
    ]


def test_list_view_none_selection_reserves_marker_columns() -> None:
    assert render_lines(ListView(["one", "two"]), 6, 2) == ["  one ", "  two "]


@pytest.mark.parametrize(
    ("width", "expected"),
    [(0, ""), (1, ">"), (2, "> "), (3, "> ."), (6, "> h...")],
)
def test_list_view_preserves_active_marker_when_narrow(width: int, expected: str) -> None:
    assert render_lines(
        ListView(["hello"], active_index=0, focused=True), width, 1
    ) == [expected]


def test_list_view_truncates_text_inside_reserved_columns() -> None:
    assert render_lines(ListView(["abcdef"]), 6, 1) == ["  a..."]


def test_list_view_empty_and_short_content_clear_the_viewport() -> None:
    assert render_lines(ListView([]), 5, 2) == ["     ", "     "]
    assert render_lines(ListView(["one"]), 5, 3) == ["  one", "     ", "     "]

    canvas = Canvas(7, 4, fill=".")
    ListView([]).draw(canvas, Rect(1, 1, 5, 2))
    assert canvas.lines() == [".......", ".     .", ".     .", "......."]


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (0, ["  zero ", "  one  "]),
        (2, ["  two  ", "  three"]),
        (3, ["  three", "  four "]),
        (99, ["  three", "  four "]),
    ],
)
def test_list_view_clamps_effective_scroll_offset(
    offset: int,
    expected: list[str],
) -> None:
    view = ListView(["zero", "one", "two", "three", "four"], scroll_offset=offset)
    assert render_lines(view, 7, 2) == expected
    assert view.scroll_offset == offset


def test_list_view_does_not_reveal_active_item_automatically() -> None:
    view = ListView(
        ["zero", "one", "two", "three", "four"],
        active_index=4,
        scroll_offset=0,
        focused=True,
    )
    assert render_lines(view, 7, 2) == ["  zero ", "  one  "]
    assert (view.active_index, view.scroll_offset, view.focused) == (4, 0, True)

    visible = ListView(view.items, active_index=4, scroll_offset=3, focused=True)
    assert render_lines(visible, 7, 2) == ["  three", "> four "]


def test_list_view_materializes_items_as_a_stable_tuple() -> None:
    source = ["one", "two"]
    view = ListView(source, active_index=1)
    source[1] = "changed"
    source.append("three")

    assert view.items == ("one", "two")
    assert render_lines(view, 7, 2) == ["  one  ", "* two  "]


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_list_view_normalizes_ansi_and_newlines(newline: str) -> None:
    view = ListView([f"\x1b[31mred\x1b[0m{newline}now"])
    assert render_lines(view, 9, 1) == ["  red now"]


def test_list_view_ansi_and_no_color_have_equal_geometry() -> None:
    view = ListView(
        ["idle", "active"],
        active_index=1,
        focused=True,
        style=Style(foreground="cyan"),
    )
    plain = render_lines(view, 9, 2, color=False)
    colored = render_lines(view, 9, 2, color=True)

    assert plain == ["  idle   ", "> active "]
    assert [strip_ansi(line) for line in colored] == plain
    assert all(visible_width(line) == 9 for line in colored)
    assert "\x1b[36m" in colored[0]
    assert "\x1b[1;97m" in colored[1]


def test_list_view_background_styles_cover_complete_populated_rows() -> None:
    view = ListView(
        ["x", "y"],
        active_index=1,
        style=Style(background="blue"),
        active_style=Style(background="red"),
    )
    assert render_lines(view, 6, 2, color=False) == ["  x   ", "* y   "]
    assert render_lines(view, 6, 2, color=True) == [
        "\x1b[44m  x   \x1b[0m",
        "\x1b[41m* y   \x1b[0m",
    ]


def test_list_view_clips_to_its_logical_rectangle() -> None:
    canvas = Canvas(6, 4, fill=".")
    view = ListView(["zero", "one", "two"], active_index=1, focused=True)
    view.draw(canvas, Rect(-2, -1, 6, 3))
    assert canvas.lines() == ["one ..", "two ..", "......", "......"]


def test_list_view_composes_with_panel_row_and_column() -> None:
    panel = Panel(
        ListView(["one", "two"], active_index=0, focused=True),
        title="Items",
        focused=True,
    )
    assert render_lines(panel, 10, 5) == [
        "+ > I... +",
        "|> one   |",
        "|  two   |",
        "|        |",
        "+--------+",
    ]

    row = Row(
        [ListView(["a"], width=3), Label("x")],
        gap=0,
        stack_when_narrow=False,
    )
    assert render_lines(row, 5, 1) == ["  ax "]

    column = Column([ListView(["a"], height=1), Label("tail")])
    assert render_lines(column, 6, 3) == ["  a   ", "tail  ", "      "]


def test_list_view_minimum_and_maximum_hints_drive_structural_layout() -> None:
    capped_width = Row(
        [ListView(["a"], max_width=3), Label("x")],
        gap=0,
        stack_when_narrow=False,
    )
    assert render_lines(capped_width, 5, 1) == ["  ax "]

    soft_widths = Row(
        [ListView(["a"], min_width=4), Label("x", min_width=4)],
        gap=1,
        stack_when_narrow=False,
    )
    assert render_lines(soft_widths, 5, 1) == ["  a x"]

    capped_height = Column([ListView(["a", "b"], max_height=1), Label("tail")])
    assert render_lines(capped_height, 6, 3) == ["  a   ", "tail  ", "      "]

    soft_heights = Column(
        [ListView(["a", "b"], min_height=3), Label("tail", min_height=3)]
    )
    assert render_lines(soft_heights, 6, 4) == ["  a   ", "  b   ", "      ", "tail  "]


@pytest.mark.parametrize("active_index", [-1, 1, 99])
def test_list_view_rejects_invalid_active_index(active_index: int) -> None:
    with pytest.raises(ValueError, match="active_index"):
        ListView(["only"], active_index=active_index)


def test_list_view_rejects_selection_for_empty_items() -> None:
    with pytest.raises(ValueError, match="active_index"):
        ListView([], active_index=0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scroll_offset": -1},
        {"width": -1},
        {"height": -1},
        {"min_width": -1},
        {"min_height": -1},
        {"max_width": -1},
        {"max_height": -1},
        {"min_width": 2, "max_width": 1},
        {"min_height": 2, "max_height": 1},
    ],
)
def test_list_view_rejects_invalid_offset_and_size_hints(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        ListView(["item"], **kwargs)


def test_list_view_zero_height_draws_no_rows() -> None:
    assert render_lines(ListView(["item"]), 5, 0) == []


def test_list_view_is_a_stable_public_export() -> None:
    assert "ListView" in thebitlab_tui.__all__
    parameters = inspect.signature(ListView).parameters
    assert list(parameters) == [
        "items",
        "active_index",
        "scroll_offset",
        "focused",
        "style",
        "active_style",
        "width",
        "height",
        "min_width",
        "min_height",
        "max_width",
        "max_height",
    ]
    assert parameters["items"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for name, parameter in parameters.items()
        if name != "items"
    )
    assert parameters["items"].default is inspect.Parameter.empty
    assert {name: parameters[name].default for name in list(parameters)[1:]} == {
        "active_index": None,
        "scroll_offset": 0,
        "focused": False,
        "style": Style(),
        "active_style": Style(bold=True, bright=True),
        "width": None,
        "height": None,
        "min_width": 1,
        "min_height": 1,
        "max_width": None,
        "max_height": None,
    }

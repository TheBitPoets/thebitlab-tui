"""Snapshots and public contracts for :class:`thebitlab_tui.ScrollView`."""

from __future__ import annotations

import inspect
from dataclasses import dataclass

import pytest

import thebitlab_tui
from thebitlab_tui import (
    Canvas,
    Column,
    Label,
    Panel,
    Rect,
    Row,
    ScrollView,
    Style,
    render_lines,
    strip_ansi,
    visible_width,
)


CONTENT = "zero\none\ntwo\nthree\nfour"


@pytest.mark.parametrize(
    ("offset", "expected"),
    [
        (0, ["zero   ", "one    ", "two    "]),
        (1, ["one    ", "two    ", "three  "]),
        (2, ["two    ", "three  ", "four   "]),
        (99, ["two    ", "three  ", "four   "]),
    ],
)
def test_scroll_view_string_snapshots(offset: int, expected: list[str]) -> None:
    view = ScrollView(CONTENT, content_height=5, scroll_offset=offset)
    assert render_lines(view, 7, 3) == expected
    assert view.scroll_offset == offset


def test_scroll_view_short_and_empty_content_clear_the_viewport() -> None:
    assert render_lines(
        ScrollView("zero\none", content_height=2, scroll_offset=99),
        7,
        4,
    ) == ["zero   ", "one    ", "       ", "       "]
    assert render_lines(ScrollView("hidden", content_height=0), 5, 2) == [
        "     ",
        "     ",
    ]

    canvas = Canvas(7, 4, fill=".")
    ScrollView("", content_height=0).draw(canvas, Rect(1, 1, 5, 2))
    assert canvas.lines() == [".......", ".     .", ".     .", "......."]


@pytest.mark.parametrize(
    ("width", "expected"),
    [(0, ""), (1, "."), (2, ".."), (3, "..."), (6, "abc...")],
)
def test_scroll_view_narrow_width_uses_stable_truncation(width: int, expected: str) -> None:
    assert render_lines(
        ScrollView("abcdefgh", content_height=1),
        width,
        1,
    ) == [expected]


def test_scroll_view_clipping_uses_the_logical_assigned_viewport() -> None:
    canvas = Canvas(5, 3, fill=".")
    view = ScrollView("AAAAA\nBBBBB\nCCCCC", content_height=3)
    view.draw(canvas, Rect(-2, -1, 5, 3))
    assert canvas.lines() == ["BBB..", "CCC..", "....."]


@dataclass
class _EscapingWidget:
    char: str = "X"

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        canvas.fill(Rect(-10, -10, 100, 100), self.char)


def test_scroll_view_isolates_children_from_adjacent_cells() -> None:
    canvas = Canvas(8, 4, fill=".")
    view = ScrollView(_EscapingWidget(), content_height=2)
    view.draw(canvas, Rect(2, 1, 4, 2))
    assert canvas.lines() == [
        "........",
        "..XXXX..",
        "..XXXX..",
        "........",
    ]

    row = Row(
        [ScrollView(_EscapingWidget(), content_height=2, width=4), Label("SAFE", width=4)],
        gap=1,
        stack_when_narrow=False,
    )
    assert render_lines(row, 9, 2) == ["XXXX SAFE", "XXXX     "]

    column = Column(
        [ScrollView(_EscapingWidget(), content_height=2, height=2), Label("SAFE", height=1)]
    )
    assert render_lines(column, 5, 3) == ["XXXXX", "XXXXX", "SAFE "]


@dataclass
class _RecordingWidget:
    canvas_size: tuple[int, int] | None = None
    assigned_rect: Rect | None = None

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        self.canvas_size = (canvas.width, canvas.height)
        self.assigned_rect = rect
        canvas.fill(rect, "#", Style(background="blue"))


def test_scroll_view_assigns_logical_content_rect_and_preserves_styles() -> None:
    child = _RecordingWidget()
    view = ScrollView(child, content_height=5, scroll_offset=2)
    plain = render_lines(view, 6, 3, color=False)
    colored = render_lines(view, 6, 3, color=True)

    assert child.canvas_size == (6, 3)
    assert child.assigned_rect == Rect(0, -2, 6, 5)
    assert plain == ["######", "######", "######"]
    assert colored == ["\x1b[44m######\x1b[0m"] * 3
    assert [strip_ansi(line) for line in colored] == plain
    assert all(visible_width(line) == 6 for line in colored)


def test_scroll_view_composes_with_panel_row_and_column() -> None:
    panel = Panel(
        ScrollView(CONTENT, content_height=5, scroll_offset=2),
        title="Log",
    )
    assert render_lines(panel, 10, 5) == [
        "+ Log ---+",
        "|two     |",
        "|three   |",
        "|four    |",
        "+--------+",
    ]

    capped_width = Row(
        [ScrollView("a", content_height=1, max_width=3), Label("x")],
        gap=0,
        stack_when_narrow=False,
    )
    assert render_lines(capped_width, 5, 1) == ["a  x "]

    fixed_width = Row(
        [ScrollView("a", content_height=1, width=2), Label("x")],
        gap=0,
        stack_when_narrow=False,
    )
    assert render_lines(fixed_width, 4, 1) == ["a x "]

    soft_widths = Row(
        [ScrollView("a", content_height=1, min_width=4), Label("x", min_width=4)],
        gap=1,
        stack_when_narrow=False,
    )
    assert render_lines(soft_widths, 5, 1) == ["a   x"]

    capped_height = Column(
        [ScrollView("a\nb", content_height=2, max_height=1), Label("tail")]
    )
    assert render_lines(capped_height, 6, 3) == ["a     ", "tail  ", "      "]

    fixed_height = Column(
        [ScrollView("a\nb", content_height=2, height=2), Label("tail")]
    )
    assert render_lines(fixed_height, 6, 3) == ["a     ", "b     ", "tail  "]

    soft_heights = Column(
        [ScrollView("a\nb", content_height=2, min_height=3), Label("tail", min_height=3)]
    )
    assert render_lines(soft_heights, 6, 4) == ["a     ", "b     ", "      ", "tail  "]


def test_scroll_view_draw_does_not_mutate_caller_owned_fields() -> None:
    content = Label("one\ntwo")
    view = ScrollView(
        content,
        content_height=2,
        scroll_offset=99,
        width=7,
        height=3,
        min_width=2,
        min_height=2,
        max_width=8,
        max_height=4,
    )
    before = (
        view.content,
        view.content_height,
        view.scroll_offset,
        view.width,
        view.height,
        view.min_width,
        view.min_height,
        view.max_width,
        view.max_height,
    )

    assert render_lines(view, 7, 3) == ["one    ", "two    ", "       "]
    assert (
        view.content,
        view.content_height,
        view.scroll_offset,
        view.width,
        view.height,
        view.min_width,
        view.min_height,
        view.max_width,
        view.max_height,
    ) == before


@pytest.mark.parametrize(
    "kwargs",
    [
        {"content_height": -1},
        {"content_height": 1, "scroll_offset": -1},
        {"content_height": 1, "width": -1},
        {"content_height": 1, "height": -1},
        {"content_height": 1, "min_width": -1},
        {"content_height": 1, "min_height": -1},
        {"content_height": 1, "max_width": -1},
        {"content_height": 1, "max_height": -1},
        {"content_height": 1, "min_width": 2, "max_width": 1},
        {"content_height": 1, "min_height": 2, "max_height": 1},
    ],
)
def test_scroll_view_rejects_invalid_dimensions(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        ScrollView("content", **kwargs)


def test_scroll_view_zero_height_draws_no_rows() -> None:
    assert render_lines(ScrollView("content", content_height=1), 5, 0) == []


def test_scroll_view_is_a_stable_public_export() -> None:
    assert "ScrollView" in thebitlab_tui.__all__
    parameters = inspect.signature(ScrollView).parameters
    assert list(parameters) == [
        "content",
        "content_height",
        "scroll_offset",
        "width",
        "height",
        "min_width",
        "min_height",
        "max_width",
        "max_height",
    ]
    assert parameters["content"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for name, parameter in parameters.items()
        if name != "content"
    )
    assert parameters["content"].default is inspect.Parameter.empty
    assert parameters["content_height"].default is inspect.Parameter.empty
    assert {name: parameters[name].default for name in list(parameters)[2:]} == {
        "scroll_offset": 0,
        "width": None,
        "height": None,
        "min_width": 1,
        "min_height": 1,
        "max_width": None,
        "max_height": None,
    }

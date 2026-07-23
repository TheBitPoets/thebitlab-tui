"""Snapshots and public contracts for :class:`utui.Modal`."""

from __future__ import annotations

import inspect
from dataclasses import dataclass

import pytest

import utui
from utui import Canvas, Column, Label, Modal, Rect, Row, Style, render_lines
from utui.styles import PLAIN, strip_ansi, visible_width


def test_modal_centers_frame_and_preserves_the_outer_canvas() -> None:
    canvas = Canvas(15, 7, fill=".")

    Modal("body", title="Hi", preferred_width=9, preferred_height=5).draw(
        canvas,
        canvas.rect,
    )

    assert canvas.lines() == [
        "...............",
        "...+ [x] . +...",
        "...|body   |...",
        "...|       |...",
        "...|       |...",
        "...+-------+...",
        "...............",
    ]


@pytest.mark.parametrize(
    ("outer_width", "outer_height", "expected_x", "expected_y"),
    [(14, 8, 2, 1), (15, 9, 3, 2), (16, 10, 3, 2)],
)
def test_modal_centering_leaves_odd_spare_cells_right_and_bottom(
    outer_width: int,
    outer_height: int,
    expected_x: int,
    expected_y: int,
) -> None:
    canvas = Canvas(outer_width, outer_height, fill=".")
    Modal("", preferred_width=9, preferred_height=5).draw(canvas, canvas.rect)

    changed = [
        (x, y)
        for y, line in enumerate(canvas.lines())
        for x, char in enumerate(line)
        if char != "."
    ]
    assert min(x for x, _ in changed) == expected_x
    assert min(y for _, y in changed) == expected_y
    assert max(x for x, _ in changed) == expected_x + 8
    assert max(y for _, y in changed) == expected_y + 4


def test_closed_modal_is_a_complete_no_op() -> None:
    canvas = Canvas(9, 5, fill=".")
    Modal("hidden", title="Secret", open=False).draw(canvas, canvas.rect)
    assert canvas.lines() == ["........."] * 5


@pytest.mark.parametrize(
    ("width", "expected"),
    [
        (0, ""),
        (1, "|"),
        (2, "++"),
        (3, "+-+"),
        (4, "+--+"),
        (5, "+ [ +"),
        (6, "+ [x +"),
        (7, "+ [x] +"),
        (8, "+ [x] -+"),
        (9, "+ [x] . +"),
        (10, "+ [x] .. +"),
    ],
)
def test_modal_close_marker_wins_over_a_long_title(width: int, expected: str) -> None:
    modal = Modal(
        "",
        title="Very long title",
        preferred_width=None,
        preferred_height=3,
        style=Style(foreground="blue"),
        title_style=Style(foreground="red"),
    )
    plain = render_lines(modal, width, 3, color=False)
    colored = render_lines(modal, width, 3, color=True)
    assert plain[0] == expected
    assert [strip_ansi(line) for line in colored] == plain
    assert all(visible_width(line) == width for line in colored)


@pytest.mark.parametrize(
    ("width", "expected"),
    [
        (6, "+ [x +"),
        (7, "+ [x] +"),
        (8, "+ [x] -+"),
        (9, "+ [x] --+"),
        (10, "+ [x] ---+"),
    ],
)
def test_empty_modal_title_still_shows_the_close_marker(width: int, expected: str) -> None:
    modal = Modal(
        "",
        preferred_width=None,
        preferred_height=3,
        style=Style(foreground="blue"),
        title_style=Style(foreground="red"),
    )
    plain = render_lines(modal, width, 3, color=False)
    colored = render_lines(modal, width, 3, color=True)
    assert plain[0] == expected
    assert [strip_ansi(line) for line in colored] == plain
    assert all(visible_width(line) == width for line in colored)


def test_modal_strips_input_ansi_before_fitting_the_title() -> None:
    modal = Modal(
        "",
        title="\x1b[31mVery long title\x1b[0m",
        preferred_width=None,
        preferred_height=3,
    )
    assert render_lines(modal, 9, 3)[0] == "+ [x] . +"


@pytest.mark.parametrize("width", [9, 10])
def test_ansi_only_modal_title_has_empty_title_geometry(width: int) -> None:
    empty = Modal("", preferred_width=None, preferred_height=3)
    ansi_only = Modal(
        "",
        title="\x1b[31m\x1b[0m",
        preferred_width=None,
        preferred_height=3,
    )

    empty_plain = render_lines(empty, width, 3, color=False)
    ansi_plain = render_lines(ansi_only, width, 3, color=False)
    ansi_colored = render_lines(ansi_only, width, 3, color=True)

    assert ansi_plain == empty_plain
    assert [strip_ansi(line) for line in ansi_colored] == empty_plain
    assert all(visible_width(line) == width for line in ansi_colored)


@pytest.mark.parametrize(
    ("height", "expected"),
    [(0, []), (1, ["- [x] -"]), (2, ["+ [x] +", "+-----+"])],
)
def test_modal_degrades_below_its_minimum_height(
    height: int,
    expected: list[str],
) -> None:
    modal = Modal("", preferred_width=None, preferred_height=None)
    assert render_lines(modal, 7, height) == expected


@pytest.mark.parametrize(
    ("modal", "outer_width", "outer_height", "expected_bounds"),
    [
        (Modal("", preferred_width=0, preferred_height=0), 15, 9, (4, 3, 7, 3)),
        (
            Modal(
                "",
                preferred_width=100,
                preferred_height=100,
                max_width=9,
                max_height=5,
            ),
            15,
            9,
            (3, 2, 9, 5),
        ),
        (
            Modal(
                "",
                preferred_width=None,
                preferred_height=None,
                max_width=9,
                max_height=5,
            ),
            15,
            9,
            (3, 2, 9, 5),
        ),
        (
            Modal("", preferred_width=None, preferred_height=None),
            15,
            9,
            (0, 0, 15, 9),
        ),
        (Modal("", preferred_width=40, preferred_height=10), 5, 2, (0, 0, 5, 2)),
    ],
)
def test_modal_preferred_minimum_maximum_and_available_extents(
    modal: Modal,
    outer_width: int,
    outer_height: int,
    expected_bounds: tuple[int, int, int, int],
) -> None:
    canvas = Canvas(outer_width, outer_height, fill=".")
    modal.draw(canvas, canvas.rect)
    changed = [
        (x, y)
        for y, line in enumerate(canvas.lines())
        for x, char in enumerate(line)
        if char != "."
    ]
    left, top, width, height = expected_bounds
    assert min(x for x, _ in changed) == left
    assert min(y for _, y in changed) == top
    assert max(x for x, _ in changed) == left + width - 1
    assert max(y for _, y in changed) == top + height - 1


def test_modal_uses_logical_outer_rect_when_canvas_clips_it() -> None:
    canvas = Canvas(8, 4, fill=".")
    Modal("body", preferred_width=7, preferred_height=3).draw(
        canvas,
        Rect(-2, -1, 11, 5),
    )
    assert canvas.lines() == [
        "+ [x] +.",
        "|body |.",
        "+-----+.",
        "........",
    ]


def test_modal_ansi_styles_do_not_change_visible_geometry() -> None:
    modal = Modal(
        Label("body", style=Style(foreground="green")),
        title="Hi",
        preferred_width=9,
        preferred_height=5,
        style=Style(background="blue"),
        title_style=Style(bold=True, foreground="red"),
    )
    plain = render_lines(modal, 13, 7, color=False)
    colored = render_lines(modal, 13, 7, color=True)

    assert [strip_ansi(line) for line in colored] == plain
    assert all(visible_width(line) == 13 for line in colored)
    assert colored[1] == (
        "  \x1b[44m+\x1b[0m\x1b[1;31m [x] . \x1b[0m\x1b[44m+\x1b[0m  "
    )
    assert colored[2] == (
        "  \x1b[44m|\x1b[0m\x1b[32mbody\x1b[0m   \x1b[44m|\x1b[0m  "
    )
    assert colored[3] == "  \x1b[44m|\x1b[0m       \x1b[44m|\x1b[0m  "
    assert colored[0] == " " * 13
    assert "\x1b[" not in "".join(plain)


@dataclass
class _RecordingWidget:
    rects: list[Rect]

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        self.rects.append(rect)
        canvas.fill(rect, "#")


def test_closed_modal_does_not_draw_its_child_or_change_cell_styles() -> None:
    child = _RecordingWidget([])
    canvas = Canvas(7, 3, fill=".")
    canvas.fill(canvas.rect, ".", Style(background="blue"))
    before_plain = canvas.lines(color=False)
    before_colored = canvas.lines(color=True)

    Modal(child, title="Hidden", open=False).draw(canvas, canvas.rect)

    assert child.rects == []
    assert canvas.lines(color=False) == before_plain
    assert canvas.lines(color=True) == before_colored


def test_modal_participates_flexibly_in_rows_and_columns() -> None:
    row_child = _RecordingWidget([])
    row = Row(
        [
            Modal(row_child, preferred_width=7, preferred_height=3),
            Label("tail", width=4),
        ],
        gap=0,
        stack_when_narrow=False,
    )
    render_lines(row, 14, 5)
    assert row_child.rects == [Rect(2, 2, 5, 1)]

    column_child = _RecordingWidget([])
    column = Column(
        [
            Modal(column_child, preferred_width=7, preferred_height=3),
            Label("tail", height=1),
        ]
    )
    render_lines(column, 11, 7)
    assert column_child.rects == [Rect(3, 2, 5, 1)]


def test_modal_draw_does_not_mutate_caller_owned_fields() -> None:
    modal = Modal(
        "body",
        title="Title",
        open=True,
        preferred_width=9,
        preferred_height=5,
        min_width=5,
        min_height=2,
        max_width=11,
        max_height=6,
        style=Style(foreground="blue"),
        title_style=Style(foreground="red"),
    )
    before = (
        modal.content,
        modal.title,
        modal.open,
        modal.preferred_width,
        modal.preferred_height,
        modal.min_width,
        modal.min_height,
        modal.max_width,
        modal.max_height,
        modal.style,
        modal.title_style,
    )

    render_lines(modal, 13, 7)

    assert (
        modal.content,
        modal.title,
        modal.open,
        modal.preferred_width,
        modal.preferred_height,
        modal.min_width,
        modal.min_height,
        modal.max_width,
        modal.max_height,
        modal.style,
        modal.title_style,
    ) == before


@pytest.mark.parametrize(
    "kwargs",
    [
        {"preferred_width": -1},
        {"preferred_height": -1},
        {"min_width": -1},
        {"min_height": -1},
        {"max_width": -1},
        {"max_height": -1},
        {"min_width": 8, "max_width": 7},
        {"min_height": 4, "max_height": 3},
    ],
)
def test_modal_rejects_invalid_dimensions(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        Modal("content", **kwargs)


def test_modal_is_a_stable_public_export() -> None:
    assert "Modal" in utui.__all__
    parameters = inspect.signature(Modal).parameters
    assert list(parameters) == [
        "content",
        "title",
        "open",
        "preferred_width",
        "preferred_height",
        "min_width",
        "min_height",
        "max_width",
        "max_height",
        "style",
        "title_style",
    ]
    assert parameters["content"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for name, parameter in parameters.items()
        if name != "content"
    )
    assert parameters["content"].default is inspect.Parameter.empty
    assert parameters["title"].default == ""
    assert parameters["open"].default is True
    assert parameters["preferred_width"].default == 40
    assert parameters["preferred_height"].default == 10
    assert parameters["min_width"].default == 7
    assert parameters["min_height"].default == 3
    assert parameters["max_width"].default is None
    assert parameters["max_height"].default is None
    assert parameters["style"].default == PLAIN
    assert parameters["title_style"].default == Style(bold=True, bright=True)
    assert not hasattr(Modal(""), "width")
    assert not hasattr(Modal(""), "height")

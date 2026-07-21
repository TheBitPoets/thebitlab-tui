"""Snapshots and contracts for the first Phase 2 presentation primitives."""

from __future__ import annotations

import inspect

import pytest

import thebitlab_tui
from thebitlab_tui import (
    Canvas,
    Column,
    Divider,
    Label,
    Rect,
    Row,
    StatusBadge,
    Style,
    render_lines,
    strip_ansi,
    visible_width,
)


def test_divider_default_snapshots() -> None:
    assert render_lines(Divider(), 7, 1) == ["-------"]
    assert render_lines(Divider("vertical"), 1, 4) == ["|", "|", "|", "|"]


def test_divider_centers_with_odd_spare_below_or_right() -> None:
    assert render_lines(Divider(), 7, 4) == [
        "       ",
        "-------",
        "       ",
        "       ",
    ]
    assert render_lines(Divider("vertical"), 4, 3) == [" |  ", " |  ", " |  "]


def test_divider_custom_character_and_color_keep_width_stable() -> None:
    assert render_lines(Divider(char="."), 5, 1) == ["....."]
    assert render_lines(Divider(char=" "), 5, 1) == ["     "]

    styled = Divider(style=Style(foreground="cyan"))
    assert render_lines(styled, 5, 1, color=False) == ["-----"]
    colored = render_lines(styled, 5, 1, color=True)
    assert colored == ["\x1b[36m-----\x1b[0m"]
    assert visible_width(colored[0]) == 5


def test_divider_clips_without_recentering() -> None:
    canvas = Canvas(5, 3, fill=".")
    Divider().draw(canvas, Rect(-2, 0, 6, 3))
    assert canvas.lines() == [".....", "----.", "....."]
    assert render_lines(Divider(), 0, 2) == ["", ""]
    assert render_lines(Divider(), 5, 0) == []


@pytest.mark.parametrize("char", ["", "--", "\n", "é", "\x1b[31m-\x1b[0m", 1])
def test_divider_rejects_invalid_characters(char: object) -> None:
    with pytest.raises(ValueError, match="printable ASCII"):
        Divider(char=char)  # type: ignore[arg-type]


def test_divider_rejects_unknown_orientation() -> None:
    with pytest.raises(ValueError, match="orientation"):
        Divider("diagonal")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="orientation"):
        Divider([])  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "kwargs",
    [
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
def test_divider_rejects_invalid_size_hints(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        Divider(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("status", "marker"),
    [
        ("neutral", "."),
        ("info", "i"),
        ("success", "+"),
        ("warning", "!"),
        ("error", "x"),
    ],
)
def test_status_badge_ascii_markers(status: str, marker: str) -> None:
    badge = StatusBadge("ready", status=status)  # type: ignore[arg-type]
    assert render_lines(badge, 9, 1, color=False) == [f"{marker} ready  "]


@pytest.mark.parametrize(
    ("status", "code"),
    [
        ("neutral", None),
        ("info", 94),
        ("success", 92),
        ("warning", 93),
        ("error", 91),
    ],
)
def test_status_badge_semantic_color_preserves_geometry(status: str, code: int | None) -> None:
    badge = StatusBadge("ready", status=status)  # type: ignore[arg-type]
    plain = render_lines(badge, 8, 1, color=False)[0]
    colored = render_lines(badge, 8, 1, color=True)[0]

    if code is None:
        assert colored == plain
    else:
        assert colored == f"\x1b[{code}m{plain.rstrip()}\x1b[0m "
    assert strip_ansi(colored) == plain
    assert visible_width(colored) == 8


@pytest.mark.parametrize(
    ("width", "expected"),
    [(0, ""), (1, "x"), (2, "x "), (3, "x ."), (6, "x r...")],
)
def test_status_badge_preserves_marker_when_narrow(width: int, expected: str) -> None:
    assert render_lines(StatusBadge("ready", status="error"), width, 1) == [expected]


def test_status_badge_normalizes_text_and_handles_empty_content() -> None:
    assert render_lines(StatusBadge("", status="info"), 4, 1) == ["i   "]
    assert render_lines(StatusBadge("\x1b[31mready\x1b[0m\nnow"), 11, 1) == [
        ". ready now"
    ]


def test_status_badge_explicit_style_overrides_color_not_marker() -> None:
    badge = StatusBadge(
        "go",
        status="warning",
        style=Style(bold=True, foreground="magenta"),
    )
    assert render_lines(badge, 6, 1, color=False) == ["! go  "]
    assert render_lines(badge, 6, 1, color=True) == ["\x1b[1;35m! go\x1b[0m  "]


def test_status_badge_has_read_only_one_row_layout_attributes() -> None:
    badge = StatusBadge("ok")
    assert (badge.height, badge.min_height, badge.max_height) == (1, 1, 1)
    for name in ("height", "min_height", "max_height"):
        with pytest.raises(AttributeError):
            setattr(badge, name, 2)

    assert "height" not in inspect.signature(StatusBadge).parameters


@pytest.mark.parametrize(
    "kwargs",
    [
        {"width": -1},
        {"min_width": -1},
        {"max_width": -1},
        {"min_width": 2, "max_width": 1},
    ],
)
def test_status_badge_rejects_invalid_size_hints(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError):
        StatusBadge("bad", **kwargs)  # type: ignore[arg-type]


def test_status_badge_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="unknown status"):
        StatusBadge("bad", status="missing")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unknown status"):
        StatusBadge("bad", status=[])  # type: ignore[arg-type]


def test_divider_and_badge_participate_in_structural_layout() -> None:
    column = Column([Label("top"), Divider(), Label("bot")])
    assert render_lines(column, 5, 5) == ["top  ", "     ", "-----", "bot  ", "     "]

    row = Row([Label("L"), Divider("vertical"), Label("R")], gap=0)
    assert render_lines(row, 7, 1) == ["L  |R  "]

    badges = Column([Label("body"), StatusBadge("ok", status="success")])
    assert render_lines(badges, 6, 3) == ["body  ", "      ", "+ ok  "]

    fixed = Column([Divider(height=3), Label("x")])
    assert render_lines(fixed, 5, 4) == ["     ", "-----", "     ", "x    "]

    capped_badge = Row(
        [StatusBadge("ok", max_width=4), Label("tail")],
        gap=1,
        stack_when_narrow=False,
    )
    assert render_lines(capped_badge, 9, 1) == [". ok tail"]

    clipped_minimum = Row(
        [StatusBadge("ok", min_width=4), Label("x", min_width=4)],
        gap=1,
        stack_when_narrow=False,
    )
    assert render_lines(clipped_minimum, 5, 1) == [". . x"]

    capped_divider = Row(
        [Divider(max_width=3), Label("x")],
        gap=0,
        stack_when_narrow=False,
    )
    assert render_lines(capped_divider, 5, 1) == ["---x "]


def test_phase_two_primitives_are_public_exports() -> None:
    assert {"Divider", "StatusBadge"} <= set(thebitlab_tui.__all__)
    divider_parameters = inspect.signature(Divider).parameters
    badge_parameters = inspect.signature(StatusBadge).parameters

    assert list(divider_parameters) == [
        "orientation",
        "char",
        "style",
        "width",
        "height",
        "min_width",
        "min_height",
        "max_width",
        "max_height",
    ]
    assert divider_parameters["orientation"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for name, parameter in divider_parameters.items()
        if name != "orientation"
    )
    assert {
        name: parameter.default for name, parameter in divider_parameters.items()
    } == {
        "orientation": "horizontal",
        "char": None,
        "style": Style(),
        "width": None,
        "height": None,
        "min_width": 1,
        "min_height": 1,
        "max_width": None,
        "max_height": None,
    }

    assert list(badge_parameters) == ["text", "status", "style", "width", "min_width", "max_width"]
    assert badge_parameters["text"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for name, parameter in badge_parameters.items()
        if name != "text"
    )
    assert badge_parameters["text"].default is inspect.Parameter.empty
    assert {name: badge_parameters[name].default for name in list(badge_parameters)[1:]} == {
        "status": "neutral",
        "style": None,
        "width": None,
        "min_width": 1,
        "max_width": None,
    }


def test_status_badge_draws_no_rows_at_zero_height() -> None:
    assert render_lines(StatusBadge("ok"), 4, 0) == []

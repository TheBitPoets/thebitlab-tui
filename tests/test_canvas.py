import inspect

import pytest

from thebitlab_tui import Canvas, Rect, Style, strip_ansi, visible_width


def test_truncation_with_ellipsis_preserves_canvas_width() -> None:
    canvas = Canvas(8, 1)
    canvas.write(0, 0, "a very long value", max_width=8)
    assert canvas.lines() == ["a ver..."]
    assert len(canvas.lines()[0]) == 8


def test_canvas_uses_available_width_for_default_ellipsis() -> None:
    canvas = Canvas(5, 1)
    canvas.write(0, 0, "abcdef")
    assert canvas.lines() == ["ab..."]


def test_short_text_keeps_stable_line_width() -> None:
    canvas = Canvas(8, 1)
    canvas.write(0, 0, "short", max_width=8)
    assert canvas.lines() == ["short   "]


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_canvas_normalizes_line_endings_to_one_space(newline: str) -> None:
    canvas = Canvas(8, 1)
    canvas.write(0, 0, f"one{newline}two", max_width=8)
    assert canvas.lines() == ["one two "]


def test_tiny_ellipsis_widths() -> None:
    for width in range(1, 4):
        canvas = Canvas(width, 1)
        canvas.write(0, 0, "long", max_width=width)
        assert canvas.lines() == ["." * width]


def test_writes_and_shapes_are_clipped() -> None:
    canvas = Canvas(5, 3)
    canvas.write(-2, 1, "abcdef")
    canvas.fill(Rect(4, 2, 4, 4), ".")
    assert canvas.lines() == ["     ", "cdef ", "    ."]


def test_ascii_border_snapshot() -> None:
    canvas = Canvas(6, 3)
    canvas.border(Rect(0, 0, 6, 3))
    assert canvas.lines() == ["+----+", "|    |", "+----+"]


def _source_canvas() -> Canvas:
    source = Canvas(4, 3)
    for y, text in enumerate(("ABCD", "EFGH", "IJKL")):
        source.write(0, y, text, ellipsis=False)
    return source


def test_blit_full_canvas_and_explicit_source_rectangle() -> None:
    source = _source_canvas()
    destination = Canvas(6, 4, fill=".")
    destination.blit(source, x=1, y=1)
    assert destination.lines() == [
        "......",
        ".ABCD.",
        ".EFGH.",
        ".IJKL.",
    ]

    cropped = Canvas(6, 3, fill=".")
    cropped.blit(source, source_rect=Rect(1, 1, 2, 2))
    assert cropped.lines() == ["FG....", "JK....", "......"]


def test_blit_preserves_requested_origin_when_source_is_clipped() -> None:
    source = Canvas(4, 2)
    source.write(0, 0, "ABCD", ellipsis=False)
    source.write(0, 1, "EFGH", ellipsis=False)
    destination = Canvas(6, 4, fill=".")

    destination.blit(source, x=1, y=1, source_rect=Rect(-1, -1, 4, 3))
    assert destination.lines() == [
        "......",
        "......",
        "..ABC.",
        "..EFG.",
    ]


def test_blit_clips_negative_destination_and_both_edges_together() -> None:
    source = Canvas(5, 2)
    source.write(0, 0, "ABCDE", ellipsis=False)
    source.write(0, 1, "FGHIJ", ellipsis=False)

    destination = Canvas(6, 2, fill=".")
    destination.blit(source, x=-2, y=-1)
    assert destination.lines() == ["HIJ...", "......"]

    combined = Canvas(6, 1, fill=".")
    combined.blit(source, x=-2, source_rect=Rect(-1, 0, 5, 1))
    assert combined.lines() == ["BCD..."]


def test_blit_clips_source_and_destination_right_and_bottom_edges() -> None:
    source = _source_canvas()
    source.set(2, 2, "K", Style(foreground="green"))
    destination = Canvas(5, 4, fill=".")

    destination.blit(source, x=3, y=2, source_rect=Rect(1, 1, 5, 4))

    assert destination.lines(color=False) == [
        ".....",
        ".....",
        "...FG",
        "...JK",
    ]
    assert destination.lines(color=True)[3] == "...J\x1b[32mK\x1b[0m"


def test_blit_preserves_styles_without_affecting_visible_width() -> None:
    source = Canvas(3, 1)
    source.set(0, 0, "A", Style(foreground="red"))
    source.set(1, 0, "B", Style(foreground="green"))
    source.set(2, 0, "C", Style(background="blue"))
    destination = Canvas(5, 1, fill=".")
    destination.blit(source, x=1)

    plain = destination.lines(color=False)[0]
    colored = destination.lines(color=True)[0]
    assert plain == ".ABC."
    assert colored == ".\x1b[31mA\x1b[0m\x1b[32mB\x1b[0m\x1b[44mC\x1b[0m."
    assert strip_ansi(colored) == plain
    assert visible_width(colored) == 5


@pytest.mark.parametrize(
    ("source_rect", "x", "expected"),
    [
        (Rect(0, 0, 3, 1), 1, "AABC"),
        (Rect(1, 0, 3, 1), 0, "BCDD"),
        (Rect(-1, 0, 4, 1), 0, "AABC"),
    ],
)
def test_blit_horizontal_self_overlap_uses_prewrite_snapshot(
    source_rect: Rect,
    x: int,
    expected: str,
) -> None:
    canvas = Canvas(4, 1)
    styles = [
        Style(foreground="red"),
        Style(foreground="green"),
        Style(foreground="blue"),
        Style(foreground="yellow"),
    ]
    for index, (char, style) in enumerate(zip("ABCD", styles)):
        canvas.set(index, 0, char, style)

    before = canvas.lines(color=True)[0]
    canvas.blit(canvas, x=x, source_rect=source_rect)

    assert canvas.lines(color=False) == [expected]
    if expected == "AABC":
        assert canvas.lines(color=True) == [
            "\x1b[31mAA\x1b[0m\x1b[32mB\x1b[0m\x1b[34mC\x1b[0m"
        ]
    else:
        assert canvas.lines(color=True) == [
            "\x1b[32mB\x1b[0m\x1b[34mC\x1b[0m\x1b[33mDD\x1b[0m"
        ]
    assert before != canvas.lines(color=True)[0]


@pytest.mark.parametrize(
    ("source_rect", "y", "expected"),
    [
        (Rect(0, 0, 1, 3), 1, ["A", "A", "B", "C"]),
        (Rect(0, 1, 1, 3), 0, ["B", "C", "D", "D"]),
    ],
)
def test_blit_vertical_self_overlap_uses_prewrite_snapshot(
    source_rect: Rect,
    y: int,
    expected: list[str],
) -> None:
    canvas = Canvas(1, 4)
    styles = [
        Style(foreground="red"),
        Style(foreground="green"),
        Style(foreground="blue"),
        Style(foreground="yellow"),
    ]
    for index, (char, style) in enumerate(zip("ABCD", styles)):
        canvas.set(0, index, char, style)

    canvas.blit(canvas, y=y, source_rect=source_rect)

    assert canvas.lines(color=False) == expected
    colored = canvas.lines(color=True)
    expected_styles = (
        [styles[0], styles[0], styles[1], styles[2]]
        if y == 1
        else [styles[1], styles[2], styles[3], styles[3]]
    )
    assert colored == [style.apply(char) for char, style in zip(expected, expected_styles)]


def test_blit_empty_regions_and_canvases_are_noops() -> None:
    destination = Canvas(3, 2, fill=".")
    destination.blit(Canvas(0, 2))
    destination.blit(Canvas(2, 0))
    destination.blit(Canvas(2, 2), source_rect=Rect(0, 0, 0, 2))
    destination.blit(Canvas(2, 2), source_rect=Rect(0, 0, 2, 0))
    Canvas(0, 0).blit(Canvas(2, 2))
    assert destination.lines() == ["...", "..."]


def test_blit_has_the_approved_public_signature() -> None:
    parameters = inspect.signature(Canvas.blit).parameters
    assert list(parameters) == ["self", "source", "x", "y", "source_rect"]
    assert parameters["source"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert all(
        parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
        for name in ("x", "y", "source_rect")
    )
    assert {name: parameters[name].default for name in ("x", "y", "source_rect")} == {
        "x": 0,
        "y": 0,
        "source_rect": None,
    }

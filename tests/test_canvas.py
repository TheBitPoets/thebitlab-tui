from thebitlab_tui import Canvas, Rect


def test_truncation_with_ellipsis_preserves_canvas_width() -> None:
    canvas = Canvas(8, 1)
    canvas.write(0, 0, "a very long value", max_width=8)
    assert canvas.lines() == ["a ver..."]
    assert len(canvas.lines()[0]) == 8


def test_short_text_keeps_stable_line_width() -> None:
    canvas = Canvas(8, 1)
    canvas.write(0, 0, "short", max_width=8)
    assert canvas.lines() == ["short   "]


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


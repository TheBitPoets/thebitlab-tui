from thebitlab_tui import Column, Label, Panel, Row, Size, render_lines
from thebitlab_tui.layout import allocate


def test_fixed_and_proportional_allocation() -> None:
    specs = [Size.fixed_size(4), Size.flexible(1), Size.flexible(2)]
    assert allocate(16, specs) == [4, 4, 8]


def test_row_and_column_snapshot() -> None:
    row = Row([Label("left"), Label("right")], sizes=[Size.fixed_size(6), Size.flexible()])
    assert render_lines(row, 14, 1) == ["left   right  "]
    column = Column([Label("top"), Label("bottom")], sizes=[Size.fixed_size(1), Size.flexible()])
    assert render_lines(column, 8, 3) == ["top     ", "bottom  ", "        "]


def _three_panels() -> Row:
    return Row(
        [
            Panel("one", title="A", min_width=10),
            Panel("two", title="B", min_width=10),
            Panel("three", title="C", min_width=10),
        ],
        gap=1,
    )


def test_three_panels_are_side_by_side_when_wide() -> None:
    assert render_lines(_three_panels(), 35, 3) == [
        "+ A ------+ + B ------+ + C ------+",
        "|one      | |two      | |three    |",
        "+---------+ +---------+ +---------+",
    ]


def test_three_panels_stack_when_terminal_is_narrow() -> None:
    lines = render_lines(_three_panels(), 20, 11)
    assert lines == [
        "+ A ---------------+",
        "|one               |",
        "+------------------+",
        "                    ",
        "+ B ---------------+",
        "|two               |",
        "+------------------+",
        "                    ",
        "+ C ---------------+",
        "|three             |",
        "+------------------+",
    ]
    assert all(len(line) == 20 for line in lines)

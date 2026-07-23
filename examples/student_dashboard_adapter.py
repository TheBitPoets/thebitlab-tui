"""Executable, non-public reference adapter for a neutral student dashboard.

This module demonstrates the approved Phase 4 integration boundary. It consumes only synthetic
presentation rows and normalized caller-owned state, builds existing public widgets, and returns
pure renderer output. It never imports the student application or reads persisted layout files.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from typing import Any

from thebitlab_tui import (
    Column,
    Divider,
    Label,
    Panel,
    Row,
    Size,
    Widget,
    get_terminal_size,
    render_lines,
    supports_color,
)

try:
    from .student_dashboard_fixtures import (
        PRESENTATION,
        SECTIONS,
        SECTION_IDS,
        SECTION_TITLES,
    )
except ImportError:  # pragma: no cover - exercised by the executable script smoke test
    from student_dashboard_fixtures import (
        PRESENTATION,
        SECTIONS,
        SECTION_IDS,
        SECTION_TITLES,
    )


BREAKPOINT = 90
MISSING_ROW = "Unavailable"


def _normalized_rows(section: Mapping[str, Any]) -> tuple[str, ...]:
    rows = section.get("rows", ())
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("section rows must be a sequence of strings")
    normalized = tuple(rows)
    if not all(isinstance(row, str) for row in normalized):
        raise ValueError("section rows must contain only strings")
    return normalized or (MISSING_ROW,)


def _section_map(sections: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    mapped: dict[str, Mapping[str, Any]] = {}
    for section in sections:
        identifier = section.get("id")
        if identifier not in SECTION_IDS:
            raise ValueError(f"unknown section id: {identifier!r}")
        if identifier in mapped:
            raise ValueError(f"duplicate section id: {identifier}")
        mapped[identifier] = section
    return mapped


def _ordered_ids(presentation: Mapping[str, Any]) -> tuple[str, ...]:
    order = tuple(presentation.get("order", ()))
    if len(order) != len(SECTION_IDS) or set(order) != set(SECTION_IDS):
        raise ValueError("order must be a permutation of all stable section ids")
    return order


def _build_panel(
    identifier: str,
    section: Mapping[str, Any] | None,
    *,
    focused: bool,
    collapsed: bool,
) -> tuple[Panel, int]:
    if section is None:
        title = SECTION_TITLES[identifier]
        rows = (MISSING_ROW,)
    else:
        title = section.get("title", SECTION_TITLES[identifier])
        if not isinstance(title, str):
            raise ValueError("section title must be a string")
        rows = _normalized_rows(section)
    height = 3 if collapsed else max(3, len(rows) + 2)
    return (
        Panel(
            Label("\n".join(rows)),
            title=title,
            focused=focused,
            collapsed=collapsed,
        ),
        height,
    )


def _build_column(entries: Sequence[tuple[Panel, int]]) -> Column:
    return Column(
        [panel for panel, _height in entries],
        sizes=[Size.fixed_size(height) for _panel, height in entries],
    )


def _wide_widths(terminal_width: int, left_width: int) -> tuple[int, int]:
    effective_left = min(left_width, max(36, terminal_width - 39))
    right_width = max(30, terminal_width - effective_left - 3)
    return effective_left, right_width


def build_dashboard(
    sections: Sequence[Mapping[str, Any]],
    presentation: Mapping[str, Any],
    *,
    width: int,
) -> Widget:
    """Build one responsive widget tree without changing fixtures or caller state.

    Args:
        sections: Neutral, already-projected section dictionaries.
        presentation: Normalized caller-owned orientation, order, width, collapse, and focus.
        width: Current terminal width used to choose the explicit wide or narrow tree.

    Returns:
        A widget composed only from the stable public uTUI API.

    Raises:
        ValueError: If the normalized reference inputs violate the approved fixture contract.
    """

    if width < 0:
        raise ValueError("width must be non-negative")
    mapped = _section_map(sections)
    order = _ordered_ids(presentation)
    orientation = presentation.get("orientation")
    if orientation not in {"horizontal", "vertical"}:
        raise ValueError("orientation must be 'horizontal' or 'vertical'")
    left_width = presentation.get("left_width")
    if not isinstance(left_width, int) or isinstance(left_width, bool) or left_width < 0:
        raise ValueError("left_width must be a non-negative integer")
    collapsed = frozenset(presentation.get("collapsed", ()))
    if not collapsed <= set(SECTION_IDS):
        raise ValueError("collapsed contains an unknown section id")
    focus = presentation.get("focus")
    if focus not in SECTION_IDS:
        raise ValueError("focus must be a stable section id")

    entries = [
        _build_panel(
            identifier,
            mapped.get(identifier),
            focused=focus == identifier,
            collapsed=identifier in collapsed,
        )
        for identifier in order
    ]
    if orientation != "horizontal" or width < BREAKPOINT:
        return _build_column(entries)

    effective_left, right_width = _wide_widths(width, left_width)
    return Row(
        [
            _build_column(entries[:5]),
            Divider("vertical"),
            _build_column(entries[5:]),
        ],
        sizes=[
            Size.fixed_size(effective_left),
            Size.fixed_size(3),
            Size.fixed_size(right_width),
        ],
        gap=0,
        stack_when_narrow=False,
    )


def render_reference_frame(
    sections: Sequence[Mapping[str, Any]] = SECTIONS,
    presentation: Mapping[str, Any] = PRESENTATION,
    *,
    width: int,
    height: int,
    color: bool = False,
) -> list[str]:
    """Render one deterministic reference frame without printing or mutating input."""

    return render_lines(
        build_dashboard(sections, presentation, width=width),
        width,
        height,
        color=color,
    )


def main() -> None:
    """Render the synthetic dashboard once for manual Windows/Linux inspection."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    arguments = parser.parse_args()
    terminal = get_terminal_size()
    width = terminal.width if arguments.width is None else max(1, arguments.width)
    height = terminal.height if arguments.height is None else max(1, arguments.height)
    color = supports_color(no_color=arguments.no_color)
    print(
        "\n".join(
            render_reference_frame(
                width=width,
                height=height,
                color=color,
            )
        )
    )


if __name__ == "__main__":
    main()

"""Executable, non-public reference adapter for a neutral student dashboard.

This module demonstrates the approved Phase 4 integration boundary. It consumes only synthetic
presentation rows and normalized caller-owned state, builds existing public widgets, and returns
pure renderer output. It never imports the student application or reads persisted layout files.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from thebitlab_tui import (
    Canvas,
    Column,
    Divider,
    Label,
    ListView,
    Modal,
    Panel,
    Rect,
    Row,
    ScrollView,
    Size,
    Widget,
    get_terminal_size,
    render_lines,
    supports_color,
)

try:
    from .student_dashboard_fixtures import (
        INTERACTION,
        PRESENTATION,
        SECTIONS,
        SECTION_IDS,
        SECTION_TITLES,
    )
except ImportError:  # pragma: no cover - exercised by the executable script smoke test
    from student_dashboard_fixtures import (
        INTERACTION,
        PRESENTATION,
        SECTIONS,
        SECTION_IDS,
        SECTION_TITLES,
    )


BREAKPOINT = 90
MISSING_ROW = "Unavailable"
PANEL_BODY_ROWS = 3


@dataclass(slots=True)
class _ReferenceFrame:
    """Draw the caller-composed dashboard first and optional modal second."""

    dashboard: Widget
    modal: Modal

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        """Draw one pure frame without owning visibility or interaction state."""

        self.dashboard.draw(canvas, rect)
        self.modal.draw(canvas, rect)


def _normalized_rows(section: Mapping[str, Any]) -> tuple[str, ...]:
    rows = section.get("rows", ())
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("section rows must be a sequence of strings")
    normalized = tuple(rows)
    if not all(isinstance(row, str) for row in normalized):
        raise ValueError("section rows must contain only strings")
    return normalized or (MISSING_ROW,)


def _normalized_items(section: Mapping[str, Any]) -> tuple[str, ...] | None:
    if "items" not in section:
        return None
    items = section["items"]
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("section items must be a sequence of strings")
    normalized = tuple(items)
    if not all(isinstance(item, str) for item in normalized):
        raise ValueError("section items must contain only strings")
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
    section_offset: int,
    list_offset: int,
    active_index: int | None,
) -> tuple[Panel, int]:
    if section is None:
        title = SECTION_TITLES[identifier]
        rows = (MISSING_ROW,)
        items = None
    else:
        title = section.get("title", SECTION_TITLES[identifier])
        if not isinstance(title, str):
            raise ValueError("section title must be a string")
        rows = _normalized_rows(section)
        items = _normalized_items(section)
    if items is None:
        content: Widget = ScrollView(
            Label("\n".join(rows)),
            content_height=len(rows),
            scroll_offset=section_offset,
        )
        body_height = min(PANEL_BODY_ROWS, len(rows))
    else:
        effective_active = (
            None if active_index is None else min(active_index, len(items) - 1)
        )
        content = ListView(
            items,
            active_index=effective_active,
            scroll_offset=list_offset,
            focused=focused,
        )
        body_height = min(PANEL_BODY_ROWS, len(items))
    height = 3 if collapsed else max(3, body_height + 2)
    return (
        Panel(
            content,
            title=title,
            focused=focused,
            collapsed=collapsed,
        ),
        height,
    )


def _build_column(entries: Sequence[tuple[Panel, int]]) -> tuple[Column, int]:
    return (
        Column(
            [panel for panel, _height in entries],
            sizes=[Size.fixed_size(height) for _panel, height in entries],
        ),
        sum(height for _panel, height in entries),
    )


def _wide_widths(terminal_width: int, left_width: int) -> tuple[int, int]:
    effective_left = min(left_width, max(36, terminal_width - 39))
    right_width = max(30, terminal_width - effective_left - 3)
    return effective_left, right_width


def _interaction_offsets(
    interaction: Mapping[str, Any],
    key: str,
) -> dict[str, int]:
    offsets = interaction.get(key, {})
    if not isinstance(offsets, Mapping):
        raise ValueError(f"{key} must be a mapping")
    normalized: dict[str, int] = {}
    for identifier, value in offsets.items():
        if identifier not in SECTION_IDS:
            raise ValueError(f"{key} contains an unknown section id")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{key} values must be non-negative integers")
        normalized[identifier] = value
    return normalized


def _modal(interaction: Mapping[str, Any]) -> Modal:
    state = interaction.get("modal", {})
    if not isinstance(state, Mapping):
        raise ValueError("modal must be a mapping")
    open_value = state.get("open", False)
    title = state.get("title", "")
    rows = state.get("rows", ())
    if not isinstance(open_value, bool):
        raise ValueError("modal open must be a boolean")
    if not isinstance(title, str):
        raise ValueError("modal title must be a string")
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("modal rows must be a sequence of strings")
    normalized_rows = tuple(rows)
    if not all(isinstance(row, str) for row in normalized_rows):
        raise ValueError("modal rows must contain only strings")
    return Modal(
        Label("\n".join(normalized_rows)),
        title=title,
        open=open_value,
        preferred_width=40,
        preferred_height=max(3, len(normalized_rows) + 2),
    )


def build_dashboard(
    sections: Sequence[Mapping[str, Any]],
    presentation: Mapping[str, Any],
    *,
    width: int,
    interaction: Mapping[str, Any] = INTERACTION,
) -> Widget:
    """Build one responsive widget tree without changing fixtures or caller state.

    Args:
        sections: Neutral, already-projected section dictionaries.
        presentation: Normalized caller-owned orientation, order, width, collapse, and focus.
        width: Current terminal width used to choose the explicit wide or narrow tree.
        interaction: Caller-owned transient offsets, selection, and modal presentation.

    Returns:
        A widget composed only from the stable public uTUI API.

    Raises:
        ValueError: If the normalized reference inputs violate the approved fixture contract.
    """

    if width < 0:
        raise ValueError("width must be non-negative")
    if not isinstance(interaction, Mapping):
        raise ValueError("interaction must be a mapping")
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
    dashboard_offset = interaction.get("dashboard_offset", 0)
    if (
        not isinstance(dashboard_offset, int)
        or isinstance(dashboard_offset, bool)
        or dashboard_offset < 0
    ):
        raise ValueError("dashboard_offset must be a non-negative integer")
    section_offsets = _interaction_offsets(interaction, "section_offsets")
    list_offsets = _interaction_offsets(interaction, "list_offsets")
    active_indices = _interaction_offsets(interaction, "active_indices")

    entries = [
        _build_panel(
            identifier,
            mapped.get(identifier),
            focused=focus == identifier,
            collapsed=identifier in collapsed,
            section_offset=section_offsets.get(identifier, 0),
            list_offset=list_offsets.get(identifier, 0),
            active_index=active_indices.get(identifier),
        )
        for identifier in order
    ]
    if orientation != "horizontal" or width < BREAKPOINT:
        dashboard, content_height = _build_column(entries)
    else:
        effective_left, right_width = _wide_widths(width, left_width)
        left, left_height = _build_column(entries[:5])
        right, right_height = _build_column(entries[5:])
        content_height = max(left_height, right_height)
        dashboard = Row(
            [left, Divider("vertical"), right],
            sizes=[
                Size.fixed_size(effective_left),
                Size.fixed_size(3),
                Size.fixed_size(right_width),
            ],
            gap=0,
            stack_when_narrow=False,
        )
    return _ReferenceFrame(
        ScrollView(
            dashboard,
            content_height=content_height,
            scroll_offset=dashboard_offset,
        ),
        _modal(interaction),
    )


def render_reference_frame(
    sections: Sequence[Mapping[str, Any]] = SECTIONS,
    presentation: Mapping[str, Any] = PRESENTATION,
    *,
    width: int,
    height: int,
    color: bool = False,
    interaction: Mapping[str, Any] = INTERACTION,
) -> list[str]:
    """Render one deterministic frame without printing or mutating caller state."""

    return render_lines(
        build_dashboard(
            sections,
            presentation,
            width=width,
            interaction=interaction,
        ),
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

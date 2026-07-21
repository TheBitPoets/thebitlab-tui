"""Render ASCII dividers and semantic status badges without application state."""

from __future__ import annotations

import argparse

from thebitlab_tui import (
    Column,
    Divider,
    Label,
    Row,
    Size,
    StatusBadge,
    render_terminal,
    supports_color,
)


def build_screen() -> Column:
    """Build a presentation-only widget tree for the Phase 2 primitives."""

    comparison = Row(
        [Label("workspace", align="right"), Divider("vertical"), Label("runner")],
        sizes=[Size.flexible(), Size.fixed_size(1), Size.flexible()],
        gap=1,
    )
    children = [
        Divider(char="."),
        StatusBadge("queued", status="neutral"),
        StatusBadge("running", status="info"),
        StatusBadge("passed", status="success"),
        StatusBadge("needs attention", status="warning"),
        StatusBadge("failed", status="error"),
        Divider(),
        comparison,
    ]
    return Column(children, sizes=[Size.fixed_size(1) for _ in children])


def main() -> None:
    """Parse color policy, render one terminal-sized frame, and print it."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()
    color = supports_color(no_color=args.no_color)
    print("\n".join(render_terminal(build_screen(), color=color)))


if __name__ == "__main__":
    main()

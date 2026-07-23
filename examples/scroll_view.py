"""Render caller-owned scrolling through an isolated ``ScrollView`` viewport."""

from __future__ import annotations

import argparse

from utui import Label, Panel, ScrollView, render, supports_color


def build_screen() -> Panel:
    """Build a presentation-only activity viewport with explicit row count."""

    lines = [
        "09:00 workspace opened",
        "09:02 instructions read",
        "09:05 exercise started",
        "09:11 tests running",
        "09:12 test 1 passed",
        "09:12 test 2 passed",
        "09:13 report generated",
        "09:14 grading pending",
        "09:15 session saved",
    ]
    viewport = ScrollView(
        Label("\n".join(lines)),
        content_height=len(lines),
        scroll_offset=3,
    )
    return Panel(viewport, title="Activity", focused=True)


def main() -> None:
    """Parse color policy, render one stable snapshot, and print it."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()
    color = supports_color(no_color=args.no_color)
    print(render(build_screen(), width=40, height=8, color=color))


if __name__ == "__main__":
    main()

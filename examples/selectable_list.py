"""Render caller-owned selection and viewport state with ``ListView``."""

from __future__ import annotations

import argparse

from thebitlab_tui import ListView, Panel, render, supports_color


def build_screen() -> Panel:
    """Build a focused list without adding navigation or application logic."""

    items = [
        "setup",
        "exercise-01",
        "exercise-02",
        "exercise-03",
        "exercise-04",
        "exercise-05",
    ]
    listing = ListView(items, active_index=2, scroll_offset=1, focused=True)
    return Panel(listing, title="Exercises", focused=True)


def main() -> None:
    """Parse color policy, render one stable snapshot, and print it."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()
    color = supports_color(no_color=args.no_color)
    print(render(build_screen(), width=28, height=7, color=color))


if __name__ == "__main__":
    main()


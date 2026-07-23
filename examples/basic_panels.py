"""Responsive three-panel example."""

from __future__ import annotations

import argparse

from utui import Panel, Row, render_terminal, supports_color


def build_screen() -> Row:
    return Row(
        [
            Panel("Exercise 01\nImplement the function", title="Assignment", min_width=24),
            Panel("No recent events", title="Activity", min_width=22),
            Panel("3 passed\n0 failed", title="Tests", focused=True, min_width=18),
        ],
        gap=1,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()
    color = supports_color(no_color=args.no_color)
    print("\n".join(render_terminal(build_screen(), color=color)))


if __name__ == "__main__":
    main()


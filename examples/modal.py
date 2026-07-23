"""Render an application-owned base layer and centered ``Modal``."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from utui import Canvas, Label, Modal, Panel, Rect, render, supports_color


@dataclass(slots=True)
class HelpOverlay:
    """Compose base content first and a caller-controlled modal second."""

    open: bool = True

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        """Draw both presentation layers without handling input or printing."""

        Panel(
            Label("Exercise 01\nTests: 3 passed\nStatus: ready"),
            title="Workspace",
        ).draw(canvas, rect)
        Modal(
            "Press Escape or q to close",
            title="Quick help",
            open=self.open,
            preferred_width=34,
            preferred_height=7,
        ).draw(canvas, rect)


def main() -> None:
    """Parse color policy, render one stable frame, and print it."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()
    color = supports_color(no_color=args.no_color)
    print(render(HelpOverlay(), width=48, height=12, color=color))


if __name__ == "__main__":
    main()

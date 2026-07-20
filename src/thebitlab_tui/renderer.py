"""Pure render entry points plus an opt-in terminal-sized helper."""

from __future__ import annotations

from .canvas import Canvas
from .geometry import Rect
from .terminal import get_terminal_size
from .widgets import Widget, draw_widget


def render_lines(widget: Widget, width: int, height: int, *, color: bool = False) -> list[str]:
    """Render a widget into stable-width lines without printing."""

    canvas = Canvas(width, height)
    draw_widget(widget, canvas, Rect(0, 0, width, height))
    return canvas.lines(color=color)


def render(widget: Widget, width: int, height: int, *, color: bool = False) -> str:
    """Render a widget to one newline-separated string without printing."""

    return "\n".join(render_lines(widget, width, height, color=color))


def render_terminal(
    widget: Widget,
    *,
    color: bool = False,
    fallback: tuple[int, int] = (80, 24),
) -> list[str]:
    """Read the current terminal size on every call, then render one frame."""

    size = get_terminal_size(fallback)
    return render_lines(widget, size.width, size.height, color=color)

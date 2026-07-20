"""Leaf and framed widgets. Widgets draw but never print."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from .canvas import Canvas
from .geometry import Rect
from .styles import PLAIN, Style, strip_ansi, truncate


@runtime_checkable
class Widget(Protocol):
    """Structural widget protocol; implementations only need ``draw``."""

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        """Draw inside ``rect`` while relying on canvas clipping."""

        ...


def draw_widget(widget: Widget | str, canvas: Canvas, rect: Rect) -> None:
    """Draw a widget or adapt a plain string to a :class:`Label`."""

    if isinstance(widget, str):
        Label(widget).draw(canvas, rect)
    else:
        widget.draw(canvas, rect)


@dataclass(slots=True)
class Label:
    """Draw text with alignment, wrapping, or ellipsis truncation.

    Args:
        text: Text to draw; explicit newlines create logical rows.
        align: ``left``, ``center``, or ``right``.
        wrap: Wrap long logical rows when true.
        truncate: Use ellipsis when wrapping is disabled and text is too wide.
        style: Cell style applied to visible text.

    ``wrap=True`` takes precedence over truncation. Explicit newlines create logical rows. Layout
    containers may use the optional fixed, minimum, and maximum dimensions.
    """

    text: str
    align: str = "left"
    wrap: bool = False
    truncate: bool = True
    style: Style = PLAIN
    width: int | None = None
    height: int | None = None
    min_width: int = 1
    min_height: int = 1
    max_width: int | None = None
    max_height: int | None = None

    def __post_init__(self) -> None:
        if self.align not in {"left", "center", "right"}:
            raise ValueError("align must be 'left', 'center', or 'right'")

    def _lines(self, width: int) -> list[str]:
        if width <= 0:
            return []
        result: list[str] = []
        for source in strip_ansi(self.text).splitlines() or [""]:
            if self.wrap:
                result.extend(
                    textwrap.wrap(
                        source,
                        width=width,
                        replace_whitespace=False,
                        drop_whitespace=True,
                    )
                    or [""]
                )
            elif self.truncate:
                result.append(truncate(source, width))
            else:
                result.append(source[:width])
        return result

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        """Draw the visible text rows inside ``rect`` without printing."""

        area = rect.intersect(canvas.rect)
        if area.is_empty:
            return
        for row, line in enumerate(self._lines(rect.width)[: rect.height]):
            if self.align == "right":
                offset = max(0, rect.width - len(line))
            elif self.align == "center":
                offset = max(0, (rect.width - len(line)) // 2)
            else:
                offset = 0
            canvas.write(
                rect.x + offset,
                rect.y + row,
                line,
                max_width=rect.width - offset,
                style=self.style,
            )


@dataclass(slots=True)
class Panel:
    """Frame content with an optional ASCII border and title.

    Args:
        content: Child widget or plain string adapted to :class:`Label`.
        title: Text embedded in the top border.
        focused: Show the textual focus marker and focus style.
        collapsed: Draw only the three-row frame and hide content.
        border: Draw the ASCII frame when true.

    Focus and collapsed state remain presentation inputs owned by the caller. Both states include
    textual markers, so they remain visible with ANSI disabled.
    """

    content: Widget | str
    title: str = ""
    focused: bool = False
    collapsed: bool = False
    border: bool = True
    style: Style = PLAIN
    title_style: Style = field(default_factory=lambda: Style(bold=True, bright=True))
    focus_style: Style = field(default_factory=lambda: Style(bold=True, foreground="bright_white"))
    width: int | None = None
    height: int | None = None
    min_width: int = 5
    min_height: int = 3
    max_width: int | None = None
    max_height: int | None = None

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        """Draw the frame, title markers, and visible content inside ``rect``."""

        if rect.is_empty or rect.intersect(canvas.rect).is_empty:
            return
        panel_height = min(rect.height, 3) if self.collapsed else rect.height
        panel_rect = Rect(rect.x, rect.y, rect.width, panel_height)
        if self.border:
            canvas.border(panel_rect, self.focus_style if self.focused else self.style)
        has_header = bool(self.title or self.focused or self.collapsed)
        self._draw_title(canvas, panel_rect, bordered=self.border)
        if self.collapsed:
            return
        if self.border:
            content_rect = panel_rect.inset(1)
        elif has_header:
            content_rect = Rect(
                panel_rect.x,
                panel_rect.y + 1,
                panel_rect.width,
                max(0, panel_rect.height - 1),
            )
        else:
            content_rect = panel_rect
        draw_widget(self.content, canvas, content_rect)

    def _draw_title(self, canvas: Canvas, rect: Rect, *, bordered: bool) -> None:
        if rect.is_empty or not (self.title or self.focused or self.collapsed):
            return
        inner_width = max(0, rect.width - 2) if bordered else rect.width
        padding = 1 if bordered else 0
        available = max(0, inner_width - (padding * 2))

        # Decorative title padding is expendable when a narrow panel needs the
        # cells to communicate state. Focus wins if only one cell is available.
        needs_state_cell = available < 1 <= inner_width
        needs_combined_state_cells = (
            self.focused and self.collapsed and available < 2 <= inner_width
        )
        if needs_state_cell or needs_combined_state_cells:
            padding = 0
            available = inner_width

        if self.focused and self.collapsed:
            if available >= 4:
                marker = ">[+]"
            elif available >= 2:
                marker = ">+"
            else:
                marker = ">"
        elif self.focused:
            marker = ">"
        elif self.collapsed:
            marker = "+" if available < 3 else "[+]"
        else:
            marker = ""
        if marker:
            prefix = marker[:available]
            if len(prefix) < available:
                prefix += " "
            remaining = max(0, available - len(prefix))
            title = prefix + truncate(self.title, remaining)
        else:
            title = truncate(self.title, available)
        if not title:
            return
        styled = self.focus_style if self.focused else self.title_style
        if bordered:
            rendered_title = f" {title} " if padding else title
            canvas.write(rect.x + 1, rect.y, rendered_title, max_width=inner_width, style=styled)
        else:
            canvas.write(rect.x, rect.y, title, max_width=rect.width, style=styled)

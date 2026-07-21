"""Pure leaf, framing, selection, divider, and semantic-status widgets."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from typing import ClassVar, Literal, Protocol, Sequence, runtime_checkable

from .canvas import Canvas
from .geometry import Rect
from .styles import PLAIN, Style, strip_ansi, truncate


_BADGE_MARKERS = {
    "neutral": ".",
    "info": "i",
    "success": "+",
    "warning": "!",
    "error": "x",
}
_BADGE_STYLES = {
    "neutral": PLAIN,
    "info": Style(foreground="bright_blue"),
    "success": Style(foreground="bright_green"),
    "warning": Style(foreground="bright_yellow"),
    "error": Style(foreground="bright_red"),
}


def _validate_size_hints(
    *,
    width: int | None,
    min_width: int,
    max_width: int | None,
    height: int | None = None,
    min_height: int = 0,
    max_height: int | None = None,
) -> None:
    values = {
        "width": width,
        "height": height,
        "min_width": min_width,
        "min_height": min_height,
        "max_width": max_width,
        "max_height": max_height,
    }
    for name, value in values.items():
        if value is not None and value < 0:
            raise ValueError(f"{name} must be non-negative")
    if max_width is not None and max_width < min_width:
        raise ValueError("max_width cannot be smaller than min_width")
    if max_height is not None and max_height < min_height:
        raise ValueError("max_height cannot be smaller than min_height")


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
class Divider:
    """Draw one centered horizontal or vertical ASCII line.

    Args:
        orientation: ``"horizontal"`` or ``"vertical"``.
        char: Optional printable one-cell ASCII character. The defaults are ``-`` horizontally
            and ``|`` vertically.
        style: Style applied to every visible divider cell.
        width: Optional fixed layout width.
        height: Optional fixed layout height.
        min_width: Soft minimum layout width.
        min_height: Soft minimum layout height.
        max_width: Optional maximum layout width.
        max_height: Optional maximum layout height.

    A horizontal divider defaults to a fixed height of one cell; a vertical divider defaults to a
    fixed width of one cell. Larger assigned rectangles place an odd spare cell below or to the
    right of the line. Invalid orientation, characters, or size hints raise :class:`ValueError`.
    """

    orientation: Literal["horizontal", "vertical"] = "horizontal"
    char: str | None = field(default=None, kw_only=True)
    style: Style = field(default=PLAIN, kw_only=True)
    width: int | None = field(default=None, kw_only=True)
    height: int | None = field(default=None, kw_only=True)
    min_width: int = field(default=1, kw_only=True)
    min_height: int = field(default=1, kw_only=True)
    max_width: int | None = field(default=None, kw_only=True)
    max_height: int | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if self.orientation not in ("horizontal", "vertical"):
            raise ValueError("orientation must be 'horizontal' or 'vertical'")
        if self.char is not None and (
            not isinstance(self.char, str)
            or len(self.char) != 1
            or not self.char.isascii()
            or not self.char.isprintable()
        ):
            raise ValueError("char must be one printable ASCII cell")
        if self.orientation == "horizontal" and self.height is None:
            self.height = 1
        if self.orientation == "vertical" and self.width is None:
            self.width = 1
        _validate_size_hints(
            width=self.width,
            min_width=self.min_width,
            max_width=self.max_width,
            height=self.height,
            min_height=self.min_height,
            max_height=self.max_height,
        )

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        """Draw the line inside ``rect`` while relying on canvas clipping."""

        if rect.is_empty:
            return
        if self.orientation == "horizontal":
            char = "-" if self.char is None else self.char
            y = rect.y + (rect.height - 1) // 2
            canvas.hline(rect.x, y, rect.width, char, self.style)
        else:
            char = "|" if self.char is None else self.char
            x = rect.x + (rect.width - 1) // 2
            canvas.vline(x, rect.y, rect.height, char, self.style)


@dataclass(slots=True)
class StatusBadge:
    """Draw a one-row semantic status with a stable ASCII marker.

    Args:
        text: Short label drawn after the marker and one separating space.
        status: ``neutral``, ``info``, ``success``, ``warning``, or ``error``.
        style: Explicit style override. ``None`` selects the status's semantic style: plain for
            neutral and bright blue, green, yellow, or red for the colored states.
        width: Optional fixed layout width.
        min_width: Soft minimum layout width.
        max_width: Optional maximum layout width.

    The public marker mapping is ``.``, ``i``, ``+``, ``!``, and ``x`` respectively. The marker
    always wins when the rectangle is narrow, and ANSI styling never changes visible geometry.
    Read-only ``height``, ``min_height``, and ``max_height`` attributes are all one, so structural
    layout always allocates exactly one row. Invalid statuses or size hints raise
    :class:`ValueError`.
    """

    height: ClassVar[int] = 1
    min_height: ClassVar[int] = 1
    max_height: ClassVar[int] = 1

    text: str
    status: Literal["neutral", "info", "success", "warning", "error"] = field(
        default="neutral", kw_only=True
    )
    style: Style | None = field(default=None, kw_only=True)
    width: int | None = field(default=None, kw_only=True)
    min_width: int = field(default=1, kw_only=True)
    max_width: int | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        if self.status not in tuple(_BADGE_MARKERS):
            raise ValueError(f"unknown status: {self.status}")
        _validate_size_hints(
            width=self.width,
            min_width=self.min_width,
            max_width=self.max_width,
        )

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        """Draw one clipped badge row inside ``rect`` without mutating state."""

        if rect.is_empty:
            return
        style = _BADGE_STYLES[self.status] if self.style is None else self.style
        canvas.write(
            rect.x,
            rect.y,
            _BADGE_MARKERS[self.status],
            max_width=min(1, rect.width),
            style=style,
            ellipsis=False,
        )
        if rect.width >= 2:
            canvas.write(rect.x + 1, rect.y, " ", max_width=1, style=style, ellipsis=False)
        if rect.width >= 3:
            canvas.write(
                rect.x + 2,
                rect.y,
                self.text,
                max_width=rect.width - 2,
                style=style,
            )


@dataclass(slots=True)
class ListView:
    """Draw a caller-owned selection and vertical viewport.

    Args:
        items: Strings to snapshot as one immutable item per row.
        active_index: Selected item, or ``None`` for no selection. A supplied index must refer to
            an item.
        scroll_offset: Requested first item. Drawing clamps the effective offset to the current
            viewport without changing this field.
        focused: Use ``>`` instead of ``*`` for the active-row marker.
        style: Style applied to inactive rows.
        active_style: Style applied to the complete active row.
        width: Optional fixed layout width.
        height: Optional fixed layout height.
        min_width: Soft minimum layout width.
        min_height: Soft minimum layout height.
        max_width: Optional maximum layout width.
        max_height: Optional maximum layout height.

    Each item occupies exactly one row. Inactive rows reserve the same two marker columns as the
    active row. Width one preserves only the marker column; longer text is truncated with an
    ellipsis. The widget never accepts events, changes selection, or scrolls automatically.
    Invalid indices, negative offsets, or invalid size hints raise :class:`ValueError`.
    """

    items: Sequence[str]
    active_index: int | None = field(default=None, kw_only=True)
    scroll_offset: int = field(default=0, kw_only=True)
    focused: bool = field(default=False, kw_only=True)
    style: Style = field(default=PLAIN, kw_only=True)
    active_style: Style = field(
        default=Style(bold=True, bright=True),
        kw_only=True,
    )
    width: int | None = field(default=None, kw_only=True)
    height: int | None = field(default=None, kw_only=True)
    min_width: int = field(default=1, kw_only=True)
    min_height: int = field(default=1, kw_only=True)
    max_width: int | None = field(default=None, kw_only=True)
    max_height: int | None = field(default=None, kw_only=True)

    def __post_init__(self) -> None:
        self.items = tuple(self.items)
        if self.active_index is not None and not 0 <= self.active_index < len(self.items):
            raise ValueError("active_index must refer to an existing item")
        if self.scroll_offset < 0:
            raise ValueError("scroll_offset must be non-negative")
        _validate_size_hints(
            width=self.width,
            min_width=self.min_width,
            max_width=self.max_width,
            height=self.height,
            min_height=self.min_height,
            max_height=self.max_height,
        )

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        """Draw the effective viewport without mutating caller-owned state."""

        if rect.is_empty or rect.intersect(canvas.rect).is_empty:
            return
        canvas.fill(rect)
        maximum_offset = max(0, len(self.items) - rect.height)
        effective_offset = min(self.scroll_offset, maximum_offset)
        for row, item in enumerate(
            self.items[effective_offset : effective_offset + rect.height]
        ):
            item_index = effective_offset + row
            active = item_index == self.active_index
            marker = ">" if active and self.focused else "*" if active else " "
            row_style = self.active_style if active else self.style
            canvas.fill(
                Rect(rect.x, rect.y + row, rect.width, 1),
                style=row_style,
            )
            canvas.write(
                rect.x,
                rect.y + row,
                marker,
                max_width=min(1, rect.width),
                style=row_style,
                ellipsis=False,
            )
            if rect.width >= 2:
                canvas.write(
                    rect.x + 1,
                    rect.y + row,
                    " ",
                    max_width=1,
                    style=row_style,
                    ellipsis=False,
                )
            if rect.width >= 3:
                canvas.write(
                    rect.x + 2,
                    rect.y + row,
                    item,
                    max_width=rect.width - 2,
                    style=row_style,
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

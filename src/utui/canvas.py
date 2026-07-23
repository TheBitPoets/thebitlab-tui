"""A clipped, fixed-size terminal-cell canvas."""

from __future__ import annotations

from dataclasses import dataclass

from .geometry import Rect
from .styles import PLAIN, Style, strip_ansi, truncate


@dataclass(slots=True)
class _Cell:
    char: str = " "
    style: Style = PLAIN


class Canvas:
    """A clipped terminal-cell grid with stable visible dimensions.

    Args:
        width: Non-negative number of columns.
        height: Non-negative number of rows.
        fill: Single character used for untouched cells.

    Styles are stored on cells and converted to ANSI only when output is requested. This keeps
    escape sequences out of all geometry calculations.
    """

    def __init__(self, width: int, height: int, fill: str = " ") -> None:
        if width < 0 or height < 0:
            raise ValueError("width and height must be non-negative")
        if len(fill) != 1:
            raise ValueError("fill must be one character")
        self.width = width
        self.height = height
        self._cells = [[_Cell(fill) for _ in range(width)] for _ in range(height)]

    @property
    def rect(self) -> Rect:
        """Return the full drawable rectangle of the canvas."""

        return Rect(0, 0, self.width, self.height)

    def set(self, x: int, y: int, char: str, style: Style = PLAIN) -> None:
        """Set one cell, silently ignoring coordinates outside the canvas."""

        if not char:
            return
        if 0 <= x < self.width and 0 <= y < self.height:
            self._cells[y][x] = _Cell(char[0], style)

    def write(
        self,
        x: int,
        y: int,
        text: str,
        *,
        max_width: int | None = None,
        style: Style = PLAIN,
        ellipsis: bool = True,
    ) -> None:
        """Write one line and clip it to the canvas.

        Args:
            x: Starting column, which may be negative.
            y: Target row.
            text: Text to draw. Newlines become spaces and existing ANSI is removed.
            max_width: Optional logical width before canvas clipping.
            style: Style stored on each written cell.
            ellipsis: Use ``...`` when ``max_width`` truncates the text.
        """

        if y < 0 or y >= self.height:
            return
        plain = (
            strip_ansi(text)
            .replace("\r\n", " ")
            .replace("\r", " ")
            .replace("\n", " ")
        )
        available = self.width - x if max_width is None else max_width
        if available <= 0:
            return
        plain = truncate(plain, available) if ellipsis else plain[:available]
        for offset, char in enumerate(plain):
            target_x = x + offset
            if target_x >= self.width:
                break
            if target_x >= 0:
                self.set(target_x, y, char, style)

    def fill(self, rect: Rect, char: str = " ", style: Style = PLAIN) -> None:
        """Fill the visible portion of ``rect`` with one character."""

        if len(char) != 1:
            raise ValueError("fill character must have length one")
        clipped = rect.intersect(self.rect)
        for y in range(clipped.y, clipped.bottom):
            for x in range(clipped.x, clipped.right):
                self.set(x, y, char, style)

    def blit(
        self,
        source: Canvas,
        *,
        x: int = 0,
        y: int = 0,
        source_rect: Rect | None = None,
    ) -> None:
        """Copy a clipped source region, including styles, onto this canvas.

        Args:
            source: Canvas whose cells are copied.
            x: Destination column corresponding to the requested source rectangle's left edge.
            y: Destination row corresponding to the requested source rectangle's top edge.
            source_rect: Requested source region, or ``None`` for the complete source canvas.

        Source and destination edges are clipped without changing their coordinate mapping. If a
        requested source origin lies outside ``source``, its clipped cells retain their original
        offset from destination ``(x, y)``. Copying a canvas onto itself reads every selected cell
        before writing, so overlapping copies are deterministic. The operation never emits ANSI or
        resizes either canvas.
        """

        requested = source.rect if source_rect is None else source_rect
        destination_in_source = Rect(
            requested.x - x,
            requested.y - y,
            self.width,
            self.height,
        )
        clipped = requested.intersect(source.rect).intersect(destination_in_source)
        snapshot = [
            (
                x + source_x - requested.x,
                y + source_y - requested.y,
                source._cells[source_y][source_x].char,
                source._cells[source_y][source_x].style,
            )
            for source_y in range(clipped.y, clipped.bottom)
            for source_x in range(clipped.x, clipped.right)
        ]
        for destination_x, destination_y, char, style in snapshot:
            self.set(destination_x, destination_y, char, style)

    def hline(self, x: int, y: int, width: int, char: str = "-", style: Style = PLAIN) -> None:
        """Draw a clipped horizontal line."""

        for offset in range(max(0, width)):
            self.set(x + offset, y, char, style)

    def vline(self, x: int, y: int, height: int, char: str = "|", style: Style = PLAIN) -> None:
        """Draw a clipped vertical line."""

        for offset in range(max(0, height)):
            self.set(x, y + offset, char, style)

    def border(self, rect: Rect, style: Style = PLAIN) -> None:
        """Draw an ASCII ``+``, ``-``, ``|`` border inside ``rect``."""

        if rect.is_empty:
            return
        if rect.height == 1:
            self.hline(rect.x, rect.y, rect.width, "-", style)
            return
        if rect.width == 1:
            self.vline(rect.x, rect.y, rect.height, "|", style)
            return
        self.hline(rect.x + 1, rect.y, rect.width - 2, "-", style)
        self.hline(rect.x + 1, rect.bottom - 1, rect.width - 2, "-", style)
        self.vline(rect.x, rect.y + 1, rect.height - 2, "|", style)
        self.vline(rect.right - 1, rect.y + 1, rect.height - 2, "|", style)
        for x, y in (
            (rect.x, rect.y),
            (rect.right - 1, rect.y),
            (rect.x, rect.bottom - 1),
            (rect.right - 1, rect.bottom - 1),
        ):
            self.set(x, y, "+", style)

    def lines(self, *, color: bool = False) -> list[str]:
        """Return all rows, optionally decorated with ANSI style sequences."""

        rendered: list[str] = []
        for row in self._cells:
            parts: list[str] = []
            start = 0
            while start < len(row):
                style = row[start].style
                end = start + 1
                while end < len(row) and row[end].style == style:
                    end += 1
                text = "".join(cell.char for cell in row[start:end])
                parts.append(style.apply(text, color=color))
                start = end
            rendered.append("".join(parts))
        return rendered

    def text(self, *, color: bool = False) -> str:
        """Return all rows joined by newline characters."""

        return "\n".join(self.lines(color=color))

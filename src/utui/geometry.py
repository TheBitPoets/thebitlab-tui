"""Small immutable geometry primitives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Rect:
    """A rectangular area using terminal-cell coordinates.

    Args:
        x: Horizontal origin. Negative values are valid and are clipped by a canvas.
        y: Vertical origin. Negative values are valid and are clipped by a canvas.
        width: Non-negative number of terminal cells.
        height: Non-negative number of terminal rows.
    """

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise ValueError("width and height must be non-negative")

    @property
    def right(self) -> int:
        """Return the exclusive right coordinate."""

        return self.x + self.width

    @property
    def bottom(self) -> int:
        """Return the exclusive bottom coordinate."""

        return self.y + self.height

    @property
    def is_empty(self) -> bool:
        """Return whether either extent is zero."""

        return self.width == 0 or self.height == 0

    def contains(self, x: int, y: int) -> bool:
        """Return whether a cell coordinate lies inside the rectangle."""

        return self.x <= x < self.right and self.y <= y < self.bottom

    def intersect(self, other: Rect) -> Rect:
        """Return the overlap with ``other``, or an empty rectangle if disjoint."""

        left = max(self.x, other.x)
        top = max(self.y, other.y)
        right = max(left, min(self.right, other.right))
        bottom = max(top, min(self.bottom, other.bottom))
        return Rect(left, top, right - left, bottom - top)

    def inset(self, horizontal: int = 0, vertical: int | None = None) -> Rect:
        """Return a rectangle reduced equally on opposing sides.

        Extents clamp to zero when the inset is larger than the rectangle.

        Raises:
            ValueError: If either inset is negative.
        """

        if horizontal < 0 or (vertical is not None and vertical < 0):
            raise ValueError("insets must be non-negative")
        vertical = horizontal if vertical is None else vertical
        width = max(0, self.width - 2 * horizontal)
        height = max(0, self.height - 2 * vertical)
        return Rect(
            self.x + min(horizontal, self.width),
            self.y + min(vertical, self.height),
            width,
            height,
        )

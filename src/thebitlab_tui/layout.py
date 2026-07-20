"""Small responsive row and column layout containers."""

from __future__ import annotations

from dataclasses import dataclass

from .canvas import Canvas
from .geometry import Rect
from .widgets import Widget, draw_widget


@dataclass(frozen=True, slots=True)
class Size:
    """A fixed or proportional size with soft minimum/maximum constraints."""

    fixed: int | None = None
    flex: int = 1
    min_size: int = 0
    max_size: int | None = None

    def __post_init__(self) -> None:
        if self.fixed is not None and self.fixed < 0:
            raise ValueError("fixed size must be non-negative")
        if self.flex < 0 or self.min_size < 0:
            raise ValueError("flex and min_size must be non-negative")
        if self.max_size is not None and self.max_size < self.min_size:
            raise ValueError("max_size cannot be smaller than min_size")

    @classmethod
    def fixed_size(cls, value: int) -> Size:
        return cls(fixed=value, flex=0, min_size=value, max_size=value)

    @classmethod
    def flexible(cls, flex: int = 1, *, minimum: int = 0, maximum: int | None = None) -> Size:
        return cls(flex=flex, min_size=minimum, max_size=maximum)


def _constraint(widget: Widget, axis: str, explicit: Size | None) -> Size:
    if explicit is not None:
        return explicit
    fixed = getattr(widget, axis, None)
    minimum = getattr(widget, f"min_{axis}", 0)
    maximum = getattr(widget, f"max_{axis}", None)
    if fixed is not None:
        return Size.fixed_size(fixed)
    return Size.flexible(minimum=minimum, maximum=maximum)


def allocate(total: int, specs: list[Size]) -> list[int]:
    """Allocate an extent deterministically, forcing clipping only when unavoidable."""

    if not specs:
        return []
    budget = max(0, total)
    wanted = [spec.fixed if spec.fixed is not None else spec.min_size for spec in specs]
    sizes = [0] * len(specs)
    if sum(wanted) > budget:
        remaining = budget
        for index, amount in enumerate(wanted):
            children_left = sum(1 for later in wanted[index + 1 :] if later > 0)
            grant = min(amount, max(0, remaining - children_left))
            if grant == 0 and amount > 0 and remaining > 0:
                grant = 1
            sizes[index] = grant
            remaining -= grant
        return sizes

    sizes = wanted[:]
    remaining = budget - sum(sizes)
    extras = [0] * len(specs)
    while remaining:
        candidates = [
            i
            for i, spec in enumerate(specs)
            if spec.fixed is None
            and spec.flex > 0
            and (spec.max_size is None or sizes[i] < spec.max_size)
        ]
        if not candidates:
            break
        index = min(candidates, key=lambda item: (extras[item] / specs[item].flex, item))
        sizes[index] += 1
        extras[index] += 1
        remaining -= 1
    return sizes


@dataclass(slots=True)
class Row:
    children: list[Widget]
    sizes: list[Size] | None = None
    gap: int = 1
    stack_when_narrow: bool = True
    width: int | None = None
    height: int | None = None
    min_width: int = 1
    min_height: int = 1
    max_width: int | None = None
    max_height: int | None = None

    def __post_init__(self) -> None:
        if self.gap < 0:
            raise ValueError("gap must be non-negative")
        if self.sizes is not None and len(self.sizes) != len(self.children):
            raise ValueError("sizes must match children")

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        if not self.children or rect.is_empty:
            return
        specs = [
            _constraint(child, "width", self.sizes[index] if self.sizes else None)
            for index, child in enumerate(self.children)
        ]
        required = sum(spec.min_size for spec in specs) + self.gap * (len(specs) - 1)
        if self.stack_when_narrow and rect.width < required:
            Column(self.children, gap=self.gap).draw(canvas, rect)
            return
        available = max(0, rect.width - self.gap * (len(specs) - 1))
        widths = allocate(available, specs)
        x = rect.x
        for child, width in zip(self.children, widths):
            draw_widget(child, canvas, Rect(x, rect.y, width, rect.height))
            x += width + self.gap


@dataclass(slots=True)
class Column:
    children: list[Widget]
    sizes: list[Size] | None = None
    gap: int = 0
    width: int | None = None
    height: int | None = None
    min_width: int = 1
    min_height: int = 1
    max_width: int | None = None
    max_height: int | None = None

    def __post_init__(self) -> None:
        if self.gap < 0:
            raise ValueError("gap must be non-negative")
        if self.sizes is not None and len(self.sizes) != len(self.children):
            raise ValueError("sizes must match children")

    def draw(self, canvas: Canvas, rect: Rect) -> None:
        if not self.children or rect.is_empty:
            return
        specs = [
            _constraint(child, "height", self.sizes[index] if self.sizes else None)
            for index, child in enumerate(self.children)
        ]
        available = max(0, rect.height - self.gap * (len(specs) - 1))
        heights = allocate(available, specs)
        y = rect.y
        for child, height in zip(self.children, heights):
            draw_widget(child, canvas, Rect(rect.x, y, rect.width, height))
            y += height + self.gap

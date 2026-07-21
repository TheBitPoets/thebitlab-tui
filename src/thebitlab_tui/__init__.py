"""Stable public API for thebitlab-tui."""

from .canvas import Canvas
from .events import Key, KeyEvent
from .geometry import Rect
from .layout import Column, Row, Size
from .renderer import render, render_lines, render_terminal
from .styles import Style, strip_ansi, truncate, visible_width
from .terminal import ResizeWatcher, TerminalSize, get_terminal_size, supports_color
from .widgets import Divider, Label, ListView, Panel, StatusBadge, Widget

__all__ = [
    "Canvas",
    "Column",
    "Divider",
    "Key",
    "KeyEvent",
    "Label",
    "ListView",
    "Panel",
    "Rect",
    "ResizeWatcher",
    "Row",
    "Size",
    "Style",
    "StatusBadge",
    "TerminalSize",
    "Widget",
    "get_terminal_size",
    "render",
    "render_lines",
    "render_terminal",
    "strip_ansi",
    "supports_color",
    "truncate",
    "visible_width",
]


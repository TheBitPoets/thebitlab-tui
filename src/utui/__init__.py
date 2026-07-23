"""Stable public API for utui."""

from .canvas import Canvas
from .events import Key, KeyEvent
from .geometry import Rect
from .layout import Column, Row, Size
from .renderer import render, render_lines, render_terminal
from .styles import Style, strip_ansi, truncate, visible_width
from .terminal import KeyReader, ResizeWatcher, TerminalSize, get_terminal_size, supports_color
from .widgets import Divider, Label, ListView, Modal, Panel, ScrollView, StatusBadge, Widget

__all__ = [
    "Canvas",
    "Column",
    "Divider",
    "Key",
    "KeyEvent",
    "KeyReader",
    "Label",
    "ListView",
    "Modal",
    "Panel",
    "Rect",
    "ResizeWatcher",
    "Row",
    "ScrollView",
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


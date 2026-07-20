"""ANSI styling kept separate from terminal-cell geometry."""

from __future__ import annotations

import re
from dataclasses import dataclass

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

_FOREGROUND = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}
_BACKGROUND = {name: code + 10 for name, code in _FOREGROUND.items()}


def strip_ansi(text: str) -> str:
    """Remove ANSI control sequences from text."""

    return ANSI_RE.sub("", text)


def visible_width(text: str) -> int:
    """Return the number of visible code points in an ANSI-styled string."""

    return len(strip_ansi(text))


def truncate(text: str, width: int) -> str:
    """Fit plain or ANSI-styled input to at most ``width`` visible cells."""

    if width <= 0:
        return ""
    plain = strip_ansi(text)
    if len(plain) <= width:
        return plain
    if width <= 3:
        return "." * width
    return plain[: width - 3] + "..."


@dataclass(frozen=True, slots=True)
class Style:
    """Optional SGR attributes for text drawn on a canvas.

    Args:
        bold: Emit the ANSI bold attribute.
        bright: Use bright white text independently of ``foreground``.
        foreground: Optional named foreground color.
        background: Optional named background color.

    Color names use the standard eight ANSI colors and their ``bright_*`` variants. Invalid names
    raise :class:`ValueError` during construction.
    """

    bold: bool = False
    bright: bool = False
    foreground: str | None = None
    background: str | None = None

    def __post_init__(self) -> None:
        if self.foreground not in _FOREGROUND and self.foreground is not None:
            raise ValueError(f"unknown foreground color: {self.foreground}")
        if self.background not in _BACKGROUND and self.background is not None:
            raise ValueError(f"unknown background color: {self.background}")

    @property
    def is_plain(self) -> bool:
        """Return whether the style would emit no ANSI attributes."""

        return not (self.bold or self.bright or self.foreground or self.background)

    def apply(self, text: str, *, color: bool = True) -> str:
        """Wrap text in ANSI SGR sequences when color output is enabled."""

        if not color or self.is_plain or not text:
            return text
        codes: list[str] = []
        if self.bold:
            codes.append("1")
        if self.bright:
            codes.append("97")
        if self.foreground:
            codes.append(str(_FOREGROUND[self.foreground]))
        if self.background:
            codes.append(str(_BACKGROUND[self.background]))
        return f"\x1b[{';'.join(codes)}m{text}\x1b[0m"


PLAIN = Style()

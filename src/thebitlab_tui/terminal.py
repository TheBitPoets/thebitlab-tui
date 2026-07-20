"""Thin, optional terminal policy helpers; no event loop or drawing."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TextIO


@dataclass(frozen=True, slots=True)
class TerminalSize:
    width: int
    height: int


def get_terminal_size(fallback: tuple[int, int] = (80, 24)) -> TerminalSize:
    size = shutil.get_terminal_size(fallback)
    return TerminalSize(max(1, size.columns), max(1, size.lines))


class ResizeWatcher:
    """Detect size changes by polling an injectable size reader."""

    def __init__(self, reader: Callable[[], TerminalSize] = get_terminal_size) -> None:
        self._reader = reader
        self._last: TerminalSize | None = None

    def poll(self) -> TerminalSize | None:
        current = self._reader()
        if current == self._last:
            return None
        self._last = current
        return current


def supports_color(
    *,
    no_color: bool = False,
    stream: TextIO | None = None,
    environ: Mapping[str, str] | None = None,
    platform: str | None = None,
) -> bool:
    """Apply a conservative ANSI policy on Linux and Windows."""

    if no_color:
        return False
    env = os.environ if environ is None else environ
    if "NO_COLOR" in env:
        return False
    output = sys.stdout if stream is None else stream
    if not output.isatty():
        return False
    current_platform = sys.platform if platform is None else platform
    if current_platform == "win32":
        return any(key in env for key in ("WT_SESSION", "ANSICON", "TERM_PROGRAM"))
    return env.get("TERM") != "dumb"


"""Abstract keys shared by future platform-specific input adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Key(str, Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    ENTER = "enter"
    ESCAPE = "escape"
    TAB = "tab"
    CHARACTER = "character"


@dataclass(frozen=True, slots=True)
class KeyEvent:
    key: Key
    character: str | None = None
    ctrl: bool = False
    alt: bool = False
    shift: bool = False

    def __post_init__(self) -> None:
        if self.key is Key.CHARACTER and (self.character is None or len(self.character) != 1):
            raise ValueError("character keys require exactly one character")


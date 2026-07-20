"""Abstract keys shared by future platform-specific input adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Key(str, Enum):
    """Platform-neutral keys emitted by future terminal input adapters."""

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
    """A normalized key and any modifiers reported by the terminal.

    Args:
        key: Platform-neutral key identifier.
        character: One-character payload required for ``Key.CHARACTER``.
        ctrl: Whether the adapter reported Ctrl.
        alt: Whether the adapter reported Alt.
        shift: Whether the adapter reported Shift.

    Applications must provide commands that do not require modifiers because Windows terminals do
    not report Alt and Ctrl combinations consistently.
    """

    key: Key
    character: str | None = None
    ctrl: bool = False
    alt: bool = False
    shift: bool = False

    def __post_init__(self) -> None:
        if self.key is Key.CHARACTER and (self.character is None or len(self.character) != 1):
            raise ValueError("character keys require exactly one character")

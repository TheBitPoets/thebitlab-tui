"""Tests for the application-owned terminal input example."""

from __future__ import annotations

from collections.abc import Iterable

import pytest

from examples.terminal_input import (
    ApplicationState,
    ITEMS,
    READ_TIMEOUT,
    apply_event,
    build_screen,
    describe_event,
    run_session,
)
from thebitlab_tui import Key, KeyEvent, TerminalSize, render


class FakeReader:
    """Return a finite sequence of optional events and record requested timeouts."""

    def __init__(self, events: Iterable[KeyEvent | None]) -> None:
        self._events = iter(events)
        self.timeouts: list[float | None] = []

    def read(self, timeout: float | None = None) -> KeyEvent | None:
        """Return the next injected event."""

        self.timeouts.append(timeout)
        return next(self._events)


class FakeWatcher:
    """Return injected initial and changed terminal sizes."""

    def __init__(self, sizes: Iterable[TerminalSize | None]) -> None:
        self._sizes = iter(sizes)

    def poll(self) -> TerminalSize | None:
        """Return the next injected resize result."""

        return next(self._sizes)


@pytest.mark.parametrize(
    ("event", "initial_active", "active", "focused", "activations", "running"),
    [
        (KeyEvent(Key.DOWN), 0, 1, 0, 0, True),
        (KeyEvent(Key.CHARACTER, "j"), 0, 1, 0, 0, True),
        (KeyEvent(Key.UP), 1, 0, 0, 0, True),
        (KeyEvent(Key.CHARACTER, "k"), 1, 0, 0, 0, True),
        (KeyEvent(Key.TAB), 0, 0, 1, 0, True),
        (KeyEvent(Key.CHARACTER, "n"), 0, 0, 1, 0, True),
        (KeyEvent(Key.ENTER), 0, 0, 0, 1, True),
        (KeyEvent(Key.CHARACTER, " "), 0, 0, 0, 1, True),
        (KeyEvent(Key.ESCAPE), 0, 0, 0, 0, False),
        (KeyEvent(Key.CHARACTER, "q"), 0, 0, 0, 0, False),
    ],
)
def test_commands_have_modifier_free_alternatives(
    event: KeyEvent,
    initial_active: int,
    active: int,
    focused: int,
    activations: int,
    running: bool,
) -> None:
    """Keep every example command usable without Alt or Ctrl."""

    state = ApplicationState(active_index=initial_active)

    assert apply_event(state, event)
    assert (state.active_index, state.focused_panel) == (active, focused)
    assert state.activations == activations
    assert state.running is running


def test_selection_stays_inside_caller_owned_items() -> None:
    """Clamp application selection without asking ``ListView`` to mutate it."""

    state = ApplicationState(active_index=len(ITEMS) - 1)

    apply_event(state, KeyEvent(Key.DOWN))

    assert state.active_index == len(ITEMS) - 1


def test_event_description_preserves_reported_modifiers_and_text() -> None:
    """Display best-effort modifier information without making it a command requirement."""

    event = KeyEvent(Key.CHARACTER, "é", ctrl=True, alt=True)

    assert describe_event(event) == "ctrl+alt+'é'"


def test_screen_has_stable_wide_and_narrow_ascii_snapshots() -> None:
    """Keep three panels responsive without changing requested frame geometry."""

    state = ApplicationState(active_index=1, last_event="down")

    wide = render(build_screen(state, TerminalSize(70, 8)), 70, 8, color=False)
    narrow = render(build_screen(state, TerminalSize(32, 14)), 32, 14, color=False)

    assert wide.splitlines() == [
        "+ > Session ---------+ + Selection --------+ + Commands -------------+",
        "|Size: 70x8          | |  assignment       | |Up/k previous          |",
        "|Last: down          | |* workspace        | |Down/j next            |",
        "|Activations: 0      | |  activity         | |Tab/n focus            |",
        "|                    | |  tests            | |Enter/Space activate   |",
        "|                    | |                   | |Esc/q quit             |",
        "|                    | |                   | |                       |",
        "+--------------------+ +-------------------+ +-----------------------+",
    ]
    assert narrow.splitlines() == [
        "+ > Session -------------------+",
        "|Size: 32x14                   |",
        "|Last: down                    |",
        "+------------------------------+",
        "                                ",
        "+ Selection -------------------+",
        "|  assignment                  |",
        "|* workspace                   |",
        "+------------------------------+",
        "                                ",
        "+ Commands --------------------+",
        "|Up/k previous                 |",
        "|Down/j next                   |",
        "+------------------------------+",
    ]
    assert all(len(row) == 70 for row in wide.splitlines())
    assert all(len(row) == 32 for row in narrow.splitlines())
    assert "\x1b[" not in wide + narrow


def test_session_uses_finite_reads_and_redraws_only_for_changes() -> None:
    """Give resize polling a finite opportunity without redundant redraws."""

    reader = FakeReader([None, KeyEvent(Key.DOWN), KeyEvent(Key.CHARACTER, "q")])
    watcher = FakeWatcher(
        [TerminalSize(70, 8), None, TerminalSize(32, 14), None]
    )
    frames: list[list[str]] = []

    state = run_session(reader, watcher, presenter=frames.append)  # type: ignore[arg-type]

    assert state.active_index == 1
    assert state.running is False
    assert reader.timeouts == [READ_TIMEOUT, READ_TIMEOUT, READ_TIMEOUT]
    assert [len(frame) for frame in frames] == [8, 14]
    assert all(len(row) == 70 for row in frames[0])
    assert all(len(row) == 32 for row in frames[1])


def test_session_propagates_requested_failure_after_input() -> None:
    """Leave exceptional cleanup to the visible ``KeyReader`` context boundary."""

    reader = FakeReader([KeyEvent(Key.ENTER)])
    watcher = FakeWatcher([TerminalSize(70, 8)])

    with pytest.raises(RuntimeError, match="requested failure"):
        run_session(  # type: ignore[arg-type]
            reader,
            watcher,  # type: ignore[arg-type]
            presenter=lambda rows: None,
            fail_after_key=True,
        )

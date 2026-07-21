"""Show caller-owned input, resize, state, and redraw around pure widgets."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from io import UnsupportedOperation
import sys
from typing import TextIO

from thebitlab_tui import (
    Key,
    KeyEvent,
    KeyReader,
    Label,
    ListView,
    Panel,
    ResizeWatcher,
    Row,
    TerminalSize,
    get_terminal_size,
    render_lines,
    supports_color,
)


ITEMS = ("assignment", "workspace", "activity", "tests")
READ_TIMEOUT = 0.05


@dataclass(slots=True)
class ApplicationState:
    """Mutable example state owned by the application, never by a widget."""

    active_index: int = 0
    focused_panel: int = 0
    activations: int = 0
    last_event: str = "none"
    running: bool = True


def describe_event(event: KeyEvent) -> str:
    """Return a compact, deterministic description of one normalized event."""

    modifiers = [
        name
        for enabled, name in (
            (event.ctrl, "ctrl"),
            (event.alt, "alt"),
            (event.shift, "shift"),
        )
        if enabled
    ]
    value = repr(event.character) if event.key is Key.CHARACTER else event.key.value
    return "+".join([*modifiers, value])


def apply_event(state: ApplicationState, event: KeyEvent) -> bool:
    """Apply one key to caller-owned state and report whether presentation changed."""

    state.last_event = describe_event(event)
    character = event.character if event.key is Key.CHARACTER else None

    if event.key is Key.UP or character == "k":
        state.active_index = max(0, state.active_index - 1)
    elif event.key is Key.DOWN or character == "j":
        state.active_index = min(len(ITEMS) - 1, state.active_index + 1)
    elif event.key is Key.TAB or character == "n":
        state.focused_panel = (state.focused_panel + 1) % 3
    elif event.key is Key.ENTER or character == " ":
        state.activations += 1
    elif event.key is Key.ESCAPE or character == "q":
        state.running = False
    return True


def build_screen(state: ApplicationState, size: TerminalSize) -> Row:
    """Build three responsive panels from an application-state snapshot."""

    status = Label(
        f"Size: {size.width}x{size.height}\n"
        f"Last: {state.last_event}\n"
        f"Activations: {state.activations}"
    )
    selection = ListView(
        ITEMS,
        active_index=state.active_index,
        focused=state.focused_panel == 1,
    )
    commands = Label(
        "Up/k previous\n"
        "Down/j next\n"
        "Tab/n focus\n"
        "Enter/Space activate\n"
        "Esc/q quit"
    )
    return Row(
        [
            Panel(
                status,
                title="Session",
                focused=state.focused_panel == 0,
                min_width=20,
            ),
            Panel(
                selection,
                title="Selection",
                focused=state.focused_panel == 1,
                min_width=20,
            ),
            Panel(
                commands,
                title="Commands",
                focused=state.focused_panel == 2,
                min_width=24,
            ),
        ],
        gap=1,
    )


def render_frame(
    state: ApplicationState,
    size: TerminalSize,
    *,
    color: bool = False,
) -> list[str]:
    """Render one frame without printing or mutating application state."""

    return render_lines(build_screen(state, size), size.width, size.height, color=color)


def present_frame(rows: list[str], *, stream: TextIO = sys.stdout) -> None:
    """Replace the visible frame; this application helper is not library behavior."""

    stream.write("\x1b[2J\x1b[H")
    stream.write("\n".join(rows))
    stream.flush()


def run_session(
    reader: KeyReader,
    watcher: ResizeWatcher,
    *,
    state: ApplicationState | None = None,
    color: bool = False,
    presenter: Callable[[list[str]], None] = present_frame,
    fail_after_key: bool = False,
) -> ApplicationState:
    """Run the example-owned loop around an already active terminal reader.

    A finite read timeout gives resize polling a deterministic opportunity to run. The function
    owns commands and redraw policy but does not hide reader activation or terminal restoration.
    """

    current_state = ApplicationState() if state is None else state
    current_size = watcher.poll()
    if current_size is None:
        raise RuntimeError("a new ResizeWatcher must report its initial size")
    presenter(render_frame(current_state, current_size, color=color))

    while current_state.running:
        event = reader.read(timeout=READ_TIMEOUT)
        state_changed = event is not None and apply_event(current_state, event)
        if event is not None and fail_after_key:
            raise RuntimeError("requested failure after input")

        resized = watcher.poll()
        if resized is not None:
            current_size = resized
        if current_state.running and (state_changed or resized is not None):
            presenter(render_frame(current_state, current_size, color=color))
    return current_state


def _parser() -> argparse.ArgumentParser:
    """Build the example command-line parser."""

    parser = argparse.ArgumentParser(
        description="Render a snapshot or run the application-owned terminal input loop."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--snapshot", action="store_true", help="render once without reading stdin")
    mode.add_argument("--interactive", action="store_true", help="read keys from a real terminal")
    parser.add_argument("--no-color", action="store_true", help="disable ANSI color styles")
    parser.add_argument(
        "--fail-after-key",
        action="store_true",
        help="raise after one key to verify exceptional terminal restoration",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a deterministic snapshot by default or the explicit interactive mode."""

    parser = _parser()
    args = parser.parse_args(argv)
    if args.fail_after_key and not args.interactive:
        parser.error("--fail-after-key requires --interactive")
    color = supports_color(no_color=args.no_color)
    if not args.interactive:
        size = get_terminal_size()
        print("\n".join(render_frame(ApplicationState(), size, color=color)))
        return 0

    watcher = ResizeWatcher()
    try:
        with KeyReader() as reader:
            try:
                run_session(
                    reader,
                    watcher,
                    color=color,
                    fail_after_key=args.fail_after_key,
                )
            finally:
                print()
    except UnsupportedOperation as error:
        print(f"terminal input unavailable: {error}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130
    except RuntimeError as error:
        print(f"terminal input example failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

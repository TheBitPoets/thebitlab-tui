# thebitlab-tui

`thebitlab-tui` is a deliberately small Python library for rendering stable ASCII terminal
interfaces. It uses only the Python standard library, targets Python 3.11+, and keeps widgets,
layout, rendering, and terminal I/O separate.

It is not a replacement for Textual, Urwid, or Rich. It does not own an event loop, print from
widgets, contain application logic, or require Unicode borders. The public surface focuses on
`Rect`, `Canvas`, `Style`, `Label`, `Panel`, `Divider`, `StatusBadge`, `ListView`, `ScrollView`,
`Modal`, responsive `Row`/`Column`, and pure ASCII rendering.

## Minimal example

```python
from thebitlab_tui import Panel, Row, render

screen = Row([
    Panel("Open the exercise", title="Assignment", min_width=18),
    Panel("No recent activity", title="Activity", min_width=18),
    Panel("3 passed", title="Tests", min_width=18),
])

frame = render(screen, width=80, height=8, color=False)
print(frame)  # The application, not the library, chooses when to print.
```

The full three-panel example is in `examples/basic_panels.py`. See
`examples/divider_badges.py` for ASCII dividers and semantic status markers.
`examples/selectable_list.py` shows caller-owned focus, selection, and vertical viewport state.
`examples/scroll_view.py` demonstrates isolated scrolling for arbitrary widget content.
`examples/modal.py` shows application-owned z-order around a centered modal frame.
`examples/terminal_input.py` shows an application-owned finite input/resize loop and provides a
deterministic `--snapshot --no-color` mode for completely ANSI-free output.

## Development and tests

```console
python -m pytest
python -m compileall -q src tests examples
python examples/basic_panels.py --no-color
python examples/terminal_input.py --snapshot --no-color
```

There are no runtime dependencies. `pytest` is needed only to run the test suite from this
source tree.

## Windows, Linux, and colors

Geometry and rendering are platform-independent. `get_terminal_size()` uses the standard
library and reads the current size on every frame requested through `render_terminal()`.

The additive Phase 3 `KeyReader` facade is available for API integration, with a single-use
context lifecycle and deterministic timeout policy. Linux interactive terminals use the POSIX
backend, which restores the exact saved terminal attributes on exit. Windows consoles use a
console-record backend that borrows standard input and never changes its mode. On both platforms,
redirected or non-interactive input is rejected with `io.UnsupportedOperation`. The library still
owns no event loop, commands, or redraw policy.
`ResizeWatcher` provides polling-based resize detection without installing signal handlers or
creating an event loop.

Run `python examples/terminal_input.py --interactive --no-color` in a real terminal for the
cross-platform example. Up/`k`, Down/`j`, Tab/`n`, Enter/Space, and Escape/`q` keep every workflow
available without modifiers. Redirected input is rejected. The example, not the library, owns its
loop, mutable state, clear/home presenter, and redraw timing.

ANSI colors are opt-in (`color=True`). Use `color=False` or the example's `--no-color` flag for
plain output. `supports_color()` follows `NO_COLOR`, checks whether the output is a TTY, and uses
a conservative Windows capability check. Focus is also shown with ASCII text, so color is never
required to understand the interface.

`ListView` uses `>` for a focused active row and `*` for an unfocused active row. The application
owns `active_index` and `scroll_offset`; rendering only clamps an effective offset for the current
height and never changes either value or handles input.

`ScrollView` uses an explicit caller-provided `content_height`; it does not measure children or
handle navigation. `Canvas.blit` composes clipped cell regions while preserving styles, including
deterministic overlapping copies on the same canvas.

`Modal` centers an ASCII `Panel` inside the rectangle assigned by the renderer or a layout. The
caller owns its `open` state and draws any base layer first. The `[x]` marker is a presentation
affordance only: the library adds no callback, backdrop, focus manager, or event loop.

## Narrow terminals

Rows place children side by side while their declared minimum widths fit. When they do not fit,
`Row` stacks them vertically. Every draw is clipped to the current canvas; text truncates with
`...`, and every returned line keeps the requested visible width. If even the minimum dimensions
cannot fit, clipping wins over horizontal overflow.

Modal minimum dimensions are soft too. Below seven columns the literal `[x]` prefix clips
deterministically, while the frame remains inside its assigned rectangle.

See `docs/architecture.md`, `docs/integration.md`, and `docs/roadmap.md` for design and migration
details.

## Documentation

Public API documentation is generated from docstrings with Sphinx. The documentation also
contains an architecture overview, user guide, developer guide, executable examples, and
reproducible SVG illustrations.

```console
python -m pip install -e ".[docs]"
python -m sphinx -W --keep-going -b html docs docs/_build/html
```

Open `docs/_build/html/index.html` after a successful build. Documentation tooling is optional and
does not add runtime dependencies.

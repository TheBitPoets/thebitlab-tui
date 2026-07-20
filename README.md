# thebitlab-tui

`thebitlab-tui` is a deliberately small Python library for rendering stable ASCII terminal
interfaces. It uses only the Python standard library, targets Python 3.11+, and keeps widgets,
layout, rendering, and terminal I/O separate.

It is not a replacement for Textual, Urwid, or Rich. It does not own an event loop, print from
widgets, contain application logic, or require Unicode borders. The initial release focuses on
`Rect`, `Canvas`, `Style`, `Label`, `Panel`, responsive `Row`/`Column`, and pure ASCII rendering.

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

The full three-panel example is in `examples/basic_panels.py`.

## Development and tests

```console
python -m pytest
python -m compileall -q src tests examples
python examples/basic_panels.py --no-color
```

There are no runtime dependencies. `pytest` is needed only to run the test suite from this
source tree.

## Windows, Linux, and colors

Geometry and rendering are platform-independent. `get_terminal_size()` uses the standard
library and reads the current size on every frame requested through `render_terminal()`.
`ResizeWatcher` provides polling-based resize detection without installing signal handlers or
creating an event loop.

ANSI colors are opt-in (`color=True`). Use `color=False` or the example's `--no-color` flag for
plain output. `supports_color()` follows `NO_COLOR`, checks whether the output is a TTY, and uses
a conservative Windows capability check. Focus is also shown with ASCII text, so color is never
required to understand the interface.

## Narrow terminals

Rows place children side by side while their declared minimum widths fit. When they do not fit,
`Row` stacks them vertically. Every draw is clipped to the current canvas; text truncates with
`...`, and every returned line keeps the requested visible width. If even the minimum dimensions
cannot fit, clipping wins over horizontal overflow.

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

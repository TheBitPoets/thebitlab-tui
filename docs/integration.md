# Integration with `scripts/student_lab_layout.py`

The normative Phase 4 design is
[`docs/architecture/phase-4-adapter-contracts.rst`](architecture/phase-4-adapter-contracts.rst).
The snippets below illustrate the current public widgets; they are not a public adapter API or a
schema for the consumer's dictionaries.

Integration belongs in the `2cornot2c` repository, not in this library. The initial adapter can
have one pure function per application section and one composition function:

```python
from collections.abc import Sequence

from thebitlab_tui import Column, Label, ListView, Modal, Panel, Row, ScrollView


def workspace_panel(workspace: dict[str, object]) -> Panel:
    lines = [f"Path: {workspace.get('path', '-')}", f"Status: {workspace.get('status', '-')}"]
    return Panel(Label("\n".join(lines)), title="Workspace", min_width=30)


def exercise_list(
    titles: Sequence[str],
    *,
    active_index: int | None,
    scroll_offset: int,
    focused: bool,
) -> Panel:
    """Adapt application-owned list state without moving it into the library."""

    listing = ListView(
        titles,
        active_index=active_index,
        scroll_offset=scroll_offset,
        focused=focused,
    )
    return Panel(listing, title="Exercises", focused=focused, min_width=24)


def report_panel(lines: Sequence[str], *, scroll_offset: int) -> Panel:
    """Adapt explicit report rows while the application owns viewport state."""

    content = Label("\n".join(lines))
    viewport = ScrollView(
        content,
        content_height=len(lines),
        scroll_offset=scroll_offset,
    )
    return Panel(viewport, title="Report", min_width=30)


def quick_help_modal(message: str, *, open: bool) -> Modal:
    """Adapt application-owned help state without adding close behavior."""

    return Modal(
        message,
        title="Quick help",
        open=open,
        preferred_width=40,
        preferred_height=8,
    )


def student_screen(data: dict[str, object], collapsed: set[str], focus: str) -> Row:
    workspace = workspace_panel(data.get("workspace", {}))
    workspace.collapsed = "workspace" in collapsed
    workspace.focused = focus == "workspace"
    activity = Panel(Label(str(data.get("activity", "-"))), title="Activity", min_width=30)
    guide = Panel(Label(str(data.get("quick_guide", "-")), wrap=True), title="Guida rapida")
    return Row([workspace, activity, guide], stack_when_narrow=True)
```

The real adapter should create panels with the persisted identifiers `assignment`, `workspace`,
`activity`, `support`, `help`, `report`, `tests`, `grading`, `runner`, and `guide`. It should
project application dictionaries directly into neutral logical rows before building widgets. Parsing
already-rendered headings is a rollout bridge only, not the approved adapter boundary.

At redraw time the existing CLI should read its own state, build the tree, call
`render_terminal(tree, color=...)`, and decide how to clear and print. A future adapter can enter
the library's `KeyReader`, map returned `KeyEvent` values to existing application commands, and
poll `ResizeWatcher` after finite reads. Existing fallback commands without Alt/Ctrl must be
retained. The loop, dictionaries, persistence, and redraw policy stay in `2cornot2c`; no change to
`scripts/student_lab_layout.py` is required for this scaffold.

The first adapter should pass explicit logical rows to ``ScrollView`` as above. If it later wraps
text responsively, the application must recalculate ``content_height`` from the current width on
each redraw; the library intentionally does not measure child widgets or persist that value.

Modal visibility must likewise remain in the application's dictionaries or persisted state. A
small application-owned composite can draw ``student_screen(...)`` first and
``quick_help_modal(...)`` second into the same rectangle. Escape or a modifier-free fallback such
as ``q`` updates the application's ``open`` value; ``Modal`` itself does not handle keys, callbacks,
z-order, or dimming. No change to ``scripts/student_lab_layout.py`` is required.

## Persisted state and responsive translation

The consumer continues to load, normalize, and save `orientation`, `order`, `left_width`,
`collapsed`, and `focus`. The adapter receives only normalized state. At each redraw it also
receives the current terminal dimensions:

- horizontal layout at 90 columns or wider uses two groups of five ordered panels;
- explicit vertical layout or a terminal below 90 columns uses one column in exact persisted
  order;
- the requested left width yields enough room for the right column and never writes a responsive
  reduction back to the JSON file;
- missing sections remain visible with a neutral placeholder;
- all panel and dashboard scroll offsets remain caller-owned.

Do not depend on stacking a `Row` containing two pre-grouped columns: that would place the entire
left group before the right group in the narrow frame for reasons unrelated to persisted order.
Choose the wide or narrow tree explicitly from the current size.

The actual migration should keep the existing text renderer as a feature/failure fallback. No
byte-for-byte identity is promised, but ASCII markers, persisted meanings, no-overflow behavior,
ANSI-independent geometry, and modifier-free commands must remain available.


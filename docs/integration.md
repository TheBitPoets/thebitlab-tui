# Integration with `scripts/student_lab_layout.py`

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

The real adapter should create panels for assignment detail, workspace, activity, allowed help,
help requests, report, tests, grading, runner, and quick guide. It may initially split the current
text renderer into lines, but direct dictionary-to-widget conversion is clearer and avoids
parsing headings.

At redraw time the existing CLI should read its own state, build the tree, call
`render_terminal(tree, color=...)`, and decide how to clear and print. Its platform-specific key
reader can later return `KeyEvent` values. Existing fallback commands without Alt/Ctrl should be
retained. No change to `scripts/student_lab_layout.py` is required for this scaffold.

The first adapter should pass explicit logical rows to ``ScrollView`` as above. If it later wraps
text responsively, the application must recalculate ``content_height`` from the current width on
each redraw; the library intentionally does not measure child widgets or persist that value.

Modal visibility must likewise remain in the application's dictionaries or persisted state. A
small application-owned composite can draw ``student_screen(...)`` first and
``quick_help_modal(...)`` second into the same rectangle. Escape or a modifier-free fallback such
as ``q`` updates the application's ``open`` value; ``Modal`` itself does not handle keys, callbacks,
z-order, or dimming. No change to ``scripts/student_lab_layout.py`` is required.


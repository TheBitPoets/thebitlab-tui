# Architecture

## Responsibilities

Widgets describe presentation and draw into a supplied rectangle. `Label` handles text,
`Panel` adds a title, state markers, and an ASCII border, and `ListView` presents caller-owned
selection and viewport state. Widgets do not print, read input, or know where their data came
from.

Layout containers assign rectangles to children. `Row` allocates fixed and proportional widths;
when the children's minimum widths do not fit, it delegates to vertical stacking. `Column` does
the same operation on heights. Minimum sizes are preferences: when the terminal is smaller than
all declared minima, clipping prevents overflow.

The renderer creates a fixed-size `Canvas`, asks the root widget to draw, and returns either
`list[str]` or one string. Styles live on canvas cells, so ANSI sequences never affect geometry.
`Canvas.blit` copies clipped character/style cells and snapshots its source before overlapping
self-copies. `ScrollView` draws its child on a viewport-sized canvas and blits that isolated result,
so a child cannot overwrite adjacent layout cells.
`Modal` computes a centered inner frame inside its assigned outer rectangle, clears only that
frame, and delegates its ASCII border and content to `Panel`. The application owns visibility and
draw order, so the library never dims or clears the surrounding underlay.
The terminal adapter only reports current dimensions, color capability, and resize changes. It
does not clear the screen or run a loop.

```text
application data -> application adapter -> widget tree -> layout rectangles
                                                      -> Canvas -> renderer output
terminal input -> platform adapter -> KeyEvent -> application state -> next widget tree
```

## Events and redraws

`KeyEvent` names arrows, Enter, Escape, Tab, and ordinary characters, with optional modifier
flags. A future Windows/Linux adapter translates bytes or console records into these values.
Applications must provide unmodified-key alternatives because Ctrl and Alt are not uniformly
reported by Windows Terminal and PowerShell.

On each redraw the application reads the terminal size (or calls `render_terminal`), builds or
updates the widget tree, and renders a complete frame. `ResizeWatcher` tells a caller when a
polled size differs from the preceding one. The application decides when to clear and print.

For list navigation the flow is equally explicit: the terminal adapter produces a `KeyEvent`, the
application computes new `active_index` and `scroll_offset` values, and the next redraw constructs
a new `ListView`. The widget only clamps an effective offset for its assigned height; it never
changes state or automatically reveals the active item.

For arbitrary scrolling, the application also supplies `content_height`, because the deliberately
small `Widget` protocol has no measurement method. It updates `scroll_offset` after input and
rebuilds `ScrollView`; drawing clamps only the effective offset for the current viewport. There is
no horizontal scrolling or hidden measurement pass.

For a modal, the application converts Escape or another modifier-free command into a new `open`
value and rebuilds the widget tree. If an overlay is needed, an application-owned composite draws
the base widget first and `Modal` second. The `[x]` marker communicates the close affordance but
does not receive events or invoke callbacks.

## Data and presentation

The library accepts strings, styles, dimensions, and child widgets. It has no assignment,
workspace, activity, help, report, grading, test, or runner model. Those remain dictionaries and
state owned by the consuming application.

## Student TUI strategy

An adapter in `2cornot2c` will map each existing domain dictionary to a `Panel` containing labels,
then compose the panels with `Row` and `Column`. Focus and collapsed state remain application
state passed into widget constructors. This repository never imports the student application;
dependency direction is one-way from the application to `thebitlab_tui`.

Animations are intentionally absent. If later justified, they can be represented as pure
sequences of widget trees or frames while timing remains the application's responsibility.

## Phase 2 state ownership

The Phase 2 widgets keep focus, active selection, modal visibility, and scroll offsets as explicit
caller-provided presentation state. They may clamp an effective offset for the current viewport but
never mutate application state, dispatch events, or install an event loop. The proposed public
signatures, ASCII markers, clipping behavior, rejected alternatives, and required snapshots are
recorded in [`docs/architecture/phase-2-contracts.rst`](architecture/phase-2-contracts.rst).


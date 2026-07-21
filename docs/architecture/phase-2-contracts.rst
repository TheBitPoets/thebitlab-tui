Phase 2 public contracts
========================

Status
------

This design record was approved in pull request `#11
<https://github.com/TheBitPoets/thebitlab-tui/pull/11>`_ for issue `#10
<https://github.com/TheBitPoets/thebitlab-tui/issues/10>`_ under parent issue `#7
<https://github.com/TheBitPoets/thebitlab-tui/issues/7>`_. Issue `#12
<https://github.com/TheBitPoets/thebitlab-tui/issues/12>`_ implements the first approved slice,
``Divider`` and ``StatusBadge``. Each remaining implementation stays in a separate issue and pull
request with its own snapshots and compatibility review.

Goals and boundaries
--------------------

Phase 2 adds ``Divider``, ``StatusBadge``, ``ListView``, ``ScrollView``, and ``Modal`` while
preserving the existing architecture:

- widgets draw into a supplied ``Canvas`` and never print;
- applications own focus, active selection, modal visibility, and scroll offsets;
- drawing may clamp state for the current viewport but never mutates caller-owned state;
- all state remains constructor data, so a redraw can rebuild the widget tree from dictionaries;
- ASCII markers carry meaning when ANSI is disabled;
- terminal input, event dispatch, callbacks, persistence, and the student adapter remain outside
  the library;
- every row returned by the renderer keeps the requested visible width.

No focus manager, event loop, measurement protocol, abstract widget base class, or mutable model is
introduced. The existing structural ``Widget`` protocol remains sufficient.

Public namespace
----------------

``Divider`` and ``StatusBadge`` are exported from ``thebitlab_tui`` and listed in
``thebitlab_tui.__all__`` by the implementation tracked in issue #12. ``ListView`` follows in the
implementation tracked by issue `#14
<https://github.com/TheBitPoets/thebitlab-tui/issues/14>`_. ``Canvas.blit`` and ``ScrollView``
follow in the implementation tracked by issue `#16
<https://github.com/TheBitPoets/thebitlab-tui/issues/16>`_. ``Modal`` follows in the implementation
tracked by issue `#18 <https://github.com/TheBitPoets/thebitlab-tui/issues/18>`_.
Orientation and status remain string literals, so Phase 2 adds no public enum, state manager,
callback type, or abstract base class.

Shared size and validation rules
--------------------------------

New widgets use the existing ``width``, ``height``, ``min_width``, ``min_height``, ``max_width``,
and ``max_height`` attributes where they participate in ``Row`` or ``Column`` allocation. Minimum
sizes remain soft when the terminal cannot fit them. Fixed sizes continue to use the current layout
rules. ``Modal`` is the exception: it deliberately omits fixed ``width`` and ``height`` attributes
so a layout can assign a flexible outer rectangle, then uses distinct preferred dimensions for the
centered inner frame. Phase 2 does not introduce a shared size-hints base class.

Widget-specific enum-like inputs use documented strings and raise ``ValueError`` for unknown
values. Negative offsets, content extents, or explicit dimensions raise ``ValueError``. Offsets
larger than the current content are safe: drawing clamps an effective offset without modifying the
public field. A maximum smaller than its corresponding minimum raises ``ValueError``. Text is
normalized through ``Canvas.write``, which removes existing ANSI sequences and replaces embedded
newlines on a single rendered row.

``Canvas.blit``
---------------

``ScrollView`` needs an isolated viewport so a child cannot draw into adjacent layout cells. The
minimal supporting canvas method is:

.. code-block:: python

   Canvas.blit(
       source: Canvas,
       *,
       x: int = 0,
       y: int = 0,
       source_rect: Rect | None = None,
   ) -> None

``source_rect=None`` means the full source canvas. The method intersects the source rectangle with
the source canvas, copies characters and ``Style`` objects to destination ``(x, y)``, and clips on
all source and destination edges. Destination ``(x, y)`` corresponds to the requested source
rectangle's original top-left cell; clipping a negative source origin shifts the first destination
cell by the same amount. The method does not resize either canvas or emit ANSI. Copying a canvas
onto itself must behave deterministically by reading the selected source cells before writing.

``Divider``
-----------

Approved constructor:

.. code-block:: python

   Divider(
       orientation: Literal["horizontal", "vertical"] = "horizontal",
       *,
       char: str | None = None,
       style: Style = PLAIN,
       width: int | None = None,
       height: int | None = None,
       min_width: int = 1,
       min_height: int = 1,
       max_width: int | None = None,
       max_height: int | None = None,
   )

The default character is ``-`` horizontally and ``|`` vertically. A custom character must be one
printable ASCII cell with no ANSI sequence; invalid values raise ``ValueError``. A horizontal
divider whose height is omitted has fixed height one. A vertical divider whose width is omitted
has fixed width one. When a larger rectangle is explicitly assigned, the line is drawn on the
center row or column, with an odd extra cell placed below or to the right. Canvas clipping handles
zero and undersized rectangles.

``StatusBadge``
---------------

Approved constructor:

.. code-block:: python

   StatusBadge(
       text: str,
       *,
       status: Literal["neutral", "info", "success", "warning", "error"] = "neutral",
       style: Style | None = None,
       width: int | None = None,
       min_width: int = 1,
       max_width: int | None = None,
   )

The badge is exactly one row high. Its stable ASCII prefixes are ``.`` for neutral, ``i`` for
information, ``+`` for success, ``!`` for warning, and ``x`` for error. The marker is followed by
one space and truncated text. At width one the marker wins, so semantic state remains visible on a
narrow terminal. ``style=None`` selects the internal semantic style: plain, bright blue, bright
green, bright yellow, or bright red respectively. An explicit style overrides the color but not
the ASCII prefix. ``color=False`` removes every ANSI sequence without changing geometry.

The widget exposes read-only layout attributes ``height=1``, ``min_height=1``, and
``max_height=1``; they are not constructor parameters. This lets ``Column`` allocate exactly one
row without offering a misleading variable-height badge API.

The status strings and ASCII markers are public behavior. The implementation may add new statuses
later, but it must not reinterpret existing ones.

Focus and ``ListView``
----------------------

Phase 2 does not add a global focus model. ``Panel.focused`` remains the standard container focus
indicator. ``ListView.focused`` only changes the marker for its active row; it does not accept
events or change the active item.

Approved constructor:

.. code-block:: python

   ListView(
       items: Sequence[str],
       *,
       active_index: int | None = None,
       scroll_offset: int = 0,
       focused: bool = False,
       style: Style = PLAIN,
       active_style: Style = Style(bold=True, bright=True),
       width: int | None = None,
       height: int | None = None,
       min_width: int = 1,
       min_height: int = 1,
       max_width: int | None = None,
       max_height: int | None = None,
   )

The constructor materializes ``items`` as a tuple so a rendered widget has a stable snapshot. Each
item occupies exactly one row. ``active_index=None`` means no active item; otherwise the index must
exist and invalid construction raises ``ValueError``. A focused active row uses ``>`` followed by
one space; an active row without focus uses ``*`` followed by one space; inactive rows reserve the
same two columns. At width one only the marker column is drawn. Empty lists draw blank cells.

``scroll_offset`` is the caller's requested first item. Drawing clamps it to the largest valid
offset for the current viewport. It does not automatically move the viewport to reveal
``active_index`` and never rewrites either field. This avoids hidden selection behavior: the
application updates both values after a key event, then redraws. Horizontal scrolling and
variable-height or widget items are not part of the first contract.

``ScrollView``
--------------

Approved constructor:

.. code-block:: python

   ScrollView(
       content: Widget | str,
       *,
       content_height: int,
       scroll_offset: int = 0,
       width: int | None = None,
       height: int | None = None,
       min_width: int = 1,
       min_height: int = 1,
       max_width: int | None = None,
       max_height: int | None = None,
   )

The caller supplies ``content_height`` because the minimal ``Widget`` protocol deliberately has no
measurement method. The view creates a canvas exactly as large as its assigned viewport, draws the
child at ``y=-effective_offset`` with logical height ``content_height``, then blits that isolated
canvas into its destination rectangle. Child output cannot escape the viewport, and styles survive
composition.

The effective vertical offset is clamped to ``0 .. max(0, content_height - viewport_height)``.
Content narrower or shorter than the viewport stays at its top-left origin and leaves the remaining
cells blank. Content always receives the viewport width, so the initial contract has no horizontal
scrolling and cannot create horizontal overflow.

``Modal``
---------

Approved constructor:

.. code-block:: python

   Modal(
       content: Widget | str,
       *,
       title: str = "",
       open: bool = True,
       preferred_width: int | None = 40,
       preferred_height: int | None = 10,
       min_width: int = 7,
       min_height: int = 3,
       max_width: int | None = None,
       max_height: int | None = None,
       style: Style = PLAIN,
       title_style: Style = Style(bold=True, bright=True),
   )

``open=False`` draws nothing. ``preferred_width=None`` or ``preferred_height=None`` requests all of
the corresponding available extent, still bounded by a maximum. When open, each preferred extent
is limited by its maximum, raised to its soft minimum, and finally clamped to the available
rectangle. This makes minima soft only when the terminal is too small. Centering uses integer
division; an odd spare cell remains on the right or bottom.

``Modal`` exposes minimum and maximum layout attributes but no fixed ``width`` or ``height``. A
``Row`` or ``Column`` therefore allocates a flexible outer rectangle using the existing layout
rules; the preferred dimensions size the centered inner frame only. As a root widget, the renderer's
full rectangle is the outer area.

The modal clears only its computed centered inner-frame rectangle and draws an ASCII ``Panel``
there. It never clears cells in the assigned outer rectangle that fall outside that frame, so a
base widget drawn first remains visible around it.

The modal header uses marker-priority composition rather than truncating ``"[x] " + title`` as one
string. Its available header width is the inner-frame width minus the border and the two decorative
padding cells used by ``Panel``. The implementation first copies as much of the literal ``[x]`` as
fits. When the complete marker and at least two more cells fit, it adds one separating space and
truncates only the caller's title into the remaining cells. It passes this already-fitted header to
``Panel``, so ``Panel`` never replaces the close marker with an ellipsis because of a long title.

The close marker is a presentation affordance, not a button or callback. The application handles
Escape or another modifier-free command by rebuilding with ``open=False``. Borders never move
outside the assigned area. Seven cells leave three header cells after the panel border and
decorative padding, so ``[x]`` is fully visible at the declared minimum for both empty and non-empty
titles. Below seven cells, the literal marker prefix is clipped to the available header cells.

``Modal`` does not dim or own an underlay and does not introduce an ``Overlay`` container. An
application that needs an overlay draws its base widget first and the modal second in its own small
composite widget. This keeps z-order and application state outside the library.

Implementation slices
---------------------

Implementation is split into focused pull requests:

1. ``Divider`` and ``StatusBadge`` plus public exports, docstrings, snapshots, and guide examples
   (issue #12).
2. ``ListView`` and focus/selection snapshots, including empty and narrow viewports (issue #14).
3. ``Canvas.blit`` and ``ScrollView`` with style-preserving clipping tests (issue #16).
4. ``Modal`` with centering, closed-state, under-minimum, and overlay-preservation snapshots
   (issue #18).
5. Final Phase 2 documentation, examples, images, and cross-platform manual verification.

Required verification
---------------------

Implementation pull requests must cover:

- exact ASCII snapshots with color disabled;
- ANSI-enabled output with equal visible widths;
- width zero/one and heights below preferred minima;
- invalid constructor values and empty content;
- offsets at zero, middle, end, and beyond the current maximum;
- active items both inside and outside the requested viewport;
- source and destination clipping plus style preservation for ``Canvas.blit``;
- overlapping self-blits left, right, up, and down plus one clipped overlap, with characters and
  styles copied from the pre-write snapshot;
- modal centering for odd/even spare space and no writes outside its rectangle;
- sentinel-background modal snapshots proving that centered and clipped inner frames leave every
  outer-rectangle cell outside the frame untouched;
- flexible ``Row``/``Column`` modal allocation independently from preferred inner-frame sizing;
- empty and non-empty modal titles at widths six through ten in ANSI and no-color mode, including
  the complete ``[x]`` marker at width seven and its deterministic literal prefix below minimum;
- Windows/Linux Python 3.11-3.13 CI, compileall, Sphinx warning-as-error, and manual examples.

Rejected alternatives
---------------------

``Enum`` exports for orientation and status
   Rejected initially because documented string literals provide validation without expanding the
   public namespace. An enum can be added only if real consumers need it.

Library-owned focus or selection manager
   Rejected because it would introduce application state, event routing, and lifecycle rules. The
   caller already owns dictionaries, persistence, and redraw timing.

Automatic scrolling to the active item
   Rejected because it silently rewrites the meaning of ``scroll_offset`` and makes resize behavior
   harder to predict. The application computes navigation state explicitly.

Variable-height widget items in ``ListView``
   Rejected because they require measurement and item identity contracts. The first list is a stable
   one-string-per-row primitive; generic content belongs in ``ScrollView``.

Horizontal scrolling
   Deferred because Phase 2 requires vertical scrolling and forbids accidental horizontal overflow.
   It can be additive later if a concrete consumer requires it.

Modal callbacks, backdrop ownership, and an overlay hierarchy
   Rejected because they couple presentation to input and application composition. ``open`` remains
   caller-owned state and z-order stays with the caller.

Shared widget base classes or size-hint mixins
   Rejected as speculative abstraction. Repeating the small set of layout attributes keeps the API
   structural and readable.

Reversibility and compatibility
-------------------------------

Before the first implementation merge, constructor names, defaults, marker choices, and internal
file placement remain reversible through this design review. After release, state ownership,
constructor parameters, accepted status/orientation values, ASCII markers, offset semantics,
``Canvas.blit`` clipping, modal preferred sizing, soft minima, ``[x]`` priority, and underlay
preservation become public compatibility commitments.

Later support for additional badge statuses, widget list items, horizontal offsets, modal backdrop
helpers, or pure navigation helpers can be additive. None is implemented pre-emptively. Existing
``Rect``, ``Canvas``, ``Style``, ``Label``, ``Panel``, ``Row``, ``Column``, renderer, terminal, and
event APIs remain unchanged by the design PR.

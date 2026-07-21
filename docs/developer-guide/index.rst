Developer guide
===============

Setup and checks
----------------

Install test and documentation tools without changing runtime dependencies:

.. code-block:: console

   python -m pip install -e ".[test,docs]"
   python -m pytest
   python -m compileall -q src tests examples
   python -m sphinx -W --keep-going -b html docs docs/_build/html
   python examples/basic_panels.py --no-color

Design contracts
----------------

Keep functions pure where practical. Widgets draw into a supplied ``Canvas`` and never print.
Layout computes rectangles; the renderer produces a frame; terminal helpers only expose platform
policy and dimensions. Application dictionaries and persisted state stay outside the package.

Names exported by ``thebitlab_tui.__all__`` are public API. Before changing a public signature,
return type, exception, import path, or documented behavior, create an issue and record whether the
change is compatible. Add tests before changing rendering output.

Tests and snapshots
-------------------

Use exact lists of ASCII rows for small snapshots. Each row must have the requested visible width.
Cover truncation, clipping, minimum dimensions, narrow stacking, focus/collapse, ANSI and
``no-color``. Terminal policy changes require explicit Windows and Linux cases.

``Divider`` orientation strings and ``StatusBadge`` status strings, markers, exceptions, and
visible-width behavior are public compatibility commitments. Changes require exact ASCII snapshots,
ANSI snapshots with equal visible widths, and width-zero/one coverage. These widgets remain pure
presentation objects and must not acquire callbacks or application state.

``ListView`` materializes items as a tuple and treats ``active_index``, ``focused``, and
``scroll_offset`` as immutable presentation inputs. Its ``>`` and ``*`` markers, two-column prefix,
viewport clamp, and no-auto-scroll behavior are compatibility commitments. Cover empty and clipped
viewports, offsets beyond the maximum, active items outside the viewport, ANSI/no-color, and widths
zero through three. Navigation and event dispatch belong to the application.

``Canvas.blit`` preserves cell characters and styles, keeps the requested source origin when
clipping, and snapshots all selected cells before an overlapping self-copy. Regression tests must
cover source and destination clipping plus left, right, up, down, and clipped self-overlap.

``ScrollView`` receives ``content_height`` and ``scroll_offset`` from the application. It draws on
a canvas exactly as large as the assigned viewport, then blits the complete result so blank cells
clear stale content and child output cannot escape. Cover short content, offsets beyond the
maximum, clipped outer rectangles, ANSI/no-color, and min/max/fixed layout. Do not add implicit
measurement, horizontal scrolling, navigation, or callbacks.

``Modal`` exposes minimum and maximum layout hints but deliberately has no fixed ``width`` or
``height`` attributes. Its preferred dimensions size only the centered inner frame. Cover odd and
even centering, ``open=False``, sentinel underlay preservation, ``None`` preferred dimensions,
min/max ordering, heights below three, widths six through ten, ANSI/no-color, and flexible
``Row``/``Column`` allocation. Keep ``[x]`` ahead of title text and do not add input, callbacks,
backdrop ownership, or a shared size-hint abstraction.

Documentation workflow
----------------------

Every public module, class, function, method, and property needs a docstring. Explain the contract,
parameters, return value, relevant exceptions, and non-obvious edge cases. Sphinx ``autodoc`` uses
those docstrings for the API reference.

Update the user guide for observable behavior, this developer guide for contribution workflow, and
the architecture guide for responsibility or dependency changes. Images must be reproducible SVG
or generated screenshots with useful alternative text.

Phase 2 API changes must follow the :doc:`../architecture/phase-2-contracts` design record. Update
the record before implementation when review changes state ownership, constructor fields, marker
semantics, clipping, or narrow-terminal behavior.

Terminal input development
--------------------------

Phase 3 follows :doc:`../architecture/phase-3-input-contracts`.  Public ``KeyReader`` owns only
single-use lifecycle and one absolute monotonic deadline per read.  Private backends own platform
readiness, decoding, partial state, and their FIFO.  Tests replace the private backend factory and
clock; these seams must not become constructor parameters, protocols, or factories in the public
namespace.

Keep platform imports lazy.  The shared facade must import on Windows and Linux without loading
``termios`` or Win32 bindings, and construction must have no terminal side effects.  A backend
receives an absolute deadline and returns at most one ``KeyEvent``; it must check already-buffered
or already-queued input before reporting expiration.  The application retains ownership of
commands, resize polling, state, and redraw.

Private backends may use the shared event FIFO, but retain ownership of decoding and partial input
state.  If activation fails after changing caller-owned state, the backend performs compensating
restoration itself because the facade cannot know whether a safe snapshot exists.  The activation
error stays primary and a restoration ``OSError`` is attached as a note; platform slices must test
that invariant with injected operations.

See ``docs/it/00-regole-operative.md`` for milestone, issue, PR, finding, and review rules.

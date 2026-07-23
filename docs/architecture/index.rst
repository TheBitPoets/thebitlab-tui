Architecture
============

Responsibility boundaries
-------------------------

.. image:: ../_static/images/architecture.svg
   :alt: Application data flows through an adapter and widget tree into layout, canvas, and renderer output, while terminal input is translated separately into key events.
   :align: center

Widgets describe presentation and draw within rectangles. Layout containers assign rectangles to
children. ``Canvas`` owns fixed-size cells and clipping. The renderer creates a canvas and returns
rows or text. The terminal layer reads dimensions, color capability, and normalized input through
private platform adapters, but never clears, prints, maps commands, or owns an event loop.
``ListView`` presents a tuple of strings plus caller-owned selection and viewport state; it does
not navigate, accept events, or mutate that state.
``Canvas.blit`` composes clipped character/style cells from a pre-write snapshot. ``ScrollView``
uses that operation to isolate oversized child rendering inside a viewport-sized canvas.
``Modal`` centers a preferred inner ``Panel`` inside a flexible outer rectangle and clears only
that inner frame. Visibility, z-order, input, and any surrounding underlay remain application
responsibilities.

Event flow
----------

Private Windows and Linux adapters translate terminal input into ``KeyEvent``. The application
updates its own focus, selection, collapse, and persistence state, rebuilds the widget tree, then
renders another complete frame. Modifier-free commands remain mandatory fallbacks.

For a list, that flow is ``KeyEvent`` to application-owned ``active_index`` and ``scroll_offset``
to a newly constructed ``ListView`` to renderer output. Clamping during drawing is local to the
current viewport and never becomes hidden application state.

``ScrollView`` follows the same ownership flow, with the application additionally supplying the
logical ``content_height`` because the structural widget protocol has no measurement operation.
The widget does not measure, navigate, or scroll horizontally.

For modal presentation the flow is ``KeyEvent`` to application-owned ``open`` state to a rebuilt
``Modal``. An application composite draws its base first and the modal second. The library does not
add an overlay hierarchy, dimming, callbacks, or hidden close behavior.

Student TUI adapter
-------------------

The future adapter lives in ``2cornot2c``, not in this package. It maps assignment-detail,
workspace, activity, allowed-help, help-request, report, test, grading, runner, and quick-guide
dictionaries to widgets. Existing ``.student-lab-layout.json`` state remains owned by the
application.

The adapter must be compatible with ``scripts/student_lab_layout.py`` and preserve its ASCII,
optional ANSI, responsive, and Windows/Linux behavior. No application code or data model is copied
into this library.

Phase design records
--------------------

.. toctree::
   :maxdepth: 1

   phase-2-contracts
   phase-2-verification
   phase-3-input-contracts
   phase-3-verification
   phase-4-adapter-contracts
   phase-4-verification
   utui-rename-contract

Student TUI integration
=======================

This guide describes the bounded Phase 4 path for integrating ``utui`` into an existing
student terminal application.  The normative decisions remain in
:doc:`../architecture/phase-4-adapter-contracts`; the corresponding automated evidence is indexed
in :doc:`../architecture/phase-4-verification`.

The executable files ``examples/student_dashboard_adapter.py`` and
``examples/student_dashboard_fixtures.py`` demonstrate the boundary with synthetic data.  They
are example and test artifacts, not public adapter API, an application schema, or an import target
for consumer code.  Phase 4 adds no names to ``utui.__all__``.

Ownership boundary
------------------

The dependency direction remains one way:

.. code-block:: text

   consumer dictionaries and state
       -> consumer-owned projection and validation
       -> neutral logical rows and normalized presentation state
       -> consumer-owned widget builder
       -> utui widgets
       -> render_lines/render
       -> consumer-owned clear, print, and redraw

The consumer owns its dictionaries, localization, missing-value policy, semantic formatting,
commands, event loop, persistence, errors, screen output, and redraw timing.  The library owns
only its existing widgets, layout, canvas, renderer, terminal-size helpers, and normalized input
contracts.  It never reads ``.student-lab-layout.json``, interprets application dictionaries, or
mutates caller state.

Persisted and transient state
-----------------------------

Keep persisted layout values separate from transient interaction values.  The persisted mapping
retains these consumer-defined meanings:

.. list-table:: Persisted layout translation
   :header-rows: 1
   :widths: 20 80

   * - Field
     - Adapter use
   * - ``orientation``
     - Select horizontal composition when it fits, or an explicit vertical composition.
   * - ``order``
     - Supply the validated order of all stable section identifiers; the adapter does not repair
       or save it.
   * - ``left_width``
     - Request the left-column allocation in a wide frame; responsive fitting never writes a
       reduced value back.
   * - ``collapsed``
     - Map membership to ``Panel(collapsed=True)``.
   * - ``focus``
     - Map equality to ``Panel(focused=True)``.

Scrolling, selection, and modal presentation are redraw inputs rather than hidden widget state:

.. list-table:: Transient presentation inputs
   :header-rows: 1
   :widths: 28 72

   * - Input
     - Responsibility
   * - ``dashboard_offset``
     - Requested first row of the complete dashboard viewport.
   * - ``section_offsets``
     - Requested first logical row for scrollable section content.
   * - ``list_offsets``
     - Requested first item for list-backed section content.
   * - ``active_indices``
     - Requested active items; any effective clamp during drawing is not persisted.
   * - ``modal``
     - Caller-owned visibility, title, and logical rows.  The application also owns close commands
       and overlay order.

Widgets may clamp an effective offset or index for the current rectangle, but rendering never
changes either mapping.  The consumer remains responsible for validation and persistence before
the adapter is called.

Responsive redraw
-----------------

Read the current terminal size and rebuild the widget tree for every redraw.  The initial
compatibility rules are:

* horizontal orientation at 90 columns or wider creates two columns of five ordered panels;
* the wide frame preserves the visible three-cell separator ``" | "``;
* explicit vertical orientation, or any width below 90 columns, creates one column in exact
  persisted order;
* the narrow tree is selected explicitly rather than by stacking two pre-grouped columns;
* logical panel and dashboard heights are recomputed for the current width;
* clipping and stable ``...`` truncation remain the final safety boundary.

Do not write a responsive width reduction, an effective scroll clamp, or a temporary focus change
back to persisted state.  Resize detection and redraw scheduling remain application decisions;
``ResizeWatcher`` can report a changed size without installing an event loop.

Reference frame
---------------

Render the synthetic reference dashboard at fixed dimensions for a reproducible, ANSI-free frame:

.. code-block:: console

   python examples/student_dashboard_adapter.py --width 100 --height 24 --no-color

The example also accepts the current terminal dimensions when ``--width`` and ``--height`` are
omitted.  Its revisioned fixture contains invented presentation rows only; real dictionaries,
business validation, and student data must not be copied into this repository.

The captures below are generated from the same ``phase4-v2`` fixture and checked against exact
renderer rows:

.. image:: ../_static/images/student-dashboard-wide.svg
   :alt: Ten synthetic student panels arranged in the wide two-column ASCII dashboard.
   :align: center

.. image:: ../_static/images/student-dashboard-narrow.svg
   :alt: The same ten synthetic student panels stacked in persisted order below the breakpoint.
   :align: center

.. image:: ../_static/images/student-dashboard-modal.svg
   :alt: A centered ASCII quick-help modal over the synthetic student dashboard.
   :align: center

Consumer migration and fallback
-------------------------------

A consumer migration should remain incremental:

1. Keep the existing dictionary loaders, normalization, and ``.student-lab-layout.json`` handling.
2. Project each application section into neutral logical rows or list items.
3. Translate the already-normalized persisted and transient state into existing widgets.
4. Rebuild and render at the current terminal size while the application continues to own output.
5. Map ``KeyEvent`` values to existing commands, always retaining alternatives that do not require
   Alt or Ctrl.
6. Preserve the existing text renderer as a feature or failure fallback during rollout.

Compatibility is semantic rather than byte-for-byte identity with the legacy renderer.  The
migration must preserve section identity and order, persisted-state meanings, complete ASCII and
``no-color`` operation, ANSI-independent geometry, the responsive breakpoint, modifier-free
commands, and a consumer-owned fallback.

Raw-dictionary projection tests, persisted JSON round trips, invalid-file recovery, command
mapping, rollout policy, and manual Windows/Linux integration evidence belong in the consumer
repository under a separately authorized issue and pull request.  Library tests never import,
vendor, or check out that repository.

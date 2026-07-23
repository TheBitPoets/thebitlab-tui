Phase 4 student TUI adapter contracts
=====================================

Status
------

Approval of this design record is recorded by merging PR `#44
<https://github.com/TheBitPoets/thebitlab-tui/pull/44>`_ for issue `#43
<https://github.com/TheBitPoets/thebitlab-tui/issues/43>`_ under parent issue `#25
<https://github.com/TheBitPoets/thebitlab-tui/issues/25>`_. The reference adapter, neutral
fixtures, and consumer integration must not begin before that merge.

Compatibility provenance
------------------------

The compatibility baseline comes from a read-only inspection of ``TheBitPoets/2cornot2c`` commit
``7a538d2edd1dca44c8f062888f508845f3441f1c``. The relevant files were
``scripts/student_lab_layout.py``, ``scripts/student_lab_cli.py``, and
``tests/test_student_lab_layout.py``; their inspected working-tree copies matched that commit.
This repository neither imports nor checks out the consumer during tests.

Decision
--------

Phase 4 uses two complementary artifacts:

* an executable reference adapter and synthetic fixtures outside ``src/thebitlab_tui``; and
* a normative recipe showing how a consumer composes the existing public widgets.

The reference adapter is example and test code, not library API. Phase 4 does not add a public
section model, adapter class, persistence API, measurement protocol, or export in
``thebitlab_tui.__all__``. A new public abstraction requires a separate design gate supported by
evidence from at least two consumers or by a missing reusable rendering primitive discovered while
building the reference adapter.

This choice keeps the contract executable without freezing student-domain vocabulary in the
micro-library. A documentation-only recipe was rejected as insufficient because prose can drift
from rendered frames. A public section or dashboard model was rejected as premature because it
would make consumer identifiers, persistence rules, and application semantics library
compatibility commitments.

One-way responsibility boundary
-------------------------------

The dependency and data flow is:

.. code-block:: text

   application dictionaries
       -> consumer-owned projection and validation
       -> neutral section rows + normalized presentation state
       -> consumer/reference widget builder
       -> existing thebitlab_tui widgets
       -> pure render_lines/render output
       -> consumer-owned clear, print, and redraw

The consumer owns:

* raw assignment, workspace, activity, support, help, report, test, grading, and runner data;
* missing-value handling, localization, formatting, and semantic-status mapping;
* loading, normalizing, saving, and migrating ``.student-lab-layout.json``;
* focus, collapse, selection, scrolling, modal visibility, and fallback state;
* key-to-command mappings, including alternatives without Alt or Ctrl;
* the event loop, terminal-size polling, screen clearing, printing, redraw timing, and errors.

The library owns only its existing widget, layout, canvas, renderer, terminal-size, and normalized
input contracts. It never imports the consumer, reads its JSON file, interprets application
dictionaries, or mutates presentation state.

Stable section identities
-------------------------

The compatibility projection always contains these ten identifiers. A missing or unavailable
application section is projected as a panel with a neutral placeholder row instead of being
removed. Titles are presentation defaults and may be localized by the consumer; identifiers are
the persisted compatibility keys.

.. list-table:: Neutral presentation roles
   :header-rows: 1

   * - Identifier
     - Current title
     - Neutral role
   * - ``assignment``
     - Dettaglio consegna
     - Assignment summary rows
   * - ``workspace``
     - Workspace
     - Workspace location and availability rows
   * - ``activity``
     - Activity
     - Activity metadata rows
   * - ``support``
     - Aiuto consentito
     - Allowed and disallowed help rows
   * - ``help``
     - Richieste aiuto
     - Help-request summary rows
   * - ``report``
     - Report
     - Report summary or scrollable rows
   * - ``tests``
     - Ultimo dettaglio test
     - Test result rows or an unavailable placeholder
   * - ``grading``
     - Grading
     - Grading status rows
   * - ``runner``
     - Runner
     - Runner status rows
   * - ``guide``
     - Guida rapida
     - Quick-guide rows and optional modal content

Neutral fixture boundary
------------------------

The next implementation slice will define revisioned synthetic fixture dictionaries outside the
installed package. Each fixture section contains only its identifier, display title, logical text
rows, and optional presentation-neutral status or list items. Fixtures contain invented values,
paths, names, and messages. They do not copy consumer dictionaries, validation code, business
rules, or real student data.

The fixture schema is test data, not public API. Tests and examples may import it from the
repository's example/test area, but application code must not import it from
``thebitlab_tui``. Changing its serialization, helper names, or synthetic contents remains
possible through focused snapshot review.

Persisted layout compatibility
------------------------------

The existing consumer owns a five-field normalized presentation mapping:

.. code-block:: json

   {
     "orientation": "horizontal",
     "order": [
       "assignment", "workspace", "activity", "support", "help",
       "report", "tests", "grading", "runner", "guide"
     ],
     "left_width": 62,
     "collapsed": [],
     "focus": "assignment"
   }

Phase 4 preserves the meaning of these fields without making their parser part of the library:

``orientation``
   ``horizontal`` requests a two-column dashboard when the current width permits it;
   ``vertical`` requests one ordered column.

``order``
   The consumer supplies a validated permutation of all ten identifiers. The adapter never
   repairs or persists an invalid order.

``left_width``
   The consumer supplies its existing normalized value. In a wide horizontal frame the adapter
   applies the legacy allocation exactly. The value stored on disk is not changed by a responsive
   frame.

``collapsed``
   Membership maps directly to ``Panel(collapsed=True)``. A collapsed panel has a three-row
   presentation and retains an ASCII state marker.

``focus``
   Equality maps directly to ``Panel(focused=True)``. The focus marker remains textual when ANSI
   is disabled.

There is no schema-version field today. Phase 4 neither adds one nor migrates the file. File
location, environment overrides, defaults, validation, atomic writes, and failure fallback remain
consumer behavior.

Responsive composition
-----------------------

Every redraw reads the current terminal size before rebuilding and rendering the frame. The
initial compatibility breakpoint is 90 columns, matching the observed consumer behavior:

* horizontal orientation at 90 columns or wider splits the validated order after five entries;
  the first five panels form the left ``Column`` and the remaining five form the right ``Column``;
* vertical orientation, or any width below 90 columns, creates one ``Column`` containing all ten
  panels in exact persisted order;
* the horizontal path retains the visible three-cell ASCII separator ``" | "``;
* the exact legacy allocation is
  ``effective_left = min(left_width, max(36, terminal_width - 39))`` followed by
  ``right_width = max(30, terminal_width - effective_left - 3)``;
* the narrow fallback is selected explicitly before constructing the tree. It does not rely on
  ``Row.stack_when_narrow`` because stacking two pre-grouped columns would not reproduce the
  persisted all-panel order.

Minimum sizes are soft when the terminal cannot satisfy them. Canvas clipping and stable-width
truncation remain the final safety boundary, so every returned row has exactly the requested
visible width and no widget can create accidental horizontal overflow.

Height, scrolling, and overlays
-------------------------------

The widget protocol deliberately has no measurement method. The reference adapter therefore
computes logical panel heights from its already-projected rows and passes explicit sizes to its
``Column`` instances. It computes the complete dashboard height at the current width, then may
place that dashboard in a ``ScrollView`` using a caller-owned dashboard offset. Responsive
wrapping requires the caller to recompute logical heights on every redraw.

Selection indices, per-section offsets, and the dashboard offset remain inputs. Drawing may clamp
an effective value for the current viewport but never writes the clamped value back. An
application-owned composite draws the dashboard first and an optional ``Modal`` second. Modal
visibility, close commands, z-order, and underlay policy never enter the library.

Compatibility promise
---------------------

Compatibility is semantic, not byte-for-byte or pixel identity with the legacy renderer. A
compatible adapter preserves:

* all ten identifiers, their order, focus, collapse, orientation, and ``left_width`` meaning;
* the 90-column initial transition between two columns and one ordered stack;
* complete ASCII borders and state markers with ANSI disabled;
* optional ANSI whose escape sequences do not affect visible geometry;
* stable clipping and ellipsis without moving borders or separators;
* modifier-free alternatives for every consumer workflow;
* a consumer-owned legacy renderer as a rollout and failure fallback.

The new widget frames may use different padding, panel heights, and internal panel decoration.
Those differences must be approved through deterministic snapshots; they must not silently change
persisted state or hide semantic information. The inter-column separator ``" | "`` remains binding
unless a separately approved consumer migration changes the compatibility baseline.

Required implementation evidence
--------------------------------

The reference-adapter slice must add neutral fixtures and deterministic checks for:

* all ten populated panels, empty data, missing optional data, and long rows;
* wide horizontal, explicit vertical, narrow stacked, and tiny clipped frames;
* reordered panels, every focused panel, collapsed panels, and unavailable sections;
* ANSI and ``no-color`` frames with identical visible geometry, including ANSI in input text;
* first, middle, and out-of-range scroll and selection inputs without state mutation;
* modal open and closed composition;
* resize sequences that rebuild at fixed injected terminal sizes;
* allocation boundaries at widths 89, 90, and 100 with persisted ``left_width`` values 36, 62,
  and 120, without mutating the persisted mapping;
* Windows and Linux example smoke tests without a runtime dependency;
* an unchanged public API manifest and strict Sphinx documentation.

The consumer repository separately owns raw-dictionary projection tests, persisted JSON round
trips and invalid-file fallback, key-command tests, its legacy renderer fallback, and manual
integration evidence. That work starts only after the verified ``utui`` rename baseline tracked
by parent issue #51 and through a separately authorized consumer issue and PR. The parent issue
records the exact library tag or commit, consumer commit or PR, fixture revision, and manual
Windows/Linux results; library CI never checks out or vendors the consumer repository.

Delivery sequence
-----------------

After this design gate is approved, Phase 4 remains split into bounded child issues:

1. add the non-public reference adapter, synthetic fixtures, and core wide/narrow snapshots;
2. verify persisted-layout translation, ASCII fallback, focus, collapse, resize, scrolling, modal,
   ANSI, and ``no-color`` behavior;
3. complete the Sphinx user/developer integration guides, reproducible images, and evidence matrix;
4. approve and complete the hard pre-v1 repository, distribution, and import rename tracked by
   parent issue #51 and :doc:`utui-rename-contract`;
5. collect separately authorized consumer evidence using only the verified ``utui`` baseline and
   without coupling the repositories;
6. run a documentation-only closeout before version ``0.4.0``, tag, release, parent, and milestone
   closure in the documented order.

Reversibility
-------------

Example paths, fixture serialization, synthetic contents, snapshot organization, non-public
helper names, and exact internal composition helpers are reversible. The initial breakpoint and
column split are fixture-level compatibility choices and may change only through an explicit
consumer migration and snapshot review.

New public exports or signatures, library acceptance of student dictionaries, library ownership
of persistence/defaults, a widget measurement protocol, an event loop, or application commands
are high-cost decisions. They are deferred and require a new design issue before implementation.

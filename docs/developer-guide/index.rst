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
Layout computes rectangles; the renderer produces a frame; terminal helpers expose platform
policy, dimensions, and normalized input through private adapters. Applications retain commands,
event loops, redraw, dictionaries, and persisted state outside the package.

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

The private POSIX implementation keeps byte decoding separate from descriptor I/O.  Its decoder
is pure and tested on every platform; the backend lazily imports POSIX modules only after Linux is
selected.  Activation deep-copies the complete ``termios`` snapshot, clears only ``ECHO`` and
``ICANON``, sets ``VMIN=1`` and ``VTIME=0``, and restores that snapshot with ``TCSANOW``.  Do not
replace this with raw mode, non-blocking descriptor flags, signal handlers, or input flushing.
Linux PTY tests provide the operating-system evidence; injected operations cover deadlines,
interruption, EOF, setup compensation, and restoration retry on Windows CI as well.

The private Windows implementation separates pure console-record decoding from ``ctypes`` I/O.
It obtains the borrowed handle through ``sys.stdin.fileno()`` and ``msvcrt.get_osfhandle()``,
requires processed input, and binds only ``GetConsoleMode``, ``WaitForSingleObject``, and
``ReadConsoleInputW``.  It never calls ``SetConsoleMode`` or ``CloseHandle``.  Fixed-width ABI
structures and injected operations keep normalization, absolute deadlines, repeat runs, and
UTF-16 surrogate handling deterministic on every CI platform.  Keep ``msvcrt`` and kernel32
loading inside the Windows-only default-operation factory.

The cross-platform ownership example is ``examples/terminal_input.py``. Keep its
``ApplicationState``, command mapping, finite polling loop, frame presenter, and resize/redraw
decision outside ``src/thebitlab_tui``. Its snapshot mode must stay non-interactive and
deterministic so Windows/Linux CI and the reproducible SVG can compare exact ASCII rows. Its
interactive mode must reject redirected stdin with ``io.UnsupportedOperation`` rather than adding
a pipe protocol to ``KeyReader``.

Before the Phase 3 release, follow :doc:`../architecture/phase-3-verification`. Automated backend
tests are necessary but do not prove terminal restoration or key delivery in a real terminal.
Record separate manual results for Linux, Windows Terminal with PowerShell, and Windows Terminal
with ``cmd.exe``; leave missing environments explicitly ``NOT RUN``.

Phase 4 reference-adapter maintenance
-------------------------------------

The Phase 4 adapter and synthetic fixtures remain under ``examples/`` and outside the installed
package. They are executable evidence, not public API or a consumer dictionary schema. Never
import, vendor, or copy application data from ``2cornot2c``; consumer projection, validation,
persistence, commands, event loops, printing, and legacy fallback stay in that repository.

Keep the five persisted layout fields separate from transient dashboard/section/list offsets,
selection, and modal presentation. Rendering may clamp an effective value but must not repair or
mutate caller mappings. If fixture structure or meaning changes, update ``FIXTURE_REVISION`` and
review every wide, narrow, tiny, resize, focus, collapse, scroll, selection, modal, ANSI, and
``no-color`` snapshot affected by that change.

Regenerate the accessible Phase 4 SVG captures with only the standard library:

.. code-block:: console

   python tools/generate_phase4_images.py

``tests/test_docs_assets.py`` compares every captured terminal row to
``render_reference_frame``. Before proposing a change, also follow
:doc:`the Phase 4 verification matrix <../architecture/phase-4-verification>` and confirm that
``src/``, ``thebitlab_tui.__all__``, and runtime dependency metadata are unchanged unless a
separate design gate explicitly approves otherwise.

See ``docs/it/00-regole-operative.md`` for milestone, issue, PR, finding, and review rules.

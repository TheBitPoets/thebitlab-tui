Phase 3 release verification
============================

Version ``0.3.0`` consolidates the dependency-free terminal input adapters without changing the
approved public signatures or moving command, state, event-loop, or redraw ownership into the
library. This page is the versioned evidence index for child issue `#39
<https://github.com/TheBitPoets/thebitlab-tui/issues/39>`_. A separate closeout issue will publish
the tag and GitHub release only after this evidence is complete.

Compatibility and evidence matrix
---------------------------------

.. list-table:: Phase 3 delivery evidence
   :header-rows: 1
   :widths: 18 18 21 22 21

   * - Capability
     - Delivery
     - Contract and API
     - Deterministic tests
     - Guide or example
   * - Shared ``KeyReader`` facade
     - `Issue #33 <https://github.com/TheBitPoets/thebitlab-tui/issues/33>`__ /
       `PR #34 <https://github.com/TheBitPoets/thebitlab-tui/pull/34>`__
     - :doc:`Input contracts <phase-3-input-contracts>`;
       :doc:`API reference <../api/index>` (``docs/api/index.rst``)
     - ``tests/test_key_reader.py`` and ``tests/test_public_api_docs.py``
     - :doc:`User guide <../user-guide/index>` (``docs/user-guide/index.rst``)
   * - Linux POSIX backend
     - `Issue #35 <https://github.com/TheBitPoets/thebitlab-tui/issues/35>`__ /
       `PR #36 <https://github.com/TheBitPoets/thebitlab-tui/pull/36>`__
     - :doc:`Input contracts <phase-3-input-contracts>`
     - ``tests/test_posix_decoder.py``, ``tests/test_posix_input.py``, and
       ``tests/test_posix_pty.py``
     - :doc:`Developer guide <../developer-guide/index>`
       (``docs/developer-guide/index.rst``)
   * - Windows console-record backend
     - `Issue #37 <https://github.com/TheBitPoets/thebitlab-tui/issues/37>`__ /
       `PR #38 <https://github.com/TheBitPoets/thebitlab-tui/pull/38>`__
     - :doc:`Input contracts <phase-3-input-contracts>`
     - ``tests/test_windows_decoder.py`` and ``tests/test_windows_input.py``
     - :doc:`Developer guide <../developer-guide/index>`
       (``docs/developer-guide/index.rst``)
   * - Application-owned loop and resize redraw
     - `Issue #39 <https://github.com/TheBitPoets/thebitlab-tui/issues/39>`__
     - No new public API; uses ``KeyReader``, ``ResizeWatcher``, and pure rendering
     - ``tests/test_terminal_input_example.py``, ``tests/test_examples.py``,
       ``tests/test_docs_assets.py``, and ``tests/test_release_metadata.py``
     - ``examples/terminal_input.py`` and ``docs/_static/images/terminal-input.svg``

Automated gates
---------------

The example's default and explicit ``--snapshot`` modes never open terminal input. The no-color
snapshot is deterministic, contains no ANSI sequence, and preserves the requested visible width
and height on Windows and Linux CI. ``tests/test_docs_assets.py`` compares the SVG terminal rows
to that executable frame and checks accessible ``title`` and ``desc`` metadata.

Run the complete automated gates from the repository root:

.. code-block:: console

   python -m pytest
   python -m compileall -q src tests examples docs/conf.py
   python -m sphinx -E -W --keep-going -b html docs docs/_build/html
   python examples/basic_panels.py --no-color
   python examples/divider_badges.py --no-color
   python examples/selectable_list.py --no-color
   python examples/scroll_view.py --no-color
   python examples/modal.py --no-color
   python examples/terminal_input.py --snapshot --no-color
   git diff --check

GitHub Actions repeats pytest and syntax checks on Windows and Linux with Python 3.11, 3.12, and
3.13, plus a warning-as-error Sphinx build. Injected backend tests and CI do not replace the real
interactive checks below.

Manual terminal protocol
------------------------

Run every row with a supported Python version (3.11 or newer) on the runtime commit proposed for
merge. Record date, OS version, terminal, shell, Python version, commit, result, and notes. An
evidence-only follow-up may record those results without repeating the interactive protocol when
it changes no runtime or example code. A redirected Codex or CI shell is **not** an interactive
terminal and cannot be recorded as a pass.

.. list-table:: Required interactive environments
   :header-rows: 1
   :widths: 28 14 58

   * - Environment
     - Current result
     - Evidence
   * - Linux terminal
     - PASS
     - 2026-07-21; Debian GNU/Linux 13 (trixie) container in Docker Desktop 28.3.2;
       Linux PTY hosted by Windows Terminal; Python 3.11.15; commit ``5e88c35``. The maintainer
       completed the full protocol, including resize, restoration, failure, and redirected-input
       checks.
   * - Windows Terminal with PowerShell
     - PASS
     - 2026-07-21; Windows 11 Pro 10.0.26200.8875; Windows Terminal 1.24.11321.0;
       PowerShell 5.1.26100.8875; isolated Python 3.11.15 virtual environment; commit
       ``5e88c35``. The maintainer completed the full protocol.
   * - Windows Terminal with ``cmd.exe``
     - PASS
     - 2026-07-21; Windows 11 Pro 10.0.26200.8875; Windows Terminal 1.24.11321.0;
       ``cmd.exe`` 10.0.26200.8875; isolated Python 3.11.15 virtual environment; commit
       ``5e88c35``. The maintainer completed the full protocol.

For each environment:

1. Run ``python examples/terminal_input.py --interactive --no-color`` and exercise arrows, Enter,
   Escape, Tab, printable ASCII, and a non-ASCII character that the terminal can transmit.
2. Confirm the modifier-free alternatives ``k``, ``j``, ``n``, Space, and ``q`` perform the same
   workflows without requiring Alt or Ctrl.
3. Resize wide to narrow to wide, including a height change. Panels must switch between adjacent
   and stacked layouts without horizontal overflow, shifted borders, or stale rows.
4. Interrupt while waiting with Ctrl+C. Confirm the process exits and the shell still accepts
   normal echoed input.
5. Run ``python examples/terminal_input.py --interactive --no-color --fail-after-key``, press one
   key, and confirm the intentional error appears only after terminal state restoration; the shell
   must remain usable.
6. Confirm ``--no-color`` removes SGR color styling. The interactive example's clear/home control
   sequences belong to its application presenter; ``--snapshot --no-color`` is the completely
   ANSI-free fallback.
7. Pipe text into interactive mode. It must exit with code 2 and a concise ``terminal input
   unavailable`` message, without a traceback or an attempt to treat the pipe as keyboard input.

Use these redirected-input commands:

.. code-block:: console

   # Linux
   printf 'q\n' | python examples/terminal_input.py --interactive --no-color

   # Windows Terminal / PowerShell
   "q" | python examples/terminal_input.py --interactive --no-color

   # Windows Terminal / cmd.exe
   echo q| python examples\terminal_input.py --interactive --no-color

Release boundary
----------------

The ``0.3.0`` source metadata and changelog are prepared here, but no tag or release is evidence
until all manual rows pass, CI is green, and two consecutive clean PR review rounds refer to the
same HEAD. ``tests/test_release_metadata.py`` keeps package, Sphinx, changelog, and dependency
metadata aligned. The follow-up closeout change must merge first. Then verify CI on its exact
``master`` commit, create annotated tag ``v0.3.0`` on that commit, publish the matching GitHub
release, close the closeout child, close parent #24, and finally close milestone ``Terminal
adapters v0.3``.

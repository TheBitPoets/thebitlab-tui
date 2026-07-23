Phase 4 integration verification
================================

This page is the versioned evidence index for Phase 4 child issue `#49
<https://github.com/TheBitPoets/utui/issues/49>`_ under parent issue `#25
<https://github.com/TheBitPoets/utui/issues/25>`_. It records library-side evidence
without turning the reference adapter, fixture schema, or student-domain vocabulary into public
API.

Provenance
----------

The evidence baseline is:

* Phase 4 contract approval in PR `#44
  <https://github.com/TheBitPoets/utui/pull/44>`_;
* reference adapter and neutral fixtures in PR `#46
  <https://github.com/TheBitPoets/utui/pull/46>`_;
* complete reference-adapter behavior matrix in PR `#48
  <https://github.com/TheBitPoets/utui/pull/48>`_;
* merged library baseline ``dbc36eabbb47562a2977597da833e092dec9f2b4``;
* synthetic fixture revision ``phase4-v2``; and
* read-only consumer compatibility baseline
  ``7a538d2edd1dca44c8f062888f508845f3441f1c``.

The consumer baseline identifies what was inspected when the contract was designed. It is not a
consumer integration result. The library test suite never imports, checks out, or vendors the
consumer repository.

Library evidence matrix
-----------------------

.. list-table:: Phase 4 library-side evidence
   :header-rows: 1
   :widths: 19 20 24 25 12

   * - Capability
     - Contract or source
     - Deterministic evidence
     - Guide or execution path
     - Status
   * - Ten neutral sections, stable identities, and unavailable placeholders
     - :doc:`Adapter contract <phase-4-adapter-contracts>`;
       ``examples/student_dashboard_fixtures.py``
     - ``tests/test_student_dashboard_adapter.py``;
       ``tests/test_student_dashboard_evidence.py``
     - :doc:`Sphinx integration guide <../integration/index>`
       (``docs/integration/index.rst``);
       ``examples/student_dashboard_adapter.py``
     - Automated PASS
   * - Persisted ``orientation``, ``order``, ``left_width``, ``collapsed``, and ``focus``
       translation
     - :doc:`Adapter contract <phase-4-adapter-contracts>`;
       ``examples/student_dashboard_adapter.py``
     - Allocation boundaries at widths 89, 90, and 100 with requested widths 36, 62, and 120 in
       ``tests/test_student_dashboard_evidence.py``
     - :doc:`Sphinx integration guide <../integration/index>`
     - Automated PASS
   * - Wide, vertical, narrow, and tiny ASCII composition
     - ``examples/student_dashboard_adapter.py``
     - Exact frames, clipping, ellipsis, ordering, and visible-width checks in
       ``tests/test_student_dashboard_adapter.py`` and
       ``tests/test_student_dashboard_evidence.py``
     - :doc:`Examples guide <../examples/index>` (``docs/examples/index.rst``);
       ``docs/_static/images/student-dashboard-wide.svg``;
       ``docs/_static/images/student-dashboard-narrow.svg``;
       executable ``--no-color`` reference frame
     - Automated PASS
   * - ANSI and ``no-color`` geometry
     - :doc:`Adapter contract <phase-4-adapter-contracts>`
     - Library-owned color and caller-supplied ANSI text checks in
       ``tests/test_student_dashboard_adapter.py`` and
       ``tests/test_student_dashboard_evidence.py``
     - :doc:`Developer guide <../developer-guide/index>`
       (``docs/developer-guide/index.rst``)
     - Automated PASS
   * - Caller-owned focus, collapse, scrolling, and selection
     - ``examples/student_dashboard_fixtures.py``;
       ``examples/student_dashboard_adapter.py``
     - Every focused and collapsed section plus first, middle, and out-of-range viewport inputs in
       ``tests/test_student_dashboard_evidence.py``
     - :doc:`User guide <../user-guide/index>` (``docs/user-guide/index.rst``)
     - Automated PASS
   * - Caller-owned modal composition
     - :doc:`Adapter contract <phase-4-adapter-contracts>`;
       ``examples/student_dashboard_adapter.py``
     - Open and closed modal checks with underlay and state preservation in
       ``tests/test_student_dashboard_evidence.py``
     - ``docs/_static/images/student-dashboard-modal.svg``
     - Automated PASS
   * - Resize rebuild and modifier-free presentation
     - ``examples/student_dashboard_adapter.py``;
       fixture revision ``phase4-v2``
     - Injected wide, narrow, tiny, and wide sequence plus portable command text checks in
       ``tests/test_student_dashboard_evidence.py``
     - :doc:`Sphinx integration guide <../integration/index>`
     - Automated PASS
   * - Windows and Linux package-side behavior
     - Dependency-free reference example
     - ``tests/test_examples.py`` on the Windows/Linux Python 3.11--3.13 CI matrix
     - ``examples/student_dashboard_adapter.py`` with ``--no-color``
     - CI PASS
   * - Stable package boundary
     - ``utui.__all__`` and project metadata
     - ``tests/test_public_api_docs.py``;
       ``tests/test_release_metadata.py``
     - :doc:`API reference <../api/index>`
     - Automated PASS

``CI PASS`` means that the synthetic package-side example ran in the supported CI environments.
It does not mean that the real student application has been integrated or manually accepted on
those platforms.

Automated verification
----------------------

Run the library-side evidence from the repository root:

.. code-block:: console

   python -m pytest
   python -m compileall -q src tests examples docs/conf.py
   python -m sphinx -E -W --keep-going -b html docs docs/_build/html
   python examples/student_dashboard_adapter.py --no-color --width 100 --height 24
   python examples/student_dashboard_adapter.py --no-color --width 89 --height 38
   git diff --check

These commands verify synthetic frames and the approved one-way boundary. They do not read
``.student-lab-layout.json``, exercise consumer dictionaries, or replace a real consumer
integration.

Versioned evidence files
------------------------

The matrix is protected by repository-relative paths so moved or missing evidence fails tests:

* ``docs/architecture/phase-4-adapter-contracts.rst`` and
  ``docs/architecture/phase-4-verification.rst``;
* ``docs/integration/index.rst``, ``docs/user-guide/index.rst``,
  ``docs/developer-guide/index.rst``, and ``docs/examples/index.rst``;
* ``docs/_static/images/student-dashboard-wide.svg``,
  ``docs/_static/images/student-dashboard-narrow.svg``, and
  ``docs/_static/images/student-dashboard-modal.svg``;
* ``examples/student_dashboard_adapter.py`` and
  ``examples/student_dashboard_fixtures.py``;
* ``tools/generate_phase4_images.py``;
* ``tests/test_student_dashboard_adapter.py``,
  ``tests/test_student_dashboard_evidence.py``, ``tests/test_examples.py``,
  ``tests/test_public_api_docs.py``, ``tests/test_phase4_contract.py``, and
  ``tests/test_docs_assets.py``.

Consumer evidence handoff
-------------------------

The following evidence remains **PENDING** and must not be recorded as PASS until separately
authorized work is completed in the consumer repository:

.. list-table:: Consumer-owned integration evidence
   :header-rows: 1
   :widths: 29 17 54

   * - Evidence
     - Current status
     - Required future record
   * - Raw application-dictionary projection
     - PENDING
     - Consumer issue and PR, exact commit, and projection tests for all ten stable identifiers
   * - ``.student-lab-layout.json`` round trips and invalid-file fallback
     - PENDING
     - Consumer tests for load, normalization, migration policy, atomic save, and failure fallback
   * - Existing command mapping and modifier-free alternatives
     - PENDING
     - Consumer tests and manual confirmation without moving command ownership into the library
   * - Legacy ASCII renderer rollout and failure fallback
     - PENDING
     - Consumer PR and manual evidence that the previous renderer remains selectable or recoverable
   * - Windows student-TUI integration
     - PENDING
     - Date, Windows version, terminal, shell, Python version, library commit or tag, consumer
       commit or PR, fixture revision, result, and notes
   * - Linux student-TUI integration
     - PENDING
     - Date, distribution, terminal, shell, Python version, library commit or tag, consumer commit
       or PR, fixture revision, result, and notes

When that work is authorized, parent issue #25 records the exact library tag or commit, consumer
commit or PR, fixture revision, and manual Windows/Linux results. The consumer continues to own
application dictionaries, persistence, commands, the event loop, terminal clearing and printing,
redraw timing, and the legacy fallback. This page must be updated through a focused evidence
change; pending rows must never be inferred from library CI.

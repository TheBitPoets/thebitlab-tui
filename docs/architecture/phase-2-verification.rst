Phase 2 release verification
============================

Version ``0.2.0`` consolidates the Phase 2 contracts without changing their public signatures or
state ownership. The matrix below is the release evidence index. Paths are repository-relative so
contributors can inspect and execute every artifact locally.

.. list-table:: Compatibility and evidence matrix
   :header-rows: 1
   :widths: 17 14 18 18 18 15

   * - Capability
     - Delivery
     - Public reference
     - Guide and example
     - Reproducible image
     - Snapshot tests
   * - ``Divider`` and ``StatusBadge``
     - `Issue #12 <https://github.com/TheBitPoets/thebitlab-tui/issues/12>`__ /
       `PR #13 <https://github.com/TheBitPoets/thebitlab-tui/pull/13>`__
     - :doc:`API reference <../api/index>` (``docs/api/index.rst``)
     - :doc:`User guide <../user-guide/index>` (``docs/user-guide/index.rst``);
       `example <https://github.com/TheBitPoets/thebitlab-tui/blob/master/examples/divider_badges.py>`__
       (``examples/divider_badges.py``)
     - Not needed: exact text snapshots carry the visual contract
     - `Snapshots <https://github.com/TheBitPoets/thebitlab-tui/blob/master/tests/test_divider_status_badge.py>`__
       (``tests/test_divider_status_badge.py``)
   * - ``ListView``
     - `Issue #14 <https://github.com/TheBitPoets/thebitlab-tui/issues/14>`__ /
       `PR #15 <https://github.com/TheBitPoets/thebitlab-tui/pull/15>`__
     - :doc:`API reference <../api/index>` (``docs/api/index.rst``)
     - :doc:`User guide <../user-guide/index>` (``docs/user-guide/index.rst``);
       `example <https://github.com/TheBitPoets/thebitlab-tui/blob/master/examples/selectable_list.py>`__
       (``examples/selectable_list.py``)
     - `SVG <https://github.com/TheBitPoets/thebitlab-tui/blob/master/docs/_static/images/selectable-list.svg>`__
       (``docs/_static/images/selectable-list.svg``)
     - `Snapshots <https://github.com/TheBitPoets/thebitlab-tui/blob/master/tests/test_list_view.py>`__
       (``tests/test_list_view.py``)
   * - ``Canvas.blit`` and ``ScrollView``
     - `Issue #16 <https://github.com/TheBitPoets/thebitlab-tui/issues/16>`__ /
       `PR #17 <https://github.com/TheBitPoets/thebitlab-tui/pull/17>`__
     - :doc:`API reference <../api/index>` (``docs/api/index.rst``)
     - :doc:`User guide <../user-guide/index>` (``docs/user-guide/index.rst``);
       `example <https://github.com/TheBitPoets/thebitlab-tui/blob/master/examples/scroll_view.py>`__
       (``examples/scroll_view.py``)
     - `SVG <https://github.com/TheBitPoets/thebitlab-tui/blob/master/docs/_static/images/scroll-view.svg>`__
       (``docs/_static/images/scroll-view.svg``)
     - `Canvas snapshots <https://github.com/TheBitPoets/thebitlab-tui/blob/master/tests/test_canvas.py>`__
       (``tests/test_canvas.py``);
       `viewport snapshots <https://github.com/TheBitPoets/thebitlab-tui/blob/master/tests/test_scroll_view.py>`__
       (``tests/test_scroll_view.py``)
   * - ``Modal``
     - `Issue #18 <https://github.com/TheBitPoets/thebitlab-tui/issues/18>`__ /
       `PR #19 <https://github.com/TheBitPoets/thebitlab-tui/pull/19>`__
     - :doc:`API reference <../api/index>` (``docs/api/index.rst``)
     - :doc:`User guide <../user-guide/index>` (``docs/user-guide/index.rst``);
       `example <https://github.com/TheBitPoets/thebitlab-tui/blob/master/examples/modal.py>`__
       (``examples/modal.py``)
     - `SVG <https://github.com/TheBitPoets/thebitlab-tui/blob/master/docs/_static/images/modal.svg>`__
       (``docs/_static/images/modal.svg``)
     - `Snapshots <https://github.com/TheBitPoets/thebitlab-tui/blob/master/tests/test_modal.py>`__
       (``tests/test_modal.py``)
   * - Responsive ``Row`` / ``Column`` baseline
     - Phase 1 baseline
     - :doc:`API reference <../api/index>` (``docs/api/index.rst``)
     - :doc:`User guide <../user-guide/index>` (``docs/user-guide/index.rst``);
       `example <https://github.com/TheBitPoets/thebitlab-tui/blob/master/examples/basic_panels.py>`__
       (``examples/basic_panels.py``)
     - `Wide SVG <https://github.com/TheBitPoets/thebitlab-tui/blob/master/docs/_static/images/three-panels-wide.svg>`__
       (``docs/_static/images/three-panels-wide.svg``);
       `narrow SVG <https://github.com/TheBitPoets/thebitlab-tui/blob/master/docs/_static/images/three-panels-narrow.svg>`__
       (``docs/_static/images/three-panels-narrow.svg``)
     - `Layout snapshots <https://github.com/TheBitPoets/thebitlab-tui/blob/master/tests/test_layout.py>`__
       (``tests/test_layout.py``);
       `renderer snapshots <https://github.com/TheBitPoets/thebitlab-tui/blob/master/tests/test_renderer.py>`__
       (``tests/test_renderer.py``)

Automated gates
---------------

``tests/test_public_api_docs.py`` freezes the complete public export manifest and requires
docstrings for every public object. ``tests/test_examples.py`` executes every documented example
with ``--no-color`` and checks stable ASCII geometry. ``tests/test_docs_assets.py`` compares each
terminal SVG capture with the corresponding example frame, in addition to checking accessible
SVG metadata.

The GitHub Actions matrix runs pytest and ``compileall`` on Windows and Linux with Python 3.11,
3.12, and 3.13. A separate job builds Sphinx with warnings treated as errors. This verifies the
supported platforms; it does not introduce platform-specific terminal input, which remains Phase
3 work.

Manual release check
--------------------

Run the same deterministic checks before publishing a release:

.. code-block:: console

   python -m pytest
   python -m compileall -q src tests examples docs/conf.py
   python -m sphinx -E -W --keep-going -b html docs docs/_build/html
   python examples/basic_panels.py --no-color
   python examples/divider_badges.py --no-color
   python examples/selectable_list.py --no-color
   python examples/scroll_view.py --no-color
   python examples/modal.py --no-color

After the Phase 2 closeout change is merged, tag its resulting ``master`` commit as ``v0.2.0`` and
publish the GitHub release from the matching changelog section. This ordering keeps the completed
roadmap and verification record inside the released source. Terminal adapters, direct student TUI
integration, mouse support, drag and drop, tmux-specific behavior, and animation timing remain
explicitly deferred.

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

See ``docs/it/00-regole-operative.md`` for milestone, issue, PR, finding, and review rules.

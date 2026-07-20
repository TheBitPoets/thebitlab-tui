Examples
========

Three responsive panels
-----------------------

``examples/basic_panels.py`` builds assignment, activity, and test panels. Run it with:

.. code-block:: console

   python examples/basic_panels.py --no-color

The same widget tree renders side by side in a wide terminal and stacks when declared minimum
widths cannot fit. The application decides when to print the returned frame.

Additional examples
-------------------

- ``examples/selectable_list.py`` represents selection with current primitives while ``ListView``
  remains roadmap work.
- ``examples/modal.py`` demonstrates manual centered composition before the public ``Modal``
  widget is introduced.

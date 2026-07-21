Examples
========

Three responsive panels
-----------------------

``examples/basic_panels.py`` builds assignment, activity, and test panels. Run it with:

.. code-block:: console

   python examples/basic_panels.py --no-color

The same widget tree renders side by side in a wide terminal and stacks when declared minimum
widths cannot fit. The application decides when to print the returned frame.

Dividers and status badges
--------------------------

``examples/divider_badges.py`` demonstrates both divider orientations and all semantic badge
states. Run it without ANSI styling with:

.. code-block:: console

   python examples/divider_badges.py --no-color

The ASCII markers retain meaning when color is disabled:

.. code-block:: text

   . queued
   i running
   + passed
   ! needs attention
   x failed

The example also composes a vertical divider through ``Row``. The application owns printing and
terminal color policy; the widgets only draw into the canvas.

Additional examples
-------------------

- ``examples/selectable_list.py`` represents selection with current primitives while ``ListView``
  remains roadmap work.
- ``examples/modal.py`` demonstrates manual centered composition before the public ``Modal``
  widget is introduced.

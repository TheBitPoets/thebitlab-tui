User guide
==========

Installation
------------

The library requires Python 3.11 or newer and has no runtime dependencies. During development it
can be installed from the repository with ``python -m pip install -e .``.

First frame
-----------

Widgets create a presentation tree; the renderer returns rows or a string. Printing remains an
application decision.

.. code-block:: python

   from thebitlab_tui import Panel, Row, render

   screen = Row([
       Panel("Exercise 01", title="Assignment", min_width=20),
       Panel("No recent events", title="Activity", min_width=20),
       Panel("3 passed", title="Tests", min_width=16),
   ])

   frame = render(screen, width=72, height=8, color=False)
   print(frame)

Widgets and layout
------------------

``Label`` draws text with left, center, or right alignment. It can wrap or truncate with ``...``.
``Panel`` adds an ASCII border, title, focus marker, and collapsed state. ``Row`` distributes width
using fixed or flexible ``Size`` values; ``Column`` distributes height.

When the minimum widths of a row no longer fit, its children stack vertically. If even the minimum
dimensions cannot fit, clipping prevents horizontal overflow.

Color and terminals
-------------------

Pass ``color=True`` only after applying the application's terminal policy. Pass ``color=False``
for ``--no-color``. ANSI styling is attached to canvas cells and is excluded from visible-width
calculations. ``render_terminal`` reads the size on every invocation, while ``ResizeWatcher``
reports changes without installing signals or an event loop.

Always provide keyboard commands without Alt or Ctrl when input adapters are added: those
modifiers are not transmitted consistently by every Windows terminal.

.. image:: ../_static/images/three-panels-narrow.svg
   :alt: The same three ASCII panels stacked in a narrow terminal.
   :align: center

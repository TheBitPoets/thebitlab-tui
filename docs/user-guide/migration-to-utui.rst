Migrating to ``utui``
=======================

The project identity changed before version 1.0 from the distribution
``thebitlab-tui`` and import package ``thebitlab_tui`` to the single name
``utui``.  This is a hard rename: the new distribution deliberately contains
no compatibility module or import alias.

Why uninstall first
-------------------

Python package managers treat ``thebitlab-tui`` and ``utui`` as different
distributions.  Installing the new project alone does not remove the old
package, so both imports could otherwise remain available in one environment.
Stop processes using the library and perform the explicit uninstall and
verification below.

Virtual environments
--------------------

Activate the target virtual environment, then remove the old distribution:

.. code-block:: console

   python -m pip uninstall thebitlab-tui
   python -c "import importlib.metadata as m, importlib.util as u; assert not any((d.metadata.get('Name') or '').lower().replace('_', '-') == 'thebitlab-tui' for d in m.distributions()); assert u.find_spec('thebitlab_tui') is None"

Install the approved ``utui`` source checkout or wheel.  Until a separate PyPI
publication decision is made, do not assume that ``pip install utui`` refers
to this project:

.. code-block:: console

   python -m pip install .

Verify the new identity and the absence of the old one:

.. code-block:: console

   python -c "import importlib.metadata as m, importlib.util as u, utui; assert m.version('utui'); assert u.find_spec('thebitlab_tui') is None"

The commands are the same in PowerShell, ``cmd.exe``, and POSIX shells once the
intended environment's ``python`` executable is active.

Editable development installs
-----------------------------

An editable install records the source directory, so uninstall it before
moving or deleting an old checkout:

.. code-block:: console

   python -m pip uninstall thebitlab-tui
   python -c "import importlib.util as u; assert u.find_spec('thebitlab_tui') is None"
   python -m pip install -e ".[test,docs]"
   python -c "import importlib.metadata as m, importlib.util as u, utui; assert m.version('utui'); assert u.find_spec('thebitlab_tui') is None"

Application code must replace every old import with ``import utui`` or
``from utui import ...``.  Public symbol names and supported signatures are
otherwise unchanged from 0.3.0.

Rollback boundary
-----------------

Before consumer adoption or publication of version 0.4.0, maintainers can
revert the code migration with a normal commit.  Do not create a new GitHub
repository under the old name: doing so would break GitHub's repository
redirect.  After consumer adoption, restoring the old import silently is not
a supported rollback.

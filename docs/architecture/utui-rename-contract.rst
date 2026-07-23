``utui`` rename contract
========================

Status and scope
----------------

This document is the normative design gate for issue `#52
<https://github.com/TheBitPoets/thebitlab-tui/issues/52>`_ under rename parent `#51
<https://github.com/TheBitPoets/thebitlab-tui/issues/51>`_ and integration parent `#25
<https://github.com/TheBitPoets/thebitlab-tui/issues/25>`_.  It approves names, compatibility,
sequencing, rollback, and evidence before the repository or installed package is changed.

This design-only slice does not rename the repository, source directory, distribution, import
package, repository skill, remotes, releases, tags, or consumer code.  Those mutations require
separate child issues and focused pull requests after this contract is approved.

Binding names
-------------

.. list-table:: Project identity after the migration
   :header-rows: 1
   :widths: 24 32 44

   * - Contract
     - Current identity
     - Required identity
   * - GitHub repository
     - ``TheBitPoets/thebitlab-tui``
     - ``TheBitPoets/utui``
   * - Python distribution
     - ``thebitlab-tui``
     - ``utui``
   * - Installed import package
     - ``thebitlab_tui``
     - ``utui``
   * - Source directory
     - ``src/thebitlab_tui``
     - ``src/utui``
   * - Repository review skill
     - ``thebitlab-tui-pr-review``
     - ``utui-pr-review``

The new project spelling is always ``utui``.  It is lowercase in distribution metadata, Python
imports, repository paths, commands, documentation prose, and skill identifiers.  No second
display name or acronym expansion is introduced by this migration.

Compatibility decision
----------------------

The migration is an intentional hard pre-v1 rename.  After implementation, ``import utui`` is the
only supported import path.  The installed distribution does not include a ``thebitlab_tui``
module, compatibility package, alias, deprecation shim, namespace bridge, or second distribution.

This is preferable before consumer integration because a bridge would:

* keep the discarded identity in the runtime and public support contract;
* require duplicate module and packaging tests;
* make later removal a second breaking migration; and
* allow the student consumer to adopt an import path that is already obsolete.

The breaking surface is limited to project identity.  The implementation must capture the current
``thebitlab_tui.__all__`` tuple before moving files and prove that ``tuple(utui.__all__)`` is
identical.  The versioned baseline must also record every export's kind, ``__qualname__``, normalized
module suffix, and ``inspect.signature`` result where supported.  After the move, module identity
may change only by replacing the ``thebitlab_tui`` prefix with ``utui``; names, qualified names, and
signatures remain otherwise exact.  Existing behavior tests continue to protect returns and
exceptions.

Public symbol names, signatures, returns, exceptions, rendering, clipping, ellipsis, ASCII
fallback, ANSI geometry, ``no-color`` output, layout allocation, key normalization, timeout
semantics, and terminal restoration remain unchanged.

Version ``0.3.0`` remains the development metadata baseline during intermediate rename work.
Version ``0.4.0`` is assigned, tagged, and published only by the existing Phase 4 closeout.  The
rename must be recorded as a breaking pre-v1 change in the Unreleased changelog, migration guide,
and eventual release notes.

PyPI publication and name reservation remain a separate explicit decision.  Availability observed
during design does not reserve the name and is not evidence that a package has been published.

Existing environment migration
------------------------------

Python package managers treat ``thebitlab-tui`` and ``utui`` as different distributions.
Installing ``utui`` does not uninstall the old distribution and can leave both import packages on
``sys.path``.  The supported upgrade procedure must therefore:

1. stop processes that import the library;
2. run ``python -m pip uninstall thebitlab-tui`` in the target environment;
3. verify that the old distribution and import package are absent;
4. install the approved ``utui`` source or distribution; and
5. verify the ``utui`` distribution metadata, ``import utui``, and absence of
   ``thebitlab_tui``.

The migration guide must provide those explicit commands for virtual environments and editable
development installs.  It must not describe ``pip install utui`` alone as an upgrade.

Automated upgrade evidence starts in an isolated environment with the old ``0.3.0`` distribution
installed, performs the documented uninstall/install sequence, and then proves:

* ``importlib.metadata`` finds ``utui`` and no ``thebitlab-tui`` distribution;
* ``import utui`` succeeds; and
* ``importlib.util.find_spec("thebitlab_tui")`` returns ``None``.

Maintained references and immutable history
-------------------------------------------

The maintained current tree must use the new identity in code, package metadata, tests, examples,
Sphinx configuration and API pages, README, architecture, guides, images, roadmap, operating
rules, AGENTS guidance, issue templates, repository skill, and repository URLs.

Old identifiers are permitted only where omitting them would make migration or provenance
ambiguous:

* this contract;
* the dedicated rename migration guide;
* the Unreleased changelog entry; and
* the legacy-identifier audit test, preferably with search terms assembled from fragments.

The implementation audit owns an explicit repository-relative allowlist for those files.  It must
reject legacy identifiers in every other tracked text file and reject ``src/thebitlab_tui`` as a
path.  Generated documentation and image titles must use ``utui``.

Immutable Git history, existing ``v0.2.0`` and ``v0.3.0`` tags and GitHub Releases, and historical
issue, pull-request, review, and comment bodies are not rewritten.  Maintained documents may
retain links to historical issues and pull requests, but their repository component must be
updated to ``TheBitPoets/utui`` after the GitHub rename.

GitHub repository contract
--------------------------

Immediately before the repository rename, the maintainer must verify:

* administrator permission;
* availability of ``TheBitPoets/utui``;
* the complete list of open pull requests and active automation;
* whether a GitHub Pages project site exists; and
* whether another workflow consumes this repository as a GitHub Action.

GitHub's `repository rename documentation
<https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository>`_
describes redirects for normal web, issue, pull-request, clone, fetch, and push traffic after a
repository rename.  Redirects are a migration aid, not the maintained configuration.  Every active
clone and worktree must update its shared ``origin`` URL to
``https://github.com/TheBitPoets/utui.git`` and verify fetch and push targets.

The old repository name must never be reused.  Creating another
``TheBitPoets/thebitlab-tui`` repository would invalidate GitHub's redirect.  GitHub Pages project
URLs and calls to a repository-hosted GitHub Action are not covered by the normal redirect
promise; if either is discovered, the rename pauses until a dedicated migration is approved.

Implementation sequence
-----------------------

The required order is:

1. Merge this design record and its roadmap/test guard without changing project identity.
2. Create implementation children under #51 for one atomic current-tree identity migration, the
   GitHub repository/remote operation, and clean-install/cross-platform evidence.  Package moves,
   imports, metadata, tests, docs, governance, skill, URLs, assets, migration guidance, and the
   identifier audit belong to the same current-tree child and pull request.
3. Capture the existing public manifest and build a legacy-identifier allowlist test before moving
   the package.
4. Prepare and review one atomic current-tree migration that moves ``src/thebitlab_tui`` to
   ``src/utui`` and synchronizes imports, packaging, tests, examples, Sphinx, governance, skill,
   maintained URLs, images, changelog, and migration guidance.
5. Immediately before merging that migration, recheck administrator permission and target-name
   availability.
6. Rename the GitHub repository, update the shared ``origin`` remote, verify the old redirect, and
   confirm that the already-reviewed migration pull request remains open, mergeable, and attached
   to its successful checks under ``TheBitPoets/utui``.
7. Merge the approved atomic current-tree migration against the renamed repository.  If it is not
   safely mergeable after the repository operation, stop without forcing it; repair the pull
   request or rename the same repository back under the rollback rules.
8. Run clean source and built-distribution installation checks, the old-install upgrade procedure,
   and Python 3.11--3.13 Windows and Linux CI under the new repository and import identity.
9. Update #51 and #25 evidence, then resume consumer integration using only ``utui``.

The current-tree rename is intentionally atomic.  Splitting package moves, imports, Sphinx API
targets, examples, or tests across separately mergeable commits would leave ``master`` in a state
that cannot be installed or verified.  Focused preparatory tests may land first, but the identity
switch itself crosses the repository in one reviewed pull request.

Rollback boundary
-----------------

Before ``v0.4.0`` is published or consumer integration starts, the code migration can be reverted
with a normal focused commit.  If the GitHub rename itself must be reversed, the maintainer may
rename the same repository back only after confirming the old name remains available; no new
repository may be created at the old location.

Rollback never rewrites commits, tags, releases, issues, or reviews.  After ``v0.4.0`` publication
or consumer adoption, restoring the old import silently is forbidden.  Any corrective change then
requires a new documented release decision.

Required evidence
-----------------

Implementation is not complete until all of the following pass:

* exact equality between the captured old public manifest and ``utui.__all__``;
* equality of export kind, qualified name, normalized module suffix, and supported signatures
  against the versioned pre-move public manifest;
* absence of ``src/thebitlab_tui`` and successful ``import utui`` from a clean environment;
* absence of an installed ``thebitlab_tui`` module;
* source and built-distribution installation tests with no runtime dependencies;
* an isolated old-``0.3.0`` install, documented uninstall, new install, and distribution/import
  absence checks;
* the complete pytest suite and deterministic ASCII/ANSI snapshots;
* ``compileall`` for source, tests, examples, tools, and Sphinx configuration;
* strict warning-as-error Sphinx with the new API module paths;
* fixed-size ``--no-color`` examples and terminal-input smoke tests;
* the tracked-text legacy-identifier audit with its explicit allowlist;
* Git remote, old-URL redirect, issues, pull requests, tags, releases, and CI verification after
  the repository rename; and
* Python 3.11--3.13 CI on Windows and Linux with two consecutive clean review rounds per child PR.

Consumer boundary
-----------------

Nothing in this migration reads or modifies ``E:\dev\2cornot2c``.  The later consumer-owned
adapter continues to own dictionaries, ``.student-lab-layout.json``, commands, event dispatch,
screen output, redraw timing, and the legacy ASCII fallback.  Its first integration branch must
depend on the verified ``utui`` baseline and must never introduce ``thebitlab_tui`` imports.

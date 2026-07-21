# Changelog

## Unreleased

- Add the approved public `KeyReader` facade with deterministic lifecycle, total monotonic
  deadlines, private backend seams, and no terminal side effects during construction.
- Add the dependency-free Linux POSIX input backend with conservative cbreak mode, exact terminal
  restoration, deterministic Escape/Alt/CSI/SS3 decoding, injected tests, and Linux PTY evidence.
- Keep the Windows console input backend as a separate Phase 3 delivery slice.

## 0.2.0 - 2026-07-21

- Add public style-preserving `Canvas.blit` composition with deterministic overlapping self-copy.
- Add public `ScrollView` with caller-owned content height and vertical viewport state.
- Add public `Modal` with caller-owned visibility, centered ASCII composition, and stable `[x]`
  title priority.
- Preserve the application underlay outside the modal inner frame and document flexible
  Row/Column allocation without callbacks or overlay ownership.
- Add clipping, isolation, ANSI, self-blit, layout, validation, guide, example, and SVG coverage.
- Add the public `ListView` widget with caller-owned focus, selection, and vertical scrolling.
- Add empty, narrow, clipped, ANSI, layout, validation, and scrolling snapshots for `ListView`.
- Add `ListView` user/developer guidance, integration notes, an executable example, and an SVG.
- Add public ASCII `Divider` and semantic `StatusBadge` widgets with optional ANSI styles.
- Add narrow, clipping, layout, validation, and color snapshots for the Phase 2 primitives.
- Add user/developer guidance and an executable divider/status example.
- Add repository operating rules, issue/PR templates, and a PR review skill.
- Add Sphinx API, user, developer, architecture, and example documentation.
- Require docstrings for the public API and validate them in the test suite.
- Add Windows/Linux CI for Python 3.11 through 3.13 and a warning-as-error docs build.

## 0.1.0 - 2026-07-20

- Add the dependency-free project scaffold.
- Add geometry, canvas, ANSI styles, labels, panels, responsive rows and columns.
- Add pure fixed-size and terminal-sized render entry points.
- Add resize polling, abstract key events, examples, documentation, and unit snapshots.

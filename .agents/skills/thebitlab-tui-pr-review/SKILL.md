---
name: thebitlab-tui-pr-review
description: Review pull requests for thebitlab-tui. Use for PR reviews, review rounds, finding triage, API compatibility checks, ASCII/ANSI rendering changes, Windows/Linux portability, snapshot coverage, docstrings, or Sphinx documentation validation.
---

# Review thebitlab-tui pull requests

Perform a read-only review unless the user explicitly asks to fix findings.

## Establish context

1. Read `AGENTS.md` and `docs/it/00-regole-operative.md`.
2. Read the child issue, parent issue, milestone, primary roadmap, and relevant architecture/API
   pages. Do not load unrelated documentation.
3. Inspect PR metadata, full diff, CI checks, previous review rounds, and unresolved threads.
4. Identify public API changes by comparing `thebitlab_tui.__all__`, signatures, return values,
   exceptions, and documented behavior.

## Review the change

Check only risks supported by the diff or repository contract:

- rendering correctness, clipping, ellipsis, stable widths, and deterministic output;
- ASCII fallback, ANSI geometry, and `no-color` output;
- narrow dimensions, min/max/flex allocation, responsive stacking, and resize behavior;
- Windows/Linux behavior and standard-library-only runtime;
- pure rendering and separation among widgets, layout, renderer, terminal adapter, and app data;
- compatibility with the future external adapter for `student_lab_layout.py` without importing or
  modifying `2cornot2c`;
- public API compatibility and absence of speculative abstractions;
- unit, regression, and snapshot coverage;
- docstrings for public modules, classes, functions, methods, and properties;
- synchronized Sphinx API, architecture, user/developer guides, examples, and images.

Run the relevant local suite, syntax check, formatting check, Sphinx warning-as-error build, and
manual example when the environment permits. Inspect GitHub Actions logs through `gh` when a check
fails; do not infer a CI cause from status alone.

## Report findings

Report only actionable findings, ordered by severity:

- `P0`: security, data loss, or total breakage;
- `P1`: functional bug, frame overflow, incompatible API, or cross-platform regression;
- `P2`: concrete edge case, material missing test, or inconsistent contract;
- `P3`: non-blocking but concrete in-scope improvement.

For each finding provide file and line, evidence or reproduction, impact, expected behavior,
recommended fix, and required regression test. Put it inline when a precise diff line exists.
Avoid style-only, speculative, duplicate, and out-of-scope findings.

If no actionable finding exists, say so and list residual validation gaps. Do not invent a
finding to make the review look substantial.

## Track review rounds and fixes

Update the PR body with `Review round N`, new-finding status, consecutive clean count, findings,
fix commit links, and validation. Keep the PR draft until two consecutive reviews find no new
issues. Stop before ready/merge and ask the maintainer.

When fixes are requested:

1. use a focused commit where practical;
2. add a regression test or document why none applies;
3. reply inline with a clickable commit link;
4. explain the original risk, the fix, and the protecting test or contract;
5. resolve the thread only after verification;
6. run another complete review round, not only a re-check of edited lines.

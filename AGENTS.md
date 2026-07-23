# Contributor and agent guidance

Read [the operating rules](docs/it/00-regole-operative.md) before non-trivial work.

## Stable project contracts

- Keep the runtime dependency-free and compatible with Python 3.11+ on Windows and Linux.
- Preserve pure rendering: widgets draw to a canvas and never print or contain application logic.
- Preserve ASCII fallback, optional ANSI color, clipping, ellipsis, and stable visible widths.
- Keep widget, layout, renderer, terminal adapter, and application data responsibilities separate.
- Do not copy or modify application code from `E:\dev\2cornot2c`.
- Integrate the student TUI only through a future adapter compatible with
  `scripts/student_lab_layout.py` and its persisted `.student-lab-layout.json` state.
- Treat the public names in `utui.__all__` as stable. Discuss and document compatibility
  before changing signatures, behavior, imports, or return types.

## Changes and verification

- Work in small, single-purpose steps. Avoid speculative abstractions and unrelated cleanup.
- Add deterministic tests and readable ASCII snapshots before changing rendering or layout.
- Test ANSI and `no-color`, narrow terminals, clipping, and Windows/Linux differences when relevant.
- Give every public module, class, function, method, and property a useful docstring.
- Update Sphinx API reference, architecture, user/developer guides, examples, and images when the
  public contract or observable behavior changes.
- Keep Sphinx and test tools optional development dependencies; never turn them into runtime
  dependencies.

## GitHub workflow

- Use a milestone for a measurable release objective and an issue madre for its implementation
  plan. Split non-trivial work into linked issue figlie and focused pull requests.
- Keep the issue madre checklist and `Implementation traceability` table synchronized.
- Link a PR to its issue figlia with `Closes #...`; do not close the issue madre prematurely.
- Keep a PR draft until it has two consecutive review rounds without new findings.
- Put actionable findings inline. A fix must link the finding, its focused commit, and a regression
  test or a documented reason why a test is not applicable.
- Use the repository skill
  [utui-pr-review](.agents/skills/utui-pr-review/SKILL.md) for PR reviews.


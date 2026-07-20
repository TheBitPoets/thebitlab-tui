# Roadmap

## Phase 1

- panels;
- rows;
- columns;
- titles;
- truncation;
- optional colors.

## Phase 2

- focus;
- selection;
- scrolling;
- modal.

## Phase 3

- Windows/Linux input adapters;
- student TUI integration;
- manual tests.

## Phase 4

- possible mouse support;
- possible drag and drop;
- possible tmux support;
- only if demonstrably necessary.

## Milestone register

Create a GitHub milestone and parent issue before starting a non-trivial phase. Keep this table in
sync with the parent issue's checklist and implementation traceability.

| Milestone | Status | Target | Dependencies | Parent issue | Outcome / deferred work |
| --- | --- | --- | --- | --- | --- |
| Project foundations v0.1 | In progress | 2026-07-27 | Core scaffold | [#2](https://github.com/TheBitPoets/thebitlab-tui/issues/2) | Governance, docstrings, Sphinx, CI |
| Phase 1 - Core rendering | Complete | 2026-07-20 | None | Pre-tracking | Initial ASCII rendering scaffold |
| Phase 2 - Interactive widgets | Planned | To schedule | Stable core API | To create | Selection, scrolling, modal |
| Phase 3 - Terminal adapters | Planned | To schedule | Phase 2 | To create | Windows/Linux input and student adapter |
| Phase 4 - Optional interaction | Deferred | None | Demonstrated need | None | Mouse, drag/drop, tmux only if required |


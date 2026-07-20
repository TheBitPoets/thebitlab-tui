# Roadmap

## Phase 1

- panels;
- rows;
- columns;
- titles;
- truncation;
- optional colors.

## Phase 2

- divider and semantic status badges;
- focus;
- selection;
- scrolling;
- modal.

Phase 2 keeps focus, selection, and viewport state owned by the calling application. Before any
new public signature is implemented, the first implementation issue must record the chosen state,
sizing, clipping, and narrow-terminal contracts. Input decoding and event dispatch remain Phase 3
work.

### Phase 2 delivery sequence

1. Approve the public contracts and compatibility decisions.
2. Add `Divider` and `StatusBadge` with ASCII and `no-color` snapshots.
3. Add focus presentation and `ListView` with caller-owned selection and viewport state.
4. Add `ScrollView` with deterministic clipping and no horizontal overflow.
5. Add `Modal` with centered composition and predictable narrow-terminal fallback.
6. Consolidate Sphinx documentation, examples, images, and cross-platform verification.

The design gate in step 1 is intentionally reversible: implementation issues and exact signatures
are created only after the contracts have been reviewed. Phase 2 does not add an event loop,
terminal input adapter, application persistence, or direct student TUI integration.

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
| Project foundations v0.1 | Complete | 2026-07-20 | Core scaffold | [#2](https://github.com/TheBitPoets/thebitlab-tui/issues/2) | Governance, docstrings, Sphinx, CI; merged in PRs #5 and #6 |
| Phase 1 - Core rendering | Complete | 2026-07-20 | None | Pre-tracking | Initial ASCII rendering scaffold |
| Interactive widgets v0.2 | In progress | 2026-08-17 | Stable core API | [#7](https://github.com/TheBitPoets/thebitlab-tui/issues/7) | Divider, status badges, selection, scrolling, modal; input adapters deferred |
| Phase 3 - Terminal adapters | Planned | To schedule | Phase 2 | To create | Windows/Linux input and student adapter |
| Phase 4 - Optional interaction | Deferred | None | Demonstrated need | None | Mouse, drag/drop, tmux only if required |


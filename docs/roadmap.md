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
new public signature is implemented, a dedicated design issue must record and approve the chosen
state, sizing, clipping, and narrow-terminal contracts. Input decoding and event dispatch remain
Phase 3 work.

### Phase 2 delivery sequence

1. Done in #10 / PR #11: approve the public contracts and compatibility decisions.
2. Done in #12 / PR #13: add `Divider` and `StatusBadge` with ASCII and `no-color` snapshots.
3. Done in #14 / PR #15: add focus presentation and `ListView` with caller-owned state.
4. Done in #16 / PR #17: add `ScrollView` with deterministic clipping and no overflow.
5. Done in #18 / PR #19: add `Modal` with centered composition and narrow fallback.
6. Done in #20 / PR #21: consolidate documentation, examples, images, and verification.

The design gate in step 1 is intentionally reversible: implementation issues and exact signatures
are created only after the contracts have been reviewed. Phase 2 does not add an event loop,
terminal input adapter, application persistence, or direct student TUI integration.

The approved contract is versioned in
[`docs/architecture/phase-2-contracts.rst`](architecture/phase-2-contracts.rst) and tracked by
[issue #10](https://github.com/TheBitPoets/thebitlab-tui/issues/10); it was approved in
[PR #11](https://github.com/TheBitPoets/thebitlab-tui/pull/11). Divider and status-badge
implementation is tracked by [issue #12](https://github.com/TheBitPoets/thebitlab-tui/issues/12).
Caller-owned focus and `ListView` implementation is tracked by
[issue #14](https://github.com/TheBitPoets/thebitlab-tui/issues/14).
Style-preserving canvas composition and `ScrollView` implementation are tracked by
[issue #16](https://github.com/TheBitPoets/thebitlab-tui/issues/16).
Centered modal composition and narrow-terminal fallback are tracked by
[issue #18](https://github.com/TheBitPoets/thebitlab-tui/issues/18).
Release documentation and cross-platform verification are tracked by
[issue #20](https://github.com/TheBitPoets/thebitlab-tui/issues/20).
Formal milestone closeout and `v0.2.0` publication are tracked by
[issue #22](https://github.com/TheBitPoets/thebitlab-tui/issues/22).

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
| Project foundations v0.1 | Complete | 2026-07-27 | Core scaffold | [#2](https://github.com/TheBitPoets/thebitlab-tui/issues/2) | Completed 2026-07-20; governance, docstrings, Sphinx, CI; merged in PRs #5 and #6 |
| Phase 1 - Core rendering | Complete | 2026-07-20 | None | Pre-tracking | Initial ASCII rendering scaffold |
| Interactive widgets v0.2 | Complete | 2026-07-21 | Stable core API | [#7](https://github.com/TheBitPoets/thebitlab-tui/issues/7) | Completed 2026-07-21; versioned as `0.2.0`; tag and GitHub release follow the closeout merge; terminal input and student adapter deferred |
| Phase 3 - Terminal adapters | Planned | To schedule | Phase 2 | To create | Windows/Linux input and student adapter |
| Phase 4 - Optional interaction | Deferred | None | Demonstrated need | None | Mouse, drag/drop, tmux only if required |


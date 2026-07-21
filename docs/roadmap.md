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

## Product path to v1.0

Version `1.0` is the stable form of the deliberately small library, not a full-screen framework.
It includes pure responsive rendering, caller-owned interactive state, optional dependency-free
terminal input adapters, and verified integration boundaries. It still does not own an event
loop, application commands, persistence, printing, screen clearing, or redraw timing.

Each active milestone has an internal delivery target and a GitHub due date seven days later. The
gap is review and release margin, not implementation scope. If evidence moves a date, update both
the live milestone and this document with the reason. Only the next milestone is decomposed into
detailed implementation issues; later parent issues retain outcome-level plans until their
dependencies are complete.

### Phase 3 - Terminal adapters v0.3

**Internal target:** 2026-08-14. **GitHub due date:** 2026-08-21.

Deliver separate standard-library Windows and POSIX input adapters that normalize supported keys
to `KeyEvent`. Approve blocking, partial-input, EOF/error, modifier, and terminal-restoration
contracts before choosing public signatures. Tests use injected I/O; manual checks cover supported
Windows and Linux terminals. The application continues to own commands, state, event dispatch,
screen output, and redraws.

Exit gates:

- arrows, Enter, Escape, Tab, and printable characters have deterministic normalized behavior;
- modifiers are best-effort and every workflow has alternatives without modifiers;
- terminal state restoration is covered for normal exit and documented error paths;
- Python 3.11-3.13 CI, manual Windows/Linux checks, Sphinx, examples, and two clean review rounds
  pass;
- version `0.3.0`, tag, and release are published after the verified closeout merge.

#### Phase 3 delivery sequence

1. Completed in [#30](https://github.com/TheBitPoets/thebitlab-tui/issues/30) and PR #31: approve
   the public facade, timeout, decoding, failure, and restoration contracts without implementation.
2. In progress in [#33](https://github.com/TheBitPoets/thebitlab-tui/issues/33): add the shared
   facade, timeout policy, pure backend seams, and public docs.
3. Add the POSIX backend with PTY integration and exact-restoration tests.
4. Add the Windows console-record backend with injected virtual-key, modifier, repeat, and Unicode
   tests.
5. Consolidate the cross-platform example, manual protocol, guides, images, and release evidence.

The design gate in step 1 preserved reversibility until approval. Later platform child issues and
exact internal file placement are created only when their slices begin. The approved contract is versioned in
[`docs/architecture/phase-3-input-contracts.rst`](architecture/phase-3-input-contracts.rst) and
tracked by [issue #30](https://github.com/TheBitPoets/thebitlab-tui/issues/30). The parent plan is
[issue #24](https://github.com/TheBitPoets/thebitlab-tui/issues/24); product-roadmap alignment was
completed in [issue #28](https://github.com/TheBitPoets/thebitlab-tui/issues/28) and PR #29.

### Phase 4 - Integration-ready v0.4

**Internal target:** 2026-09-18. **GitHub due date:** 2026-09-25.

Publish an application-neutral adapter contract, fixture dictionaries, expected frames, and
guidance compatible with `scripts/student_lab_layout.py` and `.student-lab-layout.json`.
Coverage includes assignment detail, workspace, activity, allowed help, help requests, report,
tests, grading, runner, and quick guide across wide/narrow, ANSI/`no-color`, resize, focus,
scrolling, and modal states.

The real adapter and application persistence remain in `2cornot2c` and require their own
repository plan. This repository never imports or copies its domain logic. Exit requires linked
consumer evidence, legacy ASCII fallback preservation, complete documentation, cross-platform
verification, two clean review rounds, and the `v0.4.0` release.

Tracked by [parent issue #25](https://github.com/TheBitPoets/thebitlab-tui/issues/25).

### Phase 5 - Release candidate v0.9

**Internal target:** 2026-10-16. **GitHub due date:** 2026-10-23.

Freeze the candidate public API, audit compatibility, harden behavior discovered through real
integration, validate clean source and wheel installations, and complete API, architecture,
user/developer, troubleshooting, example, image, support, versioning, and release-runbook
documentation. No speculative feature work enters this milestone.

Exit requires no known P0/P1 finding, an explicit waiver for any deferred P2, zero runtime
dependencies, complete automated/manual platform evidence, two clean review rounds, and a
published `v0.9.0` release that starts the bounded feedback window.

Tracked by [parent issue #26](https://github.com/TheBitPoets/thebitlab-tui/issues/26).

### Phase 6 - Stable product v1.0

**Internal target:** 2026-11-06. **GitHub due date:** 2026-11-13.

Resolve release-candidate findings without expanding scope, freeze the v1 compatibility contract,
complete end-to-end Windows/Linux acceptance with consumer evidence, and publish migration,
support, changelog, tag, and GitHub release artifacts. PyPI publication is an explicit maintainer
decision gate and is not implied by this schedule.

Exit requires all supported Python/platform gates, ASCII/ANSI, narrow-terminal, resize, input,
focus, scrolling, modal, documentation, and release checks to pass. The parent issue and milestone
close only after the verified `v1.0.0` release.

Tracked by [parent issue #27](https://github.com/TheBitPoets/thebitlab-tui/issues/27).

## Optional work after v1.0

- mouse support;
- drag and drop;
- tmux-specific behavior;
- animation scheduling or timing.

These items have no date and do not block v1.0. They require a demonstrated consumer need and a
new design gate. Applications can already render successive caller-provided ASCII frames; timing,
scheduling, and cancellation remain application-owned.

## Milestone register

Create a GitHub milestone and parent issue before starting a non-trivial phase. Keep this table in
sync with the parent issue's checklist and implementation traceability.

| Milestone | Status | Internal target | GitHub due | Dependencies | Parent issue | Outcome / deferred work |
| --- | --- | --- | --- | --- | --- | --- |
| Project foundations v0.1 | Complete | 2026-07-20 | 2026-07-27 | Core scaffold | [#2](https://github.com/TheBitPoets/thebitlab-tui/issues/2) | Governance, docstrings, Sphinx, CI; merged in PRs #5 and #6 |
| Phase 1 - Core rendering | Complete | 2026-07-20 | Pre-tracking | None | Pre-tracking | Initial ASCII rendering scaffold |
| Interactive widgets v0.2 | Complete | 2026-07-21 | 2026-08-17 | Stable core API | [#7](https://github.com/TheBitPoets/thebitlab-tui/issues/7) | Released as [`v0.2.0`](https://github.com/TheBitPoets/thebitlab-tui/releases/tag/v0.2.0); terminal input and integration work deferred |
| Terminal adapters v0.3 | Planned | 2026-08-14 | 2026-08-21 | v0.2 | [#24](https://github.com/TheBitPoets/thebitlab-tui/issues/24) | Dependency-free Windows/POSIX input; no event loop |
| Integration-ready v0.4 | Planned | 2026-09-18 | 2026-09-25 | v0.3 and consumer availability | [#25](https://github.com/TheBitPoets/thebitlab-tui/issues/25) | Neutral adapter contract and evidence; implementation stays in `2cornot2c` |
| Release candidate v0.9 | Planned | 2026-10-16 | 2026-10-23 | v0.4 and integration evidence | [#26](https://github.com/TheBitPoets/thebitlab-tui/issues/26) | Candidate API freeze, packaging, hardening, complete docs |
| Stable product v1.0 | Planned | 2026-11-06 | 2026-11-13 | v0.9 feedback window | [#27](https://github.com/TheBitPoets/thebitlab-tui/issues/27) | Stable API and verified `v1.0.0` release; PyPI is a separate decision gate |
| Optional interaction | Deferred | None | None | Demonstrated need after v1.0 | To create only if approved | Mouse, drag/drop, tmux, and animation timing do not block v1.0 |


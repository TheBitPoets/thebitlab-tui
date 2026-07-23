"""Executable contract checks for the non-public Phase 4 reference adapter."""

from __future__ import annotations

from copy import deepcopy

import pytest

import thebitlab_tui
from examples.student_dashboard_adapter import (
    BREAKPOINT,
    MISSING_ROW,
    _wide_widths,
    render_reference_frame,
)
from examples.student_dashboard_fixtures import (
    FIXTURE_REVISION,
    PRESENTATION,
    SECTIONS,
    SECTION_IDS,
)
from thebitlab_tui import strip_ansi, visible_width


PUBLIC_API = (
    "Canvas",
    "Column",
    "Divider",
    "Key",
    "KeyEvent",
    "KeyReader",
    "Label",
    "ListView",
    "Modal",
    "Panel",
    "Rect",
    "ResizeWatcher",
    "Row",
    "ScrollView",
    "Size",
    "Style",
    "StatusBadge",
    "TerminalSize",
    "Widget",
    "get_terminal_size",
    "render",
    "render_lines",
    "render_terminal",
    "strip_ansi",
    "supports_color",
    "truncate",
    "visible_width",
)

WIDE_SNAPSHOT = """\
+ > Dettaglio consegna -------------------------------------+ | + Report --------------------------+
|Exercise: parse a tiny text format                         | | |Summary: implementation started   |
|Status: ready                                              | | |Notes: add boundary cases         |
+-----------------------------------------------------------+ | +----------------------------------+
+ Workspace ------------------------------------------------+ | + Ultimo dettaglio test -----------+
|Path: C:/training/sample-lab                               | | |Passed: 6                         |
|Files: 4                                                   | | |Failed: 1                         |
+-----------------------------------------------------------+ | +----------------------------------+
+ Activity -------------------------------------------------+ | + Grading -------------------------+
|Last action: opened instructions                           | | |State: not submitted              |
+-----------------------------------------------------------+ | +----------------------------------+
+ Aiuto consentito -----------------------------------------+ | + Runner --------------------------+
|Allowed: standard library docs                             | | |Command: python -m pytest         |
|Not allowed: completed solution                            | | |State: idle                       |
+-----------------------------------------------------------+ | +----------------------------------+
+ [+] Richieste aiuto --------------------------------------+ | + Guida rapida --------------------+
|                                                           | | |Arrows: move                      |
+-----------------------------------------------------------+ | |Enter: open                       |
                                                              | |q: close                          |
                                                              | +----------------------------------+"""

NARROW_SNAPSHOT = """\
+ > Dettaglio consegna -----------------------------------------------------------------+
|Exercise: parse a tiny text format                                                     |
|Status: ready                                                                          |
+---------------------------------------------------------------------------------------+
+ Workspace ----------------------------------------------------------------------------+
|Path: C:/training/sample-lab                                                           |
|Files: 4                                                                               |
+---------------------------------------------------------------------------------------+
+ Activity -----------------------------------------------------------------------------+
|Last action: opened instructions                                                       |
+---------------------------------------------------------------------------------------+
+ Aiuto consentito ---------------------------------------------------------------------+
|Allowed: standard library docs                                                         |
|Not allowed: completed solution                                                        |
+---------------------------------------------------------------------------------------+
+ [+] Richieste aiuto ------------------------------------------------------------------+
|                                                                                       |
+---------------------------------------------------------------------------------------+
+ Report -------------------------------------------------------------------------------+
|Summary: implementation started                                                        |
|Notes: add boundary cases                                                              |
+---------------------------------------------------------------------------------------+
+ Ultimo dettaglio test ----------------------------------------------------------------+
|Passed: 6                                                                              |
|Failed: 1                                                                              |
+---------------------------------------------------------------------------------------+
+ Grading ------------------------------------------------------------------------------+
|State: not submitted                                                                   |
+---------------------------------------------------------------------------------------+
+ Runner -------------------------------------------------------------------------------+
|Command: python -m pytest                                                              |
|State: idle                                                                            |
+---------------------------------------------------------------------------------------+
+ Guida rapida -------------------------------------------------------------------------+
|Arrows: move                                                                           |
|Enter: open                                                                            |
|q: close                                                                               |
+---------------------------------------------------------------------------------------+"""


def test_fixture_revision_and_identifiers_are_explicit() -> None:
    """Keep synthetic fixture drift visible without creating public API."""

    assert FIXTURE_REVISION == "phase4-v1"
    assert tuple(section["id"] for section in SECTIONS) == SECTION_IDS
    assert len(set(SECTION_IDS)) == 10
    assert PRESENTATION["order"] == SECTION_IDS


@pytest.mark.parametrize(
    ("width", "left_width", "expected"),
    [
        (90, 36, (36, 51)),
        (90, 62, (51, 36)),
        (100, 36, (36, 61)),
        (100, 62, (61, 36)),
        (100, 120, (61, 36)),
    ],
)
def test_approved_wide_allocation(
    width: int, left_width: int, expected: tuple[int, int]
) -> None:
    """Protect the legacy allocation and three-cell separator budget."""

    allocated = _wide_widths(width, left_width)

    assert allocated == expected
    assert sum(allocated) + 3 == width


def test_wide_narrow_and_vertical_frames_preserve_geometry() -> None:
    """Exercise both explicit responsive trees around the approved breakpoint."""

    wide = render_reference_frame(width=100, height=24)
    narrow = render_reference_frame(width=BREAKPOINT - 1, height=40)
    vertical_state = {**PRESENTATION, "orientation": "vertical"}
    vertical = render_reference_frame(SECTIONS, vertical_state, width=100, height=40)

    assert all(visible_width(row) == 100 for row in wide)
    assert all(visible_width(row) == 89 for row in narrow)
    assert all(visible_width(row) == 100 for row in vertical)
    assert any(" | " in row for row in wide)
    assert not any(" | " in row for row in narrow)
    assert not any(" | " in row for row in vertical)


def test_core_wide_and_narrow_ascii_snapshots() -> None:
    """Freeze the first executable adapter frames at both sides of the breakpoint."""

    wide = render_reference_frame(width=100, height=20)
    narrow = render_reference_frame(width=89, height=38)

    assert wide == [line.ljust(100) for line in WIDE_SNAPSHOT.splitlines()]
    assert narrow == [line.ljust(89) for line in NARROW_SNAPSHOT.splitlines()]


def test_missing_section_remains_visible() -> None:
    """Render an unavailable placeholder instead of dropping a persisted section."""

    without_tests = tuple(section for section in SECTIONS if section["id"] != "tests")
    frame = render_reference_frame(without_tests, PRESENTATION, width=100, height=24)

    assert any(MISSING_ROW in row for row in frame)
    assert any("Ultimo dettaglio test" in row for row in frame)


def test_rendering_does_not_mutate_fixture_or_presentation_state() -> None:
    """Keep all normalized data and state caller-owned."""

    sections_before = deepcopy(SECTIONS)
    presentation_before = deepcopy(PRESENTATION)

    render_reference_frame(width=100, height=24)
    render_reference_frame(width=89, height=40)

    assert SECTIONS == sections_before
    assert PRESENTATION == presentation_before


def test_no_color_and_color_have_identical_visible_geometry() -> None:
    """Keep ANSI styling independent from every frame boundary."""

    plain = render_reference_frame(width=100, height=24, color=False)
    colored = render_reference_frame(width=100, height=24, color=True)

    assert "\x1b[" not in "\n".join(plain)
    assert [strip_ansi(row) for row in colored] == plain
    assert [visible_width(row) for row in colored] == [100] * len(colored)


def test_reference_slice_does_not_change_public_exports() -> None:
    """Prevent an example-only adapter from becoming stable library API."""

    assert tuple(thebitlab_tui.__all__) == PUBLIC_API


@pytest.mark.parametrize(
    "presentation",
    [
        {**PRESENTATION, "orientation": "diagonal"},
        {**PRESENTATION, "order": SECTION_IDS[:-1]},
        {**PRESENTATION, "collapsed": ("unknown",)},
        {**PRESENTATION, "focus": "unknown"},
        {**PRESENTATION, "left_width": -1},
    ],
)
def test_invalid_normalized_state_fails_without_repair(
    presentation: dict[str, object],
) -> None:
    """Reject invalid reference inputs instead of silently changing persisted meanings."""

    with pytest.raises(ValueError):
        render_reference_frame(SECTIONS, presentation, width=100, height=24)

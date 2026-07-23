"""Complete behavioral evidence for the non-public Phase 4 reference adapter."""

from __future__ import annotations

from copy import deepcopy
from itertools import product

import pytest

from examples.student_dashboard_adapter import (
    MISSING_ROW,
    render_reference_frame,
)
from examples.student_dashboard_fixtures import (
    INTERACTION,
    PRESENTATION,
    SECTIONS,
    SECTION_IDS,
    SECTION_TITLES,
)
from thebitlab_tui import strip_ansi, visible_width


TINY_SNAPSHOT = """\
+ > Dettagl... +
|Exercise: p...|
|Status: ready |
+--------------+
+ Workspace ---+
|Path: C:/tr...|
|Files: 4      |"""

MODAL_SNAPSHOT = """\
+ > Dettaglio consegna --------------------------+
|Exercise: parse a tiny text format              |
|Status: ready                                   |
+------------------------------------------------+
+ Wor+ [x] Guida rapida --------------------+----+
|Path|Escape or q: close                    |    |
|File+--------------------------------------+    |
+------------------------------------------------+
+ Activity --------------------------------------+
|Last action: opened instructions                |
+------------------------------------------------+
+ Aiuto consentito ------------------------------+"""

LIST_ITEMS = tuple(f"case-{index}" for index in range(6))
LONG_REPORT_ROWS = tuple(f"report-{index}" for index in range(7))


def _replace_section(
    identifier: str,
    source: tuple[dict[str, object], ...] = SECTIONS,
    **changes: object,
) -> tuple[dict[str, object], ...]:
    """Return copied fixture dictionaries with one synthetic section changed."""

    return tuple(
        {**section, **changes} if section["id"] == identifier else dict(section)
        for section in source
    )


def _vertical_presentation(**changes: object) -> dict[str, object]:
    """Return caller-owned vertical state without the default collapsed panel."""

    return {
        **PRESENTATION,
        "orientation": "vertical",
        "collapsed": (),
        **changes,
    }


def _interaction(**changes: object) -> dict[str, object]:
    """Return copied transient state with nested mappings left caller-owned."""

    return {
        **deepcopy(INTERACTION),
        **changes,
    }


@pytest.mark.parametrize(
    ("width", "left_width"),
    tuple(product((89, 90, 100), (36, 62, 120))),
)
def test_allocation_matrix_preserves_geometry_and_persisted_width(
    width: int,
    left_width: int,
) -> None:
    """Protect every approved breakpoint and persisted-width combination."""

    presentation = {**PRESENTATION, "left_width": left_width}
    before = deepcopy(presentation)

    frame = render_reference_frame(
        presentation=presentation,
        width=width,
        height=24,
    )

    assert all(visible_width(row) == width for row in frame)
    assert any(" | " in row for row in frame) is (width >= 90)
    assert presentation == before


def test_tiny_ascii_snapshot_is_clipped_without_overflow() -> None:
    """Freeze tiny clipping, ellipsis, borders, and stable visible widths."""

    frame = render_reference_frame(width=16, height=7)

    assert frame == TINY_SNAPSHOT.splitlines()
    assert all(visible_width(row) == 16 for row in frame)
    assert "\x1b[" not in "\n".join(frame)


def test_resize_sequence_rebuilds_without_state_mutation() -> None:
    """Rebuild wide, narrow, tiny, and wide frames from unchanged caller state."""

    sections = deepcopy(SECTIONS)
    presentation = deepcopy(PRESENTATION)
    interaction = deepcopy(INTERACTION)
    before = deepcopy((sections, presentation, interaction))

    wide_before = render_reference_frame(
        sections,
        presentation,
        width=100,
        height=24,
        interaction=interaction,
    )
    narrow = render_reference_frame(
        sections,
        presentation,
        width=89,
        height=24,
        interaction=interaction,
    )
    tiny = render_reference_frame(
        sections,
        presentation,
        width=16,
        height=7,
        interaction=interaction,
    )
    wide_after = render_reference_frame(
        sections,
        presentation,
        width=100,
        height=24,
        interaction=interaction,
    )

    assert wide_before == wide_after
    assert any(" | " in row for row in wide_before)
    assert not any(" | " in row for row in narrow)
    assert tiny == TINY_SNAPSHOT.splitlines()
    assert (sections, presentation, interaction) == before


@pytest.mark.parametrize("identifier", SECTION_IDS)
def test_every_section_can_be_the_only_focused_panel(identifier: str) -> None:
    """Map each valid caller focus to exactly one textual panel marker."""

    presentation = _vertical_presentation(focus=identifier)

    frame = render_reference_frame(
        presentation=presentation,
        width=100,
        height=50,
    )
    focused_headers = [row for row in frame if row.startswith("+ >")]

    assert len(focused_headers) == 1
    assert SECTION_TITLES[identifier] in focused_headers[0]
    assert presentation["focus"] == identifier


@pytest.mark.parametrize("identifier", SECTION_IDS)
def test_every_section_can_be_collapsed_without_hiding_others(identifier: str) -> None:
    """Keep one collapsed section identifiable while preserving every panel."""

    presentation = _vertical_presentation(collapsed=(identifier,))
    unique_content = next(
        section["rows"][0] for section in SECTIONS if section["id"] == identifier
    )

    frame = render_reference_frame(
        presentation=presentation,
        width=100,
        height=50,
    )
    text = "\n".join(frame)

    assert text.count("[+]") == 1
    assert unique_content not in text
    assert all(title in text for title in SECTION_TITLES.values())
    assert presentation["collapsed"] == (identifier,)


def test_empty_missing_optional_and_long_rows_remain_safe() -> None:
    """Render neutral placeholders and truncate long caller-projected rows."""

    empty = _replace_section("assignment", rows=())
    missing_rows = tuple(
        {key: value for key, value in section.items() if key != "rows"}
        if section["id"] == "workspace"
        else dict(section)
        for section in empty
    )
    sections = tuple(
        {
            **section,
            "rows": ("A caller-projected row that is intentionally much too long",),
        }
        if section["id"] == "activity"
        else section
        for section in missing_rows
    )

    frame = render_reference_frame(
        sections,
        _vertical_presentation(),
        width=24,
        height=14,
    )
    text = "\n".join(frame)

    assert text.count(MISSING_ROW) == 2
    assert "..." in text
    assert all(visible_width(row) == 24 for row in frame)


@pytest.mark.parametrize(
    ("offset", "visible", "hidden"),
    [
        (0, ("report-0", "report-2"), ("report-6",)),
        (3, ("report-3", "report-5"), ("report-0",)),
        (999, ("report-4", "report-6"), ("report-0",)),
    ],
)
def test_section_scroll_clamps_only_for_drawing(
    offset: int,
    visible: tuple[str, ...],
    hidden: tuple[str, ...],
) -> None:
    """Keep long-section offsets caller-owned at first, middle, and beyond end."""

    sections = _replace_section("report", rows=LONG_REPORT_ROWS)
    interaction = _interaction(section_offsets={"report": offset})
    before = deepcopy(interaction)

    frame = render_reference_frame(
        sections,
        _vertical_presentation(),
        width=70,
        height=50,
        interaction=interaction,
    )
    text = "\n".join(frame)

    assert all(token in text for token in visible)
    assert all(token not in text for token in hidden)
    assert interaction == before


@pytest.mark.parametrize(
    ("offset", "visible"),
    [
        (0, ("Dettaglio consegna", "Workspace")),
        (10, ("Aiuto consentito", "Report")),
        (999, ("Runner", "Guida rapida")),
    ],
)
def test_dashboard_scroll_clamps_only_for_drawing(
    offset: int,
    visible: tuple[str, ...],
) -> None:
    """Keep the complete-dashboard offset unchanged across effective clamping."""

    interaction = _interaction(dashboard_offset=offset)
    before = deepcopy(interaction)

    frame = render_reference_frame(
        presentation=_vertical_presentation(),
        width=60,
        height=10,
        interaction=interaction,
    )
    text = "\n".join(frame)

    assert all(token in text for token in visible)
    assert interaction == before


@pytest.mark.parametrize(
    ("active_index", "list_offset", "selected"),
    [
        (0, 0, "case-0"),
        (2, 0, "case-2"),
        (999, 999, "case-5"),
    ],
)
def test_list_selection_clamps_only_for_drawing(
    active_index: int,
    list_offset: int,
    selected: str,
) -> None:
    """Clamp a reference selection locally without repairing caller state."""

    sections = _replace_section("tests", items=LIST_ITEMS)
    interaction = _interaction(
        active_indices={"tests": active_index},
        list_offsets={"tests": list_offset},
    )
    before = deepcopy(interaction)

    frame = render_reference_frame(
        sections,
        _vertical_presentation(focus="tests"),
        width=70,
        height=50,
        interaction=interaction,
    )

    assert any(f"> {selected}" in row for row in frame)
    assert interaction == before


@pytest.mark.parametrize(
    ("offset", "visible", "hidden"),
    [
        (0, ("case-0", "case-2"), ("case-5",)),
        (2, ("case-2", "case-4"), ("case-0",)),
        (999, ("case-3", "case-5"), ("case-0",)),
    ],
)
def test_list_scroll_clamps_only_for_drawing(
    offset: int,
    visible: tuple[str, ...],
    hidden: tuple[str, ...],
) -> None:
    """Keep list viewport input unchanged at first, middle, and beyond end."""

    sections = _replace_section("tests", items=LIST_ITEMS)
    interaction = _interaction(list_offsets={"tests": offset})
    before = deepcopy(interaction)

    frame = render_reference_frame(
        sections,
        _vertical_presentation(),
        width=70,
        height=50,
        interaction=interaction,
    )
    text = "\n".join(frame)

    assert all(token in text for token in visible)
    assert all(token not in text for token in hidden)
    assert interaction == before


def test_closed_modal_matches_dashboard_frame_exactly() -> None:
    """Treat a closed caller-owned modal as a complete rendering no-op."""

    default = render_reference_frame(width=50, height=12)
    closed = render_reference_frame(
        width=50,
        height=12,
        interaction=_interaction(
            modal={
                "open": False,
                "title": "Different hidden title",
                "rows": ("Hidden",),
            }
        ),
    )

    assert closed == default


def test_open_modal_ascii_snapshot_preserves_underlay_and_state() -> None:
    """Freeze application-owned overlay order without moving state into widgets."""

    interaction = _interaction(
        modal={
            "open": True,
            "title": "Guida rapida",
            "rows": ("Escape or q: close",),
        }
    )
    before = deepcopy(interaction)
    underlay = render_reference_frame(width=50, height=12)

    frame = render_reference_frame(
        width=50,
        height=12,
        interaction=interaction,
    )

    assert frame == MODAL_SNAPSHOT.splitlines()
    assert frame[:4] == underlay[:4]
    assert frame[7:] == underlay[7:]
    assert interaction == before
    assert "\x1b[" not in "\n".join(frame)


def test_ansi_in_titles_rows_and_items_never_changes_geometry() -> None:
    """Strip caller ANSI before measuring while retaining library-owned color."""

    plain = _replace_section("report", rows=("plain row",))
    plain = _replace_section(
        "tests",
        plain,
        title="Test list",
        items=("case zero", "case one"),
    )
    ansi = _replace_section("report", rows=("\x1b[32mplain row\x1b[0m",))
    ansi = _replace_section(
        "tests",
        ansi,
        title="\x1b[31mTest list\x1b[0m",
        items=("\x1b[33mcase zero\x1b[0m", "\x1b[34mcase one\x1b[0m"),
    )
    presentation = _vertical_presentation(focus="tests")

    expected = render_reference_frame(
        plain,
        presentation,
        width=50,
        height=40,
    )
    plain_from_ansi = render_reference_frame(
        ansi,
        presentation,
        width=50,
        height=40,
    )
    colored_from_ansi = render_reference_frame(
        ansi,
        presentation,
        width=50,
        height=40,
        color=True,
    )

    assert plain_from_ansi == expected
    assert [strip_ansi(row) for row in colored_from_ansi] == expected
    assert all(visible_width(row) == 50 for row in colored_from_ansi)


def test_quick_guide_and_modal_expose_modifier_free_commands() -> None:
    """Document portable workflows without implementing a command dispatcher."""

    dashboard = render_reference_frame(
        presentation=_vertical_presentation(),
        width=60,
        height=50,
    )
    modal = render_reference_frame(
        width=60,
        height=16,
        interaction=_interaction(
            modal={
                "open": True,
                "title": "Guida rapida",
                "rows": ("Escape or q: close",),
            }
        ),
    )
    dashboard_text = "\n".join(dashboard)
    modal_text = "\n".join(modal)

    assert "Arrows: move" in dashboard_text
    assert "Enter: open" in dashboard_text
    assert "q: close" in dashboard_text
    assert "Escape or q: close" in modal_text
    assert "Alt+" not in dashboard_text + modal_text
    assert "Ctrl+" not in dashboard_text + modal_text


@pytest.mark.parametrize(
    "interaction",
    [
        {**INTERACTION, "dashboard_offset": -1},
        {**INTERACTION, "section_offsets": {"unknown": 0}},
        {**INTERACTION, "section_offsets": {"report": -1}},
        {**INTERACTION, "list_offsets": {"tests": True}},
        {**INTERACTION, "active_indices": []},
        {**INTERACTION, "modal": {"open": "yes"}},
    ],
)
def test_invalid_transient_state_fails_without_repair(
    interaction: dict[str, object],
) -> None:
    """Reject invalid normalized transient state without inventing defaults."""

    before = deepcopy(interaction)

    with pytest.raises(ValueError):
        render_reference_frame(
            width=100,
            height=24,
            interaction=interaction,
        )

    assert interaction == before

"""Contract tests for reproducible documentation images."""

from __future__ import annotations

from pathlib import Path
import re
from xml.etree import ElementTree

import pytest

from examples.basic_panels import build_screen as build_panels
from examples.modal import HelpOverlay
from examples.scroll_view import build_screen as build_scroll_view
from examples.selectable_list import build_screen as build_selectable_list
from examples.student_dashboard_adapter import render_reference_frame
from examples.terminal_input import ApplicationState, render_frame as render_input_frame
from utui import TerminalSize, render
from tools.generate_phase4_images import CAPTURES, Capture, _interaction, _svg


SVG_NAMESPACE = {"svg": "http://www.w3.org/2000/svg"}
ROOT = Path(__file__).parents[1]
IMAGES = ROOT / "docs" / "_static" / "images"
EVIDENCE_INDEX = ROOT / "docs" / "architecture" / "phase-2-verification.rst"
PHASE_3_EVIDENCE_INDEX = ROOT / "docs" / "architecture" / "phase-3-verification.rst"
PHASE_4_EVIDENCE_INDEX = ROOT / "docs" / "architecture" / "phase-4-verification.rst"
REQUIRED_EVIDENCE = {
    "docs/api/index.rst",
    "docs/user-guide/index.rst",
    "docs/_static/images/modal.svg",
    "docs/_static/images/scroll-view.svg",
    "docs/_static/images/selectable-list.svg",
    "docs/_static/images/three-panels-narrow.svg",
    "docs/_static/images/three-panels-wide.svg",
    "examples/basic_panels.py",
    "examples/divider_badges.py",
    "examples/modal.py",
    "examples/scroll_view.py",
    "examples/selectable_list.py",
    "tests/test_canvas.py",
    "tests/test_divider_status_badge.py",
    "tests/test_layout.py",
    "tests/test_list_view.py",
    "tests/test_modal.py",
    "tests/test_renderer.py",
    "tests/test_scroll_view.py",
}
REQUIRED_PHASE_3_EVIDENCE = {
    "docs/api/index.rst",
    "docs/user-guide/index.rst",
    "docs/developer-guide/index.rst",
    "docs/_static/images/terminal-input.svg",
    "examples/terminal_input.py",
    "tests/test_key_reader.py",
    "tests/test_posix_decoder.py",
    "tests/test_posix_input.py",
    "tests/test_posix_pty.py",
    "tests/test_public_api_docs.py",
    "tests/test_windows_decoder.py",
    "tests/test_windows_input.py",
    "tests/test_terminal_input_example.py",
    "tests/test_examples.py",
    "tests/test_docs_assets.py",
    "tests/test_release_metadata.py",
}
REQUIRED_PHASE_4_EVIDENCE = {
    "docs/architecture/phase-4-adapter-contracts.rst",
    "docs/architecture/phase-4-verification.rst",
    "docs/integration/index.rst",
    "docs/user-guide/index.rst",
    "docs/developer-guide/index.rst",
    "docs/examples/index.rst",
    "docs/_static/images/student-dashboard-wide.svg",
    "docs/_static/images/student-dashboard-narrow.svg",
    "docs/_static/images/student-dashboard-modal.svg",
    "examples/student_dashboard_adapter.py",
    "examples/student_dashboard_fixtures.py",
    "tools/generate_phase4_images.py",
    "tests/test_docs_assets.py",
    "tests/test_examples.py",
    "tests/test_phase4_contract.py",
    "tests/test_public_api_docs.py",
    "tests/test_student_dashboard_adapter.py",
    "tests/test_student_dashboard_evidence.py",
}


def _terminal_rows(path: Path) -> list[str]:
    """Return the literal terminal rows stored in an SVG capture."""

    root = ElementTree.parse(path).getroot()
    return [node.text or "" for node in root.findall(".//svg:tspan", SVG_NAMESPACE)]


def test_svg_images_include_accessible_text() -> None:
    """Keep every documentation image valid and self-described."""

    for path in sorted(IMAGES.glob("*.svg")):
        root = ElementTree.parse(path).getroot()
        assert root.find("svg:title", SVG_NAMESPACE) is not None
        assert root.find("svg:desc", SVG_NAMESPACE) is not None


def test_architecture_labels_contrast_with_white_nodes() -> None:
    """Prevent architecture labels from inheriting the node background color."""

    root = ElementTree.parse(IMAGES / "architecture.svg").getroot()
    labels = root.findall(".//svg:text", SVG_NAMESPACE)

    assert labels
    assert all(label.get("fill") not in {None, "#fff", "#ffffff"} for label in labels)


@pytest.mark.parametrize(
    ("image_name", "widget", "width", "height"),
    [
        ("three-panels-wide.svg", build_panels(), 66, 4),
        ("three-panels-narrow.svg", build_panels(), 32, 11),
        ("selectable-list.svg", build_selectable_list(), 28, 7),
        ("scroll-view.svg", build_scroll_view(), 40, 8),
        ("modal.svg", HelpOverlay(), 48, 12),
    ],
)
def test_terminal_images_match_example_frames(
    image_name: str, widget: object, width: int, height: int
) -> None:
    """Keep reproducible SVG captures synchronized with executable examples."""

    expected = render(widget, width=width, height=height, color=False).splitlines()
    assert _terminal_rows(IMAGES / image_name) == expected


def test_terminal_input_image_matches_deterministic_snapshot() -> None:
    """Keep the Phase 3 image derived from the non-interactive example frame."""

    expected = render_input_frame(ApplicationState(), TerminalSize(70, 8), color=False)

    assert _terminal_rows(IMAGES / "terminal-input.svg") == expected


@pytest.mark.parametrize("capture", CAPTURES, ids=lambda capture: capture.filename)
def test_student_dashboard_images_match_generator(capture: Capture) -> None:
    """Keep complete Phase 4 SVG files synchronized with their generator."""

    rows = render_reference_frame(
        width=capture.width,
        height=capture.height,
        color=False,
        interaction=_interaction(modal_open=capture.modal_open),
    )
    path = IMAGES / capture.filename

    assert path.read_bytes() == _svg(capture, rows).encode("utf-8")
    assert _terminal_rows(path) == rows


def test_phase_2_evidence_index_references_existing_files() -> None:
    """Reject stale paths in the versioned Phase 2 release matrix."""

    document = EVIDENCE_INDEX.read_text(encoding="utf-8")
    referenced_paths = set(
        re.findall(r"``((?:docs|examples|tests)/[^`]+)``", document)
    )

    assert REQUIRED_EVIDENCE <= referenced_paths
    assert all((ROOT / relative_path).is_file() for relative_path in referenced_paths)


def test_phase_3_evidence_index_references_existing_files() -> None:
    """Reject stale paths in the versioned Phase 3 release matrix."""

    document = PHASE_3_EVIDENCE_INDEX.read_text(encoding="utf-8")
    referenced_paths = set(
        re.findall(r"``((?:docs|examples|tests)/[^`]+)``", document)
    )

    assert REQUIRED_PHASE_3_EVIDENCE <= referenced_paths
    assert all((ROOT / relative_path).is_file() for relative_path in referenced_paths)


def test_phase_4_evidence_index_references_existing_files() -> None:
    """Reject stale paths in the versioned Phase 4 evidence matrix."""

    document = PHASE_4_EVIDENCE_INDEX.read_text(encoding="utf-8")
    referenced_paths = set(
        re.findall(r"``((?:docs|examples|tests|tools)/[^`]+)``", document)
    )

    assert REQUIRED_PHASE_4_EVIDENCE <= referenced_paths
    assert all((ROOT / relative_path).is_file() for relative_path in referenced_paths)


def test_phase_4_evidence_records_provenance_and_pending_consumer_work() -> None:
    """Keep library proof separate from consumer integration that has not run."""

    document = PHASE_4_EVIDENCE_INDEX.read_text(encoding="utf-8")
    handoff = document.split("Consumer evidence handoff", 1)[1]

    assert "phase4-v2" in document
    assert "dbc36eabbb47562a2977597da833e092dec9f2b4" in document
    assert "7a538d2edd1dca44c8f062888f508845f3441f1c" in document
    assert all(f"pull/{number}" in document for number in (44, 46, 48))
    assert handoff.count("\n     - PENDING\n") == 6
    assert "Automated PASS" not in handoff
    assert "CI PASS" not in handoff


def test_phase_3_manual_evidence_is_complete() -> None:
    """Prevent completed interactive checks from reverting to placeholder results."""

    document = PHASE_3_EVIDENCE_INDEX.read_text(encoding="utf-8")

    assert "NOT RUN" not in document
    assert document.count("\n     - PASS\n") == 3
    assert document.count("Python 3.11.15") == 3
    assert document.count("``5e88c35``") == 3

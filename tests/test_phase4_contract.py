"""Contract tests for the proposed Phase 4 integration design."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "docs" / "architecture" / "phase-4-adapter-contracts.rst"
ARCHITECTURE_INDEX = ROOT / "docs" / "architecture" / "index.rst"
INTEGRATION_GUIDE = ROOT / "docs" / "integration.md"

SECTION_IDS = (
    "assignment",
    "workspace",
    "activity",
    "support",
    "help",
    "report",
    "tests",
    "grading",
    "runner",
    "guide",
)

PERSISTED_FIELDS = (
    "orientation",
    "order",
    "left_width",
    "collapsed",
    "focus",
)


def test_phase4_contract_is_in_the_sphinx_architecture_tree() -> None:
    """Keep the normative integration design reachable from the Sphinx architecture guide."""

    index = ARCHITECTURE_INDEX.read_text(encoding="utf-8")

    assert "phase-4-adapter-contracts" in index
    assert CONTRACT.is_file()


def test_phase4_contract_names_every_compatibility_section() -> None:
    """Prevent a persisted student-view section from disappearing from the design record."""

    document = CONTRACT.read_text(encoding="utf-8")

    for section_id in SECTION_IDS:
        assert f"``{section_id}``" in document


def test_phase4_contract_keeps_persisted_fields_consumer_owned() -> None:
    """Protect the existing JSON meanings without turning their parser into library API."""

    document = CONTRACT.read_text(encoding="utf-8")

    for field in PERSISTED_FIELDS:
        assert f"``{field}``" in document
    assert "The consumer owns" in document
    assert "never imports the consumer" in document


def test_phase4_integration_guide_links_the_normative_contract() -> None:
    """Keep the practical Markdown guide subordinate to the reviewed architecture contract."""

    guide = INTEGRATION_GUIDE.read_text(encoding="utf-8")

    assert "architecture/phase-4-adapter-contracts.rst" in guide
    assert "not a public adapter API" in guide

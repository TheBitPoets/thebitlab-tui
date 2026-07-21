"""Contract tests for the Phase 4 integration design."""

from __future__ import annotations

import re
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

CONSUMER_REVISION = "7a538d2edd1dca44c8f062888f508845f3441f1c"

RESPONSIVE_RULES = (
    "width below 90 columns",
    "splits the validated order after five entries",
    'three-cell ASCII separator ``" | "``',
    "effective_left = min(left_width, max(36, terminal_width - 39))",
    "right_width = max(30, terminal_width - effective_left - 3)",
    "exact persisted order",
    "does not rely on",
    "Row.stack_when_narrow",
)

OWNERSHIP_AND_FALLBACK_RULES = (
    "consumer-owned projection and validation",
    "never imports the consumer",
    "dashboard offset remain inputs",
    "Compatibility is semantic, not byte-for-byte",
    "consumer-owned legacy renderer",
    "modifier-free alternatives",
)

EVIDENCE_RULES = (
    "all ten populated panels",
    "wide horizontal, explicit vertical, narrow stacked, and tiny clipped frames",
    "every focused panel",
    "ANSI and ``no-color`` frames with identical visible geometry",
    "modal open and closed composition",
    "widths 89, 90, and 100",
    "Windows and Linux example smoke tests",
    "unchanged public API manifest",
)


def _section(document: str, heading: str, next_heading: str) -> str:
    """Return one bounded RST section for contract assertions."""

    return document.split(heading, 1)[1].split(next_heading, 1)[0]


def test_phase4_contract_is_in_the_sphinx_architecture_tree() -> None:
    """Keep the normative integration design reachable from the Sphinx architecture guide."""

    index = ARCHITECTURE_INDEX.read_text(encoding="utf-8")

    assert "phase-4-adapter-contracts" in index
    assert CONTRACT.is_file()


def test_phase4_contract_names_every_compatibility_section() -> None:
    """Prevent a persisted student-view section from disappearing from the design record."""

    document = CONTRACT.read_text(encoding="utf-8")

    table = _section(document, "Stable section identities", "Neutral fixture boundary")
    declared_ids = tuple(re.findall(r"^   \* - ``([^`]+)``$", table, flags=re.MULTILINE))

    assert declared_ids == SECTION_IDS


def test_phase4_contract_keeps_persisted_fields_consumer_owned() -> None:
    """Protect the existing JSON meanings without turning their parser into library API."""

    document = CONTRACT.read_text(encoding="utf-8")

    persisted = _section(document, "Persisted layout compatibility", "Responsive composition")

    for field in PERSISTED_FIELDS:
        assert f"\n``{field}``\n" in persisted
    assert "The consumer owns" in document
    assert "never imports the consumer" in document


def test_phase4_contract_records_approval_and_consumer_provenance() -> None:
    """Make the design gate and inspected compatibility baseline reproducible."""

    document = CONTRACT.read_text(encoding="utf-8")

    assert "merging PR `#44" in document
    assert CONSUMER_REVISION in document
    assert "scripts/student_lab_layout.py" in document
    assert "scripts/student_lab_cli.py" in document
    assert "tests/test_student_lab_layout.py" in document


def test_phase4_contract_protects_responsive_translation() -> None:
    """Keep the approved wide/narrow allocation deterministic."""

    document = CONTRACT.read_text(encoding="utf-8")
    responsive = _section(document, "Responsive composition", "Height, scrolling, and overlays")

    assert all(rule in responsive for rule in RESPONSIVE_RULES)


def test_phase4_contract_protects_ownership_and_fallback() -> None:
    """Prevent application state or rollout policy from drifting into the library."""

    document = CONTRACT.read_text(encoding="utf-8")

    assert all(rule in document for rule in OWNERSHIP_AND_FALLBACK_RULES)


def test_phase4_contract_protects_required_evidence() -> None:
    """Keep later implementation slices accountable to the approved verification matrix."""

    document = CONTRACT.read_text(encoding="utf-8")
    evidence = _section(document, "Required implementation evidence", "Delivery sequence")

    assert all(rule in evidence for rule in EVIDENCE_RULES)


def test_phase4_integration_guide_links_the_normative_contract() -> None:
    """Keep the practical Markdown guide subordinate to the reviewed architecture contract."""

    guide = INTEGRATION_GUIDE.read_text(encoding="utf-8")

    assert "architecture/phase-4-adapter-contracts.rst" in guide
    assert "not a public adapter API" in guide

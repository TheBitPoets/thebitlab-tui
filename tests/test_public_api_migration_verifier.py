"""Tests for the isolated legacy/current public API verifier."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.verify_public_api_migration import _assert_public_api_match


ROOT = Path(__file__).parents[1]
API_BASELINE = ROOT / "tests" / "data" / "public-api-0.3.0.json"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
LEGACY_COMMIT = "51173e64b9a81844dcd485da71045a8e1f9b32fd"


def test_public_api_comparison_accepts_identical_captures() -> None:
    """Accept API evidence only when both isolated captures are identical."""

    capture = {
        "python": "3.11",
        "exports": [
            {
                "name": "Key",
                "kind": "enum",
                "module": "events",
                "qualname": "Key",
                "signature": "(value)",
            }
        ],
    }

    _assert_public_api_match(capture, capture.copy())


def test_public_api_comparison_rejects_signature_divergence() -> None:
    """Reject a renamed signature that differs from the legacy package."""

    legacy = {
        "python": "3.11",
        "exports": [{"name": "Widget", "signature": "(*args, **kwargs)"}],
    }
    current = {
        "python": "3.11",
        "exports": [{"name": "Widget", "signature": "()"}],
    }

    with pytest.raises(AssertionError, match="public API changed"):
        _assert_public_api_match(legacy, current)


def test_manifest_and_ci_split_static_and_runtime_evidence() -> None:
    """Keep pre-move evidence immutable and run dynamic proof in every CI slice."""

    baseline = json.loads(API_BASELINE.read_text(encoding="utf-8"))
    exports = {item["name"]: item for item in baseline["exports"]}
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")

    assert baseline["schema"] == 1
    assert exports["Key"]["signature"] is None
    assert exports["Widget"]["signature"] is None
    assert 'python: ["3.11", "3.12", "3.13"]' in workflow
    assert "python tools/verify_public_api_migration.py" in workflow
    assert "--legacy-root legacy-v0.3.0" in workflow
    assert workflow.count(f"ref: {LEGACY_COMMIT}") == 2
    assert "ref: v0.3.0" not in workflow

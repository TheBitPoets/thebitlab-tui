"""Checks for synchronized dependency-free release metadata."""

from __future__ import annotations

from pathlib import Path
import re
import runpy


ROOT = Path(__file__).parents[1]


def _project_section() -> str:
    """Return the literal ``[project]`` table without requiring Python 3.11 locally."""

    document = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r"(?ms)^\[project\]\s*$\n(.*?)(?=^\[|\Z)", document)
    assert match is not None
    return match.group(1)


def test_phase_3_version_metadata_is_synchronized() -> None:
    """Keep package, Sphinx, and changelog versions aligned for the closeout."""

    project = _project_section()
    sphinx = runpy.run_path(str(ROOT / "docs" / "conf.py"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    version = re.search(r'(?m)^version = "([^"]+)"$', project)

    assert version is not None
    assert version.group(1) == "0.3.0"
    assert sphinx["release"] == version.group(1)
    assert "## Unreleased\n" in changelog
    assert "## 0.3.0 - 2026-07-21\n" in changelog
    assert changelog.index("## Unreleased") < changelog.index("## 0.3.0")


def test_runtime_dependency_list_remains_empty() -> None:
    """Reject accidental runtime dependencies during documentation consolidation."""

    project = _project_section()

    assert re.search(r"(?m)^dependencies\s*=", project) is None

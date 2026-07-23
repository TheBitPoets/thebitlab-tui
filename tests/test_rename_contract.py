"""Contract tests for the planned hard rename to ``utui``."""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "docs" / "architecture" / "utui-rename-contract.rst"
PHASE4_CONTRACT = ROOT / "docs" / "architecture" / "phase-4-adapter-contracts.rst"
ARCHITECTURE_INDEX = ROOT / "docs" / "architecture" / "index.rst"
ROADMAP = ROOT / "docs" / "roadmap.md"
PROJECT = ROOT / "pyproject.toml"


def test_rename_contract_is_reachable_and_traced() -> None:
    """Keep the rename design reachable from Sphinx and the primary roadmap."""

    index = ARCHITECTURE_INDEX.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")

    assert CONTRACT.is_file()
    assert "utui-rename-contract" in index
    assert "issues/51" in roadmap
    assert "issues/52" in roadmap
    assert "utui-rename-contract.rst" in roadmap


def test_rename_contract_defines_one_hard_identity() -> None:
    """Reject ambiguity about repository, distribution, import, and shim policy."""

    document = CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(document.split())

    required_rules = (
        "``TheBitPoets/utui``",
        "``src/utui``",
        "``import utui`` is the only supported import path",
        "does not include a ``thebitlab_tui``",
        "No second display name",
        "intentional hard pre-v1 rename",
        "Version ``0.4.0`` is assigned, tagged, and published only",
        "PyPI publication",
    )

    assert all(rule in normalized for rule in required_rules)


def test_rename_contract_preserves_public_behavior() -> None:
    """Keep the identity break separate from the library's behavior contract."""

    document = CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(document.split())

    invariants = (
        "``tuple(utui.__all__)`` is identical",
        "``inspect.signature``",
        "normalized module suffix",
        "qualified names, and signatures remain otherwise exact",
        "Public symbol names, signatures, returns, exceptions",
        "ASCII fallback",
        "ANSI geometry",
        "terminal restoration remain unchanged",
        "no runtime dependencies",
    )

    assert all(invariant in normalized for invariant in invariants)


def test_rename_contract_requires_an_explicit_old_install_upgrade() -> None:
    """Prevent the new distribution from coexisting silently with the old import."""

    document = CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(document.split())

    required_rules = (
        "Installing ``utui`` does not uninstall the old distribution",
        "``python -m pip uninstall thebitlab-tui``",
        "old ``0.3.0`` distribution installed",
        '``importlib.util.find_spec("thebitlab_tui")`` returns ``None``',
        "must not describe ``pip install utui`` alone as an upgrade",
    )

    assert all(rule in normalized for rule in required_rules)


def test_rename_contract_bounds_history_redirects_and_rollback() -> None:
    """Require explicit treatment of immutable history and GitHub rename risks."""

    document = CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(document.split())

    required_rules = (
        "Immutable Git history",
        "must never be reused",
        "GitHub Pages",
        "repository-hosted GitHub Action",
        "Rollback never rewrites commits, tags, releases, issues, or reviews",
        "stop without forcing it",
    )

    assert all(rule in normalized for rule in required_rules)


def test_phase4_contract_requires_rename_before_consumer_integration() -> None:
    """Keep the earlier Phase 4 sequence subordinate to the new identity gate."""

    document = PHASE4_CONTRACT.read_text(encoding="utf-8")
    normalized = " ".join(document.split())

    assert "verified ``utui`` rename baseline tracked by parent issue #51" in normalized
    assert "hard pre-v1 repository, distribution, and import rename" in normalized
    assert "collect separately authorized consumer evidence using only" in normalized


def test_rename_sequence_is_atomic_and_repository_first_at_handoff() -> None:
    """Keep live planning from splitting the current-tree identity migration."""

    document = CONTRACT.read_text(encoding="utf-8")
    sequence = document.split("Implementation sequence", 1)[1].split(
        "Rollback boundary", 1
    )[0]
    normalized = " ".join(sequence.split())

    assert "same current-tree child and pull request" in normalized
    assert normalized.index("Rename the GitHub repository") < normalized.index(
        "Merge the approved atomic current-tree migration"
    )


def test_design_slice_does_not_perform_the_rename() -> None:
    """Keep the design PR reversible until its breaking contract is approved."""

    project = PROJECT.read_text(encoding="utf-8")
    source_packages = {path.name for path in (ROOT / "src").iterdir() if path.is_dir()}

    assert re.search(r'(?m)^name = "thebitlab-tui"$', project)
    assert "thebitlab_tui" in source_packages
    assert "utui" not in source_packages

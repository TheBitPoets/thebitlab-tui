"""Verify clean and uninstall-first distribution migration to ``utui``.

The script builds wheels from the current tree and the immutable 0.3.0 tree,
uses only temporary virtual environments, and prevents the invoking checkout
or user site-packages from satisfying import probes accidentally.
"""

from __future__ import annotations

import argparse
from email.parser import BytesParser
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile


CURRENT_DISTRIBUTION = "utui"
CURRENT_IMPORT = "utui"
LEGACY_DISTRIBUTION = "thebitlab" + "-tui"
LEGACY_IMPORT = "thebitlab" + "_tui"


def _copy_source_tree(source: Path, destination: Path) -> Path:
    """Copy a source tree without build products that could pollute a wheel."""

    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            ".git",
            ".pytest_cache",
            ".venv",
            "_build",
            "__pycache__",
            "*.egg-info",
            "build",
            "dist",
            "venv",
        ),
    )
    return destination


def _clean_environment() -> dict[str, str]:
    """Return an environment isolated from caller-owned Python paths."""

    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run(command: list[str], *, cwd: Path) -> None:
    """Run one verification command and fail with its original exit status."""

    subprocess.run(
        command,
        cwd=cwd,
        env=_clean_environment(),
        check=True,
    )


def _environment_python(environment: Path) -> Path:
    """Return the interpreter path for a Windows or POSIX virtual environment."""

    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def _create_environment(path: Path) -> Path:
    """Create a clean virtual environment and return its interpreter."""

    venv.EnvBuilder(with_pip=True, clear=True).create(path)
    return _environment_python(path)


def _build_wheel(source: Path, destination: Path, *, cwd: Path) -> Path:
    """Build exactly one dependency-free wheel from ``source``."""

    destination.mkdir(parents=True, exist_ok=True)
    before = set(destination.glob("*.whl"))
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-cache-dir",
            "--no-deps",
            "--wheel-dir",
            str(destination),
            str(source),
        ],
        cwd=cwd,
    )
    wheels = set(destination.glob("*.whl")) - before
    if len(wheels) != 1:
        raise RuntimeError(f"expected one new wheel in {destination}, found {len(wheels)}")
    return wheels.pop()


def _assert_current_wheel(wheel: Path) -> str:
    """Validate archive identity and return the wheel version."""

    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if f"{CURRENT_IMPORT}/__init__.py" not in names:
            raise AssertionError("wheel does not contain the utui import package")
        legacy_prefix = LEGACY_IMPORT + "/"
        if any(name.startswith(legacy_prefix) for name in names):
            raise AssertionError("wheel contains the retired import package")

        metadata_paths = [
            name
            for name in names
            if name.endswith(".dist-info/METADATA")
        ]
        if len(metadata_paths) != 1:
            raise AssertionError("wheel must contain exactly one METADATA file")
        metadata = BytesParser().parsebytes(archive.read(metadata_paths[0]))

    if metadata["Name"] != CURRENT_DISTRIBUTION:
        raise AssertionError(f"unexpected distribution name: {metadata['Name']!r}")
    for requirement in metadata.get_all("Requires-Dist", []):
        marker = requirement.partition(";")[2]
        if "extra ==" not in marker:
            raise AssertionError(f"unexpected runtime dependency: {requirement}")
    version = metadata["Version"]
    if not version:
        raise AssertionError("wheel metadata does not define a version")
    return version


def _probe_identity(
    python: Path,
    *,
    present_distribution: str | None,
    present_import: str | None,
    expected_version: str | None,
    absent_distribution: str,
    absent_import: str,
    cwd: Path,
) -> None:
    """Prove expected and retired identities in a fresh interpreter process."""

    probe = (
        "import importlib, importlib.metadata as m, importlib.util as u, sys\n"
        "present_dist, present_mod, version, absent_dist, absent_mod = sys.argv[1:]\n"
        "normalize = lambda value: value.lower().replace('_', '-').replace('.', '-')\n"
        "installed = {normalize(d.metadata.get('Name') or '') for d in m.distributions()}\n"
        "if present_dist:\n"
        "    assert normalize(present_dist) in installed\n"
        "    assert m.version(present_dist) == version\n"
        "if present_mod:\n"
        "    importlib.import_module(present_mod)\n"
        "assert normalize(absent_dist) not in installed\n"
        "assert u.find_spec(absent_mod) is None\n"
    )
    _run(
        [
            str(python),
            "-c",
            probe,
            present_distribution or "",
            present_import or "",
            expected_version or "",
            absent_distribution,
            absent_import,
        ],
        cwd=cwd,
    )


def verify(current_root: Path, legacy_root: Path) -> None:
    """Run clean source, wheel, and legacy-install migration verification."""

    current_root = current_root.resolve()
    legacy_root = legacy_root.resolve()
    if not (current_root / "pyproject.toml").is_file():
        raise FileNotFoundError(f"current source tree not found: {current_root}")
    if not (legacy_root / "pyproject.toml").is_file():
        raise FileNotFoundError(f"legacy source tree not found: {legacy_root}")

    with tempfile.TemporaryDirectory(prefix="utui-distribution-") as temporary:
        workspace = Path(temporary)
        current_source = _copy_source_tree(
            current_root,
            workspace / "current-source",
        )
        legacy_source = _copy_source_tree(
            legacy_root,
            workspace / "legacy-source",
        )
        current_wheel = _build_wheel(
            current_source,
            workspace / "current-wheel",
            cwd=workspace,
        )
        legacy_wheel = _build_wheel(
            legacy_source,
            workspace / "legacy-wheel",
            cwd=workspace,
        )
        current_version = _assert_current_wheel(current_wheel)

        source_python = _create_environment(workspace / "source-environment")
        _run(
            [
                str(source_python),
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "--no-deps",
                str(current_source),
            ],
            cwd=workspace,
        )
        _probe_identity(
            source_python,
            present_distribution=CURRENT_DISTRIBUTION,
            present_import=CURRENT_IMPORT,
            expected_version=current_version,
            absent_distribution=LEGACY_DISTRIBUTION,
            absent_import=LEGACY_IMPORT,
            cwd=workspace,
        )
        _run([str(source_python), "-m", "pip", "check"], cwd=workspace)

        wheel_python = _create_environment(workspace / "wheel-environment")
        _run(
            [
                str(wheel_python),
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "--no-deps",
                str(current_wheel),
            ],
            cwd=workspace,
        )
        _probe_identity(
            wheel_python,
            present_distribution=CURRENT_DISTRIBUTION,
            present_import=CURRENT_IMPORT,
            expected_version=current_version,
            absent_distribution=LEGACY_DISTRIBUTION,
            absent_import=LEGACY_IMPORT,
            cwd=workspace,
        )
        _run([str(wheel_python), "-m", "pip", "check"], cwd=workspace)

        upgrade_python = _create_environment(workspace / "upgrade-environment")
        _run(
            [
                str(upgrade_python),
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "--no-deps",
                str(legacy_wheel),
            ],
            cwd=workspace,
        )
        _probe_identity(
            upgrade_python,
            present_distribution=LEGACY_DISTRIBUTION,
            present_import=LEGACY_IMPORT,
            expected_version="0.3.0",
            absent_distribution=CURRENT_DISTRIBUTION,
            absent_import=CURRENT_IMPORT,
            cwd=workspace,
        )
        _run(
            [
                str(upgrade_python),
                "-m",
                "pip",
                "uninstall",
                "--yes",
                LEGACY_DISTRIBUTION,
            ],
            cwd=workspace,
        )
        _probe_identity(
            upgrade_python,
            present_distribution=None,
            present_import=None,
            expected_version=None,
            absent_distribution=LEGACY_DISTRIBUTION,
            absent_import=LEGACY_IMPORT,
            cwd=workspace,
        )
        _run(
            [
                str(upgrade_python),
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "--no-deps",
                str(current_wheel),
            ],
            cwd=workspace,
        )
        _probe_identity(
            upgrade_python,
            present_distribution=CURRENT_DISTRIBUTION,
            present_import=CURRENT_IMPORT,
            expected_version=current_version,
            absent_distribution=LEGACY_DISTRIBUTION,
            absent_import=LEGACY_IMPORT,
            cwd=workspace,
        )
        _run([str(upgrade_python), "-m", "pip", "check"], cwd=workspace)


def _arguments() -> argparse.Namespace:
    """Parse source-tree paths for the migration verifier."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--current-root",
        type=Path,
        default=Path.cwd(),
        help="current utui source tree (default: current directory)",
    )
    parser.add_argument(
        "--legacy-root",
        type=Path,
        required=True,
        help="immutable source checkout for version 0.3.0",
    )
    return parser.parse_args()


def main() -> None:
    """Run command-line distribution migration verification."""

    arguments = _arguments()
    verify(arguments.current_root, arguments.legacy_root)
    print("utui distribution migration verification passed")


if __name__ == "__main__":
    main()

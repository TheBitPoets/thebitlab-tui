"""Compare the legacy and renamed public APIs in isolated interpreters.

The verifier imports each source tree in a separate ``python -I`` process,
normalizes the package identity, and compares every exported name, kind,
owner, qualified name, and inspectable signature.  Running it across the
supported Python matrix proves interpreter-owned signatures without changing
the immutable manifest captured before the package move.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


LEGACY_IMPORT = "thebitlab" + "_tui"
CURRENT_IMPORT = "utui"

_CAPTURE_PROBE = r"""
import importlib
import inspect
import json
from pathlib import Path
import re
import sys
from enum import Enum

package_name, source_root = sys.argv[1:]
sys.path.insert(0, str(Path(source_root).resolve() / "src"))
package = importlib.import_module(package_name)

def public_kind(value):
    if inspect.isclass(value) and issubclass(value, Enum):
        return "enum"
    if inspect.isclass(value) and getattr(value, "_is_protocol", False):
        return "protocol"
    if inspect.isclass(value):
        return "class"
    if inspect.isfunction(value):
        return "function"
    return type(value).__name__

def stable_signature(value):
    try:
        signature = str(inspect.signature(value))
    except (TypeError, ValueError):
        return None
    signature = signature.replace(package_name, "{package}")
    return re.sub(r"at 0x[0-9A-Fa-f]+", "at 0x...", signature)

exports = []
for name in package.__all__:
    value = getattr(package, name)
    module = getattr(value, "__module__", "")
    module = module.removeprefix(f"{package_name}.")
    exports.append(
        {
            "name": name,
            "kind": public_kind(value),
            "module": module,
            "qualname": getattr(value, "__qualname__", name),
            "signature": stable_signature(value),
        }
    )

print(
    json.dumps(
        {
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "exports": exports,
        },
        sort_keys=True,
    )
)
"""


def _clean_environment() -> dict[str, str]:
    """Return an environment isolated from caller-owned Python paths."""

    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _capture_public_api(
    python: Path,
    *,
    package_name: str,
    source_root: Path,
    cwd: Path,
) -> dict[str, Any]:
    """Capture one source tree's API in an isolated interpreter."""

    completed = subprocess.run(
        [
            str(python),
            "-I",
            "-c",
            _CAPTURE_PROBE,
            package_name,
            str(source_root),
        ],
        cwd=cwd,
        env=_clean_environment(),
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def _assert_public_api_match(
    legacy: dict[str, Any],
    current: dict[str, Any],
) -> None:
    """Raise with a readable diff when legacy and current APIs diverge."""

    if legacy == current:
        return
    legacy_text = json.dumps(legacy, indent=2, sort_keys=True)
    current_text = json.dumps(current, indent=2, sort_keys=True)
    raise AssertionError(
        "public API changed during the package rename\n"
        f"legacy:\n{legacy_text}\n"
        f"current:\n{current_text}"
    )


def verify(current_root: Path, legacy_root: Path, *, python: Path) -> None:
    """Compare immutable legacy and current source trees with one interpreter."""

    current_root = current_root.resolve()
    legacy_root = legacy_root.resolve()
    for root, package_name in (
        (legacy_root, LEGACY_IMPORT),
        (current_root, CURRENT_IMPORT),
    ):
        package = root / "src" / package_name / "__init__.py"
        if not package.is_file():
            raise FileNotFoundError(f"source package not found: {package}")

    legacy = _capture_public_api(
        python,
        package_name=LEGACY_IMPORT,
        source_root=legacy_root,
        cwd=current_root,
    )
    current = _capture_public_api(
        python,
        package_name=CURRENT_IMPORT,
        source_root=current_root,
        cwd=current_root,
    )
    _assert_public_api_match(legacy, current)


def _arguments() -> argparse.Namespace:
    """Parse source-tree paths for the public API verifier."""

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
    """Run command-line public API migration verification."""

    arguments = _arguments()
    verify(
        arguments.current_root,
        arguments.legacy_root,
        python=Path(sys.executable),
    )
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"utui public API migration verification passed on Python {version}")


if __name__ == "__main__":
    main()

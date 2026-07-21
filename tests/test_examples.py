"""Cross-platform smoke checks for every documented executable example."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from thebitlab_tui import visible_width


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize(
    ("script", "arguments", "width", "height"),
    [
        ("basic_panels.py", [], 66, 4),
        ("divider_badges.py", [], 40, 8),
        ("selectable_list.py", [], 28, 7),
        ("scroll_view.py", [], 40, 8),
        ("modal.py", [], 48, 12),
        ("terminal_input.py", ["--snapshot"], 70, 8),
    ],
)
def test_documented_example_runs_without_color(
    script: str, arguments: list[str], width: int, height: int
) -> None:
    """Execute examples exactly as documented on both Windows and Linux CI."""

    environment = os.environ.copy()
    environment["COLUMNS"] = str(width)
    environment["LINES"] = str(height)
    source_path = str(ROOT / "src")
    existing_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_path if not existing_path else source_path + os.pathsep + existing_path
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / script),
            *arguments,
            "--no-color",
        ],
        cwd=ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    rows = result.stdout.splitlines()

    assert result.stderr == ""
    assert "\x1b[" not in result.stdout
    assert len(rows) == height
    assert all(visible_width(row) == width for row in rows)


def test_terminal_input_example_rejects_redirected_stdin() -> None:
    """Keep piped input distinct from an interactive Windows or Linux terminal."""

    environment = os.environ.copy()
    source_path = str(ROOT / "src")
    existing_path = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_path if not existing_path else source_path + os.pathsep + existing_path
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "examples" / "terminal_input.py"),
            "--interactive",
            "--no-color",
        ],
        cwd=ROOT,
        env=environment,
        input="q\n",
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("terminal input unavailable: ")
    assert "Traceback" not in result.stderr

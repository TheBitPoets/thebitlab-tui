"""Generate reproducible Phase 4 student-dashboard SVG captures.

The script uses only the synthetic ``phase4-v2`` fixture and the non-public
reference adapter. Run it from the repository root with
``python tools/generate_phase4_images.py``.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from html import escape
from pathlib import Path
import sys


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from examples.student_dashboard_adapter import render_reference_frame  # noqa: E402
from examples.student_dashboard_fixtures import INTERACTION  # noqa: E402


@dataclass(frozen=True, slots=True)
class Capture:
    """Describe one deterministic no-color documentation capture."""

    filename: str
    width: int
    height: int
    title: str
    description: str
    modal_open: bool = False


CAPTURES = (
    Capture(
        "student-dashboard-wide.svg",
        100,
        20,
        "Wide synthetic student dashboard",
        "Ten synthetic student panels use the Phase 4 two-column ASCII layout.",
    ),
    Capture(
        "student-dashboard-narrow.svg",
        89,
        38,
        "Narrow synthetic student dashboard",
        "The same ten synthetic panels use one ordered ASCII column below the breakpoint.",
    ),
    Capture(
        "student-dashboard-modal.svg",
        50,
        12,
        "Synthetic student dashboard with quick-help modal",
        "A centered ASCII quick-help modal overlays the caller-owned dashboard underlay.",
        modal_open=True,
    ),
)


def _interaction(*, modal_open: bool) -> dict[str, object]:
    """Return copied caller-owned interaction state for one capture."""

    interaction = deepcopy(INTERACTION)
    modal = interaction["modal"]
    assert isinstance(modal, dict)
    modal["open"] = modal_open
    return interaction


def _svg(capture: Capture, rows: list[str]) -> str:
    """Return an accessible SVG whose text rows exactly match one frame."""

    pixel_width = capture.width * 10 + 40
    pixel_height = capture.height * 20 + 40
    tspans = "\n".join(
        f'    <tspan x="20" dy="{0 if index == 0 else 20}">{escape(row)}</tspan>'
        for index, row in enumerate(rows)
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{pixel_width}" '
        f'height="{pixel_height}" viewBox="0 0 {pixel_width} {pixel_height}" '
        'role="img" aria-labelledby="title desc">\n'
        f'  <title id="title">{escape(capture.title)}</title>\n'
        f'  <desc id="desc">{escape(capture.description)}</desc>\n'
        f'  <rect width="{pixel_width}" height="{pixel_height}" rx="8" fill="#171717"/>\n'
        '  <text x="20" y="30" fill="#f4f4f4" font-family="Consolas, monospace" '
        'font-size="14" xml:space="preserve">\n'
        f"{tspans}\n"
        "  </text>\n"
        "</svg>\n"
    )


def main() -> None:
    """Write every Phase 4 capture from the executable reference adapter."""

    destination = ROOT / "docs" / "_static" / "images"
    destination.mkdir(parents=True, exist_ok=True)
    for capture in CAPTURES:
        rows = render_reference_frame(
            width=capture.width,
            height=capture.height,
            color=False,
            interaction=_interaction(modal_open=capture.modal_open),
        )
        (destination / capture.filename).write_text(
            _svg(capture, rows),
            encoding="utf-8",
            newline="\n",
        )


if __name__ == "__main__":
    main()

"""Contract tests for reproducible documentation images."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree


SVG_NAMESPACE = {"svg": "http://www.w3.org/2000/svg"}
IMAGES = Path(__file__).parents[1] / "docs" / "_static" / "images"


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

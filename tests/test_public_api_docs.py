"""Contract tests for public API documentation."""

from __future__ import annotations

import inspect
import json
from pathlib import Path
import re
from enum import Enum

import utui
from utui import canvas, events, geometry, layout, renderer, styles, terminal, widgets


API_BASELINE = Path(__file__).parent / "data" / "public-api-0.3.0.json"
MODULES = (canvas, events, geometry, layout, renderer, styles, terminal, widgets)
PUBLIC_API = (
    "Canvas",
    "Column",
    "Divider",
    "Key",
    "KeyEvent",
    "KeyReader",
    "Label",
    "ListView",
    "Modal",
    "Panel",
    "Rect",
    "ResizeWatcher",
    "Row",
    "ScrollView",
    "Size",
    "Style",
    "StatusBadge",
    "TerminalSize",
    "Widget",
    "get_terminal_size",
    "render",
    "render_lines",
    "render_terminal",
    "strip_ansi",
    "supports_color",
    "truncate",
    "visible_width",
)


def _public_kind(value: object) -> str:
    """Return the stable public kind used by the versioned API manifest."""

    if inspect.isclass(value) and issubclass(value, Enum):
        return "enum"
    if inspect.isclass(value) and getattr(value, "_is_protocol", False):
        return "protocol"
    if inspect.isclass(value):
        return "class"
    if inspect.isfunction(value):
        return "function"
    return type(value).__name__


def _stable_signature(value: object) -> str | None:
    """Normalize a supported signature across package names and processes."""

    try:
        signature = str(inspect.signature(value))
    except (TypeError, ValueError):
        return None
    signature = signature.replace(value.__module__.split(".", 1)[0], "{package}")
    return re.sub(r"at 0x[0-9A-Fa-f]+", "at 0x...", signature)


def _capture_public_api(package: object) -> dict[str, object]:
    """Capture names, ownership, kinds, and supported signatures."""

    exports = []
    for name in package.__all__:
        value = getattr(package, name)
        module = getattr(value, "__module__", "")
        module = module.removeprefix(f"{package.__name__}.")
        exports.append(
            {
                "name": name,
                "kind": _public_kind(value),
                "module": module,
                "qualname": getattr(value, "__qualname__", name),
                "signature": _stable_signature(value),
            }
        )
    return {"schema": 1, "source_version": "0.3.0", "exports": exports}


def test_public_api_manifest_is_stable() -> None:
    """Protect the complete 0.3.0 namespace and signatures during the rename."""

    assert tuple(utui.__all__) == PUBLIC_API
    assert len(utui.__all__) == len(set(utui.__all__))
    assert all(hasattr(utui, name) for name in PUBLIC_API)
    expected = json.loads(API_BASELINE.read_text(encoding="utf-8"))
    assert _capture_public_api(utui) == expected


def test_exported_api_has_docstrings() -> None:
    missing = [
        name
        for name in utui.__all__
        if not inspect.getdoc(getattr(utui, name))
    ]
    assert missing == []


def test_public_module_members_have_docstrings() -> None:
    missing: list[str] = []
    for module in MODULES:
        for name, value in inspect.getmembers(module):
            if name.startswith("_") or getattr(value, "__module__", None) != module.__name__:
                continue
            if inspect.isfunction(value) or inspect.isclass(value):
                if not inspect.getdoc(value):
                    missing.append(f"{module.__name__}.{name}")
            if inspect.isclass(value):
                for member_name, member in value.__dict__.items():
                    if member_name.startswith("_"):
                        continue
                    documented = member.fget if isinstance(member, property) else member
                    if callable(documented) and not inspect.getdoc(documented):
                        missing.append(f"{module.__name__}.{name}.{member_name}")
    assert missing == []

"""Contract tests for public API documentation."""

from __future__ import annotations

import inspect

import thebitlab_tui
from thebitlab_tui import canvas, events, geometry, layout, renderer, styles, terminal, widgets


MODULES = (canvas, events, geometry, layout, renderer, styles, terminal, widgets)


def test_exported_api_has_docstrings() -> None:
    missing = [
        name
        for name in thebitlab_tui.__all__
        if not inspect.getdoc(getattr(thebitlab_tui, name))
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

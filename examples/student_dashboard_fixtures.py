"""Synthetic, revisioned data for the non-public student dashboard reference adapter.

The values in this module are invented presentation fixtures. They are not an application schema,
do not mirror consumer dictionaries, and are not installed as part of :mod:`thebitlab_tui`.
"""

from __future__ import annotations


FIXTURE_REVISION = "phase4-v1"

SECTION_IDS = (
    "assignment",
    "workspace",
    "activity",
    "support",
    "help",
    "report",
    "tests",
    "grading",
    "runner",
    "guide",
)

SECTION_TITLES = {
    "assignment": "Dettaglio consegna",
    "workspace": "Workspace",
    "activity": "Activity",
    "support": "Aiuto consentito",
    "help": "Richieste aiuto",
    "report": "Report",
    "tests": "Ultimo dettaglio test",
    "grading": "Grading",
    "runner": "Runner",
    "guide": "Guida rapida",
}

SECTIONS = (
    {
        "id": "assignment",
        "title": SECTION_TITLES["assignment"],
        "rows": ("Exercise: parse a tiny text format", "Status: ready"),
    },
    {
        "id": "workspace",
        "title": SECTION_TITLES["workspace"],
        "rows": ("Path: C:/training/sample-lab", "Files: 4"),
    },
    {
        "id": "activity",
        "title": SECTION_TITLES["activity"],
        "rows": ("Last action: opened instructions",),
    },
    {
        "id": "support",
        "title": SECTION_TITLES["support"],
        "rows": ("Allowed: standard library docs", "Not allowed: completed solution"),
    },
    {
        "id": "help",
        "title": SECTION_TITLES["help"],
        "rows": ("Open requests: 0",),
    },
    {
        "id": "report",
        "title": SECTION_TITLES["report"],
        "rows": ("Summary: implementation started", "Notes: add boundary cases"),
    },
    {
        "id": "tests",
        "title": SECTION_TITLES["tests"],
        "rows": ("Passed: 6", "Failed: 1"),
    },
    {
        "id": "grading",
        "title": SECTION_TITLES["grading"],
        "rows": ("State: not submitted",),
    },
    {
        "id": "runner",
        "title": SECTION_TITLES["runner"],
        "rows": ("Command: python -m pytest", "State: idle"),
    },
    {
        "id": "guide",
        "title": SECTION_TITLES["guide"],
        "rows": ("Arrows: move", "Enter: open", "q: close"),
    },
)

PRESENTATION = {
    "orientation": "horizontal",
    "order": SECTION_IDS,
    "left_width": 62,
    "collapsed": ("help",),
    "focus": "assignment",
}

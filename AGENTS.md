# Contributor guidance

- Keep the runtime dependency-free and compatible with Python 3.11+ on Windows and Linux.
- Widgets draw to a canvas; they never print and never contain application data logic.
- Preserve ASCII fallbacks, clipping, and stable visible line widths.
- Keep terminal adapters separate from geometry, widgets, layout, and rendering.
- Add deterministic tests and ASCII snapshots for rendering changes.
- Do not copy application code from the student TUI into this package.


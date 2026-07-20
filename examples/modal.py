"""Centered overlay assembled manually until the Phase 2 Modal widget exists."""

from thebitlab_tui import Canvas, Label, Panel, Rect

canvas = Canvas(48, 12)
Label("Background content").draw(canvas, canvas.rect)
modal = Panel("Press Escape to close", title="Confirm", focused=True)
modal.draw(canvas, Rect(10, 4, 28, 5))
print(canvas.text(color=False))


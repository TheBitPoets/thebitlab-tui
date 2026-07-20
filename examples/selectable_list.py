"""Selection represented with today's primitive widgets."""

from thebitlab_tui import Label, Panel, render

items = ["  setup", "> exercise-01", "  exercise-02"]
screen = Panel(Label("\n".join(items)), title="Exercises", focused=True)
print(render(screen, 28, 7, color=False))


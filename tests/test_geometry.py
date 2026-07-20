import pytest

from thebitlab_tui import Rect


def test_rect_properties_and_contains() -> None:
    rect = Rect(2, 3, 5, 4)
    assert (rect.right, rect.bottom) == (7, 7)
    assert rect.contains(2, 3)
    assert not rect.contains(7, 7)


def test_rect_intersection_and_inset() -> None:
    assert Rect(0, 0, 5, 4).intersect(Rect(3, 2, 4, 4)) == Rect(3, 2, 2, 2)
    assert Rect(1, 1, 8, 6).inset(1, 2) == Rect(2, 3, 6, 2)


def test_negative_dimensions_are_rejected() -> None:
    with pytest.raises(ValueError):
        Rect(0, 0, -1, 1)


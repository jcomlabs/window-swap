import pytest

from window_swap_core import (
    next_window_in_z_order,
    point_in_swap_corner,
    popup_geometry,
    rects_match,
)


def test_rects_match_within_tolerance() -> None:
    assert rects_match((0, 0, 1000, 800), (10, -5, 1012, 793), tolerance=15)


def test_rects_do_not_match_outside_tolerance() -> None:
    assert not rects_match((0, 0, 1000, 800), (16, 0, 1000, 800), tolerance=15)


def test_negative_tolerance_is_rejected() -> None:
    try:
        rects_match((0, 0, 1, 1), (0, 0, 1, 1), tolerance=-1)
    except ValueError as error:
        assert str(error) == "tolerance must be non-negative"
    else:
        raise AssertionError("negative tolerance was accepted")


def test_bottom_right_corner_includes_edges() -> None:
    rect = (100, 100, 900, 700)
    assert point_in_swap_corner((800, 600), rect, corner_size=100)
    assert point_in_swap_corner((900, 700), rect, corner_size=100)


def test_point_outside_corner_is_rejected() -> None:
    assert not point_in_swap_corner((799, 650), (100, 100, 900, 700), corner_size=100)


def test_invalid_rectangle_is_rejected() -> None:
    assert not point_in_swap_corner((100, 100), (100, 100, 100, 100))


def test_next_window_uses_z_order_and_deduplicates() -> None:
    assert next_window_in_z_order([100, 100, 200, 300]) == 200


def test_next_window_requires_a_stack() -> None:
    assert next_window_in_z_order([]) is None
    assert next_window_in_z_order([100]) is None


def test_corner_detection_supports_negative_monitor_coordinates() -> None:
    rect = (-1920, -200, 0, 880)
    assert point_in_swap_corner((-50, 850), rect, corner_size=100)
    assert not point_in_swap_corner((-101, 850), rect, corner_size=100)


def test_popup_geometry_uses_valid_negative_tk_coordinates() -> None:
    assert popup_geometry((-1920, -200, 0, 880), 80, 30) == "-100+830"
    assert popup_geometry((0, -1080, 1920, 0), 80, 30) == "+1820-50"


def test_popup_geometry_stays_inside_a_small_window() -> None:
    assert popup_geometry((100, 200, 150, 225), 80, 30) == "+100+200"


@pytest.mark.parametrize(
    ("width", "height", "margin"),
    [(0, 20, 5), (20, 0, 5), (20, 20, -1)],
)
def test_popup_geometry_rejects_invalid_dimensions(
    width: int, height: int, margin: int
) -> None:
    with pytest.raises(ValueError):
        popup_geometry((0, 0, 100, 100), width, height, margin)

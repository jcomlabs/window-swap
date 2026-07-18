from window_swap_core import next_window_in_z_order, point_in_swap_corner, rects_match


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

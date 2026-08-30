"""Pure geometry and ordering rules used by Window Swap.

Keeping these rules independent from Win32 makes the behavior deterministic and
testable without moving real desktop windows.
"""

from __future__ import annotations

from collections.abc import Iterable

Rect = tuple[int, int, int, int]
Point = tuple[int, int]


def rects_match(first: Rect, second: Rect, tolerance: int = 15) -> bool:
    """Return whether two window rectangles occupy the same screen region."""

    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    return all(abs(a - b) <= tolerance for a, b in zip(first, second, strict=True))


def point_in_swap_corner(point: Point, rect: Rect, corner_size: int = 100) -> bool:
    """Return whether a point is inside the rectangle's bottom-right hot zone."""

    if corner_size <= 0:
        raise ValueError("corner_size must be positive")
    x, y = point
    left, top, right, bottom = rect
    if right <= left or bottom <= top:
        return False
    return (
        max(left, right - corner_size) <= x <= right
        and max(top, bottom - corner_size) <= y <= bottom
    )


def next_window_in_z_order(handles: Iterable[int]) -> int | None:
    """Select the first distinct window immediately below the foreground one."""

    unique: list[int] = []
    for handle in handles:
        if handle and handle not in unique:
            unique.append(handle)
    return unique[1] if len(unique) > 1 else None


def popup_geometry(
    rect: Rect, width: int, height: int, margin: int = 20
) -> str:
    """Return a valid Tk position that stays inside the target window region."""

    if width <= 0 or height <= 0:
        raise ValueError("popup dimensions must be positive")
    if margin < 0:
        raise ValueError("margin must be non-negative")

    left, top, right, bottom = rect
    x = max(left, right - width - margin)
    y = max(top, bottom - height - margin)
    return f"{x:+d}{y:+d}"

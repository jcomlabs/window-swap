"""Invoke Window Swap's shipped selection path for the sanitized recording."""

from __future__ import annotations

import win32gui

from window_swap_core import rects_match
from window_swapper import WindowSwapApp, get_visible_windows


def main() -> None:
    demo_windows = [
        item
        for item in get_visible_windows()
        if item[0]
        and item[1]
        and win32gui.GetWindowText(item[0]).startswith("Window Swap Demo - ")
    ]
    if len(demo_windows) != 2:
        raise RuntimeError(f"Expected exactly two demo windows, found {len(demo_windows)}")
    if not rects_match(demo_windows[0][1], demo_windows[1][1]):
        raise RuntimeError("Demo windows do not share the same region")

    app = WindowSwapApp.__new__(WindowSwapApp)
    app.current_stack = demo_windows
    app.swap()


if __name__ == "__main__":
    main()

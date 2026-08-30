from __future__ import annotations

import uuid
from pathlib import Path
from types import SimpleNamespace

import window_swapper
from window_swap_settings import AppSettings
from window_swapper import (
    acquire_instance_mutex,
    is_startup_enabled,
    release_instance_mutex,
    set_startup_enabled,
    startup_shortcut_paths,
)


def test_instance_mutex_rejects_a_second_instance() -> None:
    name = rf"Local\JCOMLabs.WindowSwap.Tests.{uuid.uuid4()}"
    first = acquire_instance_mutex(name)
    assert first is not None
    try:
        assert acquire_instance_mutex(name) is None
    finally:
        release_instance_mutex(first)

    replacement = acquire_instance_mutex(name)
    assert replacement is not None
    release_instance_mutex(replacement)


def test_legacy_startup_shortcut_is_recognized_and_removed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    canonical, legacy = startup_shortcut_paths()
    legacy.parent.mkdir(parents=True)
    legacy.touch()
    assert is_startup_enabled()

    set_startup_enabled(False)
    assert not canonical.exists()
    assert not legacy.exists()
    assert not is_startup_enabled()


def test_swap_uses_the_live_z_order_before_changing_focus(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    app.current_stack = [(10, (0, 0, 500, 500)), (20, (0, 0, 500, 500))]
    app.current_rect = (0, 0, 500, 500)
    foreground: list[int] = []
    app.set_foreground = foreground.append
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [(10, (0, 0, 500, 500)), (20, (0, 0, 500, 500))],
    )

    app.swap()

    assert foreground == [20]


def test_swap_keeps_working_when_a_live_window_adjusts_its_bounds(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    detected_rect = (0, 0, 500, 500)
    app.current_stack = [(10, detected_rect), (20, detected_rect)]
    app.current_rect = detected_rect
    foreground: list[int] = []
    app.set_foreground = foreground.append
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [
            (10, (0, 0, 500, 500)),
            (20, (24, 0, 524, 500)),
        ],
    )

    app.swap()

    assert foreground == [20]


def test_repeated_clicks_continue_cycling_the_visible_stack(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    rect = (0, 0, 500, 500)
    app.current_stack = [(10, rect), (20, rect)]
    app.current_rect = rect
    order = [[(10, rect), (20, rect)]]
    foreground: list[int] = []

    def set_foreground(hwnd: int) -> None:
        foreground.append(hwnd)
        order[0] = [(hwnd, rect), (10 if hwnd == 20 else 20, rect)]

    app.set_foreground = set_foreground
    monkeypatch.setattr(window_swapper, "get_visible_windows", lambda: order[0])

    app.swap()
    app.swap()

    assert foreground == [20, 10]


def test_default_trigger_shows_on_the_first_eligible_inspection(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    rect = (0, 0, 500, 500)
    shown: list[tuple[tuple[int, int, int, int], list[tuple[int, tuple[int, int, int, int]]]]] = []
    app.root = SimpleNamespace(frame=lambda: "0x999")
    app.settings = AppSettings()
    app.is_button_visible = False
    app.candidate_key = None
    app.candidate_since = 0.0
    app.current_stack = []
    app.current_rect = None
    app.pointer_over_button = lambda _x, _y: False
    app.hide_button = lambda **_kwargs: None
    app.show_button = lambda target_rect, stack: shown.append((target_rect, stack))
    monkeypatch.setattr(window_swapper.win32api, "GetCursorPos", lambda: (495, 495))
    monkeypatch.setattr(window_swapper.win32gui, "WindowFromPoint", lambda _point: 10)
    monkeypatch.setattr(
        window_swapper.win32gui,
        "GetAncestor",
        lambda hwnd, _flag: hwnd,
    )
    monkeypatch.setattr(window_swapper.win32gui, "GetWindowRect", lambda _hwnd: rect)
    monkeypatch.setattr(window_swapper.win32gui, "IsWindowVisible", lambda _hwnd: True)
    monkeypatch.setattr(window_swapper.win32gui, "IsIconic", lambda _hwnd: False)
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [(10, rect), (20, rect)],
    )

    app.inspect_pointer(100.0)

    assert shown == [(rect, [(10, rect), (20, rect)])]

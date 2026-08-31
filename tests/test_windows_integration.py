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


def test_swap_starts_with_the_window_below_the_detected_top(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    app.current_stack = [(10, (0, 0, 500, 500)), (20, (0, 0, 500, 500))]
    app.current_rect = (0, 0, 500, 500)
    app.cycle_handles = [10, 20]
    app.cycle_cursor = 10
    foreground: list[int] = []

    def set_foreground(hwnd: int) -> bool:
        foreground.append(hwnd)
        return True

    app.set_foreground = set_foreground
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
    app.cycle_handles = [10, 20]
    app.cycle_cursor = 10
    foreground: list[int] = []

    def set_foreground(hwnd: int) -> bool:
        foreground.append(hwnd)
        return True

    app.set_foreground = set_foreground
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
    app.cycle_handles = [10, 20]
    app.cycle_cursor = 10
    order = [[(10, rect), (20, rect)]]
    foreground: list[int] = []

    def set_foreground(hwnd: int) -> bool:
        foreground.append(hwnd)
        order[0] = [(hwnd, rect), (10 if hwnd == 20 else 20, rect)]
        return True

    app.set_foreground = set_foreground
    monkeypatch.setattr(window_swapper, "get_visible_windows", lambda: order[0])

    app.swap()
    app.swap()

    assert foreground == [20, 10]


def test_repeated_clicks_cycle_all_three_windows_despite_live_z_order(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    rect = (0, 0, 500, 500)
    app.current_stack = [(10, rect), (20, rect), (30, rect)]
    app.current_rect = rect
    app.cycle_handles = [10, 20, 30]
    app.cycle_cursor = 10
    order = [[(10, rect), (20, rect), (30, rect)]]
    foreground: list[int] = []

    def set_foreground(hwnd: int) -> bool:
        foreground.append(hwnd)
        order[0] = [
            next(item for item in order[0] if item[0] == hwnd),
            *(item for item in order[0] if item[0] != hwnd),
        ]
        return True

    app.set_foreground = set_foreground
    monkeypatch.setattr(window_swapper, "get_visible_windows", lambda: order[0])

    app.swap()
    app.swap()
    app.swap()
    app.swap()

    assert foreground == [20, 30, 10, 20]


def test_cycle_skips_a_window_that_is_no_longer_available(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    rect = (0, 0, 500, 500)
    app.current_stack = [(10, rect), (20, rect), (30, rect)]
    app.current_rect = rect
    app.cycle_handles = [10, 20, 30]
    app.cycle_cursor = 10
    foreground: list[int] = []

    def set_foreground(hwnd: int) -> bool:
        foreground.append(hwnd)
        return True

    app.set_foreground = set_foreground
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [(10, rect), (30, rect)],
    )

    app.swap()

    assert foreground == [30]


def test_cycle_retries_a_window_when_focus_change_is_refused(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    rect = (0, 0, 500, 500)
    app.current_stack = [(10, rect), (20, rect), (30, rect)]
    app.current_rect = rect
    app.cycle_handles = [10, 20, 30]
    app.cycle_cursor = 10
    foreground: list[int] = []

    def refuse_foreground(hwnd: int) -> bool:
        foreground.append(hwnd)
        return False

    app.set_foreground = refuse_foreground
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [(10, rect), (20, rect), (30, rect)],
    )

    app.swap()
    app.swap()

    assert foreground == [20, 20]
    assert app.cycle_cursor == 10


def test_cycle_uses_live_top_as_anchor_when_its_cursor_disappears(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    rect = (0, 0, 500, 500)
    app.current_stack = [(10, rect), (20, rect), (30, rect)]
    app.current_rect = rect
    app.cycle_handles = [10, 20, 30]
    app.cycle_cursor = 20
    foreground: list[int] = []

    def set_foreground(hwnd: int) -> bool:
        foreground.append(hwnd)
        return True

    app.set_foreground = set_foreground
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [(10, rect), (30, rect)],
    )

    app.swap()

    assert foreground == [30]
    assert app.cycle_cursor == 30


def test_cycle_hides_when_fewer_than_two_windows_remain(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    rect = (0, 0, 500, 500)
    app.current_stack = [(10, rect), (20, rect)]
    app.current_rect = rect
    app.cycle_handles = [10, 20]
    app.cycle_cursor = 10
    hidden: list[bool] = []
    app.hide_button = lambda *, reset_candidate: hidden.append(reset_candidate)
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [(10, rect)],
    )

    app.swap()

    assert hidden == [True]


def test_show_button_preserves_cycle_order_when_z_order_changes() -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    rect = (0, 0, 500, 500)
    app.settings = AppSettings()
    app.text = window_swapper.STRINGS["en"]
    app.button = SimpleNamespace(configure=lambda **_kwargs: None)
    app.root = SimpleNamespace(
        update_idletasks=lambda: None,
        winfo_reqwidth=lambda: 90,
        winfo_reqheight=lambda: 30,
        geometry=lambda _geometry: None,
        deiconify=lambda: None,
        attributes=lambda *_args: None,
    )
    app.is_button_visible = False
    app.current_stack = []
    app.current_rect = None
    app.cycle_handles = []
    app.cycle_cursor = None

    app.show_button(rect, [(10, rect), (20, rect), (30, rect)])
    app.cycle_cursor = 20
    app.show_button(rect, [(20, rect), (10, rect), (30, rect)])

    assert app.cycle_handles == [10, 20, 30]
    assert app.cycle_cursor == 20

    app.show_button(rect, [(20, rect), (40, rect)])

    assert app.cycle_handles == [20, 40]
    assert app.cycle_cursor == 20


def test_hide_button_resets_the_active_cycle() -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    app.is_button_visible = False
    app.current_stack = [(10, (0, 0, 500, 500)), (20, (0, 0, 500, 500))]
    app.current_rect = (0, 0, 500, 500)
    app.cycle_handles = [10, 20]
    app.cycle_cursor = 20
    app.candidate_key = (10, (0, 0, 500, 500))
    app.candidate_since = 100.0

    app.hide_button(reset_candidate=True)

    assert app.current_stack == []
    assert app.current_rect is None
    assert app.cycle_handles == []
    assert app.cycle_cursor is None
    assert app.candidate_key is None
    assert app.candidate_since == 0.0


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
    app.cycle_handles = []
    app.cycle_cursor = None
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

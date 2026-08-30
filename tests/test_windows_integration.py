from __future__ import annotations

import uuid
from pathlib import Path

import window_swapper
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


def test_candidate_filter_does_not_read_window_titles(monkeypatch) -> None:
    monkeypatch.setattr(window_swapper.win32gui, "IsWindowVisible", lambda _hwnd: True)
    monkeypatch.setattr(window_swapper.win32gui, "IsIconic", lambda _hwnd: False)
    monkeypatch.setattr(window_swapper, "get_shell_window", lambda: 1)
    monkeypatch.setattr(window_swapper.win32gui, "GetWindowLong", lambda _hwnd, _index: 0)
    monkeypatch.setattr(
        window_swapper.win32gui,
        "GetWindowRect",
        lambda _hwnd: (0, 0, 100, 100),
    )
    monkeypatch.setattr(window_swapper, "is_window_cloaked", lambda _hwnd: False)
    monkeypatch.setattr(
        window_swapper.win32gui,
        "GetWindowText",
        lambda _hwnd: (_ for _ in ()).throw(AssertionError("title was read")),
    )
    assert window_swapper.is_candidate_window(2)


def test_swap_revalidates_the_stack_before_changing_focus(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    app.current_stack = [(10, (0, 0, 500, 500)), (20, (0, 0, 500, 500))]
    app.current_rect = (0, 0, 500, 500)
    app.cooldown_until = 0.0
    foreground: list[int] = []
    app.set_foreground = foreground.append
    app.hide_button = lambda **_kwargs: None
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [(10, (0, 0, 500, 500)), (20, (0, 0, 500, 500))],
    )

    app.swap()

    assert foreground == [20]
    assert app.cooldown_until > 0


def test_swap_ignores_windows_that_moved_out_of_the_stack(monkeypatch) -> None:
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    app.current_stack = [(10, (0, 0, 500, 500)), (20, (0, 0, 500, 500))]
    app.current_rect = (0, 0, 500, 500)
    app.cooldown_until = 0.0
    foreground: list[int] = []
    app.set_foreground = foreground.append
    app.hide_button = lambda **_kwargs: None
    monkeypatch.setattr(
        window_swapper,
        "get_visible_windows",
        lambda: [(10, (0, 0, 500, 500)), (20, (600, 0, 1100, 500))],
    )

    app.swap()

    assert foreground == []

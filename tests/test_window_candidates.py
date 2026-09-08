from __future__ import annotations

from types import SimpleNamespace

import pytest

import window_swapper
from window_swap_settings import AppSettings

RECT = (0, 0, 500, 500)


def fake_desktop(monkeypatch, styles: dict[int, int]) -> None:
    """Simulate distinct same-title windows without inspecting the real desktop."""

    def enumerate_windows(callback, output) -> None:
        for hwnd in styles:
            if callback(hwnd, output) is False:
                break

    monkeypatch.setattr(window_swapper.win32gui, "EnumWindows", enumerate_windows)
    monkeypatch.setattr(window_swapper.win32gui, "IsWindowVisible", lambda _hwnd: True)
    monkeypatch.setattr(window_swapper.win32gui, "IsIconic", lambda _hwnd: False)
    monkeypatch.setattr(window_swapper.win32gui, "GetWindowText", lambda _hwnd: "Example app")
    monkeypatch.setattr(window_swapper.win32gui, "GetWindowRect", lambda _hwnd: RECT)
    monkeypatch.setattr(
        window_swapper.win32gui,
        "GetWindowLong",
        lambda hwnd, _index: styles[hwnd],
    )


def fake_app():
    app = window_swapper.WindowSwapApp.__new__(window_swapper.WindowSwapApp)
    labels: list[str] = []
    app.settings = AppSettings()
    app.text = window_swapper.STRINGS["en"]
    app.button = SimpleNamespace(configure=lambda **kwargs: labels.append(kwargs["text"]))
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
    return app, labels


def test_nonactivating_helper_does_not_count_or_consume_the_first_click(monkeypatch) -> None:
    fake_desktop(
        monkeypatch,
        {
            10: 0,
            20: window_swapper.win32con.WS_EX_NOACTIVATE | window_swapper.win32con.WS_EX_TOOLWINDOW,
            30: 0,
        },
    )
    app, labels = fake_app()
    activated: list[int] = []

    def activate(hwnd: int) -> bool:
        activated.append(hwnd)
        return True

    app.set_foreground = activate
    app.show_button(RECT, window_swapper.get_visible_windows())
    app.swap()

    assert labels == [app.button_text(2)]
    assert app.cycle_handles == [10, 30]
    assert activated == [30]


def test_three_distinct_same_title_windows_still_cycle_in_full(monkeypatch) -> None:
    fake_desktop(monkeypatch, {10: 0, 20: 0, 30: 0})
    app, labels = fake_app()
    activated: list[int] = []

    def activate(hwnd: int) -> bool:
        activated.append(hwnd)
        return True

    app.set_foreground = activate
    app.show_button(RECT, window_swapper.get_visible_windows())
    for _ in range(4):
        app.swap()

    assert labels == [app.button_text(3)]
    assert activated == [20, 30, 10, 20]


@pytest.mark.parametrize(
    "style",
    [
        window_swapper.win32con.WS_EX_TOOLWINDOW,
        window_swapper.win32con.WS_EX_NOACTIVATE | window_swapper.win32con.WS_EX_APPWINDOW,
        window_swapper.win32con.WS_EX_NOACTIVATE
        | window_swapper.win32con.WS_EX_APPWINDOW
        | window_swapper.win32con.WS_EX_TOOLWINDOW,
    ],
)
def test_activating_tools_and_explicit_task_windows_are_preserved(monkeypatch, style) -> None:
    fake_desktop(monkeypatch, {10: 0, 20: style})

    assert window_swapper.get_visible_windows() == [(10, RECT), (20, RECT)]


def test_nonactivating_window_without_a_taskbar_override_is_excluded(monkeypatch) -> None:
    fake_desktop(monkeypatch, {10: 0, 20: window_swapper.win32con.WS_EX_NOACTIVATE})

    assert window_swapper.get_visible_windows() == [(10, RECT)]


@pytest.mark.parametrize(
    "failing_call",
    ["IsWindowVisible", "IsIconic", "GetWindowText", "GetWindowLong", "GetWindowRect"],
)
def test_one_window_closing_during_enumeration_does_not_drop_the_others(
    monkeypatch,
    failing_call,
) -> None:
    fake_desktop(monkeypatch, {10: 0, 20: 0, 30: 0})
    original = getattr(window_swapper.win32gui, failing_call)

    def read_window(hwnd: int, *args):
        if hwnd == 20:
            raise window_swapper.win32gui.error(1400, failing_call, "Invalid window handle")
        return original(hwnd, *args)

    monkeypatch.setattr(window_swapper.win32gui, failing_call, read_window)

    assert window_swapper.get_visible_windows() == [(10, RECT), (30, RECT)]

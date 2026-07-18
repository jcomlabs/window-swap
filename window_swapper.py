"""Window Swap: cycle through snapped windows that share a screen region."""

from __future__ import annotations

import ctypes
import locale
import logging
import os
import sys
import threading
import tkinter as tk
from ctypes import wintypes
from pathlib import Path

import pystray
import win32api
import win32con
import win32gui
from PIL import Image, ImageDraw, ImageFont

from window_swap_core import (
    next_window_in_z_order,
    point_in_swap_corner,
    popup_geometry,
    rects_match,
)

LOGGER = logging.getLogger(__name__)

TOLERANCE = 15
CORNER_SIZE = 100
APP_NAME = "WindowSwap"
INSTANCE_MUTEX_NAME = r"Local\JCOMLabs.WindowSwap"
ERROR_ALREADY_EXISTS = 183

STRINGS = {
    "en": {
        "swap": "Swap",
        "enabled": "Enabled",
        "startup": "Start with Windows",
        "exit": "Exit",
        "active_title": "Window Swap (enabled)",
        "inactive_title": "Window Swap (disabled)",
    },
    "pt": {
        "swap": "Trocar",
        "enabled": "Ativo",
        "startup": "Arrancar com o Windows",
        "exit": "Sair",
        "active_title": "Window Swap (ativo)",
        "inactive_title": "Window Swap (inativo)",
    },
}


def configure_logging() -> None:
    """Enable opt-in diagnostics without logging window titles or contents."""

    log_path = os.environ.get("WINDOW_SWAP_LOG", "").strip()
    if not log_path:
        return
    try:
        handler = logging.FileHandler(Path(log_path).expanduser(), encoding="utf-8")
    except OSError:
        return
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.DEBUG)


def acquire_instance_mutex(name: str = INSTANCE_MUTEX_NAME) -> int | None:
    """Acquire the per-session mutex, or return None when already running."""

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.CreateMutexW(None, False, name)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.CloseHandle(handle)
        return None
    return int(handle)


def release_instance_mutex(handle: int) -> None:
    """Release a mutex handle returned by acquire_instance_mutex."""

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.restype = wintypes.BOOL
    if not kernel32.CloseHandle(handle):
        raise ctypes.WinError(ctypes.get_last_error())


def detect_language() -> str:
    override = os.environ.get("WINDOW_SWAP_LANGUAGE", "").strip().lower()
    if override in STRINGS:
        return override
    language = locale.getlocale()[0] or ""
    return "pt" if language.lower().startswith("pt") else "en"


def set_dpi_awareness() -> None:
    """Use physical pixels so Tk and Win32 agree on multi-monitor geometry."""

    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            LOGGER.debug("Per-monitor DPI awareness is unavailable", exc_info=True)


def get_visible_windows() -> list[tuple[int, tuple[int, int, int, int]]]:
    windows: list[tuple[int, tuple[int, int, int, int]]] = []

    def callback(hwnd: int, output: list[tuple[int, tuple[int, int, int, int]]]) -> bool:
        if win32gui.IsWindowVisible(hwnd) and not win32gui.IsIconic(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title != "Program Manager":
                rect = win32gui.GetWindowRect(hwnd)
                if rect[2] > rect[0] and rect[3] > rect[1]:
                    output.append((hwnd, rect))
        return True

    win32gui.EnumWindows(callback, windows)
    return windows


class WindowSwapApp:
    def __init__(self, language: str | None = None) -> None:
        self.language = language or detect_language()
        self.text = STRINGS[self.language]
        self.root = tk.Tk()
        self.root.title("Window Swap")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        self.button = tk.Button(
            self.root,
            text=f"⇄ {self.text['swap']}",
            bg="#202020",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            padx=10,
            pady=5,
            activebackground="#404040",
            activeforeground="white",
            cursor="hand2",
            command=self.swap,
        )
        self.button.pack(fill=tk.BOTH, expand=True)
        self.root.withdraw()

        self.current_stack: list[tuple[int, tuple[int, int, int, int]]] = []
        self.is_button_visible = False
        self.enabled = True
        LOGGER.debug("Window Swap initialized")
        self.check_loop()

    def toggle_enabled(self) -> bool:
        self.enabled = not self.enabled
        if not self.enabled:
            self.hide_button()
        return self.enabled

    def hide_button(self) -> None:
        if self.is_button_visible:
            self.root.withdraw()
            self.is_button_visible = False

    def set_foreground(self, hwnd: int) -> None:
        """Ask Windows to activate a selected existing top-level window."""

        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # A short ALT transition lets Windows honor a user-initiated focus change.
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            LOGGER.debug("Windows refused a foreground transition", exc_info=True)

    def swap(self) -> None:
        if len(self.current_stack) < 2:
            return

        stack_members = {handle for handle, _ in self.current_stack}
        ordered_handles = [
            handle for handle, _ in get_visible_windows() if handle in stack_members
        ]
        next_handle = next_window_in_z_order(ordered_handles)
        if next_handle is not None:
            self.set_foreground(next_handle)

    def check_loop(self) -> None:
        if not self.enabled:
            self.hide_button()
            self.root.after(100, self.check_loop)
            return

        try:
            x, y = win32api.GetCursorPos()

            if self.is_button_visible:
                button_rect = (
                    self.root.winfo_x(),
                    self.root.winfo_y(),
                    self.root.winfo_x() + self.root.winfo_width(),
                    self.root.winfo_y() + self.root.winfo_height(),
                )
                if button_rect[0] <= x <= button_rect[2] and button_rect[1] <= y <= button_rect[3]:
                    self.root.after(100, self.check_loop)
                    return

            hwnd = win32gui.GetAncestor(
                win32gui.WindowFromPoint((x, y)), win32con.GA_ROOT
            )
            own_hwnd = int(self.root.frame(), 16)
            if not hwnd or hwnd == own_hwnd:
                self.hide_button()
            else:
                rect = win32gui.GetWindowRect(hwnd)
                in_corner = point_in_swap_corner((x, y), rect, CORNER_SIZE)
                eligible = (
                    in_corner
                    and win32gui.IsWindowVisible(hwnd)
                    and not win32gui.IsIconic(hwnd)
                )
                if eligible:
                    stack = [
                        (handle, candidate_rect)
                        for handle, candidate_rect in get_visible_windows()
                        if rects_match(rect, candidate_rect, TOLERANCE)
                    ]
                    if len(stack) > 1:
                        self.current_stack = stack
                        if not self.is_button_visible:
                            self.root.update_idletasks()
                            width = self.root.winfo_reqwidth()
                            height = self.root.winfo_reqheight()
                            self.root.geometry(popup_geometry(rect, width, height))
                            self.root.deiconify()
                            self.root.attributes("-topmost", True)
                            self.is_button_visible = True
                            LOGGER.debug("Swap button shown")
                    else:
                        self.hide_button()
                else:
                    self.hide_button()
        except Exception:
            self.hide_button()
            LOGGER.debug("Desktop inspection failed", exc_info=True)

        self.root.after(100, self.check_loop)


def create_icon_image(enabled: bool = True) -> Image.Image:
    width = height = 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    background = "#202020" if enabled else "#404040"
    border = "#0078D7" if enabled else "#888888"
    foreground = "white" if enabled else "#A0A0A0"
    draw.rounded_rectangle((7, 7, 57, 57), radius=10, fill=background, outline=border, width=4)

    try:
        font = ImageFont.truetype("segoeui.ttf", 34)
    except OSError:
        font = ImageFont.load_default()
    text = "W"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        ((width - text_width) // 2, (height - text_height) // 2 - 4),
        text,
        fill=foreground,
        font=font,
    )
    return image


def startup_shortcut_path() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is unavailable; cannot manage Windows startup")
    return Path(appdata) / "Microsoft/Windows/Start Menu/Programs/Startup/WindowSwap.lnk"


def is_startup_enabled() -> bool:
    try:
        return startup_shortcut_path().is_file()
    except RuntimeError:
        return False


def set_startup_enabled(enabled: bool) -> None:
    shortcut_path = startup_shortcut_path()
    if not enabled:
        shortcut_path.unlink(missing_ok=True)
        return

    import win32com.client

    shortcut_path.parent.mkdir(parents=True, exist_ok=True)
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = sys.executable
    if getattr(sys, "frozen", False):
        shortcut.Arguments = ""
        shortcut.WorkingDirectory = str(Path(sys.executable).parent)
    else:
        script_path = Path(__file__).resolve()
        shortcut.Arguments = f'"{script_path}"'
        shortcut.WorkingDirectory = str(script_path.parent)
    shortcut.IconLocation = sys.executable
    shortcut.save()


def run_tray(app: WindowSwapApp) -> pystray.Icon:
    def toggle_active(icon: pystray.Icon, _item: pystray.MenuItem | None = None) -> None:
        enabled = app.toggle_enabled()
        icon.icon = create_icon_image(enabled)
        icon.title = app.text["active_title"] if enabled else app.text["inactive_title"]

    def toggle_startup(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        try:
            set_startup_enabled(not is_startup_enabled())
        except Exception:
            LOGGER.exception("Unable to update the Startup-folder shortcut")

    def stop(icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        icon.stop()
        app.root.after(0, app.root.quit)

    menu = pystray.Menu(
        pystray.MenuItem(
            app.text["enabled"],
            toggle_active,
            checked=lambda _item: app.enabled,
            default=True,
        ),
        pystray.MenuItem(
            app.text["startup"],
            toggle_startup,
            checked=lambda _item: is_startup_enabled(),
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(app.text["exit"], stop),
    )
    icon = pystray.Icon(
        APP_NAME,
        create_icon_image(True),
        app.text["active_title"],
        menu=menu,
    )
    threading.Thread(target=icon.run, daemon=True, name="window-swap-tray").start()
    return icon


def main() -> None:
    configure_logging()
    mutex = acquire_instance_mutex()
    if mutex is None:
        LOGGER.debug("Another Window Swap instance is already running")
        return
    try:
        set_dpi_awareness()
        app = WindowSwapApp()
        run_tray(app)
        app.root.mainloop()
    finally:
        release_instance_mutex(mutex)


if __name__ == "__main__":
    main()

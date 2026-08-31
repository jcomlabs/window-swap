"""Window Swap: cycle through snapped windows that share a screen region."""

from __future__ import annotations

import ctypes
import locale
import logging
import os
import queue
import sys
import threading
import time
import tkinter as tk
from collections.abc import Callable
from ctypes import wintypes
from pathlib import Path
from tkinter import ttk

import pystray
import win32api
import win32con
import win32gui
from PIL import Image, ImageDraw, ImageFont

from window_swap_core import (
    point_in_swap_corner,
    popup_geometry,
    rects_match,
)
from window_swap_settings import (
    ALLOWED_TRIGGER_DELAYS_MS,
    AppSettings,
    load_settings,
    save_settings,
)

LOGGER = logging.getLogger(__name__)

TOLERANCE = 15
CORNER_SIZE = 100
APP_NAME = "WindowSwap"
APP_VERSION = "1.2.0-beta.3"
INSTANCE_MUTEX_NAME = r"Local\JCOMLabs.WindowSwap"
ERROR_ALREADY_EXISTS = 183
CHECK_INTERVAL_MS = 80

STRINGS = {
    "en": {
        "swap": "Swap",
        "enabled": "Enabled",
        "startup": "Start with Windows",
        "settings": "Status and settings...",
        "exit": "Exit",
        "active_title": "Window Swap (enabled)",
        "inactive_title": "Window Swap (disabled)",
        "ready": "Ready",
        "paused": "Paused",
        "status_help": "Move the pointer to the bottom-right corner of stacked windows.",
        "trigger_delay": "Trigger delay",
        "instant": "Instant",
        "balanced": "Balanced (0.2 s)",
        "deliberate": "Deliberate (0.4 s)",
        "show_count": "Show the number of stacked windows",
        "privacy": "Local only · no telemetry · window titles are never logged",
        "close": "Close",
        "windows": "windows",
    },
    "pt": {
        "swap": "Trocar",
        "enabled": "Ativo",
        "startup": "Arrancar com o Windows",
        "settings": "Estado e definições...",
        "exit": "Sair",
        "active_title": "Window Swap (ativo)",
        "inactive_title": "Window Swap (inativo)",
        "ready": "Pronto",
        "paused": "Em pausa",
        "status_help": "Move o ponteiro para o canto inferior direito das janelas sobrepostas.",
        "trigger_delay": "Atraso de ativação",
        "instant": "Imediato",
        "balanced": "Equilibrado (0,2 s)",
        "deliberate": "Deliberado (0,4 s)",
        "show_count": "Mostrar o número de janelas sobrepostas",
        "privacy": "Apenas local · sem telemetria · nunca regista títulos de janelas",
        "close": "Fechar",
        "windows": "janelas",
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
    def __init__(
        self,
        language: str | None = None,
        settings: AppSettings | None = None,
    ) -> None:
        self.language = language or detect_language()
        self.text = STRINGS[self.language]
        self.settings = settings or load_settings()
        self.enabled = True
        self.current_stack: list[tuple[int, tuple[int, int, int, int]]] = []
        self.current_rect: tuple[int, int, int, int] | None = None
        self.cycle_handles: list[int] = []
        self.cycle_cursor: int | None = None
        self.is_button_visible = False
        self.candidate_key: tuple[int, tuple[int, int, int, int]] | None = None
        self.candidate_since = 0.0
        self.settings_window: tk.Toplevel | None = None
        self.ui_actions: queue.SimpleQueue[Callable[[], None]] = queue.SimpleQueue()

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
            padx=12,
            pady=6,
            activebackground="#303030",
            activeforeground="white",
            cursor="hand2",
            command=self.swap,
        )
        self.button.pack(fill=tk.BOTH, expand=True)
        self.root.update_idletasks()
        try:
            win32gui.SetWindowText(int(self.root.frame(), 16), "Window Swap action")
        except Exception:
            LOGGER.debug("Unable to set the overlay accessibility name", exc_info=True)
        self.root.withdraw()

        LOGGER.debug("Window Swap %s initialized", APP_VERSION)
        self.check_loop()

    def post(self, action: Callable[[], None]) -> None:
        """Queue work from tray callbacks for Tk's main thread."""

        self.ui_actions.put(action)

    def process_ui_actions(self) -> None:
        while True:
            try:
                action = self.ui_actions.get_nowait()
            except queue.Empty:
                return
            try:
                action()
            except Exception:
                LOGGER.exception("A queued UI action failed")

    def set_enabled(self, enabled: bool) -> bool:
        self.enabled = bool(enabled)
        if not self.enabled:
            self.hide_button(reset_candidate=True)
        self.refresh_settings_window()
        return self.enabled

    def toggle_enabled(self) -> bool:
        return self.set_enabled(not self.enabled)

    def hide_button(self, *, reset_candidate: bool = True) -> None:
        if self.is_button_visible:
            self.root.withdraw()
            self.is_button_visible = False
        self.current_stack = []
        self.current_rect = None
        self.cycle_handles = []
        self.cycle_cursor = None
        if reset_candidate:
            self.candidate_key = None
            self.candidate_since = 0.0

    def pointer_over_button(self, x: int, y: int) -> bool:
        if not self.is_button_visible:
            return False
        return (
            self.root.winfo_x() <= x <= self.root.winfo_x() + self.root.winfo_width()
            and self.root.winfo_y()
            <= y
            <= self.root.winfo_y() + self.root.winfo_height()
        )

    def set_foreground(self, hwnd: int) -> bool:
        """Ask Windows to activate a selected existing top-level window."""

        try:
            if not win32gui.IsWindow(hwnd):
                return False
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # A short ALT transition lets Windows honor a user-initiated focus change.
            win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32gui.SetForegroundWindow(hwnd)
            return win32gui.GetForegroundWindow() == hwnd
        except Exception:
            LOGGER.debug("Windows refused a foreground transition", exc_info=True)
            return False

    def swap(self) -> None:
        if len(self.cycle_handles) < 2:
            return

        live_order = [handle for handle, _ in get_visible_windows()]
        live_handles = set(live_order)
        cycle_members = set(self.cycle_handles)
        available_handles = [
            handle for handle in self.cycle_handles if handle in live_handles
        ]
        if len(available_handles) < 2:
            self.hide_button(reset_candidate=True)
            return

        if self.cycle_cursor not in live_handles:
            self.cycle_cursor = next(
                (
                    handle
                    for handle in live_order
                    if handle in cycle_members
                ),
                None,
            )
        if self.cycle_cursor not in self.cycle_handles:
            return

        cursor_index = self.cycle_handles.index(self.cycle_cursor)
        for offset in range(1, len(self.cycle_handles) + 1):
            next_handle = self.cycle_handles[
                (cursor_index + offset) % len(self.cycle_handles)
            ]
            if next_handle in live_handles:
                if self.set_foreground(next_handle):
                    self.cycle_cursor = next_handle
                return

    def button_text(self, stack_size: int) -> str:
        label = f"⇄ {self.text['swap']}"
        if self.settings.show_stack_count:
            label += f"  ·  {stack_size}"
        return label

    def show_button(
        self,
        rect: tuple[int, int, int, int],
        stack: list[tuple[int, tuple[int, int, int, int]]],
    ) -> None:
        stack_handles = list(dict.fromkeys(handle for handle, _ in stack if handle))
        same_group = (
            self.is_button_visible
            and set(stack_handles) == set(self.cycle_handles)
            and self.current_rect is not None
            and rects_match(rect, self.current_rect, TOLERANCE)
        )
        if not same_group:
            self.cycle_handles = stack_handles
            self.cycle_cursor = stack_handles[0] if stack_handles else None
        self.current_stack = stack
        self.current_rect = rect
        self.button.configure(text=self.button_text(len(stack)))
        self.root.update_idletasks()
        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()
        self.root.geometry(popup_geometry(rect, width, height))
        if not self.is_button_visible:
            self.root.deiconify()
            self.root.attributes("-topmost", True)
            self.is_button_visible = True
            LOGGER.debug("Swap button shown for %d windows", len(stack))

    def inspect_pointer(self, now: float) -> None:
        x, y = win32api.GetCursorPos()
        if self.pointer_over_button(x, y):
            return
        hwnd = win32gui.GetAncestor(win32gui.WindowFromPoint((x, y)), win32con.GA_ROOT)
        own_hwnd = int(self.root.frame(), 16)
        if not hwnd or hwnd == own_hwnd:
            self.hide_button(reset_candidate=True)
            return

        rect = win32gui.GetWindowRect(hwnd)
        eligible = (
            point_in_swap_corner((x, y), rect, CORNER_SIZE)
            and win32gui.IsWindowVisible(hwnd)
            and not win32gui.IsIconic(hwnd)
        )
        if not eligible:
            self.hide_button(reset_candidate=True)
            return

        stack = [
            (handle, candidate_rect)
            for handle, candidate_rect in get_visible_windows()
            if rects_match(rect, candidate_rect, TOLERANCE)
        ]
        if len(stack) < 2:
            self.hide_button(reset_candidate=True)
            return

        candidate_key = (hwnd, rect)
        same_candidate = (
            self.candidate_key is not None
            and hwnd == self.candidate_key[0]
            and rects_match(rect, self.candidate_key[1], TOLERANCE)
        )
        if not same_candidate:
            self.hide_button(reset_candidate=False)
            self.candidate_key = candidate_key
            self.candidate_since = now

        elapsed_ms = (now - self.candidate_since) * 1000
        if elapsed_ms >= self.settings.trigger_delay_ms:
            self.show_button(rect, stack)

    def check_loop(self) -> None:
        self.process_ui_actions()
        if not self.enabled:
            self.hide_button(reset_candidate=True)
        else:
            try:
                self.inspect_pointer(time.monotonic())
            except Exception:
                self.hide_button(reset_candidate=True)
                LOGGER.debug("Desktop inspection failed", exc_info=True)
        self.root.after(CHECK_INTERVAL_MS, self.check_loop)

    def refresh_settings_window(self) -> None:
        window = self.settings_window
        if window is None or not window.winfo_exists():
            return
        status_var = getattr(window, "status_var", None)
        enabled_var = getattr(window, "enabled_var", None)
        startup_var = getattr(window, "startup_var", None)
        if status_var is not None:
            status_var.set(self.text["ready"] if self.enabled else self.text["paused"])
        if enabled_var is not None:
            enabled_var.set(self.enabled)
        if startup_var is not None:
            startup_var.set(is_startup_enabled())

    def update_settings(
        self,
        delay_ms: int,
        show_stack_count: bool,
    ) -> None:
        settings = AppSettings(
            trigger_delay_ms=delay_ms,
            show_stack_count=show_stack_count,
        )
        try:
            save_settings(settings)
        except (OSError, RuntimeError):
            LOGGER.exception("Unable to save Window Swap settings")
        self.settings = settings
        self.hide_button(reset_candidate=True)

    def show_settings(self) -> None:
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.deiconify()
            self.settings_window.lift()
            self.settings_window.focus_force()
            self.refresh_settings_window()
            return

        window = tk.Toplevel(self.root)
        self.settings_window = window
        window.title(f"Window Swap {APP_VERSION}")
        window.resizable(False, False)
        window.attributes("-topmost", True)
        window.protocol("WM_DELETE_WINDOW", window.withdraw)

        frame = ttk.Frame(window, padding=20)
        frame.grid(sticky="nsew")
        status_var = tk.StringVar()
        enabled_var = tk.BooleanVar(value=self.enabled)
        startup_var = tk.BooleanVar(value=is_startup_enabled())
        count_var = tk.BooleanVar(value=self.settings.show_stack_count)
        window.status_var = status_var
        window.enabled_var = enabled_var
        window.startup_var = startup_var

        ttk.Label(frame, text="Window Swap", font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(frame, textvariable=status_var, foreground="#0067c0").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )
        ttk.Label(frame, text=self.text["status_help"], wraplength=360).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 16)
        )
        ttk.Checkbutton(
            frame,
            text=self.text["enabled"],
            variable=enabled_var,
            command=lambda: self.set_enabled(enabled_var.get()),
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        def update_startup() -> None:
            try:
                set_startup_enabled(startup_var.get())
            except Exception:
                LOGGER.exception("Unable to update the Startup-folder shortcut")
            self.refresh_settings_window()

        ttk.Checkbutton(
            frame,
            text=self.text["startup"],
            variable=startup_var,
            command=update_startup,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Label(frame, text=self.text["trigger_delay"]).grid(
            row=5, column=0, sticky="w", pady=(14, 4)
        )
        delay_labels = {
            0: self.text["instant"],
            200: self.text["balanced"],
            400: self.text["deliberate"],
        }
        reverse_delays = {label: delay for delay, label in delay_labels.items()}
        delay_var = tk.StringVar(value=delay_labels[self.settings.trigger_delay_ms])
        delay_box = ttk.Combobox(
            frame,
            textvariable=delay_var,
            values=[delay_labels[value] for value in ALLOWED_TRIGGER_DELAYS_MS],
            state="readonly",
            width=24,
        )
        delay_box.grid(row=5, column=1, sticky="e", pady=(14, 4))

        def persist_settings(_event: object | None = None) -> None:
            self.update_settings(reverse_delays[delay_var.get()], count_var.get())

        delay_box.bind("<<ComboboxSelected>>", persist_settings)
        ttk.Checkbutton(
            frame,
            text=self.text["show_count"],
            variable=count_var,
            command=persist_settings,
        ).grid(row=6, column=0, columnspan=2, sticky="w", pady=4)
        ttk.Separator(frame).grid(row=7, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(frame, text=self.text["privacy"], foreground="#666666").grid(
            row=8, column=0, sticky="w"
        )
        ttk.Button(frame, text=self.text["close"], command=window.withdraw).grid(
            row=8, column=1, sticky="e"
        )
        self.refresh_settings_window()
        window.update_idletasks()
        width = window.winfo_reqwidth()
        height = window.winfo_reqheight()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        window.geometry(f"{width}x{height}+{max(0, screen_width - width - 40)}+{max(0, screen_height - height - 80)}")


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


def startup_shortcut_paths() -> tuple[Path, Path]:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is unavailable; cannot manage Windows startup")
    startup = Path(appdata) / "Microsoft/Windows/Start Menu/Programs/Startup"
    return startup / "WindowSwap.lnk", startup / "WindowSwapper.lnk"


def startup_shortcut_path() -> Path:
    """Return the canonical shortcut path kept for API compatibility."""

    return startup_shortcut_paths()[0]


def is_startup_enabled() -> bool:
    try:
        return any(path.is_file() for path in startup_shortcut_paths())
    except RuntimeError:
        return False


def set_startup_enabled(enabled: bool) -> None:
    shortcut_path, legacy_path = startup_shortcut_paths()
    if not enabled:
        for path in (shortcut_path, legacy_path):
            path.unlink(missing_ok=True)
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
    if legacy_path != shortcut_path:
        legacy_path.unlink(missing_ok=True)


def run_tray(app: WindowSwapApp) -> pystray.Icon:
    def toggle_active(icon: pystray.Icon, _item: pystray.MenuItem | None = None) -> None:
        def apply_toggle() -> None:
            enabled = app.toggle_enabled()
            icon.icon = create_icon_image(enabled)
            icon.title = (
                app.text["active_title"] if enabled else app.text["inactive_title"]
            )

        app.post(apply_toggle)

    def toggle_startup(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        try:
            set_startup_enabled(not is_startup_enabled())
        except Exception:
            LOGGER.exception("Unable to update the Startup-folder shortcut")
        app.post(app.refresh_settings_window)

    def show_settings(_icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        app.post(app.show_settings)

    def stop(icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        icon.stop()
        app.post(app.root.quit)

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
        pystray.MenuItem(app.text["settings"], show_settings),
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
        if "--settings" in sys.argv[1:]:
            app.root.after(100, app.show_settings)
        app.root.mainloop()
    finally:
        release_instance_mutex(mutex)


if __name__ == "__main__":
    main()

"""Open two harmless overlapping windows for a repeatable manual smoke test."""

from __future__ import annotations

import tkinter as tk


def configure(window: tk.Toplevel | tk.Tk, number: int, color: str) -> None:
    window.title(f"Window Swap test {number}")
    window.geometry("640x480+120+120")
    window.configure(bg=color)
    tk.Label(
        window,
        text=f"Test window {number}",
        bg=color,
        fg="white",
        font=("Segoe UI", 24, "bold"),
    ).pack(expand=True)
    tk.Label(
        window,
        text="Move to the bottom-right corner, then select Swap.",
        bg=color,
        fg="white",
        font=("Segoe UI", 11),
    ).pack(pady=(0, 40))


def main() -> None:
    first = tk.Tk()
    configure(first, 1, "#2457a6")
    second = tk.Toplevel(first)
    configure(second, 2, "#7a3fa0")
    second.lift()
    first.mainloop()


if __name__ == "__main__":
    main()

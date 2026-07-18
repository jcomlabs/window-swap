"""Disposable, content-safe windows used only to record the Build Week demo."""

from __future__ import annotations

import tkinter as tk


GEOMETRY = "1280x740+220+80"


def build_workspace(window: tk.Toplevel | tk.Tk, *, title: str, accent: str, label: str) -> None:
    window.title(title)
    window.geometry(GEOMETRY)
    window.minsize(900, 600)
    window.configure(bg="#08111f")

    header = tk.Frame(window, bg="#0d1b2f", height=86)
    header.pack(fill="x")
    header.pack_propagate(False)
    tk.Label(
        header,
        text="WINDOW SWAP · SAFE DEMO",
        fg="#9fb2cc",
        bg="#0d1b2f",
        font=("Segoe UI", 12, "bold"),
    ).pack(side="left", padx=34)
    tk.Label(
        header,
        text=label,
        fg="white",
        bg=accent,
        font=("Segoe UI", 13, "bold"),
        padx=20,
        pady=10,
    ).pack(side="right", padx=34, pady=20)

    body = tk.Frame(window, bg="#08111f")
    body.pack(fill="both", expand=True, padx=48, pady=44)
    tk.Label(
        body,
        text="Two windows.\nOne screen region.",
        justify="left",
        fg="white",
        bg="#08111f",
        font=("Segoe UI", 38, "bold"),
    ).pack(anchor="w")
    tk.Label(
        body,
        text="Move to the corner. Select Swap. Keep your spatial context.",
        justify="left",
        fg="#a9bbd1",
        bg="#08111f",
        font=("Segoe UI", 17),
    ).pack(anchor="w", pady=(20, 36))

    cards = tk.Frame(body, bg="#08111f")
    cards.pack(fill="x")
    for heading, value in (("REGION", "Right half"), ("ACTION", "Bottom-right"), ("RESULT", label)):
        card = tk.Frame(cards, bg="#10223b", highlightthickness=1, highlightbackground="#213a5d")
        card.pack(side="left", fill="both", expand=True, padx=(0, 16))
        tk.Label(card, text=heading, fg="#7892b5", bg="#10223b", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
        tk.Label(card, text=value, fg="white", bg="#10223b", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=22, pady=(0, 20))

    tk.Frame(window, bg=accent, height=8).pack(fill="x", side="bottom")


def main() -> None:
    root = tk.Tk()
    build_workspace(
        root,
        title="Window Swap Demo - Workspace A",
        accent="#2878ff",
        label="WORKSPACE A",
    )

    second = tk.Toplevel(root)
    build_workspace(
        second,
        title="Window Swap Demo - Workspace B",
        accent="#9b5cff",
        label="WORKSPACE B",
    )
    second.lift()
    second.focus_force()
    root.mainloop()


if __name__ == "__main__":
    main()

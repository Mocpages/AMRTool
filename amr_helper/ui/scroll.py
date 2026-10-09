from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def scrollable_frame(parent: tk.Widget) -> tuple[tk.Canvas, ttk.Frame]:
    canvas = tk.Canvas(parent, highlightthickness=0)
    scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
    inner = ttk.Frame(canvas)
    inner.bind(
        "<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    window = canvas.create_window((0, 0), window=inner, anchor=tk.NW)
    canvas.configure(yscrollcommand=scroll.set)
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    return canvas, inner

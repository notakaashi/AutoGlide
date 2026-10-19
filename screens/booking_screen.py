"""
screens/booking_screen.py
=============================================================================
New Booking screen (stub).
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox
import theme
import config
import database
import validators
from components import Card, SectionHeading, Button, MapPicker


class BookingScreen(tk.Frame):
    """Minimal booking screen placeholder (keeps imports working)."""

    def __init__(self, master, app, **kwargs):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Basic layout."""
        wrap = tk.Frame(self, bg=theme.BG_APP)
        wrap.pack(fill="both", expand=True, padx=theme.PAD_LG, pady=theme.PAD_MD)
        SectionHeading(wrap, title="New Booking",
                       subtitle="Start a 5-step booking flow").pack(
                           anchor="w", fill="x")
        card = Card(wrap)
        card.pack(fill="x", pady=(theme.PAD_MD, 0))
        body = card.body
        tk.Label(body, text="Booking wizard placeholder - to be built next.",
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        Button(body, text="Back to My Bookings",
               command=lambda: self._go("my_bookings"),
               variant="ghost").pack(anchor="w", pady=(theme.PAD_MD, 0))

    def _go(self, name):
        if hasattr(self.app, "shell") and hasattr(self.app.shell, "switch_view"):
            self.app.shell.switch_view(name)
        else:
            self.app.show_screen("shell")

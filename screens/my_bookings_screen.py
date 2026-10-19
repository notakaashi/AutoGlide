"""
screens/my_bookings_screen.py
=============================================================================
Client's booking list (stub).
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox
import theme
import config
import database
from components import Card, SectionHeading, Button, DataTable, StatusPill, MapPicker


class MyBookingsScreen(tk.Frame):
    """Shows the client's bookings in a simple table."""

    def __init__(self, master, app, **kwargs):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Basic layout."""
        wrap = tk.Frame(self, bg=theme.BG_APP)
        wrap.pack(fill="both", expand=True, padx=theme.PAD_LG, pady=theme.PAD_MD)
        SectionHeading(wrap, title="My Bookings",
                       subtitle="View your past and upcoming bookings").pack(
                           anchor="w", fill="x")
        self.card = Card(wrap)
        self.card.pack(fill="both", expand=True, pady=(theme.PAD_MD, 0))
        Button(wrap, text="New Booking",
               command=lambda: self.app.request_booking("wash_vacuum"),
               variant="primary").pack(anchor="w", pady=(theme.PAD_MD, 0))
        self._load()

    def _load(self):
        """Loads bookings into the table."""
        body = self.card.body
        columns = [
            {"key": "id", "title": "Booking #", "weight": 1, "minsize": 80},
            {"key": "booking_date", "title": "Date", "weight": 2, "minsize": 110},
            {"key": "time_slot", "title": "Time", "weight": 2, "minsize": 90},
            {"key": "tier_id", "title": "Package", "weight": 2, "minsize": 140},
            {"key": "status", "title": "Status", "weight": 1, "minsize": 110, "pill": True},
            {"key": "total_price", "title": "Total (\u20b1)", "weight": 1, "minsize": 110, "anchor": "e"},
        ]
        table = DataTable(body, columns)
        table.pack(fill="both", expand=True)
        user_id = self.app.current_user["id"]
        rows = []
        for row in database.get_bookings_by_user(user_id):
            rows.append({
                "id": row["id"],
                "booking_date": row["booking_date"],
                "time_slot": row["time_slot"],
                "tier_id": config.tier_name(row["tier_id"]),
                "status": row["status"],
                "total_price": row["total_price"]
            })
        table.set_rows(rows)

"""
screens/admin_screen.py
=============================================================================
Administrator panel (stub).
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox
import theme
import config
import database
import validators
from components import Card, SectionHeading, Button, DataTable, StatCard, MapPicker


class AdminScreen(tk.Frame):
    """Minimal admin screen placeholder."""

    def __init__(self, master, app, **kwargs):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Basic layout."""
        wrap = tk.Frame(self, bg=theme.BG_APP)
        wrap.pack(fill="both", expand=True, padx=theme.PAD_LG, pady=theme.PAD_MD)
        SectionHeading(wrap, title="Admin Dashboard",
                       subtitle="Overview of bookings and activity").pack(
                           anchor="w", fill="x")
        stats = tk.Frame(wrap, bg=theme.BG_APP)
        stats.pack(fill="x", pady=(theme.PAD_MD, 0))
        s = database.get_admin_stats()
        StatCard(stats, caption="Total Bookings", value=str(s.get("total", 0))).pack(
            side="left", fill="x", expand=True, padx=(0, theme.PAD_SM))
        StatCard(stats, caption="Pending", value=str(s.get("Pending", 0))).pack(
            side="left", fill="x", expand=True, padx=theme.PAD_SM)
        StatCard(stats, caption="Revenue (Completed)", value="₱" + str(s.get("revenue", 0))).pack(
            side="left", fill="x", expand=True, padx=(theme.PAD_SM, 0))

        card = Card(wrap)
        card.pack(fill="both", expand=True, pady=(theme.PAD_LG, 0))
        body = card.body
        SectionHeading(body, title="Recent Bookings").pack(anchor="w", fill="x")
        columns = [
            {"key": "id", "title": "Booking #", "weight": 1, "minsize": 80},
            {"key": "client_name", "title": "Client", "weight": 2, "minsize": 140},
            {"key": "booking_date", "title": "Date", "weight": 1, "minsize": 110},
            {"key": "time_slot", "title": "Time", "weight": 1, "minsize": 90},
            {"key": "status", "title": "Status", "weight": 1, "minsize": 110, "pill": True},
            {"key": "total_price", "title": "Total (₱)", "weight": 1, "minsize": 110, "anchor": "e"},
        ]
        table = DataTable(body, columns)
        table.pack(fill="both", expand=True, pady=(theme.PAD_SM, 0))
        rows = []
        for row in database.get_all_bookings()[:20]:
            rows.append({
                "id": row["id"],
                "client_name": row["client_name"] or row["user_id"],
                "booking_date": row["booking_date"],
                "time_slot": row["time_slot"],
                "status": row["status"],
                "total_price": row["total_price"]
            })
        table.set_rows(rows)

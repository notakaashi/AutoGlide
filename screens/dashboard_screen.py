"""
screens/dashboard_screen.py
=============================================================================
Client dashboard shown after a client logs in.
=============================================================================
"""

import tkinter as tk
import theme
import database
from components import Card, SectionHeading, Button, StatCard


class ClientDashboardScreen(tk.Frame):
    """A simple client dashboard inside the app shell."""

    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Builds the dashboard content."""
        wrap = tk.Frame(self, bg=theme.BG_APP)
        wrap.pack(fill="both", expand=True, padx=theme.PAD_LG, pady=theme.PAD_MD)
        SectionHeading(wrap, title="Dashboard",
                       subtitle="Quick actions and your activity").pack(
                           anchor="w", fill="x")

        stats = tk.Frame(wrap, bg=theme.BG_APP)
        stats.pack(fill="x", pady=(theme.PAD_MD, 0))
        total, upcoming = database.get_client_stats(self.app.current_user["id"])
        StatCard(stats, caption="Total Bookings", value=str(total)).pack(
            side="left", fill="x", expand=True, padx=(0, theme.PAD_SM))
        StatCard(stats, caption="Upcoming Bookings", value=str(upcoming)).pack(
            side="left", fill="x", expand=True, padx=(theme.PAD_SM, 0))

        actions = Card(wrap)
        actions.pack(fill="x", pady=(theme.PAD_LG, 0))
        body = actions.body
        SectionHeading(body, title="Quick Actions").pack(anchor="w")
        row = tk.Frame(body, bg=theme.BG_SURFACE)
        row.pack(fill="x", pady=(theme.PAD_SM, 0))
        Button(row, text="New Booking",
               command=lambda: self.app.request_booking("wash_vacuum"),
               variant="primary").pack(side="left")
        Button(row, text="My Bookings",
               command=lambda: self._go("my_bookings"),
               variant="ghost").pack(side="left", padx=theme.PAD_SM)

    def _go(self, name):
        """Switches the shell view when available."""
        if hasattr(self.app, "shell") and hasattr(self.app.shell, "switch_view"):
            self.app.shell.switch_view(name)
        else:
            self.app.show_screen("shell")

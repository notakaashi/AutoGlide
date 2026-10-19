"""
screens/client_home.py
=============================================================================
The client Home page: a friendly greeting, a status card for the next
upcoming booking (or a friendly nudge to book), quick action buttons, and
the shared marketing content underneath.
=============================================================================
"""

import datetime
import tkinter as tk

import theme
import config
import database

from components import Card, Button, StatusPill
from screens.landing_screen import MarketingContent


class HomeView(tk.Frame):
    """Client Home: greeting + upcoming booking card + marketing content."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = shell.current_user
        super().__init__(master, bg=theme.BG_APP)
        self._build()

    def _build(self):
        """Greeting, booking card or nudge, then the marketing sections."""
        top = tk.Frame(self, bg=theme.BG_APP)
        top.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))

        first_name = (self.user["full_name"] or "").split(" ")[0] or "there"
        tk.Label(top, text="Hi, " + first_name + "!",
                 font=theme.FONT_TITLE, fg=theme.TEXT,
                 bg=theme.BG_APP).pack(anchor="w")
        tk.Label(top, text=config.HOME_SUBTEXT, font=theme.FONT_BODY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_APP).pack(anchor="w")

        booking = database.get_next_booking(self.user["id"])
        card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_XL)
        card.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_MD)
        if booking is None:
            self._build_no_booking(card.body)
        else:
            self._build_booking_card(card.body, booking)

        actions = tk.Frame(self, bg=theme.BG_APP)
        actions.pack(fill="x", padx=theme.PAD_LG, pady=(0, theme.PAD_MD))
        Button(actions, text="Book a Detail", command=self._go_wizard,
               variant="primary").pack(side="left")
        Button(actions, text="See My Bookings", command=self._go_bookings,
               variant="ghost").pack(side="left", padx=theme.PAD_SM)

        MarketingContent(self, self.app,
                         vehicle_type=self.app.booking_draft["vehicle_type"])

    def _build_booking_card(self, body, booking):
        """Status card for the next upcoming booking."""
        tk.Label(body, text="Your next booking", font=theme.FONT_CARD_TITLE,
                 fg=theme.PRIMARY, bg=theme.BG_SURFACE).pack(anchor="w")
        row = tk.Frame(body, bg=theme.BG_SURFACE)
        row.pack(fill="x", pady=(theme.PAD_SM, 0))
        left = tk.Frame(row, bg=theme.BG_SURFACE)
        left.pack(side="left", fill="both", expand=True)
        tk.Label(left, text="#" + str(booking["id"]) + " - "
                 + config.tier_name(booking["tier_id"]),
                 font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        date_text = config.friendly_date(booking["booking_date"])
        tk.Label(left, text=date_text + "  -  " + booking["time_slot"]
                 + "  -  " + booking["address"],
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE, wraplength=500,
                 justify="left").pack(anchor="w", pady=(2, 0))
        StatusPill(row, booking["status"]).pack(side="right", padx=(10, 0))
        Button(body, text="View details", command=self._go_bookings,
               variant="ghost").pack(anchor="w", pady=(theme.PAD_SM, 0))

    def _build_no_booking(self, body):
        """Friendly block when the client has nothing scheduled."""
        tk.Label(body, text="Nothing scheduled yet",
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(body, text=config.HOME_EMPTY_TEXT, font=theme.FONT_BODY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE,
                 wraplength=500, justify="left").pack(anchor="w",
                                                      pady=(4, 0))

    def _go_wizard(self):
        """Opens the booking wizard."""
        self.shell.switch_view("new_booking")

    def _go_bookings(self):
        """Opens My Bookings."""
        self.shell.switch_view("my_bookings")

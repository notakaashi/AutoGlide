"""
screens/client_home.py
=============================================================================
The client Home page: a greeting row with quick actions and the next
booking card, then the same scrollable marketing page the guest landing
uses (screens/marketing.py). Photos never crash the app.
=============================================================================
"""

import tkinter as tk

import theme
import config
import database

from components import Card, Button, StatusPill, ScrollFrame, CenteredColumn
from screens.marketing import MarketingBody


class HomeView(tk.Frame):
    """Client Home: greeting + next booking card + marketing content."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = shell.current_user
        super().__init__(master, bg=theme.BG_APP)
        self._build()

    def _build(self):
        """Scrollable page: greeting row, booking card, marketing."""
        scroll = ScrollFrame(self, bg=theme.BG_APP)
        scroll.pack(fill="both", expand=True)
        page = scroll.inner
        self._build_top(page)
        MarketingBody(page, self.app, target_width=self._target_width())

    def _target_width(self):
        """Centers content to a width that fits the current window."""
        try:
            win = self.winfo_toplevel().winfo_width()
        except Exception:
            win = 0
        if win <= 1:
            win = 1280
        return max(880, min(1160, win - 2 * 56))

    # ------------------------------------------------------------------
    # GREETING ROW + NEXT BOOKING CARD
    # ------------------------------------------------------------------
    def _build_top(self, page):
        column = CenteredColumn(page, width=self._target_width())
        top = tk.Frame(column, bg=theme.BG_APP)
        top.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG,
                                                    theme.PAD_XS))

        left = tk.Frame(top, bg=theme.BG_APP)
        left.pack(side="left", fill="both", expand=True)
        first_name = (self.user["full_name"] or "").split(" ")[0] or "there"
        tk.Label(left, text="Good morning, " + first_name + ".",
                 font=theme.FONT_GREETING, fg=theme.TEXT,
                 bg=theme.BG_APP).pack(anchor="w")
        tk.Label(left, text=config.HOME_SUBTEXT, font=theme.FONT_BODY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_APP).pack(
                     anchor="w", pady=(4, theme.PAD_MD))
        actions = tk.Frame(left, bg=theme.BG_APP)
        actions.pack(anchor="w")
        Button(actions, text="Book a detail", command=self._go_wizard,
               variant="primary").pack(side="left")
        Button(actions, text="My bookings", command=self._go_bookings,
               variant="ghost").pack(side="left", padx=theme.PAD_SM)

        booking = database.get_next_booking(self.user["id"])
        card = Card(top, radius=theme.RADIUS_LG, pad=theme.PAD_LG, width=330)
        card.pack(side="right", padx=(theme.PAD_MD, 0))
        if booking is None:
            self._build_no_booking(card.body)
        else:
            self._build_booking_card(card.body, booking)

    def _build_booking_card(self, body, booking):
        """The next upcoming booking, as a compact card."""
        head = tk.Frame(body, bg=theme.BG_SURFACE)
        head.pack(fill="x")
        tk.Label(head, text="Next booking", font=theme.FONT_CARD_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(side="left")
        StatusPill(head, booking["status"]).pack(side="right")

        name = config.tier_name(booking["tier_id"])
        tk.Label(body, text=name + " - " + booking["vehicle_type"],
                 font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(theme.PAD_SM, 0))
        tk.Label(body,
                 text=config.friendly_date(booking["booking_date"])
                 + "  " + booking["time_slot"],
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(1, 0))
        tk.Label(body, text=booking["address"], font=theme.FONT_SMALL,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE, wraplength=280,
                 justify="left").pack(anchor="w", pady=(1, 0))
        # one bottom row keeps the card short so the hero sits higher
        bottom = tk.Frame(body, bg=theme.BG_SURFACE)
        bottom.pack(fill="x", pady=(theme.PAD_SM, 0))
        tk.Label(bottom, text="\u20b1" + str(booking["total_price"]),
                 font=theme.FONT_PRICE, fg=theme.PRIMARY,
                 bg=theme.BG_SURFACE).pack(side="left")
        Button(bottom, text="View details", command=self._go_bookings,
               variant="ghost", height=36).pack(side="right")

    def _build_no_booking(self, body):
        """Nudge shown when there is nothing scheduled."""
        tk.Label(body, text="No booking yet", font=theme.FONT_CARD_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(body, text=config.HOME_EMPTY_TEXT, font=theme.FONT_SMALL,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE, wraplength=280,
                 justify="left").pack(anchor="w", pady=(4, theme.PAD_SM))
        Button(body, text="Book now", command=self._go_wizard,
               variant="primary").pack(anchor="w")

    # ------------------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------------------
    def _go_wizard(self):
        """Opens the booking wizard."""
        self.shell.switch_view("new_booking")

    def _go_bookings(self):
        """Opens My Bookings."""
        self.shell.switch_view("my_bookings")

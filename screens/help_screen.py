"""
screens/help_screen.py
=============================================================================
Help (client): short explanation of how booking works, an FAQ accordion,
and the business contact line.
=============================================================================
"""

import tkinter as tk

import theme
import config

from components import Card, Button, Accordion


FAQ = [
    ("Do I need to stay with my car?",
     "No. As long as the car fits the entry we agreed on, our staff can "
     "finish the wash and send you a message when it is done."),
    ("How far ahead can I book?",
     "Up to " + str(config.MAX_ADVANCE_DAYS) + " days ahead. Slots can fill "
     "up quickly, so the earlier the better."),
    ("When do I pay?",
     "After the service. We accept cash or GCash at your home."),
    ("Can I cancel a booking?",
     "Yes - while it is still Pending or Confirmed, open it in My Bookings "
     "and use Cancel booking."),
    ("What if my car is bigger than a sedan?",
     "Pick SUV or Truck in the booking form; prices in the packages already "
     "adjust for the vehicle type."),
]


class HelpView(tk.Frame):
    """Help page: how booking works, FAQ, and contact."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        super().__init__(master, bg=theme.BG_APP)
        self._build()

    def _build(self):
        """Headline, quick steps, FAQ accordion, contact card."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        tk.Label(head, text="Need help?", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")
        tk.Label(head, text="How booking works, questions, and our contact "
                 "details.", font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="w")

        steps_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        steps_card.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_MD)
        tk.Label(steps_card.body, text="Booking in four quick steps",
                 font=theme.FONT_CARD_TITLE, fg=theme.PRIMARY,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        for index, line in enumerate([
            "Pick your vehicle and the package for it.",
            "Choose a date and time slot that fits your day.",
            "Tell us where we should find the car.",
            "Review everything, then press Book it.",
        ]):
            row = tk.Frame(steps_card.body, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=(6, 0))
            dot = tk.Canvas(row, width=20, height=20, bg=theme.BG_SURFACE,
                            highlightthickness=0)
            dot.create_oval(2, 2, 18, 18, fill=theme.ACCENT_SOFT,
                            outline=theme.ACCENT_SOFT)
            dot.create_text(10, 10, text=str(index + 1),
                            font=theme.FONT_SMALL_BOLD, fill=theme.PRIMARY)
            dot.pack(side="left")
            tk.Label(row, text=line, font=theme.FONT_BODY, fg=theme.TEXT,
                     bg=theme.BG_SURFACE).pack(side="left", padx=(8, 0))

        faq_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        faq_card.pack(fill="x", padx=theme.PAD_LG, pady=(0, theme.PAD_MD))
        tk.Label(faq_card.body, text="Common questions",
                 font=theme.FONT_CARD_TITLE, fg=theme.PRIMARY,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        for question, answer in FAQ:
            acc = Accordion(faq_card.body, question, answer,
                            bg=theme.BG_SURFACE)
            acc.pack(fill="x", pady=(6, 0))

        contact_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        contact_card.pack(fill="x", padx=theme.PAD_LG, pady=(0, theme.PAD_LG))
        tk.Label(contact_card.body, text="Still stuck?",
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(contact_card.body, text=config.BRAND_INFO["contact"],
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(2, 0))
        tk.Label(contact_card.body, text=config.BRAND_INFO["service_area"],
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        Button(contact_card.body, text="Start a booking",
               command=lambda: self.shell.switch_view("new_booking"),
               variant="primary").pack(anchor="w", pady=(theme.PAD_MD, 0))

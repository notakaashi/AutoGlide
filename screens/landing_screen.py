"""
screens/landing_screen.py
=============================================================================
The guest landing page: a top bar (brand + Sign in / Book now) over the
same marketing page the logged-in client Home uses, via MarketingBody.
Guests tap "Book now" and are taken to sign in, then straight into the
booking wizard.
=============================================================================
"""

import tkinter as tk

import theme
import config
import utils.images

from components import ScrollFrame
from screens.marketing import MarketingBody


class LandingScreen(tk.Frame):
    """Guest landing: mini nav + the shared marketing page."""
    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Top bar, then the scrollable marketing content."""
        nav = tk.Frame(self, bg=theme.BG_SURFACE)
        nav.pack(fill="x")
        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill="x")

        brand = tk.Frame(nav, bg=theme.BG_SURFACE)
        brand.pack(side="left", padx=(theme.PAD_LG, 0), pady=theme.PAD_SM)
        # the actual logo picture, not the old green dot
        logo = utils.images.load_image("logo.jpg", (38, 38), rounded=8)
        logo_lbl = tk.Label(brand, image=logo, bg=theme.BG_SURFACE)
        logo_lbl.image = logo
        logo_lbl.pack(side="left", padx=(0, 6))
        tk.Label(brand, text="AutoGlide", font=theme.FONT_BRAND,
                 fg=theme.PRIMARY, bg=theme.BG_SURFACE).pack(side="left")

        buttons = tk.Frame(nav, bg=theme.BG_SURFACE)
        buttons.pack(side="right", padx=(0, theme.PAD_LG))
        from components import Button
        Button(buttons, text="Sign in", variant="ghost",
               command=lambda: self.app.show_screen("login")
               ).pack(side="left")
        Button(buttons, text="Book now", variant="primary",
               command=self._on_book).pack(side="left", padx=(10, 0))

        scroll = ScrollFrame(self, bg=theme.BG_APP)
        scroll.pack(fill="both", expand=True)
        win = self.winfo_toplevel().winfo_width()
        if win <= 1:
            win = 1280
        MarketingBody(scroll.inner, self.app,
                      target_width=max(880, min(1160, win - 2 * 56)))

    def _on_book(self):
        """Main CTA: guests go to sign in first, then resume the wizard."""
        self.app.request_booking("wash_vacuum")

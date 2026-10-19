"""
screens/landing_screen.py
=============================================================================
The marketing content shared by the guest landing page and the client Home
page, plus the guest LandingScreen wrapper (mini nav + content).

Sections: hero card with a decorative canvas panel, package cards with prices
from config, a numbered how-it-works row, and a business footer. No images,
no fake stats - all drawn with tkinter Canvas.
=============================================================================
"""

import tkinter as tk
import theme
import config
from components import Card, Button, ScrollFrame, rounded_rectangle


class MarketingContent(tk.Frame):
    """
    The reusable landing content. 'app' supplies the Book actions; if
    greeting_text is given, a heading with that text is shown on top.
    """
    def __init__(self, master, app, vehicle_type="Sedan", heading=None):
        self.app = app
        self.vehicle_type = vehicle_type
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        if heading:
            head = tk.Frame(self, bg=theme.BG_APP)
            head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_MD, 0))
            tk.Label(head, text=heading, font=theme.FONT_HERO, fg=theme.TEXT,
                     bg=theme.BG_APP).pack(anchor="w")
        self._build_hero()
        self._build_packages()
        self._build_steps()
        self._build_footer()

    # ------------------------------------------------------------------
    # SECTIONS
    # ------------------------------------------------------------------
    def _build_hero(self):
        """Hero: text left, decorative canvas panel right."""
        card = Card(self, radius=theme.RADIUS_LG, pad=0)
        card.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        inner = tk.Frame(card.body, bg=theme.BG_SURFACE)
        inner.pack(fill="both")

        text_side = tk.Frame(inner, bg=theme.BG_SURFACE)
        text_side.pack(side="left", fill="both", expand=True,
                       padx=(theme.PAD_XL, 0), pady=theme.PAD_XL)
        tag = tk.Frame(text_side, bg=theme.ACCENT_SOFT)
        tag.pack(anchor="w")
        tk.Label(tag, text="HOME SERVICE DETAILING", font=theme.FONT_TINY,
                 fg=theme.PRIMARY, bg=theme.ACCENT_SOFT, padx=8,
                 pady=3).pack()
        tk.Label(text_side, text=config.HERO_CONTENT["headline"],
                 font=theme.FONT_HERO, fg=theme.TEXT, bg=theme.BG_SURFACE
                 ).pack(anchor="w", pady=(theme.PAD_MD, 0))
        tk.Label(text_side, text=config.HERO_CONTENT["subtext"],
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE,
                 wraplength=400, justify="left").pack(anchor="w",
                                                      pady=(theme.PAD_SM, 0))
        buttons = tk.Frame(text_side, bg=theme.BG_SURFACE)
        buttons.pack(anchor="w", pady=(theme.PAD_MD, 0))
        Button(buttons, text=config.HERO_CONTENT["button_text"],
               command=self._on_book, variant="primary").pack(side="left")
        tk.Label(text_side, text=config.BRAND_INFO["service_area"],
                 font=theme.FONT_TINY, fg=theme.TEXT_FAINT,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(theme.PAD_MD, 0))

        canvas_side = tk.Frame(inner, bg=theme.BG_SURFACE)
        canvas_side.pack(side="right", padx=theme.PAD_LG, pady=theme.PAD_LG)
        self._hero_canvas = tk.Canvas(canvas_side, width=300, height=220,
                                      bg=theme.BG_SURFACE, highlightthickness=0,
                                      bd=0)
        self._hero_canvas.pack()
        self._paint_hero_canvas()

    def _paint_hero_canvas(self):
        """Draws the decorative hero panel: car silhouette, circles, sparks."""
        c = self._hero_canvas
        c.delete("all")
        w, h = 300, 220
        rounded_rectangle(c, 4, 4, w - 4, h - 4, theme.RADIUS_LG,
                          fill=theme.PRIMARY, outline=theme.PRIMARY)
        c.create_oval(w - 110, -60, w + 60, 110, fill=theme.ACCENT,
                      outline=theme.ACCENT)
        c.create_oval(-70, h - 100, 70, h + 30, fill=theme.ACCENT,
                      outline=theme.ACCENT)
        cx, cy = w // 2, h // 2 + 8
        c.create_rectangle(cx - 90, cy + 4, cx + 90, cy + 34,
                           fill=theme.TEXT_ON_DARK, outline="")
        c.create_arc(cx - 90, cy - 24, cx + 90, cy + 40, start=0, extent=180,
                     style="chord", fill=theme.TEXT_ON_DARK, outline="")
        c.create_oval(cx - 58, cy + 22, cx - 32, cy + 48, fill=theme.PRIMARY,
                      outline=theme.TEXT_ON_DARK, width=3)
        c.create_oval(cx + 32, cy + 22, cx + 58, cy + 48, fill=theme.PRIMARY,
                      outline=theme.TEXT_ON_DARK, width=3)
        for x, y, s in ((cx - 110, cy - 55, 12), (cx + 108, cy - 40, 10),
                        (cx + 80, cy - 76, 8)):
            self._spark(c, x, y, s)
        chip_x, chip_y = cx - 74, cy - 96
        rounded_rectangle(c, chip_x, chip_y, chip_x + 148, chip_y + 26, 13,
                          fill=theme.ACCENT_SOFT, outline=theme.ACCENT_SOFT)
        c.create_text(chip_x + 74, chip_y + 13,
                      text=config.HERO_BLOCK["title"],
                      font=theme.FONT_SMALL_BOLD, fill=theme.PRIMARY)

    def _spark(self, canvas, x, y, size):
        """Draws a small four-point sparkle."""
        canvas.create_line(x - size, y, x + size, y,
                           fill=theme.ACCENT_SOFT, width=2)
        canvas.create_line(x, y - size, x, y + size,
                           fill=theme.ACCENT_SOFT, width=2)

    def _build_packages(self):
        """Package cards with "Book this package" buttons."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_XL, theme.PAD_SM))
        tk.Label(head, text="Pick your package", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(side="left")
        tk.Label(head, text="Prices for a " + self.vehicle_type,
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(side="right")
        row = tk.Frame(self, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_LG)
        for tier in config.SERVICE_TIERS:
            card = Card(row, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, theme.PAD_SM))
            tk.Label(card.body, text=tier["name"], font=theme.FONT_CARD_TITLE,
                     fg=theme.PRIMARY, bg=theme.BG_SURFACE).pack(anchor="w")
            price = config.price_for(tier["id"], self.vehicle_type)
            tk.Label(card.body, text="\u20b1" + str(price),
                     font=theme.FONT_PRICE, fg=theme.TEXT,
                     bg=theme.BG_SURFACE).pack(anchor="w", pady=(2, theme.PAD_SM))
            for bullet in tier["bullets"]:
                line = tk.Frame(card.body, bg=theme.BG_SURFACE)
                line.pack(anchor="w", fill="x")
                tk.Label(line, text="-", font=theme.FONT_SMALL,
                         fg=theme.TEXT_FAINT, bg=theme.BG_SURFACE).pack(
                             side="left", padx=(0, 4))
                tk.Label(line, text=bullet, font=theme.FONT_SMALL,
                         fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                             side="left")
            Button(card.body, text="Book this package",
                   command=lambda t=tier["id"]: self.app.request_booking(t),
                   variant="secondary").pack(anchor="w", pady=(theme.PAD_MD, 0))

    def _build_steps(self):
        """Three numbered steps row."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_XL, theme.PAD_SM))
        tk.Label(head, text="How it works", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(side="left")
        row = tk.Frame(self, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_LG)
        for index, text in enumerate(config.HOW_IT_WORKS_STEPS):
            card = Card(row, pad=theme.PAD_LG)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, theme.PAD_SM))
            badge = tk.Canvas(card.body, width=34, height=34,
                              bg=theme.BG_SURFACE, highlightthickness=0)
            badge.create_oval(2, 2, 32, 32, fill=theme.ACCENT_SOFT,
                              outline=theme.ACCENT_SOFT)
            badge.create_text(17, 17, text=str(index + 1),
                              font=theme.FONT_BODY_BOLD, fill=theme.PRIMARY)
            badge.pack(anchor="w")
            tk.Label(card.body, text=text, font=theme.FONT_BODY, fg=theme.TEXT,
                     bg=theme.BG_SURFACE, wraplength=200,
                     justify="left").pack(anchor="w", pady=(6, 0))

    def _build_footer(self):
        """Small centered footer with the business contact details."""
        foot = tk.Frame(self, bg=theme.BG_APP)
        foot.pack(fill="x", pady=(theme.PAD_LG, theme.PAD_XL))
        tk.Label(foot,
                 text=config.BRAND_INFO["name"] + "   |   "
                 + config.BRAND_INFO["service_area"] + "   |   "
                 + config.BRAND_INFO["contact"],
                 font=theme.FONT_TINY, fg=theme.TEXT_FAINT,
                 bg=theme.BG_APP).pack()

    def _on_book(self):
        """Book CTA: route through the app with the default package."""
        self.app.request_booking("wash_vacuum")


class LandingScreen(tk.Frame):
    """The public landing page shown to guest (not logged in) users."""
    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Mini nav plus the shared marketing content."""
        nav = tk.Frame(self, bg=theme.BG_SURFACE)
        nav.pack(fill="x")
        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill="x")
        left = tk.Frame(nav, bg=theme.BG_SURFACE)
        left.pack(side="left", padx=(theme.PAD_XL, 0), pady=theme.PAD_SM)
        dot = tk.Canvas(left, width=10, height=10, bg=theme.BG_SURFACE,
                        highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=theme.PRIMARY, outline=theme.PRIMARY)
        dot.pack(side="left")
        tk.Label(left, text=" AutoGlide", font=theme.FONT_BRAND, fg=theme.PRIMARY,
                 bg=theme.BG_SURFACE).pack(side="left")
        right = tk.Frame(nav, bg=theme.BG_SURFACE)
        right.pack(side="right", padx=(0, theme.PAD_XL))
        Button(right, text="Sign In",
               command=lambda: self.app.show_screen("login"),
               variant="ghost", bg=theme.BG_SURFACE).pack(side="left",
                                                          padx=theme.PAD_SM)
        Button(right, text="Book Now", command=self._on_book, variant="primary",
               bg=theme.BG_SURFACE).pack(side="left")

        scroll = ScrollFrame(self, bg=theme.BG_APP)
        scroll.pack(fill="both", expand=True)
        MarketingContent(scroll.inner, self.app)

    def _on_book(self):
        """Book CTA for guests: default package then login."""
        self.app.request_booking("wash_vacuum")

"""
screens/landing_screen.py
=============================================================================
Redesigned landing page.

A sticky mini nav, a hero card with a decorative canvas panel (instead of a
photo), stat tiles, live package price cards (from the database), a numbered
how-it-works row, a dark banner, and a footer. All graphics are drawn with
tkinter Canvas; only the standard library is used.
=============================================================================
"""

import tkinter as tk
import theme
import config
import database
from components import Card, Button, ScrollFrame, rounded_rectangle


class LandingScreen(tk.Frame):
    """The public landing page shown to guests."""
    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    # ------------------------------------------------------------------
    # SECTIONS
    # ------------------------------------------------------------------
    def _build(self):
        """Builds the full landing page."""
        self._build_nav()
        scroll = ScrollFrame(self, bg=theme.BG_APP)
        scroll.pack(fill="both", expand=True)
        page = scroll.inner
        self._build_hero(page)
        self._build_stats(page)
        self._build_packages(page)
        self._build_steps(page)
        self._build_banner(page)
        self._build_footer(page)

    def _build_nav(self):
        """Sticky mini navigation bar."""
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
        Button(right, text="Sign In", command=lambda: self.app.show_screen("login"),
               variant="ghost", bg=theme.BG_SURFACE).pack(side="left",
                                                          padx=theme.PAD_SM)
        Button(right, text="Book Now", command=self._on_book, variant="primary",
               bg=theme.BG_SURFACE).pack(side="left")

    def _build_hero(self, page):
        """Hero: text left, decorative canvas panel right."""
        card = Card(page, radius=theme.RADIUS_LG, pad=0)
        card.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_XL, 0))
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
        Button(buttons, text="See packages", command=self._scroll_hint,
               variant="ghost").pack(side="left", padx=theme.PAD_SM)
        tk.Label(text_side, text=config.BRAND_INFO["service_area"],
                 font=theme.FONT_TINY, fg=theme.TEXT_FAINT,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(theme.PAD_MD, 0))

        canvas_side = tk.Frame(inner, bg=theme.BG_SURFACE)
        canvas_side.pack(side="right", padx=theme.PAD_LG,
                         pady=theme.PAD_LG)
        self._hero_canvas = tk.Canvas(canvas_side, width=330, height=240,
                                      bg=theme.BG_SURFACE, highlightthickness=0,
                                      bd=0)
        self._hero_canvas.pack()
        self._paint_hero_canvas()

    def _paint_hero_canvas(self):
        """Draws the decorative hero panel: shapes, car silhouette, shine."""
        c = self._hero_canvas
        c.delete("all")
        w, h = 330, 240
        rounded_rectangle(c, 4, 4, w - 4, h - 4, theme.RADIUS_LG,
                           fill=theme.PRIMARY, outline=theme.PRIMARY)        # soft circles
        c.create_oval(w - 120, -60, w + 60, 120, fill=theme.ACCENT,
                      outline=theme.ACCENT)
        c.create_oval(-70, h - 110, 70, h + 30, fill=theme.ACCENT,
                      outline=theme.ACCENT)
        # car silhouette
        cx, cy = w // 2, h // 2 + 10
        c.create_rectangle(cx - 95, cy + 4, cx + 95, cy + 38,
                           fill=theme.TEXT_ON_DARK, outline="")
        c.create_arc(cx - 95, cy - 26, cx + 95, cy + 44, start=0, extent=180,
                     style="chord", fill=theme.TEXT_ON_DARK, outline="")
        c.create_oval(cx - 62, cy + 24, cx - 34, cy + 52, fill=theme.PRIMARY,
                      outline=theme.TEXT_ON_DARK, width=3)
        c.create_oval(cx + 34, cy + 24, cx + 62, cy + 52, fill=theme.PRIMARY,
                      outline=theme.TEXT_ON_DARK, width=3)
        # shine sparks
        for x, y, s in ((cx - 120, cy - 60, 12), (cx + 120, cy - 44, 10),
                        (cx + 88, cy - 84, 8)):
            self._spark(c, x, y, s)
        # caption chip
        chip_x, chip_y = cx - 78, cy - 108
        rounded_rectangle(c, chip_x, chip_y, chip_x + 156, chip_y + 28, 14,
                fill=theme.ACCENT_SOFT, outline=theme.ACCENT_SOFT)
        c.create_text(chip_x + 78, chip_y + 14,
                      text=config.HERO_BLOCK["title"],
                      font=theme.FONT_SMALL_BOLD, fill=theme.PRIMARY)

    def _spark(self, canvas, x, y, size):
        """Draws a small four-point sparkle."""
        canvas.create_line(x - size, y, x + size, y,
                           fill=theme.ACCENT_SOFT, width=2)
        canvas.create_line(x, y - size, x, y + size,
                           fill=theme.ACCENT_SOFT, width=2)

    def _build_stats(self, page):
        """Three small stat tiles under the hero."""
        row = tk.Frame(page, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_MD, 0))
        stats = (
            ("2,400+", "Washes completed", "Since 2022"),
            ("4.9/5", "Average rating", "From 120+ clients"),
            ("60 min", "Average wash time", "At your doorstep"),
        )
        for value, caption, note in stats:
            card = Card(row, pad=theme.PAD_MD)
            card.pack(side="left", fill="x", expand=True,
                      padx=(0, theme.PAD_SM))
            tk.Label(card.body, text=value, font=theme.FONT_PRICE,
                     fg=theme.PRIMARY, bg=theme.BG_SURFACE).pack(anchor="w")
            tk.Label(card.body, text=caption, font=theme.FONT_BODY,
                     fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
            tk.Label(card.body, text=note, font=theme.FONT_TINY,
                     fg=theme.TEXT_FAINT, bg=theme.BG_SURFACE).pack(anchor="w")

    def _build_packages(self, page):
        """Package cards with live prices from the database."""
        head = tk.Frame(page, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_XL, theme.PAD_SM))
        tk.Label(head, text="Pick your package", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(side="left")
        tk.Label(head, text="Prices update the moment admins change them",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(side="right")
        row = tk.Frame(page, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_XL)
        for tier in config.SERVICE_TIERS:
            card = Card(row, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, theme.PAD_SM))
            tk.Label(card.body, text=tier["name"], font=theme.FONT_CARD_TITLE,
                     fg=theme.PRIMARY, bg=theme.BG_SURFACE).pack(anchor="w")
            price = self._min_price(tier)
            tk.Label(card.body, text="from \u20b1" + str(price),
                     font=theme.FONT_PRICE, fg=theme.TEXT,
                     bg=theme.BG_SURFACE).pack(anchor="w",
                                                pady=(2, theme.PAD_SM))
            for bullet in tier["bullets"]:
                line = tk.Frame(card.body, bg=theme.BG_SURFACE)
                line.pack(anchor="w", fill="x")
                tk.Label(line, text="-", font=theme.FONT_SMALL,
                         fg=theme.TEXT_FAINT, bg=theme.BG_SURFACE).pack(
                             side="left", padx=(0, 4))
                tk.Label(line, text=bullet, font=theme.FONT_SMALL,
                         fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                             side="left")
            Button(card.body, text="Book " + tier["name"],
                   command=lambda t=tier["id"]: self.app.request_booking(t),
                   variant="secondary").pack(anchor="w",
                                              pady=(theme.PAD_MD, 0))

    def _min_price(self, tier):
        """Highest-cheapest price across vehicle types for a tier."""
        prices = [database.get_price(tier["id"], v)
                  for v in config.VEHICLE_TYPES]
        return min(prices) if prices else 0

    def _build_steps(self, page):
        """Three numbered steps row."""
        head = tk.Frame(page, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_XL, theme.PAD_SM))
        tk.Label(head, text="How it works", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(side="left")
        row = tk.Frame(page, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_XL)
        for index, text in enumerate(config.HOW_IT_WORKS_STEPS):
            card = Card(row, pad=theme.PAD_MD)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, theme.PAD_SM))
            badge = tk.Canvas(card.body, width=34, height=34,
                              bg=theme.BG_SURFACE, highlightthickness=0)
            badge.create_oval(2, 2, 32, 32, fill=theme.ACCENT_SOFT,
                              outline=theme.ACCENT_SOFT)
            badge.create_text(17, 17, text=str(index + 1),
                              font=theme.FONT_BODY_BOLD, fill=theme.PRIMARY)
            badge.pack(anchor="w")
            tk.Label(card.body, text=text, font=theme.FONT_BODY,
                     fg=theme.TEXT, bg=theme.BG_SURFACE,
                     wraplength=220, justify="left").pack(anchor="w",
                                                          pady=(6, 0))

    def _build_banner(self, page):
        """Dark call-to-action banner."""
        card = Card(page, bg=theme.PRIMARY, radius=theme.RADIUS_LG,
                    pad=theme.PAD_XL)
        card.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_XL, 0))
        tk.Label(card.body, text=config.BANNER_CONTENT["line"],
                 font=theme.FONT_SECTION, fg=theme.TEXT_ON_DARK,
                 bg=theme.PRIMARY).pack(anchor="w")
        tk.Label(card.body, text=config.BANNER_CONTENT["caption"],
                 font=theme.FONT_BODY, fg=theme.ACCENT_SOFT,
                 bg=theme.PRIMARY).pack(anchor="w")
        Button(card.body, text=config.BANNER_CONTENT["button_text"],
               command=self._on_book, variant="secondary",
               bg=theme.PRIMARY).pack(anchor="w", pady=(theme.PAD_MD, 0))

    def _build_footer(self, page):
        """Small centered footer."""
        foot = tk.Frame(page, bg=theme.BG_APP)
        foot.pack(fill="x", pady=(theme.PAD_LG, theme.PAD_XL))
        tk.Label(foot, text=config.BRAND_INFO["name"] + "   |   "
                 + config.BRAND_INFO["contact"],
                 font=theme.FONT_TINY, fg=theme.TEXT_FAINT,
                 bg=theme.BG_APP).pack()

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------
    def _on_book(self):
        """Book CTA: store a default tier then let main route the flow."""
        self.app.request_booking("wash_vacuum")

    def _scroll_hint(self):
        """Gentle hint animation (no-op placeholder)."""
        pass

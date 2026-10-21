"""
screens/marketing.py
=============================================================================
The marketing sections shared by the guest landing page and the client Home
page: hero with pine panel, package cards, how-it-works photos, banner and
footer. One class so both pages always look the same.

Photos come from pictures/ through utils.images and a missing file only
leaves a flat tinted block - the app never crashes on images here.
=============================================================================
"""

import tkinter as tk

import theme
import config

from components import Card, Button, CenteredColumn, rounded_rectangle
from utils import images


class MarketingBody(tk.Frame):
    """Hero, packages, how it works, banner and footer - centered column."""
    GAP = 20

    def __init__(self, master, app, target_width=1000):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        # content is capped at target_width and centered by CenteredColumn
        self._target = target_width
        self._card_w = max(240, (target_width - 2 * self.GAP) // 3)
        self._hero_w = self._card_w * 3 + self.GAP * 2

        self._build_hero()
        self._build_packages()
        self._build_steps()
        self._build_banner()
        self._build_footer()

    # ------------------------------------------------------------------
    # HERO - photo with a pine panel on the left, text never on the photo
    # ------------------------------------------------------------------
    def _build_hero(self):
        column = CenteredColumn(self, width=self._target)
        wrap = tk.Frame(column, bg=theme.BG_APP)
        wrap.pack(fill="x", pady=(theme.PAD_MD, 0))
        height = 380
        hero = tk.Canvas(wrap, width=self._hero_w, height=height,
                         bg=theme.BG_APP, highlightthickness=0, bd=0)
        hero.pack(anchor="c")
        photo = images.load_image("hero.jpg", (self._hero_w, height),
                                  rounded=14)
        images.attach(hero, photo)
        if photo:
            hero.create_image(0, 0, image=photo, anchor="nw")
        panel_w = max(300, int(self._hero_w * 0.34))
        rounded_rectangle(hero, 0, 0, panel_w, height - 1, radius=14,
                          fill=theme.PRIMARY, outline=theme.PRIMARY)
        tx = theme.PAD_LG
        hero.create_text(tx, 74, anchor="nw", text="HOME SERVICE DETAILING",
                         font=theme.FONT_SMALL_BOLD, fill="#A8C3B2")
        hero.create_text(tx, 104, anchor="nw",
                         text="We bring the\nshine to you.",
                         font=(theme.FONT_FAMILY, 30, "bold"),
                         fill=theme.BG_SURFACE, justify="left")
        hero.create_text(tx, 232, anchor="nw", width=panel_w - 2 * tx,
                         text=config.HERO_CONTENT["subtext"],
                         font=theme.FONT_SMALL, fill="#A8C3B2",
                         justify="left")
        btn = Button(hero, text="Book now", variant="light",
                     bg=theme.PRIMARY, command=self._on_book)
        hero.create_window(tx, height - 82, window=btn, anchor="nw",
                           width=panel_w - 2 * tx, height=44)

    # ------------------------------------------------------------------
    # PACKAGES - three cards in a row, middle one highlighted
    # ------------------------------------------------------------------
    def _build_packages(self):
        column = CenteredColumn(self, width=self._target)
        head = tk.Frame(column, bg=theme.BG_APP)
        head.pack(fill="x", pady=(theme.PAD_LG, theme.PAD_MD))
        tk.Label(head, text="Pick a package", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")
        tk.Label(head,
                 text="Prices for a "
                 + self.app.booking_draft.get("vehicle_type", "Sedan")
                 + ". We come to you.",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="w", pady=(2, 0))

        row = tk.Frame(column, bg=theme.BG_APP)
        row.pack(fill="x")
        pkg_files = {
            "wash_vacuum": "pkg_wash_vacuum.jpg",
            "wash_wax": "pkg_wash_wax.jpg",
            "showroom": "pkg_showroom.jpg",
        }
        for tier in config.SERVICE_TIERS:
            most_booked = tier["id"] == "wash_wax"
            card = Card(row, radius=theme.RADIUS_LG, pad=theme.PAD_MD,
                        border_w=2 if most_booked else 1,
                        border=theme.PRIMARY if most_booked
                        else theme.BORDER, width=self._card_w)
            card.pack(side="left", padx=(0, self.GAP))
            self._paint_package_card(card, tier, pkg_files[tier["id"]],
                                     most_booked)

    def _paint_package_card(self, card, tier, image_name, most_booked):
        body = card.body
        image_w = self._card_w - 2 * theme.PAD_MD
        image_box = tk.Canvas(body, width=image_w, height=200,
                              bg=theme.BG_SURFACE, highlightthickness=0,
                              bd=0)
        image_box.pack(anchor="w", pady=(0, theme.PAD_SM))
        photo = images.load_image(image_name, (image_w, 200), rounded=10)
        images.attach(image_box, photo)
        if photo:
            image_box.create_image(0, 0, image=photo, anchor="nw")
        if most_booked:
            pill = tk.Label(image_box, text="  Most booked  ",
                            font=theme.FONT_TINY, fg=theme.BG_SURFACE,
                            bg=theme.PRIMARY)
            image_box.create_window(10, 10, window=pill, anchor="nw")

        tk.Label(body, text=tier["name"], font=theme.FONT_CARD_TITLE,
                 fg=theme.PRIMARY, bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(body,
                 text="\u20b1" + str(config.price_for(
                     tier["id"], self.app.booking_draft.get("vehicle_type",
                                                            "Sedan"))),
                 font=theme.FONT_PRICE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(2, 0))
        for bullet in tier["bullets"]:
            tk.Label(body, text="- " + bullet, font=theme.FONT_SMALL,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE,
                     wraplength=image_w, justify="left").pack(
                         anchor="w", pady=(1, 0))
        variant = "primary" if most_booked else "ghost"
        Button(body, text="Choose",
               command=lambda t=tier["id"]: self.app.request_booking(t),
               variant=variant).pack(fill="x", pady=(theme.PAD_SM, 0))

    # ------------------------------------------------------------------
    # HOW IT WORKS - three photo columns
    # ------------------------------------------------------------------
    def _build_steps(self):
        column = CenteredColumn(self, width=self._target)
        head = tk.Frame(column, bg=theme.BG_APP)
        head.pack(fill="x", pady=(theme.PAD_LG, theme.PAD_MD))
        tk.Label(head, text="How it works", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")

        row = tk.Frame(column, bg=theme.BG_APP)
        row.pack(fill="x")
        files = ["step_1.jpg", "step_2.jpg", "step_3.jpg"]
        for i, step_text in enumerate(config.HOW_IT_WORKS_STEPS):
            title = step_text.split(". ", 1)[-1]
            col = tk.Frame(row, bg=theme.BG_APP, width=self._card_w)
            col.pack(side="left", padx=(0, self.GAP))
            col.pack_propagate(False)
            box = tk.Canvas(col, width=self._card_w, height=170,
                            bg=theme.BG_APP, highlightthickness=0, bd=0)
            box.pack(anchor="w")
            photo = images.load_image(files[i], (self._card_w, 170),
                                      rounded=10)
            images.attach(box, photo)
            if photo:
                box.create_image(0, 0, image=photo, anchor="nw")
            tk.Label(col, text=title, font=theme.FONT_BODY_BOLD,
                     fg=theme.TEXT, bg=theme.BG_APP, wraplength=self._card_w,
                     justify="left").pack(anchor="w", pady=(theme.PAD_SM, 0))

    # ------------------------------------------------------------------
    # BANNER - photo with a white panel on the left
    # ------------------------------------------------------------------
    def _build_banner(self):
        column = CenteredColumn(self, width=self._target)
        wrap = tk.Frame(column, bg=theme.BG_APP)
        wrap.pack(fill="x", pady=(theme.PAD_LG, 0))
        height = 240
        canvas = tk.Canvas(wrap, width=self._hero_w, height=height,
                           bg=theme.BG_APP, highlightthickness=0, bd=0)
        canvas.pack(anchor="c")
        photo = images.load_image("banner.jpg", (self._hero_w, height),
                                  rounded=14)
        images.attach(canvas, photo)
        if photo:
            canvas.create_image(0, 0, image=photo, anchor="nw")
        panel_w = max(300, int(self._hero_w * 0.34))
        rounded_rectangle(canvas, 0, 0, panel_w, height - 1, radius=14,
                          fill=theme.BG_SURFACE, outline=theme.BG_SURFACE)
        tx = theme.PAD_LG
        canvas.create_text(tx, 50, anchor="nw",
                           text="Clean cars\nmade simple.",
                           font=theme.FONT_TITLE, fill=theme.TEXT,
                           justify="left")
        canvas.create_text(tx, 126, anchor="nw",
                           text=config.BANNER_CONTENT["caption"],
                           font=theme.FONT_SMALL, fill=theme.TEXT_MUTED,
                           justify="left")
        btn = Button(canvas, text="Book now", variant="primary",
                     bg=theme.BG_SURFACE, command=self._on_book)
        canvas.create_window(tx, height - 74, window=btn, anchor="nw")

    # ------------------------------------------------------------------
    # FOOTER LINE
    # ------------------------------------------------------------------
    def _build_footer(self):
        column = CenteredColumn(self, width=self._target)
        foot = tk.Frame(column, bg=theme.BG_APP)
        foot.pack(fill="x", pady=(theme.PAD_LG, theme.PAD_LG))
        contact = config.BRAND_INFO["contact"]
        email = contact.split("Email:")[-1].strip() if "Email:" in contact \
            else contact
        tk.Label(foot, text=config.BRAND_INFO["service_area"] + "   |   "
                 + email, font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="c")

    def _on_book(self):
        """Every CTA starts (or resumes) the booking flow."""
        self.app.request_booking("wash_vacuum")

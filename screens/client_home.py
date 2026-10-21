"""
screens/client_home.py
=============================================================================
The client Home page: greeting row with actions and the next booking card,
then a scrollable marketing page (hero, packages, how it works, banner,
footer). Photos come from pictures/ through utils.images and never crash
the app if a file is missing.
=============================================================================
"""

import tkinter as tk

import theme
import config
import database

from components import (Card, Button, StatusPill, ScrollFrame,
                        rounded_rectangle)
from utils import images

# fixed content sizes - they fit the 1000x650 minimum window
HERO_H = 380
BANNER_H = 240
CARD_W = 272
GAP = 16
CONTENT_W = CARD_W * 3 + GAP * 2          # 848 - hero uses the same width


class HomeView(tk.Frame):
    """Client Home: greeting + next booking card + scrollable marketing."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = shell.current_user
        super().__init__(master, bg=theme.BG_APP)
        self._build()

    def _build(self):
        """Scrollable page with every section."""
        scroll = ScrollFrame(self, bg=theme.BG_APP)
        scroll.pack(fill="both", expand=True)
        page = scroll.inner
        self._build_top(page)
        self._build_hero(page)
        self._build_packages(page)
        self._build_steps(page)
        self._build_banner(page)
        self._build_footer(page)

    # ------------------------------------------------------------------
    # A. GREETING ROW + NEXT BOOKING CARD
    # ------------------------------------------------------------------
    def _build_top(self, page):
        top = tk.Frame(page, bg=theme.BG_APP)
        top.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, theme.PAD_XS))

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
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(2, 0))
        tk.Label(body, text=booking["address"], font=theme.FONT_SMALL,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE, wraplength=280,
                 justify="left").pack(anchor="w", pady=(2, 0))
        price_row = tk.Frame(body, bg=theme.BG_SURFACE)
        price_row.pack(fill="x", pady=(theme.PAD_SM, 0))
        tk.Label(price_row, text="\u20b1" + str(booking["total_price"]),
                 font=theme.FONT_PRICE, fg=theme.PRIMARY,
                 bg=theme.BG_SURFACE).pack(side="left")
        Button(body, text="View details", command=self._go_bookings,
               variant="ghost", height=36).pack(anchor="w",
                                                pady=(theme.PAD_SM, 0))

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
    # B. HERO with pine panel over the photo
    # ------------------------------------------------------------------
    def _build_hero(self, page):
        wrap = tk.Frame(page, bg=theme.BG_APP)
        wrap.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_MD, 0))
        hero = tk.Canvas(wrap, width=CONTENT_W, height=HERO_H,
                         bg=theme.BG_APP, highlightthickness=0, bd=0)
        hero.pack(anchor="w")
        photo = images.load_image("hero.jpg", (CONTENT_W, HERO_H), rounded=14)
        images.attach(hero, photo)
        if photo:
            hero.create_image(0, 0, image=photo, anchor="nw",
                              tags="hero-under")
        # solid pine panel on the left so text never sits on the photo
        panel_w = 330
        rounded_rectangle(hero, 0, 0, panel_w, HERO_H - 1, radius=14,
                          fill=theme.PRIMARY, outline=theme.PRIMARY)
        tx = theme.PAD_LG
        hero.create_text(tx, 78, anchor="nw", text="HOME SERVICE DETAILING",
                         font=theme.FONT_TINY, fill="#A8C3B2")
        hero.create_text(tx, 104, anchor="nw",
                         text="We bring the\nshine to you.",
                         font=theme.FONT_HERO, fill=theme.BG_SURFACE,
                         justify="left")
        hero.create_text(tx, 228, anchor="nw", width=panel_w - 2 * tx + 8,
                         text=config.HERO_CONTENT["subtext"],
                         font=theme.FONT_SMALL, fill="#A8C3B2",
                         justify="left")
        # button inside the canvas so it lines up with the panel text
        btn = Button(hero, text="Book now", variant="light",
                     bg=theme.PRIMARY, command=self._on_book, height=44)
        hero.create_window(tx, HERO_H - 80, window=btn, anchor="nw",
                           width=panel_w - 2 * tx + 8, height=44)

    # ------------------------------------------------------------------
    # C. PACKAGES - three cards in a row
    # ------------------------------------------------------------------
    def _build_packages(self, page):
        head = tk.Frame(page, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_XL, theme.PAD_MD))
        tk.Label(head, text="Pick a package", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")
        tk.Label(head, text="Prices for a "
                 + self.app.booking_draft.get("vehicle_type", "Sedan")
                 + ". We come to you.",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="w", pady=(2, 0))

        row = tk.Frame(page, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_LG)
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
                        else theme.BORDER, width=CARD_W)
            card.pack(side="left", padx=(0, GAP))
            self._paint_package_card(card, tier, pkg_files[tier["id"]],
                                     most_booked)

    def _paint_package_card(self, card, tier, image_name, most_booked):
        body = card.body
        image_box = tk.Canvas(body, width=CARD_W - 2 * theme.PAD_MD,
                              height=200, bg=theme.BG_SURFACE,
                              highlightthickness=0, bd=0)
        image_box.pack(anchor="w", pady=(0, theme.PAD_SM))
        photo = images.load_image(image_name,
                                  (CARD_W - 2 * theme.PAD_MD, 200),
                                  rounded=10)
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
                     wraplength=CARD_W - 2 * theme.PAD_MD,
                     justify="left").pack(anchor="w", pady=(1, 0))
        if most_booked:
            Button(body, text="Choose", command=lambda t=tier["id"]:
                   self.app.request_booking(t),
                   variant="primary").pack(fill="x", pady=(theme.PAD_SM, 0))
        else:
            Button(body, text="Choose", command=lambda t=tier["id"]:
                   self.app.request_booking(t),
                   variant="ghost").pack(fill="x", pady=(theme.PAD_SM, 0))

    # ------------------------------------------------------------------
    # D. HOW IT WORKS - three photo columns
    # ------------------------------------------------------------------
    def _build_steps(self, page):
        head = tk.Frame(page, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_XL, theme.PAD_MD))
        tk.Label(head, text="How it works", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")

        row = tk.Frame(page, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_LG)
        files = ["step_1.jpg", "step_2.jpg", "step_3.jpg"]
        for i, step_text in enumerate(config.HOW_IT_WORKS_STEPS):
            title = step_text.split(". ", 1)[-1]
            col = tk.Frame(row, bg=theme.BG_APP, width=CARD_W)
            col.pack(side="left", padx=(0, GAP))
            col.pack_propagate(False)
            box = tk.Canvas(col, width=CARD_W, height=170, bg=theme.BG_APP,
                            highlightthickness=0, bd=0)
            box.pack(anchor="w")
            photo = images.load_image(files[i], (CARD_W, 170), rounded=10)
            images.attach(box, photo)
            if photo:
                box.create_image(0, 0, image=photo, anchor="nw")
            tk.Label(col, text=title, font=theme.FONT_BODY_BOLD,
                     fg=theme.TEXT, bg=theme.BG_APP, wraplength=CARD_W,
                     justify="left").pack(anchor="w", pady=(theme.PAD_SM, 0))

    # ------------------------------------------------------------------
    # E. BANNER - photo with a white panel on the left
    # ------------------------------------------------------------------
    def _build_banner(self, page):
        wrap = tk.Frame(page, bg=theme.BG_APP)
        wrap.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_XL, 0))
        canvas = tk.Canvas(wrap, width=CONTENT_W, height=BANNER_H,
                           bg=theme.BG_APP, highlightthickness=0, bd=0)
        canvas.pack(anchor="w")
        photo = images.load_image("banner.jpg", (CONTENT_W, BANNER_H),
                                  rounded=14)
        images.attach(canvas, photo)
        if photo:
            canvas.create_image(0, 0, image=photo, anchor="nw")
        panel_w = 340
        rounded_rectangle(canvas, 0, 0, panel_w, BANNER_H - 1, radius=14,
                          fill=theme.BG_SURFACE,
                          outline=theme.BG_SURFACE)
        tx = theme.PAD_LG
        canvas.create_text(tx, 52, anchor="nw",
                           text="Clean cars\nmade simple.",
                           font=theme.FONT_TITLE, fill=theme.TEXT,
                           justify="left")
        canvas.create_text(tx, 130, anchor="nw", text=config.BANNER_CONTENT[
                               "caption"], font=theme.FONT_SMALL,
                           fill=theme.TEXT_MUTED, justify="left")
        btn = Button(canvas, text="Book now", variant="primary",
                     bg=theme.BG_SURFACE, command=self._on_book)
        canvas.create_window(tx, BANNER_H - 76, window=btn, anchor="nw")

    # ------------------------------------------------------------------
    # F. FOOTER LINE
    # ------------------------------------------------------------------
    def _build_footer(self, page):
        foot = tk.Frame(page, bg=theme.BG_APP)
        foot.pack(fill="x", padx=theme.PAD_LG,
                  pady=(theme.PAD_XL, theme.PAD_LG))
        contact = config.BRAND_INFO["contact"]
        email = contact.split("Email:")[-1].strip() if "Email:" in contact \
            else contact
        tk.Label(foot, text=config.BRAND_INFO["service_area"] + "   |   "
                 + email, font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="w")

    # ------------------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------------------
    def _on_book(self):
        """Every CTA on this page starts (or resumes) the booking flow."""
        self.app.request_booking("wash_vacuum")

    def _go_wizard(self):
        """Opens the booking wizard."""
        self.shell.switch_view("new_booking")

    def _go_bookings(self):
        """Opens My Bookings."""
        self.shell.switch_view("my_bookings")

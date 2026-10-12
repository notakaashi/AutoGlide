"""
screens/landing_screen.py
=============================================================================
Landing page for AutoGlide Mobile Detailing.
Clean, restrained layout with exactly 6 sections:
  1. Navigation bar (brand name, Login, Register, Book Now)
  2. Hero (headline <= 6 words, one-sentence subtext, Book Now, large photo)
  3. How it works (exactly 3 short steps, few words each, no paragraphs)
  4. Services (3 tiers in a simple row, photo, live-updating price by vehicle, <=3 bullets)
  5. Full-width photo banner (one short line, Book Now)
  6. Minimal footer (brand name, service area, contact)
=============================================================================
"""

import tkinter as tk
import theme
import config
from components import HoverButton, CardFrame, ScrollableContainer, load_or_placeholder_image


class LandingScreen(tk.Frame):
    """
    Main storefront landing screen.
    Designed with ample whitespace, clean typography, and natural photography.
    """
    def __init__(self, master, app, **kwargs):
        super().__init__(master, bg=theme.BG_MAIN, **kwargs)
        self.app = app

        # Currently selected vehicle type (defaults to Sedan)
        self.selected_vehicle = self.app.booking_draft.get("vehicle_type", "Sedan")

        # Live price label trackers and vehicle toggle buttons
        self.tier_price_labels = {}
        self.vehicle_buttons = {}

        # 1. Navigation Bar (fixed at top)
        self._build_navbar()

        # 2. Main Scrollable Body
        self.scroll_container = ScrollableContainer(self, bg=theme.BG_MAIN)
        self.scroll_container.pack(fill="both", expand=True)

        # Build exactly the requested sections in order
        self._build_hero_section()
        self._build_how_it_works_section()
        self._build_services_section()
        self._build_banner_section()
        self._build_footer()

        # Bind mousewheel across all dynamically added child elements
        self.scroll_container.bind_mousewheel(self.scroll_container.content)

    # -----------------------------------------------------------------------
    # SECTION 1: NAVIGATION BAR
    # -----------------------------------------------------------------------
    def _build_navbar(self):
        """Top navigation bar with brand name on left, links and button on right."""
        navbar = tk.Frame(self, bg=theme.BG_SURFACE, height=64)
        navbar.pack(fill="x", side="top")
        navbar.pack_propagate(False)

        # Border separator under nav
        divider = tk.Frame(self, bg=theme.BORDER_COLOR, height=1)
        divider.pack(fill="x", side="top")

        # Brand name on the left
        brand_label = tk.Label(
            navbar,
            text=config.BRAND_INFO["name"],
            font=theme.FONT_BRAND,
            fg=theme.TEXT_DARK,
            bg=theme.BG_SURFACE
        )
        brand_label.pack(side="left", padx=theme.PAD_XL)

        # Right side: Login, Register, Book Now
        nav_right = tk.Frame(navbar, bg=theme.BG_SURFACE)
        nav_right.pack(side="right", padx=theme.PAD_XL)

        login_btn = HoverButton(
            nav_right,
            text="Login",
            command=lambda: self.app.show_screen("login"),
            bg=theme.BG_SURFACE,
            fg=theme.TEXT_DARK,
            hover_bg=theme.BG_MAIN,
            hover_fg=theme.ACCENT_COLOR,
            font=theme.FONT_BUTTON,
            padx=14,
            pady=6
        )
        login_btn.pack(side="left", padx=(0, 6))

        register_btn = HoverButton(
            nav_right,
            text="Register",
            command=lambda: self.app.show_screen("register"),
            bg=theme.BG_SURFACE,
            fg=theme.TEXT_DARK,
            hover_bg=theme.BG_MAIN,
            hover_fg=theme.ACCENT_COLOR,
            font=theme.FONT_BUTTON,
            padx=14,
            pady=6
        )
        register_btn.pack(side="left", padx=(0, 14))

        book_btn = HoverButton(
            nav_right,
            text="Book Now",
            command=lambda: self._select_package_and_book("wash_wax"),
            bg=theme.ACCENT_COLOR,
            fg=theme.TEXT_LIGHT,
            hover_bg=theme.ACCENT_HOVER,
            hover_fg=theme.TEXT_LIGHT,
            font=theme.FONT_BUTTON,
            padx=18,
            pady=7
        )
        book_btn.pack(side="left")

    # -----------------------------------------------------------------------
    # SECTION 2: HERO SECTION
    # -----------------------------------------------------------------------
    def _build_hero_section(self):
        """
        Headline (<= 6 words), ONE sentence of subtext, Book Now button,
        and a large photo with generous whitespace.
        """
        hero_frame = tk.Frame(self.scroll_container.content, bg=theme.BG_MAIN)
        hero_frame.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_XL, theme.PAD_LG))

        # Two columns: left text (weight 3), right photo (weight 4)
        hero_frame.columnconfigure(0, weight=3)
        hero_frame.columnconfigure(1, weight=4)

        # Left Column: Copy & Call-To-Action
        left_col = tk.Frame(hero_frame, bg=theme.BG_MAIN)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(theme.PAD_MD, theme.PAD_LG), pady=theme.PAD_MD)

        headline = tk.Label(
            left_col,
            text=config.HERO_CONTENT["headline"],
            font=theme.FONT_HERO,
            fg=theme.TEXT_DARK,
            bg=theme.BG_MAIN,
            justify="left",
            wraplength=380
        )
        headline.pack(anchor="w", pady=(theme.PAD_MD, theme.PAD_MD))

        subtext = tk.Label(
            left_col,
            text=config.HERO_CONTENT["subtext"],
            font=theme.FONT_HERO_SUB,
            fg=theme.TEXT_MUTED,
            bg=theme.BG_MAIN,
            justify="left",
            wraplength=380
        )
        subtext.pack(anchor="w", pady=(0, theme.PAD_LG))

        book_cta = HoverButton(
            left_col,
            text=config.HERO_CONTENT["button_text"],
            command=lambda: self._select_package_and_book("wash_wax"),
            bg=theme.ACCENT_COLOR,
            fg=theme.TEXT_LIGHT,
            hover_bg=theme.ACCENT_HOVER,
            hover_fg=theme.TEXT_LIGHT,
            font=theme.FONT_BUTTON,
            padx=24,
            pady=10
        )
        book_cta.pack(anchor="w")

        # Right Column: Large Natural Photograph
        right_col = tk.Frame(hero_frame, bg=theme.BG_MAIN)
        right_col.grid(row=0, column=1, sticky="nsew", padx=(theme.PAD_MD, 0))

        hero_img = load_or_placeholder_image(
            right_col,
            config.HERO_CONTENT["image_path"],
            target_width=580,
            target_height=360,
            placeholder_text="Driveway Detailing Photo"
        )
        hero_img.pack(fill="both", expand=True)

    # -----------------------------------------------------------------------
    # SECTION 3: HOW IT WORKS
    # -----------------------------------------------------------------------
    def _build_how_it_works_section(self):
        """
        Exactly 3 short steps with a few words each.
        No paragraphs, no icons in boxes, no chips.
        """
        container = tk.Frame(self.scroll_container.content, bg=theme.BG_MAIN)
        container.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_LG, theme.PAD_LG))

        # Thin divider line above
        div_top = tk.Frame(container, bg=theme.BORDER_COLOR, height=1)
        div_top.pack(fill="x", pady=(0, theme.PAD_LG))

        # Row with 3 short steps
        steps_row = tk.Frame(container, bg=theme.BG_MAIN)
        steps_row.pack(fill="x", pady=(theme.PAD_SM, theme.PAD_SM))

        for i in range(3):
            steps_row.columnconfigure(i, weight=1)

        for idx, step_text in enumerate(config.HOW_IT_WORKS_STEPS):
            step_box = tk.Frame(steps_row, bg=theme.BG_MAIN)
            step_box.grid(row=0, column=idx, sticky="w", padx=theme.PAD_MD)

            tk.Label(
                step_box,
                text=step_text,
                font=theme.FONT_BODY_BOLD,
                fg=theme.TEXT_DARK,
                bg=theme.BG_MAIN
            ).pack(anchor="w")

        # Thin divider line below
        div_bottom = tk.Frame(container, bg=theme.BORDER_COLOR, height=1)
        div_bottom.pack(fill="x", pady=(theme.PAD_LG, 0))

    # -----------------------------------------------------------------------
    # SECTION 4: SERVICES & PRICING
    # -----------------------------------------------------------------------
    def _build_services_section(self):
        """
        3 tiers in a simple row, each with a plain original name, a photo,
        a price, and at most 3 short bullet points.
        Includes live vehicle switch (Sedan, SUV, Truck).
        """
        section_frame = tk.Frame(self.scroll_container.content, bg=theme.BG_MAIN)
        section_frame.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_MD, theme.PAD_LG))

        # Header row: Title on left, vehicle toggle buttons on right
        top_bar = tk.Frame(section_frame, bg=theme.BG_MAIN)
        top_bar.pack(fill="x", pady=(0, theme.PAD_LG))

        title_lbl = tk.Label(
            top_bar,
            text="Services",
            font=theme.FONT_SECTION,
            fg=theme.TEXT_DARK,
            bg=theme.BG_MAIN
        )
        title_lbl.pack(side="left")

        # Vehicle switch buttons: Sedan / SUV / Truck
        selector_box = tk.Frame(top_bar, bg=theme.BG_MAIN)
        selector_box.pack(side="right")

        for v_name in config.VEHICLE_TYPES:
            is_active = (v_name == self.selected_vehicle)
            btn = HoverButton(
                selector_box,
                text=v_name,
                command=lambda vn=v_name: self._on_vehicle_change(vn),
                bg=theme.ACCENT_COLOR if is_active else theme.BG_SURFACE,
                fg=theme.TEXT_LIGHT if is_active else theme.TEXT_DARK,
                hover_bg=theme.ACCENT_HOVER if is_active else theme.BG_PLACEHOLDER,
                hover_fg=theme.TEXT_LIGHT if is_active else theme.TEXT_DARK,
                font=theme.FONT_SMALL,
                padx=14,
                pady=5
            )
            btn.pack(side="left", padx=3)
            self.vehicle_buttons[v_name] = btn

        # 3 Tiers Cards in a simple row
        tiers_row = tk.Frame(section_frame, bg=theme.BG_MAIN)
        tiers_row.pack(fill="x")

        for i in range(3):
            tiers_row.columnconfigure(i, weight=1, uniform="tier_col")

        for idx, tier in enumerate(config.SERVICE_TIERS):
            card = CardFrame(tiers_row, bg=theme.BG_SURFACE, border_color=theme.BORDER_COLOR)
            card.grid(row=0, column=idx, padx=theme.PAD_SM, sticky="nsew")

            # 1. Tier Photo
            photo_widget = load_or_placeholder_image(
                card,
                tier["image_path"],
                target_width=330,
                target_height=200,
                placeholder_text=tier["name"]
            )
            photo_widget.pack(fill="x")

            # 2. Card Content Area
            body = tk.Frame(card, bg=theme.BG_SURFACE)
            body.pack(fill="both", expand=True, padx=theme.PAD_MD, pady=theme.PAD_MD)

            # Plain Tier Name
            tk.Label(
                body,
                text=tier["name"],
                font=theme.FONT_CARD_TITLE,
                fg=theme.TEXT_DARK,
                bg=theme.BG_SURFACE
            ).pack(anchor="w", pady=(0, 4))

            # Live Updating Price
            current_price = tier["prices"][self.selected_vehicle]
            price_lbl = tk.Label(
                body,
                text=f"₱{current_price:,}",
                font=theme.FONT_PRICE,
                fg=theme.TEXT_DARK,
                bg=theme.BG_SURFACE
            )
            price_lbl.pack(anchor="w", pady=(0, theme.PAD_SM))
            self.tier_price_labels[tier["id"]] = price_lbl

            # Divider line inside card
            tk.Frame(body, bg=theme.BORDER_COLOR, height=1).pack(fill="x", pady=(0, theme.PAD_SM))

            # At most 3 short bullet points
            bullets_frame = tk.Frame(body, bg=theme.BG_SURFACE)
            bullets_frame.pack(fill="both", expand=True, pady=(0, theme.PAD_MD))

            for bullet_text in tier["bullets"][:3]:
                row = tk.Frame(bullets_frame, bg=theme.BG_SURFACE)
                row.pack(fill="x", anchor="w", pady=2)

                tk.Label(
                    row,
                    text="•",
                    font=theme.FONT_BODY,
                    fg=theme.TEXT_MUTED,
                    bg=theme.BG_SURFACE
                ).pack(side="left", padx=(0, 6))

                tk.Label(
                    row,
                    text=bullet_text,
                    font=theme.FONT_BODY,
                    fg=theme.TEXT_DARK,
                    bg=theme.BG_SURFACE
                ).pack(side="left")

            # Select / Book CTA Button
            select_btn = HoverButton(
                body,
                text="Book Now",
                command=lambda tid=tier["id"]: self._select_package_and_book(tid),
                bg=theme.ACCENT_COLOR,
                fg=theme.TEXT_LIGHT,
                hover_bg=theme.ACCENT_HOVER,
                hover_fg=theme.TEXT_LIGHT,
                font=theme.FONT_BUTTON,
                pady=7
            )
            select_btn.pack(fill="x", side="bottom")

    def _on_vehicle_change(self, new_vehicle):
        """
        Updates the selected vehicle filter, adjusts button highlights,
        and recalculates prices on all 3 package cards instantly.
        """
        self.selected_vehicle = new_vehicle
        self.app.booking_draft["vehicle_type"] = new_vehicle

        # Toggle button visual states
        for v_name, btn in self.vehicle_buttons.items():
            btn.set_active(
                is_active=(v_name == new_vehicle),
                active_bg=theme.ACCENT_COLOR,
                active_fg=theme.TEXT_LIGHT,
                inactive_bg=theme.BG_SURFACE,
                inactive_fg=theme.TEXT_DARK
            )

        # Update price labels
        for tier in config.SERVICE_TIERS:
            tier_id = tier["id"]
            if tier_id in self.tier_price_labels:
                new_price = tier["prices"][new_vehicle]
                self.tier_price_labels[tier_id].configure(text=f"₱{new_price:,}")

    def _select_package_and_book(self, tier_id):
        """Passes the chosen tier and vehicle into the app draft and opens booking screen."""
        self.app.booking_draft["vehicle_type"] = self.selected_vehicle
        self.app.booking_draft["tier_id"] = tier_id
        self.app.show_screen("booking")

    # -----------------------------------------------------------------------
    # SECTION 5: FULL-WIDTH PHOTO BANNER
    # -----------------------------------------------------------------------
    def _build_banner_section(self):
        """
        One full-width photo banner with one short line and a Book Now button.
        """
        banner_container = tk.Frame(self.scroll_container.content, bg=theme.BG_MAIN)
        banner_container.pack(fill="x", padx=theme.PAD_XL, pady=(theme.PAD_LG, theme.PAD_XL))

        card = CardFrame(banner_container, bg=theme.BG_SURFACE, border_color=theme.BORDER_COLOR)
        card.pack(fill="x")

        # Full-width photo
        banner_photo = load_or_placeholder_image(
            card,
            config.BANNER_CONTENT["image_path"],
            target_width=1050,
            target_height=240,
            placeholder_text="Clean Driveway Detailing"
        )
        banner_photo.pack(fill="x")

        # Overlay / text bar underneath photo
        bar = tk.Frame(card, bg=theme.BG_SURFACE)
        bar.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_MD)

        tk.Label(
            bar,
            text=config.BANNER_CONTENT["line"],
            font=theme.FONT_SECTION,
            fg=theme.TEXT_DARK,
            bg=theme.BG_SURFACE
        ).pack(side="left")

        HoverButton(
            bar,
            text=config.BANNER_CONTENT["button_text"],
            command=lambda: self._select_package_and_book("wash_wax"),
            bg=theme.ACCENT_COLOR,
            fg=theme.TEXT_LIGHT,
            hover_bg=theme.ACCENT_HOVER,
            hover_fg=theme.TEXT_LIGHT,
            font=theme.FONT_BUTTON,
            padx=20,
            pady=8
        ).pack(side="right")

    # -----------------------------------------------------------------------
    # SECTION 6: FOOTER
    # -----------------------------------------------------------------------
    def _build_footer(self):
        """
        Clean, minimal footer: brand name, service area line, and contact.
        Nothing else.
        """
        footer = tk.Frame(self.scroll_container.content, bg=theme.BG_SURFACE)
        footer.pack(fill="x", side="bottom")

        # Top divider line
        tk.Frame(footer, bg=theme.BORDER_COLOR, height=1).pack(fill="x")

        inner = tk.Frame(footer, bg=theme.BG_SURFACE)
        inner.pack(fill="x", padx=theme.PAD_XL, pady=theme.PAD_LG)

        # Brand name
        tk.Label(
            inner,
            text=config.BRAND_INFO["name"],
            font=theme.FONT_BODY_BOLD,
            fg=theme.TEXT_DARK,
            bg=theme.BG_SURFACE
        ).pack(anchor="w", pady=(0, 2))

        # Service area line
        tk.Label(
            inner,
            text=config.BRAND_INFO["service_area"],
            font=theme.FONT_SMALL,
            fg=theme.TEXT_MUTED,
            bg=theme.BG_SURFACE
        ).pack(anchor="w", pady=(0, 2))

        # Contact line
        tk.Label(
            inner,
            text=config.BRAND_INFO["contact"],
            font=theme.FONT_SMALL,
            fg=theme.TEXT_MUTED,
            bg=theme.BG_SURFACE
        ).pack(anchor="w")

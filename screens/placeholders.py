"""
screens/placeholders.py
=============================================================================
Placeholder screens for Login, Register, and Booking Flow.
Restyled to match the calm, unified warm linen and pine green aesthetic.
Allows navigation testing from the landing page.
=============================================================================
"""

import tkinter as tk
import theme
import config
from components import HoverButton, CardFrame


class PlaceholderScreen(tk.Frame):
    """
    Placeholder screen that renders a clean preview for upcoming modules:
      - 'login': Client & Admin authentication
      - 'register': Customer registration
      - 'booking': Schedule & location picker
    """
    def __init__(self, master, app, screen_type="login", **kwargs):
        super().__init__(master, bg=theme.BG_MAIN, **kwargs)
        self.app = app
        self.screen_type = screen_type

        # Build screen layout
        self._build_top_bar()
        self._build_body()

    def _build_top_bar(self):
        """Top navigation bar with logo and a Return button."""
        top_bar = tk.Frame(self, bg=theme.BG_SURFACE, height=64)
        top_bar.pack(fill="x", side="top")
        top_bar.pack_propagate(False)

        # Border separator under nav
        tk.Frame(self, bg=theme.BORDER_COLOR, height=1).pack(fill="x", side="top")

        # Brand title
        brand_label = tk.Label(
            top_bar,
            text=config.BRAND_INFO["name"],
            font=theme.FONT_BRAND,
            fg=theme.TEXT_DARK,
            bg=theme.BG_SURFACE
        )
        brand_label.pack(side="left", padx=theme.PAD_XL)

        # Back to Home Button
        back_btn = HoverButton(
            top_bar,
            text="Back to Home",
            command=lambda: self.app.show_screen("landing"),
            bg=theme.BG_MAIN,
            fg=theme.TEXT_DARK,
            hover_bg=theme.BORDER_COLOR,
            hover_fg=theme.TEXT_DARK,
            font=theme.FONT_BUTTON,
            padx=16,
            pady=6
        )
        back_btn.pack(side="right", padx=theme.PAD_XL)

    def _build_body(self):
        """Builds centered preview card with clean forms and explanations."""
        center_container = tk.Frame(self, bg=theme.BG_MAIN)
        center_container.pack(expand=True, fill="both", padx=theme.PAD_XL, pady=theme.PAD_XL)

        # Center card
        card = CardFrame(center_container, bg=theme.BG_SURFACE, border_color=theme.BORDER_COLOR)
        card.place(relx=0.5, rely=0.5, anchor="center", width=500)

        # Header tag & Title depending on screen type
        if self.screen_type == "login":
            title_text = "Login"
            subtitle_text = "Sign in to manage your appointments and car details."
            self._render_login_form(card)
        elif self.screen_type == "register":
            title_text = "Register"
            subtitle_text = "Create an account to schedule doorstep detailing."
            self._render_register_form(card)
        elif self.screen_type == "booking":
            title_text = "Schedule Detailing"
            subtitle_text = "Confirm your package and set your location."
            self._render_booking_form(card)
        else:
            title_text = "Coming Soon"
            subtitle_text = "This screen will be built in the next step."

        # Header labels
        title = tk.Label(card, text=title_text, font=theme.FONT_SECTION, fg=theme.TEXT_DARK, bg=theme.BG_SURFACE)
        title.pack(pady=(theme.PAD_LG, 4))

        sub = tk.Label(card, text=subtitle_text, font=theme.FONT_SMALL, fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE, wraplength=440)
        sub.pack(pady=(0, theme.PAD_MD))

    def _render_login_form(self, card):
        """Displays login preview fields."""
        form_frame = tk.Frame(card, bg=theme.BG_SURFACE)
        form_frame.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_SM)

        # Email field
        tk.Label(form_frame, text="Email or Phone", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_DARK, bg=theme.BG_SURFACE).pack(anchor="w", pady=(6, 2))
        email_entry = tk.Entry(form_frame, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_DARK, relief="flat", highlightbackground=theme.BORDER_COLOR, highlightthickness=1)
        email_entry.pack(fill="x", ipady=6, pady=(0, 10))
        email_entry.insert(0, "client@example.ph")

        # Password field
        tk.Label(form_frame, text="Password", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_DARK, bg=theme.BG_SURFACE).pack(anchor="w", pady=(6, 2))
        pass_entry = tk.Entry(form_frame, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_DARK, show="•", relief="flat", highlightbackground=theme.BORDER_COLOR, highlightthickness=1)
        pass_entry.pack(fill="x", ipady=6, pady=(0, 14))
        pass_entry.insert(0, "password123")

        # Notice
        info_box = tk.Label(
            form_frame,
            text="User database and login authentication will be connected in Step 2.",
            font=theme.FONT_SMALL,
            fg=theme.TEXT_MUTED,
            bg=theme.BG_SURFACE,
            wraplength=420
        )
        info_box.pack(pady=(0, 14))

        # Action button
        login_btn = HoverButton(
            form_frame,
            text="Login (Preview)",
            command=lambda: None,
            bg=theme.ACCENT_COLOR,
            fg=theme.TEXT_LIGHT,
            hover_bg=theme.ACCENT_HOVER,
            hover_fg=theme.TEXT_LIGHT,
            pady=8
        )
        login_btn.pack(fill="x", pady=(0, theme.PAD_LG))

    def _render_register_form(self, card):
        """Displays registration preview fields."""
        form_frame = tk.Frame(card, bg=theme.BG_SURFACE)
        form_frame.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_SM)

        fields = [
            ("Full Name", "Juan Dela Cruz"),
            ("Phone Number", "0917-000-0000"),
            ("Email Address", "juan@example.ph"),
            ("Vehicle Type", "Sedan / SUV / Truck")
        ]

        for label_text, default_val in fields:
            tk.Label(form_frame, text=label_text, font=theme.FONT_BODY_BOLD, fg=theme.TEXT_DARK, bg=theme.BG_SURFACE).pack(anchor="w", pady=(4, 2))
            ent = tk.Entry(form_frame, font=theme.FONT_BODY, bg=theme.BG_MAIN, fg=theme.TEXT_DARK, relief="flat", highlightbackground=theme.BORDER_COLOR, highlightthickness=1)
            ent.pack(fill="x", ipady=5, pady=(0, 8))
            ent.insert(0, default_val)

        reg_btn = HoverButton(
            form_frame,
            text="Create Account (Preview)",
            command=lambda: None,
            bg=theme.ACCENT_COLOR,
            fg=theme.TEXT_LIGHT,
            hover_bg=theme.ACCENT_HOVER,
            hover_fg=theme.TEXT_LIGHT,
            pady=8
        )
        reg_btn.pack(fill="x", pady=(8, theme.PAD_LG))

    def _render_booking_form(self, card):
        """Displays chosen booking parameters from landing page."""
        form_frame = tk.Frame(card, bg=theme.BG_SURFACE)
        form_frame.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_SM)

        # Retrieve draft booking state from app if available
        vehicle = self.app.booking_draft.get("vehicle_type", "Sedan")
        tier_id = self.app.booking_draft.get("tier_id", "wash_wax")

        tier_obj = next((t for t in config.SERVICE_TIERS if t["id"] == tier_id), config.SERVICE_TIERS[0])
        tier_price = tier_obj["prices"].get(vehicle, 1499)

        # Summary box
        summary_box = tk.Frame(form_frame, bg=theme.BG_MAIN, highlightbackground=theme.BORDER_COLOR, highlightthickness=1)
        summary_box.pack(fill="x", pady=(0, 14), ipadx=10, ipady=10)

        tk.Label(summary_box, text=f"Package: {tier_obj['name']}", font=theme.FONT_BODY_BOLD, fg=theme.TEXT_DARK, bg=theme.BG_MAIN).pack(anchor="w", padx=10, pady=(4, 2))
        tk.Label(summary_box, text=f"Vehicle: {vehicle}", font=theme.FONT_BODY, fg=theme.TEXT_MUTED, bg=theme.BG_MAIN).pack(anchor="w", padx=10, pady=(0, 2))
        tk.Label(summary_box, text=f"Price: ₱{tier_price:,}", font=theme.FONT_PRICE, fg=theme.TEXT_DARK, bg=theme.BG_MAIN).pack(anchor="w", padx=10, pady=(4, 4))

        tk.Label(
            form_frame,
            text="The date picker, service address pin, and add-on checklist will be integrated into this screen next.",
            font=theme.FONT_SMALL,
            fg=theme.TEXT_MUTED,
            bg=theme.BG_SURFACE,
            wraplength=420
        ).pack(pady=(0, 14))

        proceed_btn = HoverButton(
            form_frame,
            text="Continue to Date & Address (Preview)",
            command=lambda: None,
            bg=theme.ACCENT_COLOR,
            fg=theme.TEXT_LIGHT,
            hover_bg=theme.ACCENT_HOVER,
            hover_fg=theme.TEXT_LIGHT,
            pady=8
        )
        proceed_btn.pack(fill="x", pady=(0, theme.PAD_LG))

"""
screens/login_screen.py
=============================================================================
Login screen for clients and the admin. Two columns: a full-height photo on
the left, the sign-in form on a white card on the right.
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox
import theme
import database
import utils.images
from components import EntryField, Button, Toast


class LoginScreen(tk.Frame):
    """Login screen: photo column + form column."""
    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Left half: big full-bleed photo. Right half: cream panel + form."""
        photo_side = tk.Canvas(self, bg=theme.BG_SOFT,
                               highlightthickness=0, bd=0)
        photo_side.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        utils.images.cover_photo(photo_side, "login_side.jpg")

        right = tk.Frame(self, bg=theme.BG_APP)
        right.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        center = tk.Frame(right, bg=theme.BG_APP)
        center.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72)

        # brand mark up top with the real logo picture
        brand = tk.Frame(center, bg=theme.BG_APP)
        brand.pack(anchor="w", pady=(0, theme.PAD_HERO))
        logo = utils.images.load_image("logo.jpg", (38, 38), rounded=8)
        logo_lbl = tk.Label(brand, image=logo, bg=theme.BG_APP)
        logo_lbl.image = logo
        logo_lbl.pack(side="left", padx=(0, 8))
        tk.Label(brand, text="AutoGlide", font=theme.FONT_BRAND, fg=theme.TEXT,
                 bg=theme.BG_APP).pack(side="left")

        tk.Label(center, text="Welcome back!", font=theme.FONT_GREETING,
                 fg=theme.PRIMARY, bg=theme.BG_APP).pack(anchor="w")
        tk.Label(center, text="Please log in to your account.",
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="w", pady=(4, theme.PAD_LG))

        self.username = EntryField(center, label="Username",
                                   placeholder="e.g. jdoe", width=30,
                                   font=theme.FONT_INPUT, pad_y=12)
        self.username.pack(fill="x")
        self.password = EntryField(center, label="Password", show="*",
                                   placeholder="Enter your password", width=30,
                                   font=theme.FONT_INPUT, pad_y=12)
        self.password.pack(fill="x", pady=(theme.PAD_MD, 0))

        actions = tk.Frame(center, bg=theme.BG_APP)
        actions.pack(fill="x", pady=(theme.PAD_XL, 0))
        # two half-width buttons side by side, like the reference
        Button(actions, text="Log In", command=self.do_login,
               variant="primary", height=48).pack(
                   side="left", expand=True, fill="x", padx=(0, theme.PAD_SM))
        Button(actions, text="Create an account",
               command=lambda: self.app.show_screen("register"),
               variant="secondary", height=48).pack(
                   side="left", expand=True, fill="x")
        # way out for people who landed here by accident
        Button(center, text="Return to homepage",
               command=lambda: self.app.show_screen("landing"),
               variant="ghost").pack(fill="x", pady=(theme.PAD_MD, 0))

    def do_login(self):
        """Reads the fields and checks them against the database."""
        username = self.username.get()
        password = self.password.get()
        if username == "" or password == "":
            if username == "":
                self.username.set_error("Username is required.")
            if password == "":
                self.password.set_error("Password is required.")
            return
        try:
            user = database.login_user(username, password)
        except Exception as error:
            messagebox.showerror("Database error", "Could not log in: " + str(error))
            return
        if user is None:
            self.username.set_error("Invalid username or password.")
            self.password.set_error("Invalid username or password.")
            return
        Toast.show(self.winfo_toplevel(), "Signed in successfully.", kind="success")
        self.app.login_success(user)

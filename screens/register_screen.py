"""
screens/register_screen.py
=============================================================================
Register screen for new clients.
Validates input and creates the user account.
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox
import theme
import database
import validators
import utils.images
from components import Card, EntryField, Button, Toast, ScrollFrame


class RegisterScreen(tk.Frame):
    """Register screen."""
    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Left: cover photo. Right: the registration form on a white card."""
        photo_side = tk.Canvas(self, width=460, bg=theme.BG_SOFT,
                               highlightthickness=0, bd=0)
        photo_side.pack(side="left", fill="y", expand=True)
        utils.images.cover_photo(photo_side, "login_side.jpg")

        right = tk.Frame(self, bg=theme.BG_APP)
        right.pack(side="right", fill="both", expand=True)
        # scroll so the tall form still fits the smallest window
        scroll = ScrollFrame(right, bg=theme.BG_APP)
        scroll.pack(fill="both", expand=True)
        center = tk.Frame(scroll.inner, bg=theme.BG_APP)
        center.pack(pady=theme.PAD_XL)
        card = Card(center, pad=theme.PAD_XL)
        card.pack()
        body = card.body

        tk.Label(body, text="Create your account", font=theme.FONT_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(body, text="Just a few details to start booking",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(2, theme.PAD_LG))

        self.full_name = EntryField(body, label="Full name",
                                    placeholder="Juan Dela Cruz", width=36)
        self.full_name.pack(fill="x")
        self.username = EntryField(body, label="Username",
                                   placeholder="jdoe", width=36)
        self.username.pack(fill="x", pady=(theme.PAD_MD, 0))
        self.phone = EntryField(body, label="Phone",
                                placeholder="0917 890 2886", width=36)
        self.phone.pack(fill="x", pady=(theme.PAD_MD, 0))
        self.email = EntryField(body, label="Email",
                                placeholder="hello@example.com", width=36)
        self.email.pack(fill="x", pady=(theme.PAD_MD, 0))
        self.password = EntryField(body, label="Password", show="*",
                                   placeholder="At least 6 characters", width=36)
        self.password.pack(fill="x", pady=(theme.PAD_MD, 0))
        self.confirm = EntryField(body, label="Confirm password", show="*",
                                  placeholder="Re-enter your password", width=36)
        self.confirm.pack(fill="x", pady=(theme.PAD_MD, 0))

        actions = tk.Frame(body, bg=theme.BG_SURFACE)
        actions.pack(fill="x", pady=(theme.PAD_LG, 0))
        Button(actions, text="Register", command=self._register,
               variant="primary").pack(side="left")
        Button(actions, text="Back to Sign In",
               command=lambda: self.app.show_screen("login"),
               variant="ghost").pack(side="left", padx=theme.PAD_SM)

    def _register(self):
        """Validates and creates a new client account."""
        full_name = self.full_name.get()
        username = self.username.get()
        phone = self.phone.get()
        email = self.email.get()
        password = self.password.get()
        confirm = self.confirm.get()

        valid, message = validators.validate_registration(
            full_name, username, phone, email, password, confirm)
        if not valid:
            self._clear_errors()
            self._show_error(message)
            return

        if database.username_exists(username):
            self._clear_errors()
            self.username.set_error("Username is already taken.")
            return

        try:
            database.create_user(full_name, username, phone, email, password,
                                 role="client")
        except Exception as error:
            messagebox.showerror("Database error", "Could not create account: " + str(error))
            return

        Toast.show(self.winfo_toplevel(), "Account created successfully.", kind="success")
        user = database.login_user(username, password)
        if user is not None:
            self.app.login_success(user)
        else:
            self.app.show_screen("login")

    def _clear_errors(self):
        """Clears all field errors."""
        self.full_name.clear_error()
        self.username.clear_error()
        self.phone.clear_error()
        self.email.clear_error()
        self.password.clear_error()
        self.confirm.clear_error()

    def _show_error(self, message):
        """Shows an error on the most likely field (basic heuristic)."""
        lower = message.lower()
        if "full name" in lower:
            self.full_name.set_error(message)
        elif "username" in lower:
            self.username.set_error(message)
        elif "phone" in lower:
            self.phone.set_error(message)
        elif "email" in lower:
            self.email.set_error(message)
        elif "password" in lower:
            self.password.set_error(message)
        else:
            self.username.set_error(message)

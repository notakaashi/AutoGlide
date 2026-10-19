"""
screens/login_screen.py
=============================================================================
Login screen for clients and the admin.
Checks the username and password against the database.
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox
import theme
import database
from components import Card, EntryField, Button, Toast


class LoginScreen(tk.Frame):
    """Login screen."""
    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Centers the login form."""
        center = tk.Frame(self, bg=theme.BG_APP)
        center.pack(expand=True)
        card = Card(center, pad=theme.PAD_XL)
        card.pack()
        body = card.body

        tk.Label(body, text="Welcome back", font=theme.FONT_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(body, text="Sign in to manage your bookings",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(2, theme.PAD_LG))

        self.username = EntryField(body, label="Username",
                                   placeholder="e.g. jdoe", width=32)
        self.username.pack(fill="x")
        self.password = EntryField(body, label="Password", show="*",
                                   placeholder="Enter your password", width=32)
        self.password.pack(fill="x", pady=(theme.PAD_MD, 0))

        actions = tk.Frame(body, bg=theme.BG_SURFACE)
        actions.pack(fill="x", pady=(theme.PAD_LG, 0))
        Button(actions, text="Sign In", command=self.do_login,
               variant="primary").pack(side="left")
        Button(actions, text="Create an account",
               command=lambda: self.app.show_screen("register"),
               variant="ghost").pack(side="left", padx=theme.PAD_SM)

        footer = tk.Frame(body, bg=theme.BG_SURFACE)
        footer.pack(fill="x", pady=(theme.PAD_MD, 0))
        tk.Label(footer, text="Default admin: username admin / password admin123",
                 font=theme.FONT_TINY, fg=theme.TEXT_FAINT,
                 bg=theme.BG_SURFACE).pack(anchor="w")

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

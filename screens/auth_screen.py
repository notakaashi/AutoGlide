"""
screens/auth_screen.py
=============================================================================
Login and Register screens.
Uses the new design system (Card, EntryField, Button) and follows the
spec: one line of instruction per block, plain strings.
=============================================================================
"""

import tkinter as tk
import theme
import config
import database
import validators
from components import Card, EntryField, Button, Toast


class AuthBase(tk.Frame):
    """Base frame for authentication screens (shared layout)."""
    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        """Centers a single card in the middle of the screen."""
        center = tk.Frame(self, bg=theme.BG_APP)
        center.pack(expand=True)
        self.card = Card(center, pad=theme.PAD_XL)
        self.card.pack()
        self.body = self.card.body


class LoginScreen(AuthBase):
    """Login screen."""
    def __init__(self, master, app):
        super().__init__(master, app)
        self._build_form()

    def _build_form(self):
        """Builds the login form fields and actions."""
        tk.Label(self.body, text="Welcome back", font=theme.FONT_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(self.body, text="Sign in to manage your bookings",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(2, theme.PAD_LG))

        self.username = EntryField(self.body, label="Username",
                                   placeholder="e.g. jdoe", width=32)
        self.username.pack(fill="x")
        self.password = EntryField(self.body, label="Password", show="*",
                                   placeholder="Enter your password", width=32)
        self.password.pack(fill="x", pady=(theme.PAD_MD, 0))

        actions = tk.Frame(self.body, bg=theme.BG_SURFACE)
        actions.pack(fill="x", pady=(theme.PAD_LG, 0))
        Button(actions, text="Sign In", command=self._login,
               variant="primary").pack(side="left")
        Button(actions, text="Create an account", command=self._go_register,
               variant="ghost").pack(side="left", padx=theme.PAD_SM)

        footer = tk.Frame(self.body, bg=theme.BG_SURFACE)
        footer.pack(fill="x", pady=(theme.PAD_MD, 0))
        tk.Label(footer, text="Default admin: username admin / password admin123",
                 font=theme.FONT_TINY, fg=theme.TEXT_FAINT,
                 bg=theme.BG_SURFACE).pack(anchor="w")

    def _go_register(self):
        """Opens the register screen."""
        self.app.show_screen("register")

    def _login(self):
        """Validates and attempts to log in."""
        username = self.username.get()
        password = self.password.get()
        if username == "" or password == "":
            if username == "":
                self.username.set_error("Username is required.")
            if password == "":
                self.password.set_error("Password is required.")
            return
        user = database.login_user(username, password)
        if user is None:
            self.username.set_error("Invalid username or password.")
            self.password.set_error("Invalid username or password.")
            return
        Toast.show(self.winfo_toplevel(), "Signed in successfully.",
                   kind="success")
        self.app.login_success(user)


class RegisterScreen(AuthBase):
    """Register screen."""
    def __init__(self, master, app):
        super().__init__(master, app)
        self._build_form()

    def _build_form(self):
        """Builds the registration form."""
        tk.Label(self.body, text="Create your account", font=theme.FONT_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(self.body, text="Just a few details to start booking",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(2, theme.PAD_LG))

        self.full_name = EntryField(self.body, label="Full name",
                                    placeholder="Juan Dela Cruz", width=36)
        self.full_name.pack(fill="x")
        self.username = EntryField(self.body, label="Username",
                                   placeholder="jdoe", width=36)
        self.username.pack(fill="x", pady=(theme.PAD_MD, 0))
        self.phone = EntryField(self.body, label="Phone",
                                placeholder="0917 890 2886", width=36)
        self.phone.pack(fill="x", pady=(theme.PAD_MD, 0))
        self.email = EntryField(self.body, label="Email",
                                placeholder="hello@example.com", width=36)
        self.email.pack(fill="x", pady=(theme.PAD_MD, 0))
        self.password = EntryField(self.body, label="Password", show="*",
                                   placeholder="At least 6 characters", width=36)
        self.password.pack(fill="x", pady=(theme.PAD_MD, 0))
        self.confirm = EntryField(self.body, label="Confirm password", show="*",
                                  placeholder="Re-enter your password", width=36)
        self.confirm.pack(fill="x", pady=(theme.PAD_MD, 0))

        actions = tk.Frame(self.body, bg=theme.BG_SURFACE)
        actions.pack(fill="x", pady=(theme.PAD_LG, 0))
        Button(actions, text="Register", command=self._register,
               variant="primary").pack(side="left")
        Button(actions, text="Back to Sign In", command=self._go_login,
               variant="ghost").pack(side="left", padx=theme.PAD_SM)

    def _go_login(self):
        """Opens the login screen."""
        self.app.show_screen("login")

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

        database.create_user(full_name, username, phone, email, password,
                             role="client")
        Toast.show(self.winfo_toplevel(), "Account created successfully.",
                   kind="success")
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

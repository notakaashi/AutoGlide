"""
screens/profile_screen.py
=============================================================================
Profile and Security (client): shows account info, lets the client edit
their name/phone/email, and change the password. The old password must be
typed correctly first.
=============================================================================
"""

import tkinter as tk

import theme
import config
import database
import validators

from components import Card, Button, EntryField, Toast


class ProfileView(tk.Frame):
    """Editable client profile with a password-change card."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = database.get_user(self.shell.current_user["id"])
        super().__init__(master, bg=theme.BG_APP)
        self._build()
        self.reload()

    def _build(self):
        """Title, info card, edit form card, password card."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        tk.Label(head, text="Profile and Security", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")

        self._info_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        self._info_card.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_MD)
        self._info = tk.Frame(self._info_card.body, bg=theme.BG_SURFACE)
        self._info.pack(fill="x")

        self._form_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        self._form_card.pack(fill="x", padx=theme.PAD_LG,
                             pady=(0, theme.PAD_MD))
        tk.Label(self._form_card.body, text="Edit information",
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        grid = tk.Frame(self._form_card.body, bg=theme.BG_SURFACE)
        grid.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._name = EntryField(grid, label="Full name *", width=20)
        self._name.grid(row=0, column=0, padx=(0, 12), sticky="w")
        self._phone = EntryField(grid, label="Phone *",
                                 placeholder="0917-000-0000", width=16)
        self._phone.grid(row=0, column=1, padx=(0, 12), sticky="w")
        self._email = EntryField(grid, label="Email *", width=22)
        self._email.grid(row=0, column=2, sticky="w")
        tk.Label(self._form_card.body,
                 text="Username " + self.user["username"] + " can't be "
                 "changed.", font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(theme.PAD_SM, 0))
        Button(self._form_card.body, text="Save changes",
               command=self._save_info, variant="primary").pack(
                   anchor="w", pady=(theme.PAD_SM, 0))

        self._pw_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        self._pw_card.pack(fill="x", padx=theme.PAD_LG,
                           pady=(0, theme.PAD_LG))
        tk.Label(self._pw_card.body, text="Change password",
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        pw_grid = tk.Frame(self._pw_card.body, bg=theme.BG_SURFACE)
        pw_grid.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._old_pw = EntryField(pw_grid, label="Current password *",
                                  show="-", width=18)
        self._old_pw.grid(row=0, column=0, padx=(0, 12), sticky="w")
        self._new_pw = EntryField(pw_grid, label="New password *",
                                  show="-", width=18)
        self._new_pw.grid(row=0, column=1, padx=(0, 12), sticky="w")
        self._confirm_pw = EntryField(pw_grid, label="Re-type new password *",
                                      show="-", width=18)
        self._confirm_pw.grid(row=0, column=2, sticky="w")
        Button(self._pw_card.body, text="Update password",
               command=self._save_password, variant="primary").pack(
                   anchor="w", pady=(theme.PAD_SM, 0))

    def reload(self):
        """Refreshes the account info card and the form values."""
        self.user = database.get_user(self.shell.current_user["id"])
        for widget in self._info.winfo_children():
            widget.destroy()
        rows = [("Username", self.user["username"]),
                ("Signed up", config.friendly_date(self.user["created_at"][:10])),
                ("Bookings", str(database.count_user_bookings(self.user["id"]))
                 + " made so far")]
        for title, value in rows:
            line = tk.Frame(self._info, bg=theme.BG_SURFACE)
            line.pack(fill="x")
            tk.Label(line, text=title, font=theme.FONT_SMALL, width=10,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE,
                     anchor="w").pack(side="left")
            tk.Label(line, text=value, font=theme.FONT_BODY, fg=theme.TEXT,
                     bg=theme.BG_SURFACE).pack(side="left", padx=(12, 0))
        if not hasattr(self, "_loaded_once"):
            self._name.set(self.user["full_name"])
            self._phone.set(self.user["phone"])
            self._email.set(self.user["email"])
            self._loaded_once = True

    def _save_info(self):
        """Validates and saves the changed account info."""
        ok, message = validators.validate_profile(
            self._name.get(), self._phone.get(), self._email.get())
        if not ok:
            Toast(self, message, variant="error")
            return
        database.update_user(self.user["id"], self._name.get(),
                             self._phone.get(), self._email.get())
        Toast(self, "Profile updated.", variant="ok")
        self.reload()

    def _save_password(self):
        """Checks the old password, then updates to the new one."""
        if not self._old_pw.get():
            Toast(self, "Type your current password.", variant="error")
            return
        check = database.login_user(self.user["username"],
                                    self._old_pw.get())
        if not check:
            Toast(self, "Current password is wrong.", variant="error")
            return
        ok, message = validators.validate_new_password(
            self._new_pw.get(), self._confirm_pw.get())
        if not ok:
            Toast(self, message, variant="error")
            return
        database.update_user(self.user["id"], self.user["full_name"],
                             self.user["phone"], self.user["email"],
                             password=self._new_pw.get())
        Toast(self, "Password changed.", variant="ok")
        for field in (self._old_pw, self._new_pw, self._confirm_pw):
            field.set("")

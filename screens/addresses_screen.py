"""
screens/addresses_screen.py
=============================================================================
Addresses (client): saved service addresses with an Add/Edit form and
delete actions; one address can be set as the default for booking.
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox

import theme
import config
import database
import validators

from components import Card, Button, EntryField, Toast


class AddressesView(tk.Frame):
    """Saved addresses page with add/edit/delete and a default address."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = shell.current_user
        super().__init__(master, bg=theme.BG_APP)
        self._editing_id = None
        self._build()
        self.reload()

    def _build(self):
        """Title, list of saved address cards, then the form card."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        tk.Label(head, text="Addresses", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")
        tk.Label(head, text="We come to your home to detail the car - save "
                 "the addresses here.", font=theme.FONT_BODY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_APP).pack(anchor="w")

        self._list = tk.Frame(self, bg=theme.BG_APP)
        self._list.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_MD)

        self._form_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        self._form_card.pack(fill="x", padx=theme.PAD_LG,
                             pady=(0, theme.PAD_LG))
        self._title = tk.Label(self._form_card.body, text="Save an address",
                               font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                               bg=theme.BG_SURFACE)
        self._title.pack(anchor="w")

        grid = tk.Frame(self._form_card.body, bg=theme.BG_SURFACE)
        grid.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._label_in = EntryField(grid, label="Label *",
                                    placeholder="Home / Office", width=14)
        self._label_in.grid(row=0, column=0, padx=(0, 12), sticky="w")
        self._street = EntryField(grid, label="Street address *",
                                  placeholder="House number and street",
                                  width=22)
        self._street.grid(row=0, column=1, sticky="w")
        self._barangay = EntryField(grid, label="Barangay *", width=14)
        self._barangay.grid(row=1, column=0, padx=(0, 12), sticky="w",
                            pady=(6, 0))
        self._city = EntryField(grid, label="City *", width=14)
        self._city.grid(row=1, column=1, sticky="w", pady=(6, 0))
        self._landmark = EntryField(grid, label="Landmark",
                                    placeholder="e.g. beside the bakery",
                                    width=26)
        self._landmark.grid(row=2, column=0, columnspan=2, sticky="w",
                            pady=(6, 0))

        buttons = tk.Frame(self._form_card.body, bg=theme.BG_SURFACE)
        buttons.pack(fill="x", pady=(theme.PAD_MD, 0))
        self._save_btn = Button(buttons, text="Save address",
                                command=self._save, variant="primary")
        self._save_btn.pack(side="right")
        self._cancel_btn = Button(buttons, text="Cancel",
                                  command=self._reset_form, variant="ghost")
        tk.Label(self._form_card.body,
                 text="Fields marked * are required.",
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(theme.PAD_SM, 0))

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------
    def reload(self):
        """Re-reads saved addresses and repaints the list."""
        for widget in self._list.winfo_children():
            widget.destroy()
        addresses = database.get_saved_addresses(self.user["id"])
        if not addresses:
            card = Card(self._list, pad=theme.PAD_LG)
            card.pack(fill="x")
            tk.Label(card.body, text="No saved addresses yet. Add one below.",
                     font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w")
            return
        for a in addresses:
            card = Card(self._list, pad=theme.PAD_LG)
            card.pack(fill="x", pady=(0, 8))
            head = tk.Frame(card.body, bg=theme.BG_SURFACE)
            head.pack(fill="x")
            tk.Label(head, text=a["label"], font=theme.FONT_BODY_BOLD,
                     fg=theme.TEXT, bg=theme.BG_SURFACE).pack(side="left")
            if a["is_default"]:
                tk.Label(head, text="  Default", font=theme.FONT_SMALL_BOLD,
                         fg=theme.PRIMARY,
                         bg=theme.BG_SURFACE).pack(side="left")
            tk.Label(card.body,
                     text=database.address_lines(a["address"], a["barangay"],
                                                 a["city"], a["landmark"]),
                     font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w")
            actions = tk.Frame(card.body, bg=theme.BG_SURFACE)
            actions.pack(side="right")
            if not a["is_default"]:
                Button(actions, text="Make default",
                       command=lambda row=a: self._make_default(row),
                       variant="ghost").pack(side="left", padx=(0, 8))
            Button(actions, text="Edit", command=lambda row=a: self._edit(row),
                   variant="ghost").pack(side="left", padx=(0, 8))
            Button(actions, text="Delete",
                   command=lambda row=a: self._delete(row),
                   variant="ghost").pack(side="left")

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------
    def _make_default(self, row):
        """Sets one address as the default for future bookings."""
        database.set_default_address(row["id"], self.user["id"])
        Toast(self, "'" + row["label"] + "' is now the default address.",
              variant="ok")
        self.reload()

    def _edit(self, row):
        """Puts a saved address into the form for editing."""
        self._editing_id = row["id"]
        self._title.configure(text="Edit " + row["label"])
        self._label_in.set(row["label"])
        self._street.set(row["address"])
        self._barangay.set(row["barangay"])
        self._city.set(row["city"])
        self._landmark.set(row["landmark"] or "")
        self._cancel_btn.pack_forget()
        self._cancel_btn.pack_configure(side="right", padx=(0, 8))

    def _delete(self, row):
        """Asks once with a messagebox and deletes the address."""
        go_on = messagebox.askyesno(
            "Delete address",
            "Delete '" + row["label"] + "'? This cannot be undone.")
        if not go_on:
            return
        database.delete_saved_address(row["id"])
        Toast(self, "'" + row["label"] + "' deleted.", variant="info")
        self._reset_form()
        self.reload()

    def _reset_form(self):
        """Clears the form and leaves edit mode."""
        self._editing_id = None
        self._title.configure(text="Save an address")
        for field in (self._label_in, self._street, self._barangay,
                      self._city, self._landmark):
            field.clear_error()
            field.set("")
        self._cancel_btn.pack_forget()

    def _save(self):
        """Validates the form, then saves a new or updated address."""
        ok, message = validators.validate_address(
            self._label_in.get(), self._street.get(), self._barangay.get(),
            self._city.get(), self._landmark.get())
        if not ok:
            Toast(self, message, variant="error")
            return
        if self._editing_id:
            database.update_saved_address(
                self._editing_id, self._label_in.get(), self._street.get(),
                self._barangay.get(), self._city.get(), self._landmark.get())
            Toast(self, "Address updated.", variant="ok")
        else:
            database.add_saved_address(
                self.user["id"], self._label_in.get(), self._street.get(),
                self._barangay.get(), self._city.get(), self._landmark.get(),
                is_default=0)
            Toast(self, "Address saved.", variant="ok")
        self._reset_form()
        self.reload()

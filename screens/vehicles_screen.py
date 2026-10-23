"""
screens/vehicles_screen.py
=============================================================================
Vehicles (client): the client's saved vehicles, an Add vehicle form, and
edit/delete actions (delete uses a messagebox confirm; everything else
shows a toast).
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox

import theme
import config
import database
import validators

from components import Card, Button, EntryField, CheckField, Toast


class VehiclesView(tk.Frame):
    """Saved vehicles page with add/edit/delete."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = shell.current_user
        super().__init__(master, bg=theme.BG_APP)
        self._editing_id = None
        self._build()
        self.reload()

    def _build(self):
        """Title, vehicle list, and the add/edit form card."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        tk.Label(head, text="Vehicles", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")
        tk.Label(head, text="Saved cars speed up booking - we fill them "
                 "in for you.", font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="w")

        self._list = tk.Frame(self, bg=theme.BG_APP)
        self._list.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_MD)

        self._form_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        self._form_card.pack(fill="x", padx=theme.PAD_LG,
                             pady=(0, theme.PAD_LG))
        self._title = tk.Label(self._form_card.body, text="Save a vehicle",
                               font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                               bg=theme.BG_SURFACE)
        self._title.pack(anchor="w")

        top_row = tk.Frame(self._form_card.body, bg=theme.BG_SURFACE)
        top_row.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._label = EntryField(top_row, label="Nickname *", width=16,
                                 placeholder="e.g. Old blue")
        self._label.pack(side="left", padx=(0, 12))
        self._v_type = tk.StringVar(value=config.VEHICLE_TYPES[0])
        type_row = tk.Frame(top_row, bg=theme.BG_SURFACE)
        type_row.pack(side="left")
        tk.Label(type_row, text="Type *", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        for vt in config.VEHICLE_TYPES:
            tk.Radiobutton(type_row, text=vt, variable=self._v_type,
                           value=vt, bg=theme.BG_SURFACE,
                           cursor="hand2").pack(side="left", padx=(0, 10))

        grid = tk.Frame(self._form_card.body, bg=theme.BG_SURFACE)
        grid.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._make = EntryField(grid, label="Make *", placeholder="e.g. Toyota",
                                width=14)
        self._make.grid(row=0, column=0, padx=(0, 12), sticky="w")
        self._model = EntryField(grid, label="Model *", width=14)
        self._model.grid(row=0, column=1, padx=(0, 12), sticky="w")
        self._color = EntryField(grid, label="Color", width=12)
        self._color.grid(row=0, column=2, padx=(0, 12), sticky="w")
        self._plate = EntryField(grid, label="Plate", placeholder="ABC 1234",
                                 width=12)
        self._plate.grid(row=0, column=3, sticky="w")

        buttons = tk.Frame(self._form_card.body, bg=theme.BG_SURFACE)
        buttons.pack(fill="x", pady=(theme.PAD_MD, 0))
        self._save_btn = Button(buttons, text="Save vehicle",
                                command=self._save, variant="primary")
        self._save_btn.pack(side="right")
        self._cancel_btn = Button(buttons, text="Cancel",
                                  command=self._reset_form, variant="ghost")
        # hidden until an edit is running
        tk.Label(self._form_card.body,
                 text="Fields marked * are required.",
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(theme.PAD_SM, 0))

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------
    def reload(self):
        """Re-reads the saved vehicles and repaints the list."""
        for widget in self._list.winfo_children():
            widget.destroy()
        vehicles = database.get_saved_vehicles(self.user["id"])
        if not vehicles:
            card = Card(self._list, pad=theme.PAD_LG)
            card.pack(fill="x")
            tk.Label(card.body, text="No saved vehicles yet. Add one below - "
                     "it takes a second.",
                     font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w")
            return
        for v in vehicles:
            card = Card(self._list, pad=theme.PAD_LG)
            card.pack(fill="x", pady=(0, 8))
            left = tk.Frame(card.body, bg=theme.BG_SURFACE)
            left.pack(side="left", fill="x", expand=True)
            head = tk.Frame(left, bg=theme.BG_SURFACE)
            head.pack(fill="x")
            # bigger text on the cards - the old tiny sizes were hard to read
            tk.Label(head, text=v["label"], font=theme.FONT_CARD_TITLE,
                     fg=theme.TEXT, bg=theme.BG_SURFACE).pack(side="left")
            tk.Label(head, text="  " + v["vehicle_type"],
                     font=theme.FONT_SMALL, fg=theme.PRIMARY,
                     bg=theme.BG_SURFACE).pack(side="left")
            detail = [v["make"], v["model"], v["color"], v["plate"]]
            text = " - ".join(p for p in detail if p)
            tk.Label(left, text=text if text else "(no details)",
                     font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w")
            actions = tk.Frame(card.body, bg=theme.BG_SURFACE)
            actions.pack(side="right")
            small = None
            Button(actions, text="Edit",
                   command=lambda row=v: self._edit(row),
                   variant="ghost").pack(side="left", padx=(0, 8))
            Button(actions, text="Delete",
                   command=lambda row=v: self._delete(row),
                   variant="ghost").pack(side="left")

    def _edit(self, row):
        """Puts a saved vehicle into the form for editing."""
        self._editing_id = row["id"]
        self._title.configure(text="Edit " + row["label"])
        self._label.set(row["label"])
        self._v_type.set(row["vehicle_type"])
        self._make.set(row["make"])
        self._model.set(row["model"])
        self._color.set(row["color"] or "")
        self._plate.set(row["plate"] or "")
        self._cancel_btn.pack_forget()
        self._cancel_btn.pack_configure(side="right", padx=(0, 8))

    def _delete(self, row):
        """Asks once with a messagebox and deletes the vehicle."""
        go_on = messagebox.askyesno(
            "Delete vehicle",
            "Delete '" + row["label"] + "'? This cannot be undone.")
        if not go_on:
            return
        database.delete_saved_vehicle(row["id"])
        Toast(self, vehicle_msg(row["label"]), variant="info")
        self._reset_form()
        self.reload()

    def _reset_form(self):
        """Clears the form and goes back to 'Save a vehicle' mode."""
        self._editing_id = None
        self._title.configure(text="Save a vehicle")
        for field in (self._label, self._make, self._model, self._color,
                      self._plate):
            field.clear_error()
            field.set("")
        self._v_type.set(config.VEHICLE_TYPES[0])
        self._cancel_btn.pack_forget()

    def _save(self):
        """Validates the form, then saves a new or updated vehicle."""
        ok, message = validators.validate_vehicle(
            self._label.get(), self._v_type.get(), self._make.get(),
            self._model.get(), self._color.get(), self._plate.get())
        if not ok:
            Toast(self, message, variant="error")
            return
        if self._editing_id:
            database.update_saved_vehicle(
                self._editing_id, self._label.get(), self._v_type.get(),
                self._make.get(), self._model.get(), self._color.get(),
                self._plate.get())
            Toast(self, "Vehicle updated.", variant="ok")
        else:
            database.add_saved_vehicle(
                self.user["id"], self._label.get(), self._v_type.get(),
                self._make.get(), self._model.get(), self._color.get(),
                self._plate.get())
            Toast(self, "Vehicle saved.", variant="ok")
        self._reset_form()
        self.reload()


def vehicle_msg(label):
    """One shared feedback message."""
    return "'" + label + "' deleted."

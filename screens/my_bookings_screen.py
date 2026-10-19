"""
screens/my_bookings_screen.py
=============================================================================
My Bookings (client): filter chips, a bookings table, and a details panel
with the status timeline and a cancel button.

Fresh-data rules (important for the school demo):
  - The page re-reads the database when it is shown.
  - Every 5 seconds it re-reads as well, so status changes made by the
    admin show up while the client is reading this page.
  - When a row's status changed since the last read, "Updated" is shown
    on that row and a toast announces the change.
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox

import theme
import config
import database

from components import (Card, Button, StatusPill, DataTable, Toast)


FILTERS = [("all", "All"),
           ("active", "Active"),
           ("Completed", "Completed"),
           ("Cancelled", "Cancelled")]


class MyBookingsView(tk.Frame):
    """The client's bookings list with live refresh and a details side."""
    ACTIVE_STATUSES = ["Pending", "Confirmed", "On the Way", "In Progress"]

    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = shell.current_user
        super().__init__(master, bg=theme.BG_APP)
        self.filter_key = "all"
        self._last_rows = {}       # booking id -> status seen last time
        self._db_rows = []         # booking rows behind the table (same order)
        self._updated_ids = []     # ids flagged "Updated" this refresh
        self._selected_id = None
        self._refresh_job = None
        self._build()
        self._refresh(initial=True)
        self._poll_tick()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        """Filter chips on top, then table left and details card right."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        tk.Label(head, text="My Bookings", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")

        chips = tk.Frame(head, bg=theme.BG_APP)
        chips.pack(fill="x", pady=(theme.PAD_MD, 0))
        self._filter_buttons = []
        for key, label in FILTERS:
            b = Button(chips, text=label,
                       command=lambda k=key: self._pick_filter(k),
                       variant="ghost")
            b.pack(side="left", padx=(0, 8))
            self._filter_buttons.append((key, b))

        body = tk.Frame(self, bg=theme.BG_APP)
        body.pack(fill="both", expand=True, padx=theme.PAD_LG,
                  pady=(theme.PAD_MD, theme.PAD_LG))
        table_card = Card(body, radius=theme.RADIUS_LG, pad=theme.PAD_SM)
        table_card.pack(side="left", fill="both", expand=True)
        self._table = DataTable(
            table_card.body,
            columns=[
                {"key": "id", "title": "Ref", "minsize": 60, "weight": 0},
                {"key": "package", "title": "Package", "minsize": 160,
                 "weight": 1},
                {"key": "when", "title": "Date and time", "minsize": 210,
                 "weight": 1},
                {"key": "total", "title": "Total", "minsize": 90,
                 "weight": 0, "anchor": "e"},
                {"key": "status", "title": "Status", "minsize": 120,
                 "weight": 0, "pill": True},
            ],
            on_select=self._on_pick)
        self._table.pack(fill="both", expand=True)

        self._detail_card = Card(body, radius=theme.RADIUS_LG,
                                 pad=theme.PAD_LG)
        self._detail_card.pack(side="right", fill="y", expand=False,
                               padx=(theme.PAD_MD, 0))
        self._detail = tk.Frame(self._detail_card.body, bg=theme.BG_SURFACE)
        self._detail.pack(fill="both", expand=True)
        self._paint_detail()

    # ------------------------------------------------------------------
    # DATA
    # ------------------------------------------------------------------
    def _pick_filter(self, key):
        """Filter chip clicked."""
        self.filter_key = key
        self._refresh()

    def _refresh(self, initial=False):
        """Reloads bookings, flags changed rows, repaints table + details."""
        try:
            rows = database.get_bookings_by_user(self.user["id"])
        except Exception:
            return  # database closed; skip this tick

        filtered = []
        for row in rows:
            if self.filter_key == "active":
                if row["status"] not in MyBookingsView.ACTIVE_STATUSES:
                    continue
            elif self.filter_key != "all" and row["status"] != self.filter_key:
                continue
            filtered.append(row)
        self._db_rows = filtered

        new_updated = []
        table_rows = []
        for row in filtered:
            seen = self._last_rows.get(row["id"])
            if not initial and seen and seen != row["status"]:
                new_updated.append(row["id"])
            mark = "  (Updated)" if (
                not initial and seen and seen != row["status"]) else ""
            table_rows.append({
                "id": "#" + str(row["id"]),
                "package": config.tier_name(row["tier_id"]) + mark,
                "when": config.friendly_date(row["booking_date"]) + "  -  "
                        + row["time_slot"],
                "total": "\u20b1" + str(row["total_price"]),
                "status": row["status"],
            })
        self._table.set_rows(table_rows)
        if not initial and new_updated:
            Toast(self, "Booking #" + str(new_updated[0]) + " is now "
                  + self._status_of(new_updated[0]), variant="info")
        self._updated_ids = new_updated
        self._last_rows = {row["id"]: row["status"] for row in rows}
        if self._selected_id is not None:
            found = any(row["id"] == self._selected_id for row in filtered)
            if not found:
                self._selected_id = None
        self._paint_detail()
        self._paint_filter_buttons()

    def _poll_tick(self):
        """Runs every 5 seconds: refresh, then schedule the next tick."""
        self._refresh()
        self._refresh_job = self.after(5000, self._poll_tick)

    def on_hide(self):
        """Called when the client leaves this page - stops the 5s poll."""
        if self._refresh_job:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
            self._refresh_job = None

    def destroy(self):
        """Stops polling when the page is torn down."""
        self.on_hide()
        tk.Frame.destroy(self)

    def _status_of(self, booking_id):
        """Finds the current status of one booking id."""
        for row in self._db_rows:
            if row["id"] == booking_id:
                return row["status"]
        return ""

    def _find_booking(self, booking_id):
        """Returns the booking row for an id, or None."""
        for row in self._db_rows:
            if row["id"] == booking_id:
                return row
        return None

    def _on_pick(self, table_row, index=None):
        """A table row was clicked - remember the booking id."""
        ref = str(table_row.get("id", "")).replace("#", "")
        if ref.isdigit():
            self._selected_id = int(ref)
        self._paint_detail()

    # ------------------------------------------------------------------
    # DETAIL PANEL
    # ------------------------------------------------------------------
    def _paint_detail(self):
        """Fills the right-side card for the selected booking."""
        for widget in self._detail.winfo_children():
            widget.destroy()
        booking = self._find_booking(self._selected_id)
        if booking is None:
            tk.Label(self._detail, text="Select a booking to see "
                     "everything about it.",
                     font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE, wraplength=280,
                     justify="left").pack(pady=theme.PAD_LG)
            return

        tk.Label(self._detail, text="Booking #" + str(booking["id"]),
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        StatusPill(self._detail, booking["status"]).pack(anchor="w",
                                                         pady=(4, 0))
        self._info_line("Package", config.tier_name(booking["tier_id"]))
        self._info_line("Vehicle", _vehicle_text(booking))
        self._info_line("When", config.friendly_date(booking["booking_date"])
                        + "  -  " + booking["time_slot"])
        self._info_line("Where", _where_text(booking))
        self._info_line("Add-ons", config.addons_text(booking["addons"]))
        self._info_line("Total", "\u20b1" + str(booking["total_price"]))

        self._timeline(booking["status"])

        if booking["status"] in config.CANCELLABLE_STATUSES:
            Button(self._detail, text="Cancel booking",
                   command=lambda: self._cancel(booking),
                   variant="ghost").pack(anchor="w", pady=(theme.PAD_MD, 0))
        elif booking["status"] == "Completed":
            tk.Label(self._detail, text="Thanks for booking with us!",
                     font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w",
                                               pady=(theme.PAD_MD, 0))

    def _timeline(self, status):
        """Simple steps from Pending to Completed; the current one is green."""
        box = tk.Frame(self._detail, bg=theme.BG_SURFACE)
        box.pack(fill="x", pady=(theme.PAD_MD, 0))
        tk.Label(box, text="Progress", font=theme.FONT_SMALL_BOLD,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(anchor="w")
        steps = ["Pending", "Confirmed", "On the Way", "In Progress",
                 "Completed"]
        if status == "Cancelled":
            current = -1
        else:
            current = steps.index(status) if status in steps else -1
        for index, name in enumerate(steps):
            if current == -1:
                color = theme.TEXT_FAINT
            else:
                color = theme.PRIMARY if index <= current else theme.TEXT_FAINT
            dot = tk.Canvas(box, width=10, height=10, bg=theme.BG_SURFACE,
                            highlightthickness=0)
            dot.create_oval(1, 1, 9, 9, fill=color, outline=color)
            dot.pack(side="left", padx=(0, 3), pady=2)
            tk.Label(box, text=name, font=theme.FONT_TINY, fg=color,
                     bg=theme.BG_SURFACE).pack(side="left", padx=(0, 8))
        if status == "Cancelled":
            tk.Label(box, text="Cancelled", font=theme.FONT_TINY,
                     fg=theme.DANGER, bg=theme.BG_SURFACE).pack(side="left",
                                                                padx=(0, 8))

    def _info_line(self, title, value):
        """One label + value line used by the details card."""
        tk.Label(self._detail, text=title, font=theme.FONT_SMALL_BOLD,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                     anchor="w", pady=(theme.PAD_SM, 0))
        tk.Label(self._detail, text=value, font=theme.FONT_BODY,
                 fg=theme.TEXT, bg=theme.BG_SURFACE, wraplength=280,
                 justify="left").pack(anchor="w")

    def _paint_filter_buttons(self):
        """The active filter chip switches to the primary look."""
        for key, button in self._filter_buttons:
            if key == self.filter_key:
                button.set_variant("primary")
            else:
                button.set_variant("ghost")

    def _cancel(self, booking):
        """Asks once with messagebox, then cancels the booking."""
        go_on = messagebox.askyesno(
            "Cancel booking",
            "Cancel booking #" + str(booking["id"]) + " ("
            + config.tier_name(booking["tier_id"]) + ")?")
        if not go_on:
            return
        database.update_status(booking["id"], "Cancelled")
        self._selected_id = booking["id"]
        self._refresh()


# One-line row helpers (kept together so the class stays readable) ---------
def _where_text(row):
    """Street address line with barangay and city for the details card."""
    return database.address_lines(
        row["address"], row["barangay"], row["city"], row["landmark"])


def _vehicle_text(row):
    """Make model color (plate) line for the details card."""
    parts = []
    make_model = (row["vehicle_make"] + " " + (row["vehicle_model"] or "")).strip()
    if make_model:
        parts.append(make_model)
    if row["vehicle_color"]:
        parts.append(row["vehicle_color"])
    text = " ".join(parts)
    if row["vehicle_plate"]:
        text = text + " (" + row["vehicle_plate"] + ")"
    return text

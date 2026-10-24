"""
screens/admin_bookings.py
=============================================================================
Admin Bookings: search box, status filter chips, sortable columns, a
bookings table, and a details panel where the admin can change the status
(Save with a toast) or delete the booking (messagebox confirm).
=============================================================================
"""

import tkinter as tk
from tkinter import messagebox

import theme
import config
import database

from components import (Card, Button, StatusPill, EntryField, DataTable,
                        SegmentedControl, ScrollFrame, Toast, PageHeader,
                        EmptyState)


class AdminBookingsView(tk.Frame):
    """The staff bookings manager."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        super().__init__(master, bg=theme.BG_APP)
        self.filter_status = "All"
        self.search_text = ""
        self.sort_mode = "Newest"
        self._selected = None
        self._rows = []
        self._build()
        self.reload()

    def _build(self):
        """Filter bar on top, table left, details card right."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        # same header style as the dashboard: title + muted subtitle
        PageHeader(head, "Bookings",
                   "Find a booking, then update its status here.").pack(
                       anchor="w")

        # search box on its own row
        search_row = tk.Frame(head, bg=theme.BG_APP)
        search_row.pack(fill="x", pady=(theme.PAD_MD, 0))
        self._search = EntryField(search_row, label="", placeholder="Search client, "
                                  "package, address...", width=26)
        self._search.pack(side="left")
        self._search.entry.bind("<KeyRelease>", lambda e=None: self.reload())
        # filter chips on their own row below the search box
        chips_row = tk.Frame(head, bg=theme.BG_APP)
        chips_row.pack(fill="x", pady=(theme.PAD_XS, 0))
        chips = tk.Frame(chips_row, bg=theme.BG_APP)
        chips.pack(side="left")
        self._chips = []
        for status in ["All"] + list(config.BOOKING_STATUSES):
            b = Button(chips, text=status,
                       command=lambda s=status: self._pick_status(s),
                       variant="ghost")
            b.pack(side="left", padx=(0, 6))
            self._chips.append((status, b))
        sort_bar = tk.Frame(head, bg=theme.BG_APP)
        sort_bar.pack(fill="x", pady=(2, 0))
        tk.Label(sort_bar, text="Sort", font=theme.FONT_TINY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_APP).pack(side="left")
        self._sort_control = SegmentedControl(
            sort_bar, ["Newest", "Oldest", "Highest total"],
            command=lambda mode: self._pick_sort(mode))
        self._sort_control.pack(side="left", padx=(10, 0))

        body = tk.Frame(self, bg=theme.BG_APP)
        body.pack(fill="both", expand=True, padx=theme.PAD_LG,
                  pady=(theme.PAD_MD, theme.PAD_LG))

        # stretch lets the table body fill the whole card (no empty strip
        # below the last row when the card is taller than the table)
        table_card = Card(body, radius=theme.RADIUS_LG, pad=theme.PAD_SM,
                          stretch=True)
        table_card.pack(side="left", fill="both", expand=True)
        self._table = DataTable(
            table_card.body,
            columns=[
                # explicit widths so no column clips at 1280x780
                {"key": "id", "title": "Ref", "minsize": 55, "weight": 0},
                {"key": "client", "title": "Client", "minsize": 150,
                 "weight": 1},
                {"key": "package", "title": "Package", "minsize": 150,
                 "weight": 1},
                {"key": "when", "title": "Date and time", "minsize": 200,
                 "weight": 1},
                {"key": "total", "title": "Total", "minsize": 90,
                 "weight": 0, "anchor": "e"},
                {"key": "status", "title": "Status", "minsize": 120,
                 "weight": 0, "pill": True},
            ],
            on_select=self._on_pick)
        self._table.pack(fill="both", expand=True)
        tk.Label(table_card.body,
                 text="Tip: click a booking to see all of its details.",
                 font=theme.FONT_TINY, fg=theme.TEXT_FAINT,
                 bg=theme.BG_SURFACE).pack(anchor="w", padx=10)

        self._detail_card = Card(body, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        # hug the content (no tall empty strip), but cap the height to the
        # window so Save/Accept/Decline scroll into view instead of clipping
        self._detail_card.pack(side="right", anchor="n",
                               padx=(theme.PAD_MD, 0))
        self._detail_scroll = ScrollFrame(self._detail_card.body,
                                          bg=theme.BG_SURFACE)
        self._detail_scroll.pack(fill="x")
        self._detail = self._detail_scroll.inner
        self._body_frame = body
        self._paint_detail()
        # re-cap whenever the window changes size
        body.bind("<Configure>", lambda e=None: self._fit_detail())

    def _pick_status(self, status):
        """Status filter chip clicked."""
        self.filter_status = status
        self.reload()

    def _pick_sort(self, mode):
        """A sort option was chosen."""
        self.sort_mode = mode
        self.reload()

    def _filtered_rows(self):
        """Search + status + sort applied to all bookings."""
        text = self._search.get().lower()
        rows = database.get_all_bookings()
        result = []
        for row in rows:
            if self.filter_status != "All" and row["status"] != self.filter_status:
                continue
            haystack = " ".join([
                row["client_name"] or "", row["client_username"] or "",
                config.tier_name(row["tier_id"]), row["address"] or "",
                row["city"] or ""])
            if text and text not in haystack.lower():
                continue
            result.append(row)
        if self.sort_mode == "Oldest":
            result.sort(key=lambda r: (r["booking_date"], r["time_slot"]))
        elif self.sort_mode == "Highest total":
            result.sort(key=lambda r: r["total_price"], reverse=True)
        else:
            result.sort(key=lambda r: (r["booking_date"], r["time_slot"]),
                        reverse=True)
        self._rows = result
        return result

    # ------------------------------------------------------------------
    # LIST
    # ------------------------------------------------------------------
    def reload(self):
        """Rereads the database and repaints the table."""
        rows = self._filtered_rows()
        table_rows = []
        for row in rows:
            table_rows.append({
                "id": "#" + str(row["id"]),
                "client": (row["client_name"] or "").title(),
                "package": config.tier_name(row["tier_id"]),
                "when": config.friendly_date(row["booking_date"]) + "  -  "
                        + row["time_slot"],
                "total": "\u20b1" + str(row["total_price"]),
                "status": row["status"],
            })
        self._table.set_rows(table_rows)
        # show the newest booking in the details panel by default, so the
        # user doesn't have to click a row first
        if self._selected is None and table_rows:
            self._table._select(0)
        for chip_status, button in self._chips:
            if chip_status == self.filter_status:
                button.set_variant("primary")
            else:
                button.set_variant("ghost")
        self._paint_detail()

    def _on_pick(self, table_row, index=None):
        # Remembers the selected booking id, then repaints the details.
        ref = str(table_row.get("id", "")).replace("#", "")
        if ref.isdigit():
            self._selected = int(ref)
        self._paint_detail()

    # ------------------------------------------------------------------
    # DETAIL
    # ------------------------------------------------------------------
    def _find(self, booking_id):
        """Finds the booking row of the selected id."""
        for row in self._rows:
            if row["id"] == booking_id:
                return row
        return None

    def _paint_detail(self):
        """Details card: client info, full address, price breakdown, status."""
        for widget in self._detail.winfo_children():
            widget.destroy()
        booking = self._find(self._selected)
        if booking is None:
            EmptyState(self._detail, "Select a booking",
                       bg=theme.BG_SURFACE, icon="\u25A4").pack(fill="x")
            self._fit_detail()
            return
        self._label("Client", "#" + str(booking["user_id"]) + "  "
                    + (booking["client_name"] or "-").title())
        self._label("Contact", (booking["client_phone"] or "-") + "   "
                    + (booking["client_email"] or "-"))
        self._label("Package", config.tier_name(booking["tier_id"]) + " ("
                    + booking["vehicle_type"] + ")")
        self._label("Vehicle", self._vehicle_text(booking))
        self._label("Schedule", config.friendly_date(booking["booking_date"])
                    + " at " + booking["time_slot"])
        self._label("Address", database.address_lines(
            booking["address"], booking["barangay"], booking["city"],
            booking["landmark"]))
        self._label("Add-ons", config.addons_text(booking["addons"]))
        self._label("Price", "\u20b1" + str(booking["total_price"]))

        status_row = tk.Frame(self._detail, bg=theme.BG_SURFACE)
        status_row.pack(fill="x", pady=(theme.PAD_MD, 0))
        tk.Label(status_row, text="Change status", font=theme.FONT_SMALL_BOLD,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(anchor="w")
        # (comment: the admin picks a new status, then presses Save)
        # wrap=2 so the six long status names fit inside the card
        self._status_choice = SegmentedControl(
            self._detail, list(config.BOOKING_STATUSES),
            value=booking["status"], wrap=2)
        self._status_choice.pack(anchor="w", pady=(4, 0))
        save_row = tk.Frame(self._detail, bg=theme.BG_SURFACE)
        save_row.pack(fill="x", pady=(theme.PAD_MD, 0))
        Button(save_row, text="Save status",
               command=self._save_status, variant="primary").pack(side="right")
        # quick answers: a fresh Pending request can go both ways at once
        if booking["status"] == "Pending":
            quick = tk.Frame(self._detail, bg=theme.BG_SURFACE)
            quick.pack(fill="x", pady=(theme.PAD_SM, 0))
            tk.Label(quick, text="Quick answer", font=theme.FONT_SMALL_BOLD,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                         anchor="w")
            row = tk.Frame(quick, bg=theme.BG_SURFACE)
            row.pack(anchor="w", pady=(4, 0))
            Button(row, text="Accept", height=36,
                   command=lambda: self._set_status(booking["id"],
                                                    "Confirmed"),
                   variant="primary").pack(side="left")
            Button(row, text="Decline", height=36, variant="ghost",
                   command=lambda: self._set_status(booking["id"],
                                                    "Cancelled")
                   ).pack(side="left", padx=(theme.PAD_SM, 0))
        Button(self._detail, text="Delete booking",
               command=self._delete, variant="ghost").pack(
                   anchor="w", pady=(theme.PAD_MD, 0))
        self._fit_detail()

    def _fit_detail(self):
        """Caps the details card: hug the content, but never taller than the
        window - the ScrollFrame takes over when the panel really overflows."""
        def fit():
            if not self.winfo_exists() or \
                    not self._detail_scroll.winfo_exists():
                return
            content = self._detail_scroll.inner.winfo_reqheight()
            # body height minus the card's own padding
            room = max(self._body_frame.winfo_height() - 2 * theme.PAD_LG,
                       260)
            self._detail_scroll.canvas.configure(
                height=max(140, min(content, room)))
        self.after_idle(fit)

    def _set_status(self, booking_id, status):
        """One-click accept / decline, then repaints the table."""
        database.update_status(booking_id, status)
        Toast(self, "Booking #" + str(booking_id) + " saved as " + status,
              variant="ok")
        self.reload()

    def _label(self, title, value):
        """One title + value line."""
        tk.Label(self._detail, text=title, font=theme.FONT_SMALL_BOLD,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                     anchor="w", pady=(theme.PAD_SM, 0))
        tk.Label(self._detail, text=value, font=theme.FONT_BODY,
                 fg=theme.TEXT, bg=theme.BG_SURFACE, wraplength=250,
                 justify="left").pack(anchor="w")

    def _save_status(self):
        """Writes the chosen status with a toast back on success."""
        booking = self._find(self._selected)
        if booking is None:
            return
        new_status = self._status_choice.get() if hasattr(
            self, "_status_choice") else booking["status"]
        database.update_status(booking["id"], new_status)
        Toast(self, "Booking #" + str(booking["id"]) + " saved as "
              + new_status, variant="ok")
        self.reload()

    def _delete(self):
        """Asks with a messagebox, then deletes the booking."""
        booking = self._find(self._selected)
        if booking is None:
            return
        go_on = messagebox.askyesno(
            "Delete booking",
            "Delete booking #" + str(booking["id"]) + "? This cannot be "
            "undone.")
        if not go_on:
            return
        database.delete_booking(booking["id"])
        Toast(self, "Booking #" + str(booking["id"]) + " deleted.",
              variant="info")
        self._selected = None
        self.reload()

    def _vehicle_text(self, row):
        """Vehicle line for the details card."""
        text = (row["vehicle_make"] + " " + (row["vehicle_model"] or "")).strip()
        if row["vehicle_color"]:
            text = (text + " " + row["vehicle_color"]).strip()
        if row["vehicle_plate"]:
            text = text + " (" + row["vehicle_plate"] + ")"
        return text or row["vehicle_type"]

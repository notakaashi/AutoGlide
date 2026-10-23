"""
screens/admin_clients.py
=============================================================================
Admin Clients: a read-only list of client accounts (admins are filtered
out on purpose) with a details card showing booking counts and account
info. Search box at the top.
=============================================================================
"""

import tkinter as tk

import theme
import config
import database

from components import (Card, EntryField, DataTable, Button, PageHeader,
                        EmptyState)


class AdminClientsView(tk.Frame):
    """Read-only client accounts table with a details card."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        super().__init__(master, bg=theme.BG_APP)
        self._selected = None
        self._build()
        self.reload()

    def _build(self):
        """Title, search, table left, details card right."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        # same header style as the dashboard: title + muted subtitle
        PageHeader(head, "Clients", "Client accounts only - staff accounts "
                   "stay private.").pack(anchor="w")

        bar = tk.Frame(head, bg=theme.BG_APP)
        bar.pack(fill="x", pady=(theme.PAD_MD, 0))
        self._search = EntryField(bar, label="", placeholder="Search by "
                                  "name, username or email...", width=26)
        self._search.pack(side="left")
        self._search.entry.bind("<KeyRelease>", lambda e: self.reload())

        body = tk.Frame(self, bg=theme.BG_APP)
        body.pack(fill="both", expand=True, padx=theme.PAD_LG,
                  pady=(theme.PAD_MD, theme.PAD_LG))
        table_card = Card(body, radius=theme.RADIUS_LG, pad=theme.PAD_SM)
        table_card.pack(side="left", fill="both", expand=True)
        self._table = DataTable(
            table_card.body,
            columns=[
                # explicit widths so no column clips at 1280x780
                {"key": "id", "title": "ID", "minsize": 55, "weight": 0},
                {"key": "name", "title": "Name", "minsize": 160,
                 "weight": 1},
                {"key": "username", "title": "Username", "minsize": 130,
                 "weight": 1},
                {"key": "phone", "title": "Phone", "minsize": 140,
                 "weight": 1},
                {"key": "email", "title": "Email", "minsize": 200,
                 "weight": 1},
                {"key": "bookings", "title": "Bookings", "minsize": 90,
                 "weight": 0, "anchor": "e"},
            ],
            on_select=self._on_pick)
        self._table.pack(fill="both", expand=True)

        detail_card = Card(body, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        detail_card.pack(side="right", fill="y", expand=False,
                         padx=(theme.PAD_MD, 0))
        self._detail = tk.Frame(detail_card.body, bg=theme.BG_SURFACE)
        self._detail.pack(fill="both", expand=True)
        self._paint_detail()

    def reload(self):
        """Rereads clients + booking counts, applies the search, repaints."""
        text = self._search.get().lower()
        counts = database.get_client_counts()
        clients = database.get_clients()
        rows = []
        for client in clients:
            haystack = " ".join([client["full_name"], client["username"],
                                 client["email"]]).lower()
            if text and text not in haystack:
                continue
            rows.append({
                "id": str(client["id"]),
                "name": (client["full_name"] or "").title(),
                "username": client["username"],
                "phone": client["phone"] or "-",
                "email": client["email"] or "-",
                "bookings": str(counts.get(client["id"], 0)),
                "_user": client,
            })
        self._rows = rows
        self._table.set_rows([{k: v for k, v in r.items()
                               if not k.startswith("_")} for r in rows])
        self._paint_detail()

    def _on_pick(self, table_row, index=None):
        """A client row was clicked - show the details card."""
        # Find the account behind the clicked table row by id.
        picked = str(table_row.get("id", ""))
        if picked.isdigit():
            self._selected = int(picked)
        self._paint_detail()

    def _paint_detail(self):
        """Details: contact info, member since and the booking count."""
        for widget in self._detail.winfo_children():
            widget.destroy()
        client = None
        for row in getattr(self, "_rows", []):
            if row["_user"]["id"] == self._selected:
                client = row["_user"]
        if client is None:
            EmptyState(self._detail, "Select a client",
                       bg=theme.BG_SURFACE, icon="\u25A4").pack(fill="x")
            return
        self._line("Name", (client["full_name"] or "").title())
        self._line("Username", client["username"])
        self._line("Phone", client["phone"] or "-")
        self._line("Email", client["email"] or "-")
        self._line("Member since",
                   config.friendly_date(client["created_at"][:10]))
        counts = database.get_client_counts()
        self._line("Bookings made", str(counts.get(client["id"], 0)))

    def _line(self, title, value):
        """One title + value pair in the details card."""
        tk.Label(self._detail, text=title, font=theme.FONT_SMALL_BOLD,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                     anchor="w", pady=(theme.PAD_SM, 0))
        tk.Label(self._detail, text=value, font=theme.FONT_BODY,
                 fg=theme.TEXT, bg=theme.BG_SURFACE, wraplength=240,
                 justify="left").pack(anchor="w")

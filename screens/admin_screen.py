"""
screens/admin_screen.py
=============================================================================
Admin Dashboard: stat cards (today, this week, in progress, clients),
a bar chart of bookings for the last 7 days drawn on a canvas, and a
recent-booking list.
=============================================================================
"""

import datetime
import tkinter as tk

import theme
import config
import database

from components import (Card, Button, StatusPill, StatCard,
                        rounded_rectangle)


class AdminDashboard(tk.Frame):
    """Staff overview with numbers, a small chart and recent bookings."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        super().__init__(master, bg=theme.BG_APP)
        self._build()

    def _build(self):
        """Header, four stat cards, chart card, recent list."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        tk.Label(head, text="Dashboard", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")
        tk.Label(head, text="A quick look at how AutoGlide is doing today.",
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="w")

        stats = database.get_admin_stats()
        cards = tk.Frame(self, bg=theme.BG_APP)
        cards.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_MD)
        StatCard(cards, "Bookings today", str(stats["today"])).pack(
            side="left", fill="both", expand=True, padx=(0, theme.PAD_SM))
        StatCard(cards, "Bookings this week", str(stats["week"])).pack(
            side="left", fill="both", expand=True, padx=(0, theme.PAD_SM))
        StatCard(cards, "Active jobs", str(stats["active"])).pack(
            side="left", fill="both", expand=True, padx=(0, theme.PAD_SM))
        StatCard(cards, "Pending requests", str(stats["Pending"])).pack(
            side="left", fill="both", expand=True, padx=(0, theme.PAD_SM))

        chart_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG,
                          bg=theme.PRIMARY)
        chart_card.pack(fill="x", padx=theme.PAD_LG, pady=(0, theme.PAD_MD))
        tk.Label(chart_card.body, text="Bookings in the last 7 days",
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT_ON_DARK,
                 bg=theme.PRIMARY).pack(anchor="w")
        self._chart = tk.Canvas(chart_card.body, height=140, bg=theme.PRIMARY,
                                highlightthickness=0)
        self._chart.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._paint_chart()

        recent_card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        recent_card.pack(fill="x", padx=theme.PAD_LG, pady=(0, theme.PAD_LG))
        bottom = tk.Frame(recent_card.body, bg=theme.BG_SURFACE)
        bottom.pack(fill="x")
        tk.Label(bottom, text="Recent bookings", font=theme.FONT_CARD_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(side="left")
        Button(bottom, text="Open bookings",
               command=lambda: self.shell.switch_view("bookings"),
               variant="ghost").pack(side="right")
        self._recent = tk.Frame(recent_card.body, bg=theme.BG_SURFACE)
        self._recent.pack(fill="x")
        self._paint_recent()

    def _paint_chart(self):
        """Draws 7 bars (last 7 days, oldest on the left) on the canvas."""
        self._chart.delete("all")
        counts = database.get_bookings_last_days(7)
        self._chart.update_idletasks()
        width = max(self._chart.winfo_width(), 400)
        height = 120
        top_pad = 18
        bottom_pad = 26
        usable = height - top_pad - bottom_pad
        biggest = max(1, max(counts.values()) if counts else 1)
        slot_w = width / 7.0
        for index, offset in enumerate(range(6, -1, -1)):
            day = datetime.date.today() - datetime.timedelta(days=offset)
            count = counts.get(day.isoformat(), 0)
            x = width - (index + 1) * slot_w
            bar_w = slot_w * 0.42
            bar_h = 0 if count == 0 else max(6, usable * count / biggest)
            x0 = x + (slot_w - bar_w) / 2
            y1 = top_pad + usable - bar_h
            self._chart.create_rectangle(
                x0, y1, x0 + bar_w, top_pad + usable, fill=theme.ACCENT,
                outline=theme.ACCENT)
            if count:
                self._chart.create_text(x0 + bar_w / 2, y1 - 8,
                                        text=str(count),
                                        font=theme.FONT_SMALL_BOLD,
                                        fill=theme.TEXT_ON_DARK)
            label = day.strftime("%a")
            self._chart.create_text(x0 + bar_w / 2, top_pad + usable + 12,
                                    text=label, font=theme.FONT_TINY,
                                    fill=theme.TEXT_ON_DARK)

    def _paint_recent(self):
        """Lists the newest bookings with client, package, date and status."""
        for widget in self._recent.winfo_children():
            widget.destroy()
        rows = database.get_all_bookings()
        if not rows:
            tk.Label(self._recent, text="No bookings yet today - they will "
                     "show up here.", font=theme.FONT_BODY,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                         anchor="w", pady=(theme.PAD_SM, 0))
            return
        for row in rows[:6]:
            line = tk.Frame(self._recent, bg=theme.BG_SURFACE)
            line.pack(fill="x", pady=2)
            left = tk.Frame(line, bg=theme.BG_SURFACE)
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left,
                     text="#" + str(row["id"]) + "  "
                     + (row["client_name"] or "Client #"
                        + str(row["user_id"])) + "  -  "
                     + config.tier_name(row["tier_id"]),
                     font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                     bg=theme.BG_SURFACE).pack(anchor="w")
            tk.Label(left,
                     text=config.friendly_date(row["booking_date"]) + "  -  "
                     + row["time_slot"],
                     font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w")
            StatusPill(line, row["status"]).pack(side="right", padx=(10, 0))

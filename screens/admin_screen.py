"""
screens/admin_screen.py
=============================================================================
Admin Dashboard: header with date, four compact stat cards (today, pending,
this month, completed revenue), a 7-day bar chart with gridlines on a
canvas, a "Needs your answer" list of Pending bookings with Accept / Decline
buttons, and a Today list. Everything scrolls if the window is short.
=============================================================================
"""

import datetime
import tkinter as tk

import theme
import config
import database

from components import Card, Button, StatusPill, ScrollFrame, Toast


class AdminDashboard(tk.Frame):
    """Staff overview: numbers, chart, pending answers, today's list."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        super().__init__(master, bg=theme.BG_APP)
        self._build()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        """Scrollable dashboard page."""
        scroll = ScrollFrame(self, bg=theme.BG_APP)
        scroll.pack(fill="both", expand=True)
        page = scroll.inner

        head = tk.Frame(page, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        tk.Label(head, text="Dashboard", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_APP).pack(anchor="w")
        tk.Label(head, text=_today_line(), font=theme.FONT_BODY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_APP).pack(anchor="w")

        self._build_stats(page)

        columns = tk.Frame(page, bg=theme.BG_APP)
        columns.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_MD, 0))
        # left: the 7-day chart; right: pending requests that need an answer
        self._build_chart(columns)
        self._build_pending(columns)

        self._build_today_list(page)

    def _build_stats(self, page):
        """Four compact stat cards of equal size in one row."""
        stats = database.get_admin_stats()
        month = database.get_bookings_in_month(
            datetime.date.today().year, datetime.date.today().month)
        self._stat_values = (
            ("Bookings today", str(stats["today"])),
            ("Pending", str(stats["Pending"])),
            ("Bookings this month", str(len(month))),
            ("Completed revenue", "\u20b1" + str(stats["revenue"] or 0)),
        )
        row = tk.Frame(page, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_MD, 0))
        self._stat_labels = {}
        for caption, value in self._stat_values:
            card = Card(row, radius=theme.RADIUS_LG, pad=theme.PAD_MD)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, theme.PAD_SM))
            body = tk.Frame(card.body, bg=theme.BG_SURFACE)
            body.pack(fill="both", expand=True)
            self._stat_labels[caption] = body
            self._paint_stat(body, caption, value)

    def _paint_stat(self, body, caption, value):
        """(Re)paints one stat card content."""
        for widget in body.winfo_children():
            widget.destroy()
        tk.Label(body, text=caption, font=theme.FONT_SMALL,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE,
                 wraplength=150, justify="left").pack(anchor="w")
        tk.Label(body, text=value, font=theme.FONT_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(4, 0))

    def _build_chart(self, columns):
        """Card with the last-7-days canvas chart (oldest to newest)."""
        chart_card = Card(columns, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        chart_card.pack(side="left", fill="both", expand=True,
                        padx=(0, theme.PAD_MD))
        tk.Label(chart_card.body, text="Bookings in the last 7 days",
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        self._chart = tk.Canvas(chart_card.body, height=170,
                                bg=theme.BG_SURFACE, highlightthickness=0)
        self._chart.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._paint_chart()

    def _build_pending(self, columns):
        """Right column: Pending bookings with quick answers."""
        card = Card(columns, radius=theme.RADIUS_LG, pad=theme.PAD_LG,
                    width=340)
        card.pack(side="right", fill="y", expand=False)
        top = tk.Frame(card.body, bg=theme.BG_SURFACE)
        top.pack(fill="x")
        tk.Label(top, text="Needs your answer", font=theme.FONT_CARD_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(side="left")
        self._pending_list = tk.Frame(card.body, bg=theme.BG_SURFACE)
        self._pending_list.pack(fill="both", expand=True)
        self._pending_note = tk.Label(card.body, text="", font=theme.FONT_TINY,
                                      fg=theme.TEXT_MUTED,
                                      bg=theme.BG_SURFACE)
        self._pending_note.pack(anchor="w")
        self._paint_pending()

    # ------------------------------------------------------------------
    # CHART
    # ------------------------------------------------------------------
    def _paint_chart(self):
        """Draws gridlines, 7 bars (oldest left) and day labels."""
        self._chart.delete("all")
        counts = database.get_bookings_last_days(7)
        self._chart.update_idletasks()
        width = max(self._chart.winfo_width(), 420)
        height = 160
        top_pad = 14
        bottom_pad = 30
        usable = height - top_pad - bottom_pad
        biggest = max(1, max(counts.values()) if counts else 1)
        slot_w = width / 7.0
        # light gridlines every quarter of the tallest bar
        for i in range(4):
            y = top_pad + usable - usable * i / 3.0
            self._chart.create_line(0, y, width, y,
                                    fill=theme.BORDER, dash=(2, 3))
        # oldest day first: offsets run 6 (a week ago) down to 0 (today)
        for index, offset in enumerate(range(6, -1, -1)):
            day = datetime.date.today() - datetime.timedelta(days=offset)
            count = counts.get(day.isoformat(), 0)
            x = width - (index + 1) * slot_w
            bar_w = slot_w * 0.44
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
                                        fill=theme.TEXT)
            label = day.strftime("%a %d") if index == 6 \
                else day.strftime("%a %d")
            self._chart.create_text(x0 + bar_w / 2, top_pad + usable + 12,
                                    text=label, font=theme.FONT_TINY,
                                    fill=theme.TEXT_MUTED)

    # ------------------------------------------------------------------
    # PENDING LIST
    # ------------------------------------------------------------------
    def _paint_pending(self):
        """Pending bookings first, each with Accept / Decline buttons."""
        for widget in self._pending_list.winfo_children():
            widget.destroy()
        rows = []
        for row in database.get_bookings_filtered(status="Pending"):
            rows.append(row)
        if not rows:
            self._pending_note.configure(
                text="Nothing waiting - every request has an answer.")
            return
        self._pending_note.configure(
            text=str(len(rows)) + " request(s) waiting.")
        for row in rows[:5]:
            self._pending_row(row)

    def _pending_row(self, row):
        """One pending booking with its two answer buttons."""
        client = row["client_name"] or ("Client #" + str(row["user_id"]))
        when = config.friendly_date(row["booking_date"])[:6] + ", " + \
            row["time_slot"]
        area = row["city"] or ""
        item = tk.Frame(self._pending_list, bg=theme.BG_SURFACE)
        item.pack(fill="x", pady=(theme.PAD_SM, 0))
        tk.Label(item, text="#%d  %s" % (row["id"], client),
                 font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(item, text=when + "  -  " + config.tier_name(row["tier_id"]),
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(item, text=area, font=theme.FONT_TINY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(anchor="w")
        actions = tk.Frame(item, bg=theme.BG_SURFACE)
        actions.pack(anchor="w", pady=(4, 0))
        Button(actions, text="Accept", height=34,
               command=lambda r=row: self._answer(r, "Confirmed"),
               variant="primary").pack(side="left")
        Button(actions, text="Decline", height=34, variant="ghost",
               command=lambda r=row: self._answer(r, "Cancelled")
               ).pack(side="left", padx=(theme.PAD_SM, 0))

    def _answer(self, row, status):
        """Accept or Decline updates the DB right away, then repaints."""
        database.update_status(row["id"], status)
        Toast.show(self.winfo_toplevel(),
                   "#" + str(row["id"]) + " is now " + status,
                   kind="success")
        self.refresh()

    # ------------------------------------------------------------------
    # TODAY LIST
    # ------------------------------------------------------------------
    def _build_today_list(self, page):
        """Card with today's bookings: time, client, package, status pill."""
        card = Card(page, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        card.pack(fill="x", padx=theme.PAD_LG, pady=theme.PAD_MD)
        top = tk.Frame(card.body, bg=theme.BG_SURFACE)
        top.pack(fill="x")
        tk.Label(top, text="Today", font=theme.FONT_CARD_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(side="left")
        Button(top, text="Open bookings",
               command=lambda: self.shell.switch_view("bookings"),
               variant="ghost", height=36).pack(side="right")
        self._today_list = tk.Frame(card.body, bg=theme.BG_SURFACE)
        self._today_list.pack(fill="x")
        self._paint_today()

    def _paint_today(self):
        """Fill the Today list from the database."""
        for widget in self._today_list.winfo_children():
            widget.destroy()
        rows = database.get_bookings_on_date(_iso_today())
        if not rows:
            tk.Label(self._today_list, text="No bookings scheduled today.",
                     font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w",
                                               pady=(theme.PAD_SM, 0))
            return
        rows.sort(key=lambda r: r["time_slot"])
        for row in rows:
            line = tk.Frame(self._today_list, bg=theme.BG_SOFT)
            line.pack(fill="x", pady=2)
            left = tk.Frame(line, bg=theme.BG_SOFT)
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=row["time_slot"] + "   "
                     + (row["client_name"] or "Client #"
                        + str(row["user_id"])), font=theme.FONT_BODY_BOLD,
                     fg=theme.TEXT, bg=theme.BG_SOFT).pack(anchor="w",
                                                           padx=8,
                                                           pady=(6, 0))
            tk.Label(left, text=config.tier_name(row["tier_id"]),
                     font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SOFT).pack(anchor="w", padx=8,
                                            pady=(0, 6))
            StatusPill(line, row["status"]).pack(side="right", padx=8)

    # ------------------------------------------------------------------
    # REFRESH (after an answer is clicked)
    # ------------------------------------------------------------------
    def refresh(self):
        """Rereads stats and repaints the cards and lists."""
        self._build_stats_new()
        self._paint_pending()
        self._paint_today()
        self._paint_chart()

    def _build_stats_new(self):
        """Same four cards, values reread (contents destroyed and repainted)."""
        stats = database.get_admin_stats()
        month = database.get_bookings_in_month(
            datetime.date.today().year, datetime.date.today().month)
        values = (
            ("Bookings today", str(stats["today"])),
            ("Pending", str(stats["Pending"])),
            ("Bookings this month", str(len(month))),
            ("Completed revenue", "\u20b1" + str(stats["revenue"] or 0)),
        )
        for caption, value in values:
            body = self._stat_labels.get(caption)
            if body is not None:
                self._paint_stat(body, caption, value)


def _iso_today():
    """Today as YYYY-MM-DD text."""
    return datetime.date.today().isoformat()


def _today_line():
    """'Wednesday, Oct 21, 2026' for the dashboard header."""
    return datetime.date.today().strftime("%A, %b %d, %Y")

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

from components import (Card, Button, StatusPill, ScrollFrame, Toast,
                        IconBadge, EmptyState)


class AdminDashboard(tk.Frame):
    """Staff overview: numbers, chart, pending answers, today's list."""
    # icon per stat card (MDL2 glyphs, peso uses the currency sign)
    STAT_ICONS = {
        "Bookings today": "\uE787",
        "Pending": "\uE917",
        "Bookings this month": "\uE9D2",
        "Completed revenue": "\u20b1",
    }

    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        super().__init__(master, bg=theme.BG_APP)
        self._build()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        """Scrollable dashboard page.

        Built straight into the shell content (full shell width): sections
        fill the page with PAD_LG margins, and stat/chart cards stretch.
        Do NOT wrap this page in a fixed-width CenteredColumn - the four
        stat-card canvases naturally want ~1592px, so the column's padx
        feedback loop makes the page width grow unbounded.
        """
        scroll = ScrollFrame(self, bg=theme.BG_APP)
        scroll.pack(fill="both", expand=True)
        page = scroll.inner

        head = tk.Frame(page, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        left = tk.Frame(head, bg=theme.BG_APP)
        left.pack(side="left", fill="x", expand=True)
        # friendly greeting instead of a plain page title
        tk.Label(left, text=_greeting(self.shell.current_user),
                 font=theme.FONT_SECTION, fg=theme.TEXT,
                 bg=theme.BG_APP).pack(anchor="w")
        tk.Label(left, text="Here is how things are going today.",
                 font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(anchor="w")

        right = tk.Frame(head, bg=theme.BG_APP)
        right.pack(side="right")
        Button(right, text="View bookings", variant="primary", height=40,
               command=lambda: self.shell.switch_view("bookings")).pack(
                   side="right")
        # small rounded date/time chip beside the button
        chip = Card(right, radius=theme.RADIUS_MD, pad=theme.PAD_SM)
        chip.pack(side="right", padx=(0, theme.PAD_SM))
        tk.Label(chip.body, text=_clock_line(), font=theme.FONT_SMALL,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack()

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
        # four equal-width columns via grid uniform group
        for col_i in range(4):
            row.columnconfigure(col_i, weight=1, uniform="stat")
        self._stat_labels = {}
        for col_i, (caption, value) in enumerate(self._stat_values):
            card = Card(row, radius=theme.RADIUS_LG, pad=theme.PAD_MD)
            # same padx on every card so all four are identical width
            card.grid(row=0, column=col_i, sticky="nsew",
                      padx=(0, theme.PAD_SM))
            body = tk.Frame(card.body, bg=theme.BG_SURFACE)
            body.pack(fill="both", expand=True)
            self._stat_labels[caption] = body
            self._paint_stat(body, caption, value)

    def _paint_stat(self, body, caption, value):
        """(Re)paints one stat card: icon badge, caption, big number."""
        for widget in body.winfo_children():
            widget.destroy()
        glyph = self.STAT_ICONS.get(caption, "\uE80F")
        badge_font = theme.FONT_BODY_BOLD if glyph == "\u20b1" else None
        top = tk.Frame(body, bg=theme.BG_SURFACE)
        top.pack(fill="x")
        IconBadge(top, glyph, size=36, font=badge_font).pack(side="left")
        tk.Label(top, text=caption, font=theme.FONT_SMALL,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE, wraplength=120,
                 justify="left").pack(side="left", padx=(10, 0))
        tk.Label(body, text=value, font=theme.FONT_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w",
                                           pady=(theme.PAD_SM, 0))

    def _build_chart(self, columns):
        """Card with the last-7-days canvas chart (oldest to newest)."""
        chart_card = Card(columns, radius=theme.RADIUS_LG, pad=theme.PAD_LG,
                          stretch=True)
        chart_card.pack(side="left", fill="both", expand=True,
                        padx=(0, theme.PAD_MD))
        tk.Label(chart_card.body, text="Bookings in the last 7 days",
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        # fill="both" lets the chart use the full card height
        self._chart = tk.Canvas(chart_card.body, height=220,
                                bg=theme.BG_SURFACE, highlightthickness=0)
        self._chart.pack(fill="both", expand=True, pady=(theme.PAD_SM, 0))
        # the canvas reports width 1 at build time, so repaint once the card
        # gives it its real size (after_idle keeps us out of the Configure
        # handler; the chart is inside a stretch card, no loop risk)
        self._chart.bind(
            "<Configure>", lambda e: self.after_idle(self._paint_chart))
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
        """Draws y-axis numbers, dotted gridlines, 7 bars and day labels."""
        if not self.winfo_exists():
            return
        self._chart.delete("all")
        counts = database.get_bookings_last_days(7)
        self._chart.update_idletasks()
        width = max(self._chart.winfo_width(), 260)
        height = max(self._chart.winfo_height(), 180)
        gutter = 34
        top_pad = 22
        bottom_pad = 30
        usable = max(40, height - top_pad - bottom_pad)
        values = list(counts.values()) or [0]
        biggest = max(1, max(values))
        # round the top label up to a multiple of 4 so ticks stay whole
        y_max = max(4, ((biggest + 3) // 4) * 4)
        baseline = top_pad + usable
        # y-axis numbers + light dotted gridlines (0 at the bottom)
        for i in range(5):
            y = baseline - usable * i / 4.0
            self._chart.create_line(gutter, y, width, y,
                                    fill=theme.BORDER, dash=(2, 3))
            self._chart.create_text(gutter - 8, y, anchor="e",
                                    text=str(int(round(y_max * i / 4.0))),
                                    font=theme.FONT_TINY,
                                    fill=theme.TEXT_MUTED)
        slot_w = (width - gutter) / 7.0
        # oldest day first: offsets run 6 (a week ago) down to 0 (today)
        for index, offset in enumerate(range(6, -1, -1)):
            day = datetime.date.today() - datetime.timedelta(days=offset)
            count = counts.get(day.isoformat(), 0)
            x = gutter + index * slot_w
            bar_w = slot_w * 0.44
            bar_h = 0 if count == 0 else max(6, usable * count / float(y_max))
            x0 = x + (slot_w - bar_w) / 2
            y1 = baseline - bar_h
            self._chart.create_rectangle(
                x0, y1, x0 + bar_w, baseline, fill=theme.ACCENT,
                outline=theme.ACCENT)
            # count above every bar, even the zero ones
            self._chart.create_text(x0 + bar_w / 2, y1 - 9, text=str(count),
                                    font=theme.FONT_SMALL_BOLD,
                                    fill=theme.TEXT)
            self._chart.create_text(x0 + bar_w / 2, baseline + 12,
                                    text=day.strftime("%a %d"),
                                    font=theme.FONT_TINY,
                                    fill=theme.TEXT_MUTED)

    # ------------------------------------------------------------------
    # PENDING LIST
    # ------------------------------------------------------------------
    def _paint_pending(self):
        """Pending bookings first, each with Accept / Decline buttons."""
        for widget in self._pending_list.winfo_children():
            widget.destroy()
        rows = database.get_bookings_filtered(status="Pending")
        if not rows:
            self._pending_note.configure(text="")
            EmptyState(self._pending_list,
                       "Nothing waiting. Every request has an answer.",
                       bg=theme.BG_SURFACE, icon="\u2713").pack(fill="x")
            return
        self._pending_note.configure(
            text=str(len(rows)) + " request(s) waiting.")
        for row in rows[:5]:
            self._pending_row(row)

    def _pending_row(self, row):
        """One pending booking as a soft row with right-aligned answers."""
        client = (row["client_name"] or "Client #" + str(row["user_id"])).title()
        when = datetime.date.fromisoformat(row["booking_date"]).strftime(
            "%a, %b %d") + ", " + row["time_slot"]
        area = (row["city"] or "").title()
        item = tk.Frame(self._pending_list, bg=theme.ROW_SOFT)
        item.pack(fill="x", pady=(theme.PAD_SM, 0))
        inner = tk.Frame(item, bg=theme.ROW_SOFT)
        inner.pack(fill="x", padx=theme.PAD_MD, pady=theme.PAD_SM)
        left = tk.Frame(inner, bg=theme.ROW_SOFT)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="#" + str(row["id"]) + "  " + client,
                 font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                 bg=theme.ROW_SOFT).pack(anchor="w")
        tk.Label(left, text=when + "  -  " + config.tier_name(row["tier_id"]),
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.ROW_SOFT).pack(anchor="w")
        tk.Label(left, text=area, font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.ROW_SOFT).pack(anchor="w")
        actions = tk.Frame(inner, bg=theme.ROW_SOFT)
        actions.pack(side="right")
        Button(actions, text="Accept", height=32,
               command=lambda r=row: self._answer(r, "Confirmed"),
               variant="primary").pack(side="left")
        Button(actions, text="Decline", height=32, variant="ghost",
               bg=theme.ROW_SOFT,
               command=lambda r=row: self._answer(r, "Cancelled")).pack(
                   side="left", padx=(theme.PAD_SM, 0))

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
            EmptyState(self._today_list,
                       "No bookings scheduled today.",
                       bg=theme.BG_SURFACE, icon="\u25A5").pack(fill="x")
            return
        rows.sort(key=lambda r: r["time_slot"])
        for row in rows:
            # soft row, same style as the pending requests above
            line = tk.Frame(self._today_list, bg=theme.ROW_SOFT)
            line.pack(fill="x", pady=(theme.PAD_SM, 0))
            inner = tk.Frame(line, bg=theme.ROW_SOFT)
            inner.pack(fill="x", padx=theme.PAD_MD, pady=theme.PAD_SM)
            left = tk.Frame(inner, bg=theme.ROW_SOFT)
            left.pack(side="left", fill="x", expand=True)
            client = (row["client_name"] or "Client #"
                      + str(row["user_id"])).title()
            tk.Label(left, text=row["time_slot"] + "   " + client,
                     font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                     bg=theme.ROW_SOFT).pack(anchor="w")
            tk.Label(left, text=config.tier_name(row["tier_id"]),
                     font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                     bg=theme.ROW_SOFT).pack(anchor="w")
            StatusPill(inner, row["status"]).pack(side="right")

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


def _greeting(user):
    """'Good evening, AutoGlide Admin.' from the clock and the user."""
    hour = datetime.datetime.now().hour
    if hour < 12:
        part = "morning"
    elif hour < 18:
        part = "afternoon"
    else:
        part = "evening"
    name = (user["full_name"] or user["username"] or "there").title()
    return "Good " + part + ", " + name + "."


def _clock_line():
    """'Thu, Oct 23  -  6:42 PM' for the dashboard chip."""
    return datetime.datetime.now().strftime("%a, %b %d  -  %I:%M %p")

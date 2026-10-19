"""
screens/admin_schedule.py
=============================================================================
Admin Schedule: a month calendar grid (per-day booking count as a badge,
red tint when a day has pending bookings), prev/next/Today buttons, and a
list of the selected day's bookings that opens the details when clicked
(by jumping to the Bookings page with the booking selected).
=============================================================================
"""

import calendar as cal
import datetime
import tkinter as tk

import theme
import config
import database

from components import Card, Button, StatusPill, Toast


def _today():
    """Returns today as a date object (helper kept for clarity)."""
    return datetime.date.today()


class AdminScheduleView(tk.Frame):
    """Staff month calendar with per-day counts and a day list."""
    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        super().__init__(master, bg=theme.BG_APP)
        today = _today()
        self.year = today.year
        self.month = today.month
        self.selected_date = today.isoformat()
        self._build()
        self._refresh()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        """Title bar, then calendar left and day list right."""
        head = tk.Frame(self, bg=theme.BG_APP)
        head.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, 0))
        self._title = tk.Label(head, text="Schedule", font=theme.FONT_SECTION,
                               fg=theme.TEXT, bg=theme.BG_APP)
        self._title.pack(side="left")

        nav = tk.Frame(head, bg=theme.BG_APP)
        nav.pack(side="right")
        Button(nav, text="< prev", command=self._prev_month,
               variant="ghost").pack(side="left")
        Button(nav, text="Today", command=self._go_today,
               variant="primary").pack(side="left", padx=(8, 8))
        Button(nav, text="next >", command=self._next_month,
               variant="ghost").pack(side="left")

        body = tk.Frame(self, bg=theme.BG_APP)
        body.pack(fill="both", expand=True, padx=theme.PAD_LG,
                  pady=(theme.PAD_MD, theme.PAD_LG))
        self._cal_card = Card(body, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        self._cal_card.pack(side="left", fill="both", expand=True)
        self._grid = tk.Frame(self._cal_card.body, bg=theme.BG_SURFACE)
        self._grid.pack(fill="both", expand=True)

        self._day_card = Card(body, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        self._day_card.pack(side="right", fill="y", expand=False,
                            padx=(theme.PAD_MD, 0))
        self._day_list = tk.Frame(self._day_card.body, bg=theme.BG_SURFACE)
        self._day_list.pack(fill="both", expand=True)

        # Legend line under the calendar explaining the cell colors.
        row = tk.Frame(self, bg=theme.BG_APP)
        row.pack(fill="x", padx=theme.PAD_LG, pady=(0, theme.PAD_LG))
        tk.Label(row, text="A dull red cell means the day still has Pending "
                 "requests.",
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_APP).pack(side="left")

    # ------------------------------------------------------------------
    # CALENDAR
    # ------------------------------------------------------------------
    def _prev_month(self):
        """Moves the calendar one month back."""
        year, month = self.year, self.month - 1
        if month == 0:
            year, month = year - 1, 12
        self.year, self.month = year, month
        self._refresh()

    def _next_month(self):
        """Moves the calendar one month forward."""
        year, month = self.year, self.month + 1
        if month == 13:
            year, month = year + 1, 1
        self.year, self.month = year, month
        self._refresh()

    def _go_today(self):
        """Jumps back to this month and selects today."""
        today = _today()
        self.year, self.month = today.year, today.month
        self.selected_date = today.isoformat()
        self._refresh()

    def _refresh(self):
        """Repaints the grid and the day list for the visible month."""
        self._title.configure(text="Schedule - "
                              + _month_name(self.year, self.month))
        for widget in self._grid.winfo_children():
            widget.destroy()
        days = database.get_bookings_in_month(self.year, self.month)
        counts = {}
        pending_days = set()
        for row in days:
            counts[row["booking_date"]] = counts.get(row["booking_date"], 0) + 1
            if row["status"] == "Pending":
                pending_days.add(row["booking_date"])

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for index, name in enumerate(weekdays):
            tk.Label(self._grid, text=name, font=theme.FONT_SMALL_BOLD,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).grid(
                         row=0, column=index, sticky="ew", pady=(0, 4))
        for index in range(7):
            self._grid.columnconfigure(index, weight=1)

        weeks = cal.monthcalendar(self.year, self.month)
        for r, week in enumerate(weeks):
            for c, day in enumerate(week):
                if day == 0:
                    continue
                iso = "%04d-%02d-%02d" % (self.year, self.month, day)
                self._day_cell(r + 1, c, iso, day, counts.get(iso, 0),
                               iso in pending_days)
        self._refresh_day_list()

    def _day_cell(self, r, c, iso, day, count, has_pending):
        """One calendar cell: date number, count badge, click to select."""
        selected = iso == self.selected_date
        if selected:
            bg = theme.PRIMARY
            fg = theme.TEXT_ON_DARK
        elif has_pending:
            bg = "#F4E3DC"
            fg = theme.DANGER
        else:
            bg = theme.BG_SOFT
            fg = theme.TEXT
        cell = tk.Canvas(self._grid, bg=bg, highlightthickness=1,
                         highlightbackground=theme.BORDER, cursor="hand2")
        cell.grid(row=r, column=c, sticky="nsew", ipady=8, padx=2, pady=2)
        cell.create_text(10, 8, text=str(day), anchor="nw",
                         font=theme.FONT_SMALL_BOLD, fill=fg)
        if count:
            cell.create_rectangle(2, 2, 14 + len(str(count)) * 9, 18,
                                  fill=theme.ACCENT, outline=theme.ACCENT)
            cell.create_text(8 + len(str(count)) * 9, 10, text=str(count),
                             font=theme.FONT_SMALL_BOLD,
                             fill=theme.TEXT_ON_DARK)
        cell.bind("<Button-1>", lambda e, iso=iso: self._pick_day(iso))

    def _pick_day(self, iso):
        """A calendar cell was clicked - show that day's bookings."""
        self.selected_date = iso
        self._refresh()

    # ------------------------------------------------------------------
    # DAY LIST
    # ------------------------------------------------------------------
    def _refresh_day_list(self):
        """Lists the selected day's bookings sorted by time slot."""
        for widget in self._day_list.winfo_children():
            widget.destroy()
        heading = tk.Frame(self._day_list, bg=theme.BG_SURFACE)
        heading.pack(fill="x")
        date_value = datetime.date.fromisoformat(self.selected_date)
        tk.Label(heading, text=_day_heading(date_value),
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        rows = database.get_bookings_on_date(self.selected_date)
        if not rows:
            tk.Label(self._day_list, text="No bookings for this day.",
                     font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w", pady=(8, 0))
            return
        rows.sort(key=lambda r: r["time_slot"])
        for row in rows:
            item = tk.Frame(self._day_list, bg=theme.BG_HOVER, cursor="hand2")
            item.pack(fill="x", pady=3, padx=(0, 4))
            tk.Label(item,
                     text=row["time_slot"] + "  -  #"
                     + str(row["id"]) + "  "
                     + (row["client_name"] or ""),
                     font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                     bg=theme.BG_HOVER).pack(anchor="w", padx=8, pady=(6, 0))
            tk.Label(item,
                     text=config.tier_name(row["tier_id"])
                     + " for a " + row["vehicle_type"],
                     font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_HOVER).pack(anchor="w", padx=8, pady=(0, 6))
            StatusPill(item, row["status"]).pack(anchor="w", padx=8)
            for widget in (item,):
                widget.bind("<Button-1>",
                            lambda e, bid=row["id"]: self._open_booking(bid))

    def _open_booking(self, booking_id):
        """Opens the Bookings page with the row selected."""
        admin = self.shell
        admin.switch_view("bookings")
        if admin.current_view and hasattr(admin.current_view,
                                          "_selected"):
            admin.current_view._selected = booking_id
            admin.current_view.reload()


def _month_name(year, month):
    """'October 2026' for the schedule title."""
    return cal.month_name[month] + " " + str(year)


def _day_heading(date_value):
    """'Mon, Oct 19, 2026' + 'today' note if it is today."""
    text = date_value.strftime("%a, %b %d, %Y")
    if date_value.isoformat() == _today().isoformat():
        text = text + "  (today)"
    return text

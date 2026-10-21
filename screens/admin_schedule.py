"""
screens/admin_schedule.py
=============================================================================
Admin Schedule: month calendar grid with FIXED-height day cells. Each cell
shows the day number plus small status-coloured count chips (pending,
confirmed, done); today gets a pine outline. A right panel (340px) lists the
selected day's bookings with time, client, package, area, status pill and
Accept / Decline buttons on Pending ones, plus a line with the open slots.
=============================================================================
"""

import calendar as cal
import datetime
import tkinter as tk

import theme
import config
import database

from components import (Card, Button, StatusPill, ScrollFrame, Toast,
                        rounded_rectangle)


def _today():
    """Returns today as a date object (helper kept for clarity)."""
    return datetime.date.today()


# status groups shown as chips on each calendar day
CHIPS_NAMES = ["Pending", "Confirmed", "Completed"]


class AdminScheduleView(tk.Frame):
    """Staff month calendar with per-day status chips and a day list."""
    # fixed height for every calendar row so the grid never jiggles
    # (a 6-week month then fits even the 1000x650 minimum window)
    CELL_H = 72

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
        """Title bar, then calendar left and a 340px day panel right."""
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

        # day panel: scrollable list card, fixed width
        self._day_card = Card(body, radius=theme.RADIUS_LG, pad=theme.PAD_SM,
                              width=340)
        self._day_card.pack(side="right", fill="y", expand=False,
                            padx=(theme.PAD_MD, 0))
        tk.Frame(self._day_card.body, bg=theme.BG_SURFACE, height=8
                 ).pack(fill="x")
        self._day_scroll = ScrollFrame(self._day_card.body,
                                       bg=theme.BG_SURFACE)
        self._day_scroll.pack(fill="both", expand=True)
        self._day_list = self._day_scroll.inner

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
        # iso date -> counts per chip group
        chip_counts = {}
        for row in days:
            statuses = chip_counts.setdefault(row["booking_date"], {})
            if row["status"] == "Pending":
                statuses["Pending"] = statuses.get("Pending", 0) + 1
            elif row["status"] in ("Confirmed", "On the Way",
                                   "In Progress"):
                statuses["Confirmed"] = statuses.get("Confirmed", 0) + 1
            elif row["status"] == "Completed":
                statuses["Completed"] = statuses.get("Completed", 0) + 1

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
                self._day_cell(r + 1, c, iso, day,
                               chip_counts.get(iso, {}))
        # fixed heights keep every calendar row the same size
        self._grid.rowconfigure(0, pad=8)
        for r in range(1, len(weeks) + 1):
            self._grid.rowconfigure(r, minsize=self.CELL_H)
        self._refresh_day_list()

    def _day_cell(self, r, c, iso, day, chips):
        """One calendar cell: day number + status chips, click to select.
        The canvas gets an explicit height - without it every row is the
        265px Canvas default and the month overflows the window."""
        selected = iso == self.selected_date
        is_today = iso == _today().isoformat() and not selected
        cell = tk.Canvas(self._grid, height=self.CELL_H,
                         bg=theme.PRIMARY if selected
                         else theme.BG_SOFT,
                         highlightthickness=2 if (selected or is_today) else 1,
                         highlightbackground=theme.PRIMARY
                         if (selected or is_today) else theme.BORDER,
                         cursor="hand2")
        cell.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
        fg = theme.TEXT_ON_DARK if selected else theme.TEXT
        cell.create_text(10, 8, text=str(day), anchor="nw",
                         font=theme.FONT_SMALL_BOLD, fill=fg)
        # one chip per status group that has bookings, left aligned in a row
        chip_x = 10
        chip_y = 34
        for name in CHIPS_NAMES:
            count = chips.get(name, 0)
            if not count:
                continue
            text_color, chip_color = theme.STATUS.get(
                name, (theme.TEXT, theme.BG_HOVER))
            if selected:
                text_color, chip_color = theme.BG_SURFACE, theme.ACCENT
            text = str(count)
            width = 16 + len(text) * 7
            self._chip(cell, chip_x, chip_y, width, chip_color, text,
                       text_color)
            chip_x += width + 4
            if chip_x > 110:
                chip_x = 10
                chip_y += 20
        cell.bind("<Button-1>", lambda e, iso=iso: self._pick_day(iso))

    def _chip(self, cell, x, y, width, color, text, text_color):
        """Draws one small rounded count chip on the cell canvas."""
        rounded_rectangle(cell, x, y, x + width, y + 16, radius=8,
                          fill=color, outline=color)
        cell.create_text(x + width // 2, y + 8, text=text,
                         font=("Segoe UI", 9, "bold"), fill=text_color)

    def _pick_day(self, iso):
        """A calendar cell was clicked - show that day's bookings."""
        self.selected_date = iso
        self._refresh()

    # ------------------------------------------------------------------
    # DAY PANEL
    # ------------------------------------------------------------------
    def _refresh_day_list(self):
        """Selected day's bookings + open slot count in the right panel."""
        for widget in self._day_list.winfo_children():
            widget.destroy()
        body = self._day_list
        heading = tk.Frame(body, bg=theme.BG_SURFACE)
        heading.pack(fill="x", padx=theme.PAD_SM)
        date_value = datetime.date.fromisoformat(self.selected_date)
        tk.Label(heading, text=_day_heading(date_value),
                 font=theme.FONT_CARD_TITLE, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        rows = database.get_bookings_on_date(self.selected_date)
        # how many cars can still be booked that day across the time slots
        open_slots = 0
        for slot in config.TIME_SLOTS:
            used = database.count_slot_bookings(self.selected_date, slot)
            open_slots += max(0, config.SLOT_CAPACITY - used)
        tk.Label(body, text="Open slots: " + str(open_slots),
                 font=theme.FONT_SMALL, fg=theme.PRIMARY,
                 bg=theme.BG_SURFACE).pack(anchor="w", padx=theme.PAD_SM,
                                           pady=(2, 6))
        if not rows:
            tk.Label(body, text="No bookings for this day.",
                     font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w",
                                               padx=theme.PAD_SM,
                                               pady=(8, 0))
            return
        rows.sort(key=lambda r: r["time_slot"])
        for row in rows:
            self._day_row(row)

    def _day_row(self, row):
        """One booking in the day panel, with answers for Pending rows."""
        item = tk.Frame(self._day_list, bg=theme.BG_HOVER, cursor="hand2")
        item.pack(fill="x", pady=3, padx=theme.PAD_SM)
        head = tk.Frame(item, bg=theme.BG_HOVER)
        head.pack(fill="x")
        tk.Label(head, text=row["time_slot"], font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_HOVER).pack(side="left",
                                                        padx=8,
                                                        pady=(6, 0))
        StatusPill(head, row["status"]).pack(side="right", padx=8)
        tk.Label(item, text=row["client_name"] or "Client #"
                 + str(row["user_id"]), font=theme.FONT_SMALL,
                 fg=theme.TEXT, bg=theme.BG_HOVER).pack(anchor="w",
                                                        padx=8)
        tk.Label(item, text=config.tier_name(row["tier_id"]) + "  -  "
                 + (row["city"] or ""), font=theme.FONT_TINY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_HOVER).pack(
                     anchor="w", padx=8)
        if row["status"] == "Pending":
            actions = tk.Frame(item, bg=theme.BG_HOVER)
            actions.pack(anchor="w", padx=8, pady=(2, 6))
            Button(actions, text="Accept", height=32,
                   command=lambda r=row: self._answer(r, "Confirmed"),
                   variant="primary").pack(side="left")
            Button(actions, text="Decline", height=32, variant="ghost",
                   command=lambda r=row: self._answer(r, "Cancelled")
                   ).pack(side="left", padx=(6, 0))
        else:
            tk.Frame(item, bg=theme.BG_HOVER, height=6).pack(padx=8)
        for widget in (item,):
            widget.bind("<Button-1>",
                        lambda e, bid=row["id"]: self._open_booking(bid))

    def _answer(self, row, status):
        """Accept / Decline writes the new status and repaints the panel."""
        database.update_status(row["id"], status)
        Toast.show(self.winfo_toplevel(),
                   "#" + str(row["id"]) + " is now " + status,
                   kind="success")
        self._refresh()

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

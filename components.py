"""
components.py
=============================================================================
Reusable interface pieces for AutoGlide.

Everything on screen is built from these widgets so the whole app looks
consistent:
  Button, Card, SectionHeading, StatCard, StatusPill, SegmentedControl, Chip,
  ScrollFrame, EntryField, DateField, CalendarPopup, DataTable, EmptyState,
  Toast, Dialog helper, and MapPicker.

Only the Python standard library is used (tkinter, ttk, calendar, datetime).
=============================================================================
"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk
import calendar
import datetime
import theme


# ---------------------------------------------------------------------------
# SMALL HELPERS
# ---------------------------------------------------------------------------
def bg_of(widget):
    """Returns a widget's background color so canvases can blend in."""
    try:
        return widget.cget("bg")
    except Exception:
        return theme.BG_APP


def rounded_rectangle(canvas, x1, y1, x2, y2, radius=10, **kwargs):
    """Draws a rounded rectangle on a canvas and returns its id."""
    points = [
        x1 + radius, y1, x2 - radius, y1, x2, y1,
        x2, y1 + radius, x2, y2 - radius, x2, y2,
        x2 - radius, y2, x1 + radius, y2, x1, y2,
        x1, y2 - radius, x1, y1 + radius, x1, y1
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


def bind_wheel(widget, handler):
    """Binds mouse wheel scrolling to a widget and all of its children."""
    widget.bind("<MouseWheel>", handler, add="+")
    widget.bind("<Button-4>", handler, add="+")
    widget.bind("<Button-5>", handler, add="+")
    for child in widget.winfo_children():
        bind_wheel(child, handler)


# ---------------------------------------------------------------------------
# BUTTON
# ---------------------------------------------------------------------------
class Button(tk.Canvas):
    """A flat rounded button with primary, secondary, ghost, and danger styles."""
    def __init__(self, master, text="", command=None, variant="primary",
                 height=36, font=theme.FONT_BUTTON, pad=18, bg=None):
        self._parent_bg = bg if bg else bg_of(master)
        self._font = tkfont.Font(font=font)
        self._font_spec = font
        self._text = text
        self._command = command
        self._variant = variant
        self._enabled = True

        width = self._font.measure(text) + 2 * pad
        super().__init__(master, width=width, height=height, bg=self._parent_bg,
                         highlightthickness=0, bd=0, cursor="hand2")

        self._colors = self._variant_colors(variant)
        self.bind("<Configure>", lambda e: self._draw())
        self.bind("<Enter>", lambda e: self._hover(True))
        self.bind("<Leave>", lambda e: self._hover(False))
        self.bind("<Button-1>", lambda e: self._paint(self._colors[2]))
        self.bind("<ButtonRelease-1>", self._on_release)

    def _variant_colors(self, variant):
        """Returns (fill, hover, active, text, outline) for a variant."""
        if variant == "secondary":
            return (theme.BG_SURFACE, theme.BG_HOVER, theme.BORDER, theme.TEXT,
                    theme.BORDER_STRONG)
        if variant == "ghost":
            return (self._parent_bg, theme.BG_HOVER, theme.BORDER, theme.TEXT,
                    self._parent_bg)
        if variant == "danger":
            return (theme.DANGER, theme.DANGER_HOVER, theme.DANGER,
                    theme.TEXT_ON_DARK, theme.DANGER)
        return (theme.PRIMARY, theme.PRIMARY_HOVER, theme.PRIMARY_ACTIVE,
                theme.TEXT_ON_DARK, theme.PRIMARY)

    def _paint(self, fill):
        """Draws the button with the given fill color."""
        self.delete("all")
        w = self.winfo_width() or int(self["width"])
        h = self.winfo_height() or int(self["height"])
        _, _, _, fg, outline = self._colors
        if not self._enabled:
            fill = theme.BG_HOVER
            fg = theme.TEXT_FAINT
            outline = theme.BORDER
        rounded_rectangle(self, 1, 1, w - 1, h - 1, theme.RADIUS_SM,
                          fill=fill, outline=outline, width=1)
        self.create_text(w // 2, h // 2, text=self._text, font=self._font_spec,
                         fill=fg)

    def _draw(self):
        """Draws the button in its normal state."""
        self._paint(self._colors[0])

    def _hover(self, entering):
        """Hover fill when enabled."""
        if self._enabled:
            self._paint(self._colors[1] if entering else self._colors[0])

    def set_variant(self, variant):
        """Changes the look variant after creation (used by filter chips)."""
        self._variant = variant
        self._colors = self._variant_colors(variant)
        self._draw()

    def _on_release(self, event=None):
        """Runs the command when the mouse is released on the button."""
        if not self._enabled:
            return
        self._paint(self._colors[1])
        if self._command:
            self._command()

    def set_enabled(self, enabled):
        """Enables or disables the button."""
        self._enabled = enabled
        self.configure(cursor="hand2" if enabled else "arrow")
        self._draw()

    def set_text(self, text):
        """Changes the button label."""
        self._text = text
        self._draw()


# ---------------------------------------------------------------------------
# CARD (rounded panel that grows with its content)
# ---------------------------------------------------------------------------
class Card(tk.Canvas):
    """A rounded surface panel. Put content inside card.body."""
    def __init__(self, master, radius=theme.RADIUS_MD, bg=theme.BG_SURFACE,
                 border=theme.BORDER, pad=theme.PAD_MD, **kwargs):
        self._parent_bg = bg_of(master)
        super().__init__(master, bg=self._parent_bg, highlightthickness=0,
                         bd=0, **kwargs)
        self._card_bg = bg
        self.card_bg = bg  # public alias used when screens repaint cards
        self._radius = radius
        self._border = border
        self._pad = pad
        self._last_h = -1
        self._last_w = -1

        self.body = tk.Frame(self, bg=bg)
        self._win = self.create_window(pad, pad, window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._sync)
        self.bind("<Configure>", self._sync)

    def _sync(self, event=None):
        """Keeps the card sized to its content and redraws the border."""
        w = self.winfo_width()
        if w <= 1:
            return
        want_h = self.body.winfo_reqheight() + 2 * self._pad
        if want_h != self._last_h:
            self._last_h = want_h
            self.configure(height=want_h)
        inner_w = w - 2 * self._pad
        if inner_w != self._last_w:
            self._last_w = inner_w
            self.itemconfigure(self._win, width=inner_w)
        self._draw(w, self.winfo_height())

    def set_card_bg(self, bg):
        """Repaints the card fill (used to highlight a selected card)."""
        self._card_bg = bg
        self.card_bg = bg
        self.body.configure(bg=bg)
        self._draw(self.winfo_width(), self.winfo_height())

    def _draw(self, w, h):
        """Draws the rounded background and thin border."""
        self.delete("cardbg")
        rounded_rectangle(self, 1, 1, w - 1, h - 1, self._radius,
                          fill=self._card_bg, outline=self._border, width=1,
                          tags="cardbg")
        self.tag_lower("cardbg")


# ---------------------------------------------------------------------------
# SECTION HEADING
# ---------------------------------------------------------------------------
class SectionHeading(tk.Frame):
    """A title with an optional subtitle."""
    def __init__(self, master, title, subtitle=None, bg=None):
        bg = bg or bg_of(master)
        super().__init__(master, bg=bg)
        tk.Label(self, text=title, font=theme.FONT_TITLE, fg=theme.TEXT,
                 bg=bg).pack(anchor="w")
        if subtitle:
            tk.Label(self, text=subtitle, font=theme.FONT_SMALL,
                     fg=theme.TEXT_MUTED, bg=bg).pack(anchor="w", pady=(2, 0))


# ---------------------------------------------------------------------------
# STAT CARD
# ---------------------------------------------------------------------------
class StatCard(Card):
    """A card showing one big number with a caption."""
    def __init__(self, master, caption, value="0", note=""):
        super().__init__(master, pad=theme.PAD_MD)
        self.value_label = tk.Label(self.body, text=value, font=theme.FONT_HERO,
                                    fg=theme.TEXT, bg=theme.BG_SURFACE)
        self.value_label.pack(anchor="w")
        tk.Label(self.body, text=caption, font=theme.FONT_SMALL,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(anchor="w")
        self.note_label = tk.Label(self.body, text=note, font=theme.FONT_TINY,
                                   fg=theme.TEXT_FAINT, bg=theme.BG_SURFACE)
        self.note_label.pack(anchor="w", pady=(4, 0))

    def set_value(self, value, note=None):
        """Updates the number and optional note."""
        self.value_label.configure(text=value)
        if note is not None:
            self.note_label.configure(text=note)


# ---------------------------------------------------------------------------
# STATUS PILL
# ---------------------------------------------------------------------------
class StatusPill(tk.Canvas):
    """A small rounded colored tag for a booking status."""
    def __init__(self, master, status, bg=None):
        self._parent_bg = bg or bg_of(master)
        text_color, fill = theme.STATUS.get(status,
                                            (theme.TEXT_MUTED, theme.BG_HOVER))
        font = tkfont.Font(font=theme.FONT_SMALL_BOLD)
        width = font.measure(status) + 22
        super().__init__(master, width=width, height=24, bg=self._parent_bg,
                         highlightthickness=0, bd=0)
        rounded_rectangle(self, 1, 1, width - 1, 23, 12, fill=fill,
                          outline=fill)
        self.create_text(width // 2, 12, text=status, font=theme.FONT_SMALL_BOLD,
                         fill=text_color)


# ---------------------------------------------------------------------------
# SEGMENTED CONTROL (replaces radio buttons)
# ---------------------------------------------------------------------------
class SegmentedControl(tk.Frame):
    """A row of connected options where one is selected."""
    def __init__(self, master, options, command=None, value=None, bg=None):
        bg = bg or bg_of(master)
        super().__init__(master, bg=bg, highlightbackground=theme.BORDER,
                         highlightthickness=1)
        self.command = command
        self.value = value if value is not None else options[0]
        self.labels = {}
        for option in options:
            label = tk.Label(self, text=option, font=theme.FONT_SMALL, padx=14,
                             pady=6, cursor="hand2", bg=theme.BG_SURFACE,
                             fg=theme.TEXT_MUTED)
            label.pack(side="left")
            label.bind("<Button-1>", lambda e, opt=option: self._select(opt))
            label.bind("<Enter>", lambda e, opt=option: self._hover(opt, True))
            label.bind("<Leave>", lambda e, opt=option: self._hover(opt, False))
            self.labels[option] = label
        self._refresh()

    def _select(self, option):
        """Selects an option and notifies the command."""
        self.value = option
        self._refresh()
        if self.command:
            self.command(option)

    def _hover(self, option, entering):
        """Light hover effect on unselected options."""
        if option == self.value:
            return
        self.labels[option].configure(
            bg=theme.BG_HOVER if entering else theme.BG_SURFACE)

    def _refresh(self):
        """Repaints all options to show the selected one."""
        for option, label in self.labels.items():
            if option == self.value:
                label.configure(bg=theme.PRIMARY, fg=theme.TEXT_ON_DARK)
            else:
                label.configure(bg=theme.BG_SURFACE, fg=theme.TEXT_MUTED)

    def get(self):
        """Returns the selected option."""
        return self.value

    def set(self, option):
        """Sets the selection without calling the command."""
        self.value = option
        self._refresh()


# ---------------------------------------------------------------------------
# CHIP (used for time slots)
# ---------------------------------------------------------------------------
class Chip(tk.Canvas):
    """A small selectable tag. States: normal, selected, full (disabled)."""
    def __init__(self, master, text, command=None, state="normal", bg=None):
        self._parent_bg = bg or bg_of(master)
        self._font = tkfont.Font(font=theme.FONT_SMALL)
        self.text = text
        self.command = command
        self.state = state
        width = self._font.measure(text) + 28
        super().__init__(master, width=width, height=26, bg=self._parent_bg,
                         highlightthickness=0, bd=0)
        self._hovering = False
        self._draw()
        if state != "full":
            self.configure(cursor="hand2")
            self.bind("<Enter>", lambda e: self._set_hover(True))
            self.bind("<Leave>", lambda e: self._set_hover(False))
            self.bind("<Button-1>", lambda e: self._click())

    def _draw(self):
        """Paints the chip to match its current state."""
        self.delete("all")
        w = int(self["width"])
        if self.state == "selected":
            fill, text_color, outline = theme.PRIMARY, theme.TEXT_ON_DARK, theme.PRIMARY
        elif self.state == "full":
            fill, text_color, outline = theme.BG_HOVER, theme.TEXT_FAINT, theme.BORDER
        else:
            fill = theme.BG_HOVER if self._hovering else theme.BG_SURFACE
            text_color, outline = theme.TEXT, theme.BORDER_STRONG
        rounded_rectangle(self, 1, 1, w - 1, 25, 12, fill=fill, outline=outline,
                          width=1)
        self.create_text(w // 2, 13, text=self.text, font=theme.FONT_SMALL,
                         fill=text_color)

    def _set_hover(self, entering):
        """Hover effect for normal chips."""
        if self.state == "normal":
            self._hovering = entering
            self._draw()

    def _click(self):
        """Selects the chip and notifies the command."""
        if self.state == "full":
            return
        self.state = "selected"
        self._draw()
        if self.command:
            self.command()

    def set_state(self, state):
        """Changes the chip state."""
        self.state = state
        self._draw()


# ---------------------------------------------------------------------------
# SCROLL FRAME
# ---------------------------------------------------------------------------
class ScrollFrame(tk.Frame):
    """A vertical scrolling area with a thin scroll bar."""
    def __init__(self, master, bg=theme.BG_SURFACE, **kwargs):
        super().__init__(master, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical",
                                       style="Thin.Vertical.TScrollbar",
                                       command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.bind_wheel(self.canvas)
        self.bind_wheel(self.inner)

    def _on_inner(self, event=None):
        """Updates the scroll region when content changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, event):
        """Stretches the inner frame to the canvas width."""
        self.canvas.itemconfigure(self._win, width=event.width)

    def _wheel(self, event):
        """Scrolls the canvas with the mouse wheel."""
        if event.delta:
            self.canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def bind_wheel(self, widget):
        """Binds the wheel to a widget and all of its current children."""
        widget.bind("<MouseWheel>", self._wheel, add="+")
        widget.bind("<Button-4>", self._wheel, add="+")
        widget.bind("<Button-5>", self._wheel, add="+")
        for child in widget.winfo_children():
            self.bind_wheel(child)


# ---------------------------------------------------------------------------
# ENTRY FIELD
# ---------------------------------------------------------------------------
class EntryField(tk.Frame):
    """A labeled text input with a focus border, placeholder, and error text."""
    def __init__(self, master, label, placeholder="", show=None, width=30,
                 text=None, bg=None):
        bg = bg or bg_of(master)
        super().__init__(master, bg=bg)
        self._placeholder = placeholder
        self._showing_placeholder = False

        if label:
            tk.Label(self, text=label, font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                     bg=bg).pack(anchor="w", pady=(0, 4))

        self.var = tk.StringVar(value=text or "")
        options = {
            "textvariable": self.var,
            "font": theme.FONT_BODY,
            "bg": theme.BG_INPUT,
            "fg": theme.TEXT,
            "relief": "flat",
            "highlightthickness": 1,
            "highlightbackground": theme.BORDER,
            "highlightcolor": theme.BORDER,
            "width": width,
            "insertbackground": theme.TEXT
        }
        if show:
            options["show"] = show
        self.entry = tk.Entry(self, **options)
        self.entry.pack(fill="x", ipady=6)
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self._on_type)

        self.error_label = tk.Label(self, text="", font=theme.FONT_TINY,
                                    fg=theme.DANGER, bg=bg)

        if placeholder and not (text and text.strip()):
            self._show_placeholder()

    def _show_placeholder(self):
        """Shows the placeholder text in a faint color."""
        self._showing_placeholder = True
        self.var.set(self._placeholder)
        self.entry.configure(fg=theme.TEXT_FAINT)

    def _clear_placeholder(self):
        """Removes the placeholder text."""
        self._showing_placeholder = False
        self.var.set("")
        self.entry.configure(fg=theme.TEXT)

    def _on_focus_in(self, event=None):
        """Highlights the border and clears any placeholder."""
        self.entry.configure(highlightbackground=theme.PRIMARY,
                             highlightcolor=theme.PRIMARY, highlightthickness=1)
        if self._showing_placeholder:
            self._clear_placeholder()

    def _on_focus_out(self, event=None):
        """Restores the border and re-adds the placeholder if empty."""
        self.entry.configure(highlightbackground=theme.BORDER,
                             highlightcolor=theme.BORDER)
        if self._placeholder and self.var.get().strip() == "":
            self._show_placeholder()

    def _on_type(self, event=None):
        """Clears the error message while the user types."""
        if self.error_label.winfo_ismapped():
            self.clear_error()

    def get(self):
        """Returns the current text (empty if the placeholder is showing)."""
        if self._showing_placeholder:
            return ""
        return self.var.get().strip()

    def set(self, value):
        """Sets the field value."""
        self._showing_placeholder = False
        self.entry.configure(fg=theme.TEXT)
        self.var.set(value if value is not None else "")

    def set_error(self, message):
        """Shows an error message under the field and colors the border."""
        self.error_label.configure(text=message)
        self.error_label.pack(anchor="w", pady=(4, 0))
        self.entry.configure(highlightbackground=theme.DANGER,
                             highlightcolor=theme.DANGER)

    def clear_error(self):
        """Removes the error text."""
        self.error_label.configure(text="")
        self.error_label.pack_forget()
        self.entry.configure(highlightbackground=theme.BORDER,
                             highlightcolor=theme.BORDER)


# ---------------------------------------------------------------------------
# CALENDAR POPUP (custom date picker)
# ---------------------------------------------------------------------------
class CalendarPopup(tk.Toplevel):
    """A small month calendar. Past dates are disabled."""
    def __init__(self, master, initial=None, on_pick=None):
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(bg=theme.BORDER_STRONG)
        self.on_pick = on_pick
        self.today = datetime.date.today()
        if initial:
            try:
                self.view = datetime.datetime.strptime(initial, "%Y-%m-%d").date()
            except ValueError:
                self.view = self.today
        else:
            self.view = self.today
        self.view = self.view.replace(day=1)

        self.inner = tk.Frame(self, bg=theme.BG_SURFACE)
        self.inner.pack(padx=1, pady=1)
        self._build()
        self.bind("<Escape>", lambda e: self.destroy())
        self.grab_set()

    def _build(self):
        """Builds the header, weekday row, and day grid."""
        for child in self.inner.winfo_children():
            child.destroy()

        header = tk.Frame(self.inner, bg=theme.BG_SURFACE)
        header.pack(fill="x", padx=8, pady=8)
        prev = tk.Label(header, text="<", font=theme.FONT_BUTTON, bg=theme.BG_SURFACE,
                        fg=theme.TEXT, padx=8, cursor="hand2")
        prev.pack(side="left")
        prev.bind("<Button-1>", lambda e: self._shift(-1))
        nxt = tk.Label(header, text=">", font=theme.FONT_BUTTON, bg=theme.BG_SURFACE,
                       fg=theme.TEXT, padx=8, cursor="hand2")
        nxt.pack(side="right")
        nxt.bind("<Button-1>", lambda e: self._shift(1))
        title = self.view.strftime("%B %Y")
        tk.Label(header, text=title, font=theme.FONT_BODY_BOLD, bg=theme.BG_SURFACE,
                 fg=theme.TEXT).pack(side="left", expand=True)

        grid = tk.Frame(self.inner, bg=theme.BG_SURFACE)
        grid.pack(padx=8, pady=(0, 8))
        for index, day in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
            tk.Label(grid, text=day, font=theme.FONT_TINY, fg=theme.TEXT_FAINT,
                     bg=theme.BG_SURFACE, width=3).grid(row=0, column=index)

        weeks = calendar.Calendar().monthdatescalendar(self.view.year, self.view.month)
        for r, week in enumerate(weeks, start=1):
            for c, day in enumerate(week):
                self._day_cell(grid, day, r, c)

    def _day_cell(self, grid, day, row, col):
        """Draws one day number, disabling past days."""
        in_month = (day.month == self.view.month)
        is_past = day < self.today
        if not in_month or is_past:
            color = theme.TEXT_FAINT
        else:
            color = theme.TEXT
        label = tk.Label(grid, text=str(day.day), font=theme.FONT_SMALL,
                         fg=color, bg=theme.BG_SURFACE, width=3, pady=4)
        label.grid(row=row, column=col)
        if in_month and not is_past:
            label.configure(cursor="hand2")
            label.bind("<Enter>", lambda e, l=label: l.configure(bg=theme.BG_HOVER))
            label.bind("<Leave>", lambda e, l=label: l.configure(bg=theme.BG_SURFACE))
            label.bind("<Button-1>", lambda e, d=day: self._pick(d))

    def _shift(self, months):
        """Moves the view one month forward or back."""
        month = self.view.month + months
        year = self.view.year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        self.view = datetime.date(year, month, 1)
        self._build()

    def _pick(self, day):
        """Returns the chosen date and closes."""
        if self.on_pick:
            self.on_pick(day.strftime("%Y-%m-%d"))
        self.destroy()


class DateField(tk.Frame):
    """A read-only date input that opens the calendar popup."""
    def __init__(self, master, label="Date", value="", on_change=None,
                 bg=None):
        bg = bg or bg_of(master)
        super().__init__(master, bg=bg)
        self._bg = bg
        self._value = value
        self.on_change = on_change
        if label:
            tk.Label(self, text=label, font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                     bg=bg).pack(anchor="w", pady=(0, 4))
        self.canvas = tk.Canvas(self, height=34, bg=bg, highlightthickness=0, bd=0,
                                cursor="hand2")
        self.canvas.pack(fill="x")
        self.canvas.bind("<Configure>", lambda e: self._draw())
        self.canvas.bind("<Button-1>", lambda e: self._open())
        self._draw()

    def _min_width(self):
        """Returns the canvas width or a default."""
        w = self.canvas.winfo_width()
        if w <= 1:
            return 240
        return w

    def _draw(self):
        """Draws the input box with the current date text."""
        c = self.canvas
        c.delete("all")
        w = self._min_width()
        rounded_rectangle(c, 1, 1, w - 1, 33, theme.RADIUS_SM,
                          fill=theme.BG_INPUT, outline=theme.BORDER, width=1)
        text = self._value if self._value else "Select a date"
        color = theme.TEXT if self._value else theme.TEXT_FAINT
        c.create_text(12, 17, text=text, anchor="w", font=theme.FONT_BODY,
                      fill=color)
        c.create_text(w - 14, 17, text="v", anchor="center",
                      font=theme.FONT_SMALL_BOLD, fill=theme.TEXT_MUTED)

    def _open(self):
        """Opens the calendar popup below the field."""
        self.canvas.update_idletasks()
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty() + self.canvas.winfo_height() + 2
        popup = CalendarPopup(self, initial=self._value, on_pick=self.set)
        popup.geometry("+%d+%d" % (x, y))
        popup.focus_set()

    def get(self):
        """Returns the chosen date string."""
        return self._value

    def set(self, value):
        """Sets the date, redraws, and notifies on_change."""
        self._value = value
        self._draw()
        if self.on_change:
            self.on_change()


# ---------------------------------------------------------------------------
# DATA TABLE (custom, supports a colored status pill column)
# ---------------------------------------------------------------------------
class DataTable(tk.Frame):
    """
    A scrollable table built from labels so a status column can show a real
    pill. Columns are dictionaries: key, title, weight, minsize, anchor, pill.
    """
    def __init__(self, master, columns, on_select=None, bg=theme.BG_SURFACE):
        super().__init__(master, bg=bg)
        self.columns = columns
        self.on_select = on_select
        self._rows = []
        self._row_frames = []
        self._selected = None

        # Header row (with a spacer to line up with the scroll bar).
        self.header = tk.Frame(self, bg=theme.BG_SOFT)
        self.header.pack(fill="x")
        self._configure_columns(self.header)
        for index, column in enumerate(columns):
            tk.Label(self.header, text=column["title"], font=theme.FONT_SMALL_BOLD,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SOFT, anchor=column.get("anchor", "w")
                     ).grid(row=0, column=index, sticky="ew", padx=10, pady=9)
        tk.Frame(self.header, bg=theme.BG_SOFT, width=12).grid(
            row=0, column=len(columns), sticky="ns")
        self.header.columnconfigure(len(columns), weight=0, minsize=12)

        # Body.
        self.body = ScrollFrame(self, bg=bg)
        self.body.pack(fill="both", expand=True)
        self.body.inner.configure(bg=bg)

    def _configure_columns(self, frame):
        """Applies the same column weights to a frame so rows line up."""
        for index, column in enumerate(self.columns):
            frame.columnconfigure(index, weight=column.get("weight", 1),
                                  minsize=column.get("minsize", 90))

    def set_rows(self, rows):
        """Replaces the table content."""
        self._rows = rows
        for child in self.body.inner.winfo_children():
            child.destroy()
        self._row_frames = []
        self._selected = None

        if not rows:
            tk.Label(self.body.inner, text="Nothing to show yet.",
                     font=theme.FONT_SMALL, fg=theme.TEXT_FAINT, bg=theme.BG_SURFACE,
                     pady=20).pack(fill="x")
            return

        for index, row in enumerate(rows):
            self._build_row(index, row)

        self.body.bind_wheel(self.body.inner)
        self.body.inner.update_idletasks()
        self.body.canvas.configure(scrollregion=self.body.canvas.bbox("all"))

    def _build_row(self, index, row):
        """Builds one row of cells."""
        base = theme.BG_SOFT if index % 2 else theme.BG_SURFACE
        frame = tk.Frame(self.body.inner, bg=base)
        frame.pack(fill="x")
        self._configure_columns(frame)
        widgets = []

        for col_index, column in enumerate(self.columns):
            key = column["key"]
            value = row.get(key, "")
            if column.get("pill"):
                holder = tk.Frame(frame, bg=base)
                holder.grid(row=0, column=col_index, sticky="w", padx=10, pady=6)
                pill = StatusPill(holder, str(value), bg=base)
                pill.pack()
                widgets.append(holder)
                widgets.append(pill)
            else:
                label = tk.Label(frame, text=str(value), font=theme.FONT_BODY,
                                 fg=theme.TEXT, bg=base, anchor=column.get("anchor", "w"),
                                 justify="left")
                label.grid(row=0, column=col_index, sticky="ew", padx=10, pady=8)
                widgets.append(label)

        frame._widgets = widgets
        frame._index = index
        frame._base = base
        self._row_frames.append(frame)

        for widget in [frame] + widgets:
            widget.bind("<Button-1>", lambda e, i=index: self._select(i))
            widget.bind("<Enter>", lambda e, f=frame: self._hover(f, True))
            widget.bind("<Leave>", lambda e, f=frame: self._hover(f, False))

    def _paint_row(self, frame, color):
        """Recolors a row and its cells."""
        frame.configure(bg=color)
        for widget in frame._widgets:
            try:
                widget.configure(bg=color)
            except Exception:
                pass

    def _hover(self, frame, entering):
        """Hover highlight for a row."""
        if frame is self._selected:
            return
        self._paint_row(frame, theme.BG_HOVER if entering else frame._base)

    def _select(self, index):
        """Selects a row and notifies the listener."""
        if self._selected is not None:
            self._paint_row(self._selected, self._selected._base)
        frame = self._row_frames[index]
        self._selected = frame
        self._paint_row(frame, theme.ACCENT_SOFT)
        if self.on_select:
            self.on_select(self._rows[index], index)

    def clear(self):
        """Empties the table."""
        self.set_rows([])

    def selected_row(self):
        """Returns the selected row dictionary or None."""
        if self._selected is None:
            return None
        return self._rows[self._selected._index]


# ---------------------------------------------------------------------------
# CHECK FIELD (a canvas checkbox with a text label)
# ---------------------------------------------------------------------------
class CheckField(tk.Frame):
    """A simple toggle checkbox drawn on a canvas with a text label."""
    def __init__(self, master, label, checked=False, bg=None):
        bg = bg or bg_of(master)
        super().__init__(master, bg=bg)
        self._bg = bg
        self.checked = checked
        self.box = tk.Canvas(self, width=18, height=18, bg=bg,
                             highlightthickness=0, bd=0, cursor="hand2")
        self.text = tk.Label(self, text=label, font=theme.FONT_BODY,
                             fg=theme.TEXT, bg=bg, cursor="hand2")
        self.box.pack(side="left")
        self.text.pack(side="left", padx=(6, 0))
        self.box.bind("<Button-1>", lambda e: self.toggle())
        self.text.bind("<Button-1>", lambda e: self.toggle())
        self._draw()

    def _draw(self):
        """Paints the box and the check mark when checked."""
        c = self.box
        c.delete("all")
        outline = theme.PRIMARY if self.checked else theme.BORDER_STRONG
        fill = theme.PRIMARY if self.checked else theme.BG_SURFACE
        rounded_rectangle(c, 1, 1, 17, 17, 4, fill=fill, outline=outline)
        if self.checked:
            c.create_text(9, 9, text="\u2713", font=theme.FONT_TINY,
                          fill=theme.TEXT_ON_DARK)

    def toggle(self):
        """Flips the checkbox and repaints."""
        self.checked = not self.checked
        self._draw()

    def get(self):
        """Returns True when the box is checked."""
        return self.checked

    def set(self, value):
        """Sets the checkbox state directly."""
        self.checked = bool(value)
        self._draw()


# ---------------------------------------------------------------------------
# ACCORDION (a question row that expands/collapses, used by the Help page)
# ---------------------------------------------------------------------------
class Accordion(tk.Frame):
    """One FAQ row: clicking the question shows or hides the answer."""
    def __init__(self, master, question, answer, bg=theme.BG_SURFACE):
        super().__init__(master, bg=bg)
        self._bg = bg
        self.answer_data = answer
        self._open = False
        self.header = tk.Frame(self, bg=bg, cursor="hand2")
        self.header.pack(fill="x")
        self.q_text = tk.Label(self.header, text=question,
                               font=theme.FONT_BODY_BOLD, fg=theme.TEXT, bg=bg,
                               anchor="w")
        self.q_text.pack(side="left", fill="x", expand=True)
        self.arrow = tk.Label(self.header, text="v", font=theme.FONT_SMALL_BOLD,
                              fg=theme.TEXT_MUTED, bg=bg)
        self.arrow.pack(side="right", padx=10)
        self.body = None
        for widget in (self.header, self.q_text, self.arrow):
            widget.bind("<Button-1>", lambda e: self.toggle())
        self.header.bind("<Enter>", lambda e: self.header.configure(
            bg=theme.BG_HOVER) or self.q_text.configure(bg=theme.BG_HOVER))
        self.header.bind("<Leave>", lambda e: self.header.configure(
            bg=self._bg) or self.q_text.configure(bg=self._bg))

    def toggle(self):
        """Opens or closes the answer area."""
        if self._open:
            self.body.destroy()
            self.body = None
            self.arrow.configure(text="v")
            self._open = False
        else:
            self.body = tk.Frame(self, bg=self._bg)
            self.body.pack(fill="x")
            tk.Label(self.body, text=self.answer_text(), font=theme.FONT_SMALL,
                     fg=theme.TEXT_MUTED, bg=self._bg, wraplength=620,
                     justify="left").pack(anchor="w", padx=(24, 10),
                                          pady=(0, 10))
            self.arrow.configure(text="^")
            self._open = True

    def answer_text(self):
        """Returns the stored answer text."""
        return self.answer_data if isinstance(self.answer_data, str) else ""


# ---------------------------------------------------------------------------
# EMPTY STATE
# ---------------------------------------------------------------------------
class EmptyState(tk.Frame):
    """A friendly message with a button, shown when a table has no rows."""
    def __init__(self, master, text, button_text=None, command=None, bg=None):
        bg = bg or bg_of(master)
        super().__init__(master, bg=bg)
        tk.Label(self, text="", bg=bg).pack(pady=(20, 0))
        tk.Label(self, text=text, font=theme.FONT_BODY, fg=theme.TEXT_MUTED,
                 bg=bg, wraplength=360, justify="center").pack()
        if button_text:
            Button(self, text=button_text, command=command, variant="primary",
                   bg=bg).pack(pady=14)


# ---------------------------------------------------------------------------
# TOAST (small message that appears bottom-right and fades)
# ---------------------------------------------------------------------------
class Toast:
    """
    Shows a short-lived message near the bottom right of the window.
    Two calling styles: Toast.show(root, message, kind="success") or the
    shortcut Toast(master, message, variant="ok"/"error"/"info").
    """
    _active = None
    _KINDS = {"ok": "success", "info": "success", "error": "error"}

    def __init__(self, master=None, message="", variant="ok"):
        # (comment: screens can say Toast(self, "...") instead of Toast.show)
        root = master.winfo_toplevel() if master is not None else None
        kind = Toast._KINDS.get(variant, "success")
        if root is not None:
            Toast.show(root, message, kind=kind)
        else:
            root = tk._get_default_root()
            Toast.show(root, message, kind=kind)

    @staticmethod
    def show(root, message, kind="success"):
        """Displays a toast near the bottom right of a window."""
        if Toast._active is not None:
            try:
                Toast._active.destroy()
            except Exception:
                pass

        color = theme.PRIMARY if kind == "success" else (
            theme.ACCENT if kind == "info" else theme.DANGER)
        top = tk.Toplevel(root)
        Toast._active = top
        top.overrideredirect(True)
        top.configure(bg=theme.BG_SURFACE)
        try:
            top.attributes("-topmost", True)
        except Exception:
            pass

        canvas = tk.Canvas(top, bg=theme.BG_SURFACE, highlightthickness=0, bd=0)
        canvas.pack()
        font = tkfont.Font(font=theme.FONT_BODY)
        width = font.measure(message) + 56
        height = 46
        canvas.configure(width=width, height=height)
        rounded_rectangle(canvas, 1, 1, width - 1, height - 1, theme.RADIUS_SM,
                          fill=theme.BG_SURFACE, outline=theme.BORDER, width=1)
        canvas.create_rectangle(1, 1, 5, height - 1, fill=color, outline=color)
        canvas.create_text(24, height / 2, text=message, anchor="w",
                           font=theme.FONT_BODY, fill=theme.TEXT)

        # Position bottom-right of the main window.
        root.update_idletasks()
        x = root.winfo_rootx() + root.winfo_width() - width - 24
        y = root.winfo_rooty() + root.winfo_height() - height - 24
        top.geometry("+%d+%d" % (x, y))

        try:
            top.attributes("-alpha", 0.0)
        except Exception:
            pass
        Toast._fade_in(top, 0.0)
        top.after(2600, lambda: Toast._fade_out(top, 0.95))

    @staticmethod
    def _fade_in(top, alpha):
        """Fades the toast in."""
        if not top.winfo_exists():
            return
        alpha = min(0.95, alpha + 0.12)
        try:
            top.attributes("-alpha", alpha)
        except Exception:
            return
        if alpha < 0.95:
            top.after(16, lambda: Toast._fade_in(top, alpha))

    @staticmethod
    def _fade_out(top, alpha):
        """Fades the toast out and destroys it."""
        if not top.winfo_exists():
            return
        alpha = alpha - 0.08
        try:
            top.attributes("-alpha", max(0.0, alpha))
        except Exception:
            alpha = 0
        if alpha > 0:
            top.after(16, lambda: Toast._fade_out(top, alpha))
        else:
            try:
                top.destroy()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# DIALOG HELPER (modal window with a dimmed backdrop)
# ---------------------------------------------------------------------------
def open_dialog(parent, title, width, height, build, on_close=None):
    """
    Opens a modal Toplevel with a dimmed backdrop.
    'build' is a function that receives the content frame to fill.
    Returns the dialog window.
    """
    root = parent.winfo_toplevel()

    # Dim backdrop over the whole window (alpha may not work on every OS).
    backdrop = tk.Toplevel(root)
    backdrop.overrideredirect(True)
    backdrop.configure(bg="#000000")
    try:
        backdrop.attributes("-alpha", 0.28)
    except Exception:
        pass
    root.update_idletasks()
    backdrop.geometry("%dx%d+%d+%d" % (root.winfo_width(), root.winfo_height(),
                                       root.winfo_rootx(), root.winfo_rooty()))

    dialog = tk.Toplevel(root)
    dialog.title(title)
    dialog.configure(bg=theme.BG_APP)
    dialog.transient(root)

    header = tk.Frame(dialog, bg=theme.BG_SURFACE)
    header.pack(fill="x")
    tk.Label(header, text=title, font=theme.FONT_TITLE, fg=theme.TEXT,
             bg=theme.BG_SURFACE).pack(side="left", padx=theme.PAD_LG, pady=theme.PAD_MD)
    close = tk.Label(header, text="x", font=theme.FONT_BUTTON, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE, padx=12, cursor="hand2")
    close.pack(side="right", padx=theme.PAD_SM)
    close.bind("<Button-1>", lambda e: close_dialog())
    tk.Frame(dialog, bg=theme.BORDER, height=1).pack(fill="x")

    content = tk.Frame(dialog, bg=theme.BG_APP)
    content.pack(fill="both", expand=True)
    build(content)

    def close_dialog():
        """Closes the dialog and removes the backdrop."""
        if on_close:
            on_close()
        try:
            backdrop.destroy()
        except Exception:
            pass
        dialog.destroy()

    dialog.close = close_dialog
    dialog.bind("<Escape>", lambda e: close_dialog())

    # Center on the main window.
    root.update_idletasks()
    x = root.winfo_rootx() + (root.winfo_width() - width) // 2
    y = root.winfo_rooty() + (root.winfo_height() - height) // 3
    dialog.geometry("%dx%d+%d+%d" % (width, height, max(0, x), max(0, y)))

    dialog.grab_set()
    dialog.focus_set()
    return dialog


# ---------------------------------------------------------------------------

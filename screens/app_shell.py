"""
screens/app_shell.py
=============================================================================
The two main app layouts, chosen by role.

ClientShell   - top navigation bar (brand left, page tabs center, profile
                button right). Content sits in a centered column.
AdminShell    - left sidebar with the four staff pages. Content is wide.

Both shells expose switch_view(name), current_view_name and a refresh()
that the screens use when data changes.
=============================================================================
"""

import tkinter as tk

import theme
import config
import database

from screens.admin_clients import AdminClientsView
from screens.client_home import HomeView
from screens.booking_wizard import BookingWizard
from screens.my_bookings_screen import MyBookingsView
from screens.vehicles_screen import VehiclesView
from screens.addresses_screen import AddressesView
from screens.profile_screen import ProfileView
from screens.help_screen import HelpView
from screens.admin_screen import AdminDashboard
from screens.admin_bookings import AdminBookingsView
from screens.admin_schedule import AdminScheduleView
from screens.admin_clients import AdminClientsView


class ClientShell(tk.Frame):
    """The client app layout with a top navigation bar."""
    # tab key -> label shown in the top bar
    TABS = [
        ("home", "Home"),
        ("my_bookings", "My Bookings"),
        ("new_booking", "New Booking"),
        ("vehicles", "Vehicles"),
        ("addresses", "Addresses"),
        ("help", "Help"),
    ]

    def __init__(self, master, app):
        self.app = app
        self.current_user = app.current_user
        # beige app background, not white, so page edges blend with content
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self.current_view = None
        self.current_view_name = ""
        self._tabs = {}
        self._refresh_job = None
        app.shell = self
        self._build()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        """Top nav bar + the content column below it."""
        nav = tk.Frame(self, bg=theme.BG_SURFACE)
        nav.pack(fill="x")
        tk.Frame(self, bg=theme.BORDER, height=1).pack(fill="x")
        self._nav = nav

        brand = tk.Frame(nav, bg=theme.BG_SURFACE)
        brand.pack(side="left", padx=(theme.PAD_LG, 0), pady=theme.PAD_SM)
        dot = tk.Canvas(brand, width=10, height=10, bg=theme.BG_SURFACE,
                        highlightthickness=0)
        dot.create_oval(1, 1, 9, 9, fill=theme.PRIMARY,
                        outline=theme.PRIMARY)
        dot.pack(side="left")
        tk.Label(brand, text=" AutoGlide", font=theme.FONT_BRAND,
                 fg=theme.PRIMARY, bg=theme.BG_SURFACE).pack(side="left")

        middle = tk.Frame(nav, bg=theme.BG_SURFACE)
        middle.pack(side="left", padx=theme.PAD_XL)
        for key, label in ClientShell.TABS:
            tab = tk.Label(middle, text=label, font=theme.FONT_BODY,
                           fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE,
                           cursor="hand2", padx=10, pady=6)
            tab.pack(side="left")
            tab.bind("<Button-1>", lambda e=None, k=key: self.switch_view(k))
            tab.bind("<Enter>", lambda e=None, t=tab: self._hover_tab(t, True))
            tab.bind("<Leave>", lambda e=None, t=tab: self._hover_tab(t, False))
            self._tabs[key] = tab

        profile = tk.Frame(nav, bg=theme.BG_SURFACE)
        profile.pack(side="right", padx=(0, theme.PAD_LG))
        self._profile_btn = tk.Label(
            profile, text=self._initials(), font=theme.FONT_SMALL_BOLD,
            fg=theme.TEXT_ON_DARK, bg=theme.PRIMARY, width=3,
            cursor="hand2", pady=2)
        self._profile_btn.pack()
        self._profile_btn.bind("<Button-1>", self._open_profile_menu)

        # one content frame only - the old nested pair left empty frames
        # behind and showed white gutters around each page
        # padx keeps the page margin that views expected before
        content = tk.Frame(self, bg=theme.BG_APP)
        content.pack(fill="both", expand=True, padx=theme.PAD_LG * 2)
        self._content = content
        self._content_holder = content
        self.switch_view("home")

    def _initials(self):
        """The two letters shown in the round profile button."""
        parts = (self.current_user["full_name"] or "").split()
        letters = "".join(p[0] for p in parts if p)[:2]
        return (letters or "?").upper()

    def _hover_tab(self, tab, inside):
        """Light hover feedback that respects the active tab color."""
        if tab is self._current_tab:
            return
        tab.configure(fg=theme.TEXT if inside else theme.TEXT_MUTED)

    # ------------------------------------------------------------------
    # PROFILE MENU
    # ------------------------------------------------------------------
    def _open_profile_menu(self, event=None):
        """Small menu under the initials button: profile and logout."""
        menu = tk.Menu(self, tearoff=0, font=theme.FONT_BODY,
                       bg=theme.BG_SURFACE, fg=theme.TEXT,
                       activebackground=theme.BG_HOVER,
                       activeforeground=theme.TEXT)
        menu.add_command(label="Profile and Security",
                         command=lambda: self.switch_view("profile"))
        menu.add_separator()
        menu.add_command(label="Log Out", command=self.app.logout)
        try:
            menu.tk_popup(self._profile_btn.winfo_rootx(),
                          self._profile_btn.winfo_rooty()
                          + self._profile_btn.winfo_height() + 4)
        finally:
            menu.grab_release()

    # ------------------------------------------------------------------
    # VIEW SWITCHING
    # ------------------------------------------------------------------
    def switch_view(self, name):
        """Destroys the current page and builds the requested one."""
        if name == self.current_view_name and self.current_view:
            return
        if self._refresh_job:
            try:
                self.after_cancel(self._refresh_job)
            except Exception:
                pass
            self._refresh_job = None
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None
        for key, tab in self._tabs.items():
            if key == name:
                tab.configure(fg=theme.PRIMARY, font=theme.FONT_BODY_BOLD)
            else:
                tab.configure(fg=theme.TEXT_MUTED, font=theme.FONT_BODY)
        self._current_tab = self._tabs.get(name)

        builders = {
            "home": HomeView,
            "my_bookings": MyBookingsView,
            "new_booking": BookingWizard,
            "vehicles": VehiclesView,
            "addresses": AddressesView,
            "profile": ProfileView,
            "help": HelpView,
        }
        if name not in builders:
            name = "home"
        self.current_view_name = name
        self.built_name = name
        # rebuild inside the single content frame so no empty frame stacks up
        for child in self._content.winfo_children():
            child.destroy()
        self._content_holder = self._content
        view = builders[name](self._content, self)
        view.pack(fill="both", expand=True)
        self.current_view = view


class AdminShell(tk.Frame):
    """The staff app layout with a left sidebar."""
    ITEMS = [
        ("dashboard", "Dashboard"),
        ("bookings", "Bookings"),
        ("schedule", "Schedule"),
        ("clients", "Clients"),
    ]

    def __init__(self, master, app):
        self.app = app
        self.current_user = app.current_user
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)
        self.current_view = None
        self.current_view_name = ""
        self._rows = {}
        app.shell = self
        self._build()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build(self):
        """Sidebar + wide content area."""
        sidebar = tk.Frame(self, bg=theme.PRIMARY, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand_area = tk.Frame(sidebar, bg=theme.PRIMARY)
        brand_area.pack(fill="x", pady=(theme.PAD_LG, theme.PAD_XL))
        dot = tk.Canvas(brand_area, width=10, height=10, bg=theme.PRIMARY,
                        highlightthickness=0)
        dot.pack(side="left", padx=(theme.PAD_LG, 0))
        dot.create_oval(1, 1, 9, 9, fill=theme.ACCENT, outline=theme.ACCENT)
        tk.Label(brand_area, text=" AutoGlide", font=theme.FONT_BRAND,
                 fg=theme.TEXT_ON_DARK, bg=theme.PRIMARY).pack(side="left")

        middle = tk.Frame(sidebar, bg=theme.PRIMARY)
        middle.pack(fill="both", expand=True)
        for key, label in AdminShell.ITEMS:
            row = tk.Label(middle, text="  " + label,
                           font=theme.FONT_BODY, fg=theme.TEXT_ON_DARK,
                           bg=theme.PRIMARY, anchor="w", pady=9,
                           cursor="hand2")
            row.pack(fill="x")
            row.bind("<Button-1>", lambda e=None, k=key: self.switch_view(k))
            row.bind("<Enter>", lambda e=None, r=row: self._hover(r, True))
            row.bind("<Leave>", lambda e=None, r=row: self._hover(r, False))
            self._rows[key] = row

        bottom = tk.Frame(sidebar, bg=theme.PRIMARY)
        bottom.pack(fill="x", pady=theme.PAD_MD)
        tk.Label(bottom, text=self._who(), font=theme.FONT_TINY,
                 fg=theme.ACCENT_SOFT, bg=theme.PRIMARY,
                 anchor="w").pack(fill="x", padx=theme.PAD_LG)
        logout = tk.Label(bottom, text="  Log Out", font=theme.FONT_BODY_BOLD,
                          fg=theme.TEXT_ON_DARK, bg=theme.PRIMARY,
                          anchor="w", pady=6, cursor="hand2")
        logout.pack(fill="x")
        logout.bind("<Button-1>", lambda e=None: self.app.logout())

        content = tk.Frame(self, bg=theme.BG_APP)
        content.pack(side="left", fill="both", expand=True)
        self._content_holder = content
        self.switch_view("dashboard")

    def _who(self):
        """Shows who is signed in under the menu."""
        return (self.current_user["username"] or "").strip()

    def _hover(self, row, inside):
        """Sidebar hover color, skipping the active row."""
        if row is self._current_row:
            return
        # PRIMARY_HOVER exists; PRIMARY_DARK does not (crashed on hover)
        row.configure(bg=theme.PRIMARY_HOVER if inside else theme.PRIMARY)

    # ------------------------------------------------------------------
    # VIEW SWITCHING
    # ------------------------------------------------------------------
    def switch_view(self, name):
        """Builds one of the four staff pages."""
        if name == self.current_view_name and self.current_view:
            return
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None
        for key, row in self._rows.items():
            active = key == name
            row.configure(font=theme.FONT_BODY_BOLD if active
                          else theme.FONT_BODY,
                          bg=theme.BG_APP if active else theme.PRIMARY,
                          fg=theme.PRIMARY if active else theme.TEXT_ON_DARK)
        bar = self._rows.get(name)
        if bar:
            self._current_row = bar
        if name not in ("dashboard", "bookings", "schedule", "clients"):
            name = "dashboard"
        self.current_view_name = name
        self.built_name = name
        self._content_holder.destroy()
        self._content_holder = tk.Frame(self, bg=theme.BG_APP)
        self._content_holder.pack(side="left", fill="both", expand=True)
        builders = {
            "dashboard": AdminDashboard,
            "bookings": AdminBookingsView,
            "schedule": AdminScheduleView,
            "clients": AdminClientsView,
        }
        view = builders[name](self._content_holder, self)
        view.pack(fill="both", expand=True)
        self.current_view = view

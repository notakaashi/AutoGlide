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
import utils.images

from components import (CenteredColumn, ScrollFrame, Card, Button,
                        SidebarItem, IconBadge, nav_glyph)


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
        # the actual logo picture, not the old green dot
        logo = utils.images.load_image("logo.jpg", (38, 38), rounded=8)
        logo_lbl = tk.Label(brand, image=logo, bg=theme.BG_SURFACE)
        logo_lbl.image = logo
        logo_lbl.pack(side="left", padx=(0, 6))
        tk.Label(brand, text="AutoGlide", font=theme.FONT_BRAND,
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
        # round profile picture replaces the initials button
        pfp = utils.images.load_image("pfp.jpg", (36, 36), rounded=18)
        self._profile_btn = tk.Label(profile, image=pfp,
                                     bg=theme.BG_SURFACE, cursor="hand2")
        self._profile_btn.image = pfp
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

    def _hover_tab(self, tab, inside):
        """Light hover feedback that respects the active tab color."""
        if tab is self._current_tab:
            return
        tab.configure(fg=theme.TEXT if inside else theme.TEXT_MUTED)

    # ------------------------------------------------------------------
    # PROFILE MENU
    # ------------------------------------------------------------------
    def _open_profile_menu(self, event=None):
        """Small menu under the profile picture: profile and logout."""
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
        # views that handle their own centering (Home centers a scroll page)
        if name == "home":
            holder = self._content
        elif name == "new_booking":
            # the wizard owns the window and scrolls inside its card
            holder = CenteredColumn(self._content, width=1100,
                                    fill_height=True)
            self._content_holder = holder
        elif name == "my_bookings":
            # table + details page fills the window like the staff one
            available = self._content.winfo_width() - 2 * theme.PAD_LG
            holder = CenteredColumn(self._content,
                                    width=max(1020, available),
                                    fill_height=True)
            self._content_holder = holder
        else:
            # every other page scrolls on its own, so a long list of saved
            # vehicles/addresses never pushes content out of reach
            scroll = ScrollFrame(self._content, bg=theme.BG_APP)
            scroll.pack(fill="both", expand=True)
            self._content_holder = scroll
            holder = CenteredColumn(scroll.inner, width=1020)
        view = builders[name](holder, self)
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
        """Sidebar with pill menu + wide content area."""
        sidebar = tk.Frame(self, bg=theme.PRIMARY, width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand_area = tk.Frame(sidebar, bg=theme.PRIMARY)
        brand_area.pack(fill="x", padx=theme.PAD_MD,
                        pady=(theme.PAD_LG, theme.PAD_LG))
        # the actual logo picture, not the old accent dot
        logo = utils.images.load_image("logo.jpg", (38, 38), rounded=8)
        logo_lbl = tk.Label(brand_area, image=logo, bg=theme.PRIMARY)
        logo_lbl.image = logo
        logo_lbl.pack(side="left")
        tk.Label(brand_area, text=" AutoGlide", font=theme.FONT_BRAND,
                 fg=theme.TEXT_ON_DARK, bg=theme.PRIMARY).pack(side="left")

        # small section caption above the menu items
        tk.Label(sidebar, text="MENU", font=theme.FONT_TINY,
                 fg=theme.ACCENT_SOFT, bg=theme.PRIMARY, anchor="w").pack(
                     fill="x", padx=theme.PAD_LG, pady=(0, 6))

        middle = tk.Frame(sidebar, bg=theme.PRIMARY)
        middle.pack(fill="both", expand=True, padx=theme.PAD_SM)
        for key, label in AdminShell.ITEMS:
            glyph, icon_font = nav_glyph(key)
            item = SidebarItem(middle, glyph, label, font=icon_font,
                               command=lambda k=key: self.switch_view(k))
            item.pack(fill="x", pady=2)
            self._rows[key] = item

        # bottom user card: avatar initials, name, role and Sign out
        user_card = Card(sidebar, bg=theme.ACCENT, border=theme.ACCENT,
                         pad=theme.PAD_MD)
        user_card.pack(side="bottom", fill="x", padx=theme.PAD_MD,
                       pady=(theme.PAD_MD, theme.PAD_LG))

        # Top part of the card: avatar and name/role
        top = tk.Frame(user_card.body, bg=theme.ACCENT)
        top.pack(fill="x")

        avatar = IconBadge(top, self._initials(), size=36,
                           bg=theme.ACCENT, fill=theme.ACCENT_SOFT,
                           fg=theme.PRIMARY, font=theme.FONT_SMALL_BOLD)
        avatar.pack(side="left")

        info = tk.Frame(top, bg=theme.ACCENT)
        info.pack(side="left", padx=(10, 0))
        tk.Label(info, text=self._display_name(), font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT_ON_DARK, bg=theme.ACCENT,
                 anchor="w").pack(anchor="w")
        tk.Label(info, text="Admin", font=theme.FONT_TINY,
                 fg=theme.ACCENT_SOFT, bg=theme.ACCENT,
                 anchor="w").pack(anchor="w")

        # Bottom part: the sign out button (now correctly below the name)
        Button(user_card.body, text="Sign out", command=self.app.logout,
               variant="light", height=34).pack(fill="x",
                                                pady=(theme.PAD_MD, 0))

        content = tk.Frame(self, bg=theme.BG_APP)
        content.pack(side="left", fill="both", expand=True)
        self._content = content
        self._content_holder = content
        self.switch_view("dashboard")

    def _display_name(self):
        """Full name when we have one, otherwise the username."""
        user = self.current_user
        return (user["full_name"] or user["username"] or "Admin").strip()

    def _initials(self):
        """Two letters for the round avatar."""
        parts = (self.current_user["full_name"]
                 or self.current_user["username"] or "A").split()
        letters = "".join(p[0] for p in parts if p)[:2]
        return (letters or "A").upper()

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
        if name not in ("dashboard", "bookings", "schedule", "clients"):
            name = "dashboard"
        for key, row in self._rows.items():
            row.set_active(key == name)
        self.current_view_name = name
        self.built_name = name
        # clear the old column, then build the staff page
        for child in self._content.winfo_children():
            child.destroy()
        # The dashboard is a full scroll page that handles its own centering
        # (like client home). Wrapping it in a fixed-width column clipped the
        # page to the canvas-default height, which squeezed the chart and
        # pending cards into a thin strip.
        if name == "dashboard":
            holder = self._content
            self._content_holder = self._content
        else:
            # staff pages fill the window and scroll inside their cards
            # (tables and the calendar stretch; no page-level scrollbar)
            available = self._content.winfo_width() - 2 * theme.PAD_LG
            holder = CenteredColumn(self._content, width=max(1150, available),
                                    fill_height=True)
            self._content_holder = holder
        builders = {
            "dashboard": AdminDashboard,
            "bookings": AdminBookingsView,
            "schedule": AdminScheduleView,
            "clients": AdminClientsView,
        }
        view = builders[name](holder, self)
        view.pack(fill="both", expand=True)
        self.current_view = view

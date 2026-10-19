"""
screens/app_shell.py
=============================================================================
Application shell after login.

Contains the left sidebar (navigation), the slim top bar (page title and
avatar with initials), and the content area. Each nav item switches the
content view. Simple views placeholder until their screens are built.
=============================================================================
"""

import tkinter as tk
import theme
import components
from screens.dashboard_screen import ClientDashboardScreen
from screens.booking_wizard import BookingWizard
from screens.my_bookings_screen import MyBookingsScreen
from screens.admin_screen import AdminScreen


class PlaceholderView(tk.Frame):
    """A simple card used for views that are not built yet."""
    def __init__(self, master, text):
        super().__init__(master, bg=theme.BG_APP)
        card = components.Card(self)
        card.pack(fill="both", expand=True)
        tk.Label(card.body, text=text, font=theme.FONT_SECTION,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                     expand=True, pady=theme.PAD_XL)


class AppShell(tk.Frame):
    """The main shell that wraps all logged-in screens."""
    def __init__(self, master, app):
        self.app = app
        app.shell = self
        bg = theme.BG_APP
        super().__init__(master, bg=bg)

        self.nav_items = []
        self.current_view = None
        self._avatar_canvas = None
        self._top_avatar = None
        self._user_label = None
        self._role_label = None

        self._build_layout()
        self._build_sidebar()
        self._build_topbar()
        self._build_content()
        self.show_default()

    # ------------------------------------------------------------------
    # STRUCTURE
    # ------------------------------------------------------------------
    def _build_layout(self):
        """Splits the shell into sidebar and main area."""
        self.pack(fill="both", expand=True)
        self.sidebar = tk.Frame(self, bg=theme.BG_SIDEBAR, width=230)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.main = tk.Frame(self, bg=theme.BG_APP)
        self.main.pack(side="left", fill="both", expand=True)

    def _build_sidebar(self):
        """Builds brand, navigation frame, user block, and logout."""
        brand = tk.Frame(self.sidebar, bg=theme.BG_SIDEBAR)
        brand.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_LG, theme.PAD_MD))
        tk.Label(brand, text="AutoGlide", font=theme.FONT_BRAND,
                 fg=theme.PRIMARY, bg=theme.BG_SIDEBAR).pack(anchor="w")
        tk.Label(brand, text="Mobile Detailing", font=theme.FONT_TINY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SIDEBAR).pack(anchor="w")

        self.nav_frame = tk.Frame(self.sidebar, bg=theme.BG_SIDEBAR)
        self.nav_frame.pack(fill="x", padx=theme.PAD_SM)

        user_block = tk.Frame(self.sidebar, bg=theme.BG_SIDEBAR)
        user_block.pack(side="bottom", fill="x", padx=theme.PAD_LG,
                        pady=theme.PAD_MD)
        self._avatar_canvas = tk.Canvas(user_block, width=40, height=40,
                                        bg=theme.BG_SIDEBAR, highlightthickness=0,
                                        bd=0)
        self._avatar_canvas.pack(side="left")
        self._draw_avatar()

        info = tk.Frame(user_block, bg=theme.BG_SIDEBAR)
        info.pack(side="left", padx=(theme.PAD_SM, 0), fill="x", expand=True)
        self._user_label = tk.Label(info, text="", font=theme.FONT_BODY_BOLD,
                                    fg=theme.TEXT, bg=theme.BG_SIDEBAR,
                                    anchor="w")
        self._user_label.pack(fill="x")
        self._role_label = tk.Label(info, text="", font=theme.FONT_TINY,
                                    fg=theme.TEXT_MUTED, bg=theme.BG_SIDEBAR,
                                    anchor="w")
        self._role_label.pack(fill="x")
        self._logout_label = tk.Label(info, text="Log out", font=theme.FONT_SMALL_BOLD,
                                      fg=theme.DANGER, bg=theme.BG_SIDEBAR,
                                      cursor="hand2", anchor="w")
        self._logout_label.pack(fill="x", pady=(4, 0))
        self._logout_label.bind("<Button-1>", lambda e: self.app.logout())
        self._logout_label.bind("<Enter>", lambda e: self._logout_label.configure(
            fg=theme.DANGER_HOVER))
        self._logout_label.bind("<Leave>", lambda e: self._logout_label.configure(
            fg=theme.DANGER))

    def _draw_avatar(self):
        """Draws the sidebar initials avatar."""
        if not self._avatar_canvas:
            return
        c = self._avatar_canvas
        c.delete("all")
        initials = self._initials()
        c.create_oval(1, 1, 39, 39, fill=theme.PRIMARY, outline=theme.PRIMARY)
        c.create_text(20, 20, text=initials, font=theme.FONT_BODY_BOLD,
                      fill=theme.TEXT_ON_DARK)

    def _draw_top_avatar(self):
        """Draws the top-right initials avatar."""
        if not self._top_avatar:
            return
        c = self._top_avatar
        c.delete("all")
        c.create_oval(1, 1, 33, 33, fill=theme.ACCENT_SOFT, outline=theme.ACCENT)
        c.create_text(17, 17, text=self._initials(), font=theme.FONT_SMALL_BOLD,
                      fill=theme.PRIMARY)

    def _initials(self):
        """Returns the user's initials."""
        user = self.app.current_user
        name = user["full_name"] if user else "GU"
        return "".join(n[0] for n in name.split() if n)[:2].upper() or "U"

    def _build_topbar(self):
        """Builds the slim top bar."""
        skin = tk.Frame(self.main, bg=theme.BG_SURFACE, height=60)
        skin.pack(fill="x")
        skin.pack_propagate(False)
        self.title_label = tk.Label(skin, text="My Bookings", font=theme.FONT_TITLE,
                                    fg=theme.TEXT, bg=theme.BG_SURFACE)
        self.title_label.pack(side="left", padx=theme.PAD_LG,
                              pady=theme.PAD_MD)
        self.subtitle_label = tk.Label(skin, text="", font=theme.FONT_SMALL,
                                       fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE)
        self.subtitle_label.pack(side="left", padx=(0, theme.PAD_SM))
        right = tk.Frame(skin, bg=theme.BG_SURFACE)
        right.pack(side="right", padx=theme.PAD_LG)
        self._top_avatar = tk.Canvas(right, width=34, height=34, bg=theme.BG_SURFACE,
                                     highlightthickness=0, bd=0)
        self._top_avatar.pack(side="left")
        self._draw_top_avatar()
        line = tk.Frame(self.main, bg=theme.BORDER, height=1)
        line.pack(fill="x")

    def _build_content(self):
        """Builds the content area that hosts the current view."""
        outer = tk.Frame(self.main, bg=theme.BG_APP)
        outer.pack(fill="both", expand=True)
        self.content_frame = tk.Frame(outer, bg=theme.BG_APP)
        self.content_frame.pack(fill="both", expand=True,
                                padx=theme.PAD_LG, pady=theme.PAD_LG)

    # ------------------------------------------------------------------
    # NAVIGATION
    # ------------------------------------------------------------------
    def _clear_nav(self):
        """Removes all nav items."""
        for item in self.nav_items:
            item.destroy()
        self.nav_items = []

    def _add_nav(self, text, view_name):
        """Adds one nav item and binds its click action."""
        btn = tk.Frame(self.nav_frame, bg=theme.BG_SIDEBAR)
        btn.pack(fill="x", pady=1)
        bar = tk.Canvas(btn, width=4, height=26, bg=theme.BG_SIDEBAR,
                        highlightthickness=0, bd=0)
        bar.pack(side="left")
        label = tk.Label(btn, text=text, font=theme.FONT_BODY,
                         fg=theme.TEXT_MUTED, bg=theme.BG_SIDEBAR,
                         anchor="w", cursor="hand2")
        label.pack(side="left", fill="x", expand=True, padx=(6, 8),
                   ipady=6)
        btn._bar = bar
        btn._label = label
        btn._view = view_name
        btn._is_active = False
        for widget in (btn, label):
            widget.bind("<Enter>", lambda e: self._nav_hover(btn, True))
            widget.bind("<Leave>", lambda e: self._nav_hover(btn, False))
        label.bind("<Button-1>", lambda e, v=view_name: self.switch_view(v))
        self.nav_items.append(btn)

    def _nav_hover(self, btn, entering):
        """Hover tint for inactive nav items."""
        if getattr(btn, "_is_active", False):
            return
        color = theme.BG_HOVER if entering else theme.BG_SIDEBAR
        btn._label.configure(bg=color)
        btn.configure(bg=color)

    def _set_active(self, view_name):
        """Marks one nav item as the active one."""
        for btn in self.nav_items:
            is_active = (btn._view == view_name)
            btn._is_active = is_active
            if is_active:
                btn._label.configure(bg=theme.ACCENT_SOFT, fg=theme.PRIMARY,
                                     font=theme.FONT_BODY_BOLD)
                btn._bar.delete("all")
                btn._bar.create_rectangle(0, 0, 3, 26, fill=theme.PRIMARY,
                                          outline=theme.PRIMARY)
                btn.configure(bg=theme.ACCENT_SOFT)
            else:
                btn._label.configure(bg=theme.BG_SIDEBAR, fg=theme.TEXT_MUTED,
                                     font=theme.FONT_BODY)
                btn._bar.delete("all")
                btn.configure(bg=theme.BG_SIDEBAR)

    # ------------------------------------------------------------------
    # VIEWS
    # ------------------------------------------------------------------
    def _clear_content(self):
        """Removes the current view."""
        for child in self.content_frame.winfo_children():
            child.destroy()

    def switch_view(self, view_name):
        """Switches the content area to the requested view."""
        self.current_view = view_name
        self._set_active(view_name)
        meta = self._meta_for(view_name)
        self.title_label.configure(text=meta.get("title",
                                                 view_name.replace("_", " ").title()))
        self.subtitle_label.configure(text=meta.get("subtitle", ""))
        self._clear_content()
        view = self._view_for(view_name)
        if view is not None:
            view.pack(fill="both", expand=True)

    def _view_for(self, view_name):
        """Creates the correct view for a nav name."""
        user = self.app.current_user
        if user is None:
            return None
        if user["role"] == "admin":
            if view_name == "dashboard":
                return AdminScreen(self.content_frame, app=self.app)
            if view_name == "bookings":
                return PlaceholderView(self.content_frame,
                                       "Bookings management coming next.")
        else:
            if view_name == "new_booking":
                return BookingWizard(self.content_frame, app=self.app)
            if view_name == "my_bookings":
                return MyBookingsScreen(self.content_frame, app=self.app)
            if view_name == "saved_vehicles":
                return PlaceholderView(self.content_frame,
                                       "Saved vehicles coming next.")
            if view_name == "saved_addresses":
                return PlaceholderView(self.content_frame,
                                       "Saved addresses coming next.")
            if view_name == "profile":
                return PlaceholderView(self.content_frame,
                                       "Profile and security coming next.")
            if view_name == "help":
                return PlaceholderView(self.content_frame,
                                       "Help center coming next.")
        return PlaceholderView(self.content_frame,
                               view_name.replace("_", " ").title()
                               + " is on the way.")

    def _meta_for(self, view_name):
        """Returns title and optional subtitle for a view."""
        return {
            "dashboard": {"title": "Dashboard",
                           "subtitle": "Today at a glance"},
            "bookings": {"title": "Bookings", "subtitle": "All bookings"},
            "schedule": {"title": "Schedule", "subtitle": "Month overview"},
            "detailers": {"title": "Detailers", "subtitle": "Team roster"},
            "services": {"title": "Services and Prices",
                          "subtitle": "Packages, add-ons, zones"},
            "clients": {"title": "Clients", "subtitle": "Customer accounts"},
            "settings": {"title": "Settings", "subtitle": "Preferences"},
            "my_bookings": {"title": "My Bookings",
                             "subtitle": "Past and upcoming"},
            "new_booking": {"title": "New Booking",
                             "subtitle": "Five quick steps"},
            "saved_vehicles": {"title": "Saved Vehicles",
                                "subtitle": "Cars you can reuse"},
            "saved_addresses": {"title": "Saved Addresses",
                                 "subtitle": "Locations you book often"},
            "profile": {"title": "Profile and Security",
                         "subtitle": "Your details"},
            "help": {"title": "Help", "subtitle": "Answers and contacts"},
        }.get(view_name, {"title": view_name.replace("_", " ").title()})

    def show_default(self):
        """Shows the default view for the user role and builds the nav."""
        user = self.app.current_user
        if not user:
            return
        self._clear_nav()
        role = user["role"]
        if role == "admin":
            self._add_nav("Dashboard", "dashboard")
            self._add_nav("Bookings", "bookings")
            self._add_nav("Schedule", "schedule")
            self._add_nav("Detailers", "detailers")
            self._add_nav("Services and Prices", "services")
            self._add_nav("Clients", "clients")
            self._add_nav("Settings", "settings")
            self.switch_view("dashboard")
        else:
            self._add_nav("My Bookings", "my_bookings")
            self._add_nav("New Booking", "new_booking")
            self._add_nav("Saved Vehicles", "saved_vehicles")
            self._add_nav("Saved Addresses", "saved_addresses")
            self._add_nav("Profile and Security", "profile")
            self._add_nav("Help", "help")
            self.switch_view("my_bookings")
        if self._user_label:
            self._user_label.configure(text=user["full_name"])
        if self._role_label:
            self._role_label.configure(text=role.title())

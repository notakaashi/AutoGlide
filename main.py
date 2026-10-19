"""
main.py
=============================================================================
AutoGlide - Mobile Auto Detailing Scheduler
Main application entry point.

Responsibilities:
  - Creates the Tkinter window
  - Holds session state (logged in user and the booking draft)
  - Creates the database on first run
  - Switches between screens (landing/login/register and the app shell)
=============================================================================
"""

import ctypes
import tkinter as tk
import theme
import config
import database

from screens.landing_screen import LandingScreen
from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.app_shell import AppShell


class AutoGlideApp(tk.Tk):
    """The main window. It also acts as the controller for the whole app."""
    def __init__(self):
        super().__init__()

        # DPI awareness (comment: keep rendering crisp on Windows).
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        # 1. Window settings
        self.title(config.BRAND_INFO["name"] + " - Mobile Auto Detailing Scheduler")
        self.geometry("1280x780")
        self.minsize(1000, 650)
        self.configure(bg=theme.BG_APP)

        # 2. Session state
        self.current_user = None      # a database row, or None for guests
        self.pending_screen = None    # screen to open after a successful login
        self.booking_draft = {
            "vehicle_type": "Sedan",
            "tier_id": "wash_vacuum"
        }

        # 3. Make sure the database and its tables exist
        database.initialize_database()

        # 4. Container that holds the current screen
        self.container = tk.Frame(self, bg=theme.BG_APP)
        self.container.pack(fill="both", expand=True)
        self.current_screen = None

        # 5. Start on the landing page
        self.show_screen("landing")

    def show_screen(self, screen_name):
        """Destroys the current screen and builds the requested one."""
        if self.current_screen is not None:
            self.current_screen.destroy()

        if screen_name == "landing":
            self.current_screen = LandingScreen(self.container, app=self)
        elif screen_name == "login":
            self.current_screen = LoginScreen(self.container, app=self)
        elif screen_name == "register":
            self.current_screen = RegisterScreen(self.container, app=self)
        elif screen_name == "shell":
            self.current_screen = AppShell(self.container, app=self)
        else:
            self.current_screen = LandingScreen(self.container, app=self)

        self.current_screen.pack(fill="both", expand=True)

    def login_success(self, user):
        """Called by the login screen after a correct username and password."""
        self.current_user = user
        pending = self.pending_screen
        self.pending_screen = None
        self.show_screen("shell")
        if pending == "new_booking":
            if hasattr(self, "shell"):
                self.shell.switch_view("new_booking")

    def logout(self):
        """Clears the session and returns to the landing page."""
        self.current_user = None
        self.pending_screen = None
        if hasattr(self, "shell"):
            del self.shell
        self.show_screen("landing")

    def request_booking(self, tier_id):
        """
        Called by the landing page. Stores the chosen package. If the guest
        is not logged in yet, login is shown first, then the booking wizard.
        """
        self.booking_draft["tier_id"] = tier_id
        if self.current_user is None:
            self.pending_screen = "new_booking"
            self.show_screen("login")
        elif isinstance(self.current_screen, AppShell):
            self.shell.switch_view("new_booking")
        else:
            self.show_screen("shell")


# Application entry point
if __name__ == "__main__":
    app = AutoGlideApp()
    app.mainloop()

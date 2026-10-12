"""
main.py
=============================================================================
AutoGlide — Mobile Auto Detailing Scheduler
Main application entry point.

Responsibilities:
  - Initializes the primary Tkinter window and styling properties
  - Maintains global session state (logged in user, current booking draft)
  - Manages screen navigation and transitions between views
=============================================================================
"""

import tkinter as tk
import theme
import config
from screens import LandingScreen, PlaceholderScreen


class AutoGlideApp(tk.Tk):
    """
    Primary application window class.
    Inherits from tk.Tk and acts as the central controller for the app.
    """
    def __init__(self):
        super().__init__()

        # 1. Window Configuration
        self.title(f"{config.BRAND_INFO['name']} — Mobile Auto Detailing Scheduler")
        self.geometry("1200x780")
        self.minsize(1020, 650)
        self.configure(bg=theme.BG_MAIN)

        # 2. Session and Application State
        # - current_user: None for guest, or user dict once logged in
        # - booking_draft: holds selected vehicle, service tier, and add-ons
        self.current_user = None
        self.booking_draft = {
            "vehicle_type": "Sedan",
            "tier_id": "wash_wax",
            "add_ons": []
        }

        # 3. Main Screen Host Container
        # Holds whatever screen is currently active
        self.container = tk.Frame(self, bg=theme.BG_MAIN)
        self.container.pack(fill="both", expand=True)

        # Active screen tracker
        self.current_screen = None

        # 4. Load the Landing Screen by default
        self.show_screen("landing")

    def show_screen(self, screen_name, **kwargs):
        """
        Switches the currently displayed screen.
        Destroys the previous screen frame and instantiates the new one.

        Supported screen names:
          - 'landing'  : Main storefront landing page
          - 'login'    : User & Admin login portal (placeholder)
          - 'register' : Customer sign-up page (placeholder)
          - 'booking'  : Detailing schedule & location wizard (placeholder)
        """
        # Clean up existing screen if present
        if self.current_screen is not None:
            self.current_screen.destroy()

        # Instantiate requested screen
        if screen_name == "landing":
            self.current_screen = LandingScreen(self.container, app=self)
        elif screen_name in ("login", "register", "booking"):
            self.current_screen = PlaceholderScreen(
                self.container,
                app=self,
                screen_type=screen_name
            )
        else:
            # Fallback for unrecognized screen
            self.current_screen = PlaceholderScreen(
                self.container,
                app=self,
                screen_type="unknown"
            )

        # Display the new screen
        self.current_screen.pack(fill="both", expand=True)


# Application execution entry point
if __name__ == "__main__":
    app = AutoGlideApp()
    app.mainloop()

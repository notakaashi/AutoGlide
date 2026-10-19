"""
screens/__init__.py
=============================================================================
Package initializer for the application screens.
Exports every screen used by main.py.
=============================================================================
"""

from screens.landing_screen import LandingScreen
from screens.login_screen import LoginScreen
from screens.register_screen import RegisterScreen
from screens.dashboard_screen import ClientDashboardScreen
from screens.booking_screen import BookingScreen
from screens.my_bookings_screen import MyBookingsScreen
from screens.admin_screen import AdminScreen

__all__ = [
    "LandingScreen",
    "LoginScreen",
    "RegisterScreen",
    "ClientDashboardScreen",
    "BookingScreen",
    "MyBookingsScreen",
    "AdminScreen"
]

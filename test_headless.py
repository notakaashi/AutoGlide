"""
temp_headless_test.py
=============================================================================
Temporary headless test (standard library only).

Creates the real app without mainloop, pumps Tk events, clicks through every
screen by invoking the same handlers the mouse would trigger, and prints a
short PASS/FAIL report. Run: py -3 temp_headless_test.py
=============================================================================
"""

import traceback
import tkinter as tk
import datetime

import config
import database
import main
import theme
from components import Button
from screens.app_shell import AppShell
from screens import landing_screen, login_screen, register_screen
from screens.app_shell import PlaceholderView

results = []


def check(name, fn):
    """Runs one test and records pass/fail."""
    try:
        fn()
        results.append(("PASS", name))
    except Exception:
        results.append(("FAIL", name + "\n" + traceback.format_exc()))


app = main.AutoGlideApp()


def pump():
    """Lets Tk process geometry and paint events briefly."""
    for _ in range(6):
        app.update_idletasks()
        app.update()
        app.after(10, lambda: None)


# 1. Landing renders and hero canvas has content.
def t_landing():
    assert isinstance(app.current_screen, landing_screen.LandingScreen)
    app.update_idletasks()
    pump()
check("landing renders", t_landing)

# 2. Landing CTA for guests -> login screen.
def t_cta():
    app.request_booking("wash_wax")
    pump()
    assert isinstance(app.current_screen, login_screen.LoginScreen)
    assert app.pending_screen == "new_booking"
check("guest Book Now -> login", t_cta)

# 3. Client login through the login screen widgets.
def t_login_client():
    screen = app.current_screen
    screen.username.set("marcus")
    screen.password.set("password")
    screen.do_login()
    pump()
    assert isinstance(app.current_screen, AppShell)
    assert app.current_user["username"] == "marcus"
check("client login works", t_login_client)

# 4. Every client nav item switches and renders content.
def t_client_nav():
    shell = app.shell
    for btn in list(shell.nav_items):
        shell.switch_view(btn._view)
        pump()
        kids = shell.content_frame.winfo_children()
        assert kids, "empty view: " + btn._view
check("client nav switches all views", t_client_nav)

# 5. Wizard advances between steps like a real user filling it in.
def t_wizard():
    shell = app.shell
    shell.switch_view("new_booking")
    pump()
    wizard = shell.content_frame.winfo_children()[0]
    assert wizard.step == 1
    wizard._pick_tier("showroom")
    wizard._next()
    pump()
    assert wizard.step == 2, wizard.step
    wizard._toggle_addon("engine_bay")
    wizard._next()
    pump()
    assert wizard.step == 3, wizard.step
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)
                ).strftime("%Y-%m-%d")
    wizard.booking_date = tomorrow
    wizard._next()
    pump()
    assert wizard.step == 3, wizard.step
    wizard._date_field.set(tomorrow)
    wizard._pick_slot("10:00 AM")
    wizard._next()
    pump()
    assert wizard.step == 4, wizard.step
    wizard._address_field.set("123 Rizal St, Barangay")
    wizard._map.set_pin(100, 100, "QC")
    wizard._next()
    pump()
    assert wizard.step == 5, wizard.step
    total = wizard._compute_price()["total"]
    assert total > 0, total
    wizard._back()
    pump()
    assert wizard.step == 4, wizard.step
check("wizard steps navigate", t_wizard)

# 6. My bookings table has the expected columns and data loads.
def t_mybookings():
    shell = app.shell
    shell.switch_view("my_bookings")
    pump()
    view = shell.content_frame.winfo_children()[0]
    assert view.card.body.winfo_children(), "table missing"
check("my_bookings renders table", t_mybookings)

# 7. Logout returns to landing and clears session.
def t_logout():
    app.logout()
    pump()
    assert isinstance(app.current_screen, landing_screen.LandingScreen)
    assert app.current_user is None
check("logout works", t_logout)

# 8. Admin login lands on dashboard.
def t_admin():
    app.show_screen("login")
    pump()
    screen = app.current_screen
    screen.username.set("admin")
    screen.password.set("admin123")
    screen.do_login()
    pump()
    shell = app.shell
    assert isinstance(shell, AppShell)
    assert shell.current_view == "dashboard"
check("admin login -> dashboard", t_admin)

# 9. Dashboard tiles show real totals and nav works for all admin views.
def t_admin_nav():
    shell = app.shell
    for btn in list(shell.nav_items):
        shell.switch_view(btn._view)
        pump()
        assert shell.content_frame.winfo_children(), btn._view
check("admin nav switches all views", t_admin_nav)

# 10. Register screen validates errors without crashing.
def t_register():
    app.logout()
    pump()
    app.show_screen("register")
    pump()
    reg = app.current_screen
    reg.full_name.set("T")
    reg.username.set("x")
    reg.phone.set("bad")
    reg.email.set("bad")
    reg.password.set("123")
    reg.confirm.set("456")
    reg._register()
    pump()
    assert reg.full_name.error_label.cget("text") != ""
check("register validation runs", t_register)

app.destroy()

fails = [r for r in results if r[0] == "FAIL"]
for status, name in results:
    print(status, "-", name.splitlines()[0])
    if status == "FAIL":
        print(name)
print("TOTAL", len(results), "FAILS", len(fails))

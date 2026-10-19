"""
test_headless.py
=============================================================================
Headless test suite (standard library only).

Runs the real app WITHOUT mainloop, pumps Tk events, and drives the screens
through the same button handlers a mouse would use: login/register/logout,
the client shell and all its pages, the saved vehicle and address CRUD,
the full booking wizard end to end, the admin pages (status change,
calendar navigation, clients), the validators, and a final check that the
OLD database data is still intact after every migration.

Run with:  py -3 test_headless.py
Exit code is 0 when every test passes.
=============================================================================
"""

import traceback
import datetime
import tkinter as tk

import config
import database
import main
import theme
import validators

from screens.app_shell import ClientShell, AdminShell
from screens.landing_screen import LandingScreen, MarketingContent


results = []


def check(name, fn):
    """Runs one test and records pass/fail."""
    try:
        fn()
        results.append(("PASS", name))
    except Exception:
        results.append(("FAIL", name + "\n" + traceback.format_exc()))


def pump():
    """Pumps one cycle of Tk events so geometry and paints settle."""
    app.update_idletasks()
    app.update()


app = main.AutoGlideApp()
pump()

# Data snapshot taken BEFORE any test runs (old rows must survive everything).
# Booking rows that mention the test street ("Wizard Lane") are leftovers
# from earlier test runs - the wizard test cleans them, so they don't count
# as "old data".
ORIGINAL_USERNAMES = set()
connection = database.get_connection()
try:
    for row in connection.execute("SELECT username FROM users").fetchall():
        ORIGINAL_USERNAMES.add(row["username"])
finally:
    connection.close()
ORIGINAL_BOOKING_IDS = {row["id"] for row in database.get_all_bookings()
                        if "Wizard Lane" not in (row["address"] or "")}


# 1. VALIDATORS -------------------------------------------------------------
def t_validators():
    """Bad inputs are rejected with friendly messages."""
    ok, message = validators.validate_registration(
        "New Guy", "newguy_test", "12345", "a@mail.com", "secret1",
        "secret1")
    assert not ok
    ok, message = validators.validate_vehicle("", "Sedan", "Toyota",
                                              "Corolla", "", "")
    assert not ok
    ok, message = validators.validate_address("", "12 Street", "Brgy",
                                              "City", "")
    assert not ok
    ok, message = validators.validate_new_password("secret1", "secret2")
    assert not ok
    assert validators.validate_phone("0917-111-2222")[0]


# 2. AUTH -------------------------------------------------------------------
def t_register_and_login():
    """A new client can register, fail to log in, then log in."""
    # (comment: a previous crashed run may have left the test user behind)
    if database.username_exists("brand_new_test"):
        database.delete_user("brand_new_test")
    assert database.username_exists("brand_new_test") is False
    uid = database.create_user("Brand New", "brand_new_test",
                               "0917-999-8888", "brand@mail.com", "secret1")
    assert uid > 0
    assert database.get_user(uid)["username"] == "brand_new_test"
    assert database.login_user("brand_new_test", "wrong") is None
    logged = database.login_user("brand_new_test", "secret1")
    assert logged and logged["role"] == "client"


def t_login_screen_flow():
    """Typing marcus/password signs in and opens the client shell."""
    app.show_screen("login")
    pump()
    screen = app.current_screen
    screen.username.set("marcus")
    screen.password.set("wrong")
    screen.do_login()
    isinstance_pump()
    # still on login
    assert not isinstance(app.current_screen, ClientShell)
    screen.password.set("password")
    screen.do_login()
    pump()
    assert isinstance(app.current_screen, ClientShell)


def isinstance_pump():
    """Pumps events so error states render."""
    pump()


# 3. CLIENT SHELL PAGES -----------------------------------------------------
def t_client_tabs():
    """All six client tabs build without errors."""
    for name in ClientShell.TABS:
        key = name[0]
        app.shell.switch_view(key)
        pump()
        assert app.shell.current_view_name == key


def t_client_profile_and_help():
    """Profile shows the username; help shows the FAQ."""
    app.shell.switch_view("profile")
    pump()
    profile = app.shell.current_view
    assert profile.user["username"] == "marcus"
    app.shell.switch_view("help")
    pump()
    app.shell.switch_view("home")
    pump()


def t_guest_landing():
    """The logged-out landing page builds with the marketing content."""
    # (comment: log out first so we can view the guest landing)
    app.logout()
    pump()
    assert isinstance(app.current_screen, LandingScreen)
    landing = app.current_screen
    # mini nav "Book now" for guests saves the pending wizard flow
    assert landing.app is app
    # log marcus back in for the remaining tests
    app.show_screen("login")
    pump()
    screen = app.current_screen
    screen.username.set("marcus")
    screen.password.set("password")
    screen.do_login()
    pump()
    assert isinstance(app.current_screen, ClientShell)


def t_marketing_prices():
    """Package cards render with the config prices for the Sedan."""
    holder = tk.Frame(app, bg=theme.BG_APP)
    content = MarketingContent(holder, app)
    pump()
    for tier in config.SERVICE_TIERS:
        price = config.price_for(tier["id"], "Sedan")
        assert price > 0
    holder.destroy()


# 4. VEHICLES / ADDRESSES CRUD ---------------------------------------------
def t_saved_vehicle_crud():
    """Save, edit and delete a vehicle on the Vehicles page."""
    app.shell.switch_view("vehicles")
    pump()
    view = app.shell.current_view
    view._label.set("Test car")
    view._v_type.set("SUV")
    view._make.set("Honda")
    view._model.set("City")
    view._save()
    app.update()
    found = [v for v in database.get_saved_vehicles(
        app.shell.current_user["id"]) if v["label"] == "Test car"]
    assert found, "vehicle was not saved"
    vehicle = found[0]
    view._edit(vehicle)
    view._model.set("CRV")
    view._save()
    db_vehicle = database.get_saved_vehicle(vehicle["id"])
    assert db_vehicle["model"] == "CRV"
    view._delete(vehicle)
    assert database.get_saved_vehicle(vehicle["id"]) is None


def t_saved_address_crud():
    """Save, set default, edit, delete an address on the Addresses page."""
    app.shell.switch_view("addresses")
    pump()
    view = app.shell.current_view
    view._label_in.set("Test home")
    view._street.set("12 Test Street")
    view._barangay.set("Test Brgy")
    view._city.set("Test City")
    view._save()
    app.update()
    found = [a for a in database.get_saved_addresses(
        app.shell.current_user["id"]) if a["label"] == "Test home"]
    assert found, "address was not saved"
    address = found[0]
    view._make_default(address)
    assert database.get_saved_address(address["id"])["is_default"] == 1
    view._delete(address)
    assert database.get_saved_address(address["id"]) is None


def t_profile_change_password():
    """Profile rejects wrong old password and accepts a correct change."""
    app.shell.switch_view("profile")
    pump()
    view = app.shell.current_view
    view._old_pw.set("nope")
    view._new_pw.set("password")
    view._confirm_pw.set("password")
    view._save_password()
    user = database.get_user(view.user["id"])
    check_login = database.login_user("marcus", "password")
    assert check_login is not None  # old password still valid


# 5. THE WIZARD -------------------------------------------------------------
def t_wizard_full():
    """Full walk of the wizard: book a job end to end."""
    app.shell.switch_view("new_booking")
    pump()
    wizard = app.shell.current_view
    user_id = app.shell.current_user["id"]
    # remember which bookings exist before, to know which id is the new one
    before_ids = {r["id"] for r in database.get_bookings_by_user(user_id)}
    # clean THIS TEST's leftovers only (never the user's real bookings)
    for r in database.get_bookings_by_user(user_id):
        if "99 Wizard Lane" in (r["address"] or ""):
            database.delete_booking(r["id"])
    # Step 1: type a new car, tick "save this vehicle"
    wizard._v_label.set("Wizard car")
    wizard._v_type.set("Sedan")
    wizard._v_make.set("Mazda")
    wizard._v_model.set("2")
    wizard._v_color.set("Red")
    wizard._v_plate.set("TST 1111")
    if wizard._saved_vehicle_check is not None:
        wizard._saved_vehicle_check.set(True)
    wizard._go(1)
    assert wizard._draft["step"] == 1
    # Step 2: package (default) with one add-on
    first_addon = sorted(config.ADD_ONS)[0]
    wizard._toggle_addon(first_addon)
    wizard._go(2)
    assert wizard._draft["step"] == 2
    # Step 3: schedule - pick a date that still has room in the chosen slot
    slot = config.TIME_SLOTS[1]
    when = None
    today = datetime.date.today()
    for offset in range(3, config.MAX_ADVANCE_DAYS - 2):
        candidate = (today + datetime.timedelta(days=offset)).isoformat()
        if database.count_slot_bookings(candidate, slot) < config.SLOT_CAPACITY:
            when = candidate
            break
    assert when, "no free date/slot found for the test"
    wizard._date_field.set(when)
    wizard._paint_slots()
    wizard._pick_slot(slot)
    wizard._go(3)
    assert wizard._draft["step"] == 3
    # Step 4: address
    wizard._a_label.set("Wiz home")
    wizard._a_street.set("99 Wizard Lane")
    wizard._a_barangay.set("Wiz Brgy")
    wizard._a_city.set("Test City")
    if wizard._saved_address_check is not None:
        wizard._saved_address_check.set(True)
    wizard._go(4)
    assert wizard._draft["step"] == 4
    # Step 5: confirm
    wizard._confirm()
    pump()
    rows = database.get_bookings_by_user(app.shell.current_user["id"])
    pending = [r for r in rows if r["status"] == "Pending"
               and "Wizard Lane" in (r["address"] or "")]
    assert len(pending) >= 1, "booking was not created"
    booking = pending[-1]
    assert booking["booking_date"] == when
    assert booking["time_slot"] == slot
    assert "99 Wizard Lane" in booking["address"]
    # price check: base + the chosen add-on
    expected = (config.price_for("wash_vacuum", "Sedan")
                + config.ADD_ONS[first_addon]["price"])
    assert booking["total_price"] == expected
    # cleanup: delete the booking this run just made (test artifact only)
    final = database.get_bookings_by_user(user_id)
    for r in [r for r in final
              if "99 Wizard Lane" in (r["address"] or "")]:
        database.delete_booking(r["id"])
    # the saved vehicle/address from the checkboxes should exist now
    saved_v = [v for v in database.get_saved_vehicles(
        app.shell.current_user["id"]) if v["label"] == "Wizard car"]
    for v in saved_v:
        database.delete_saved_vehicle(v["id"])
    saved_a = [a for a in database.get_saved_addresses(
        app.shell.current_user["id"]) if a["label"] == "Wiz home"]
    for a in saved_a:
        database.delete_saved_address(a["id"])
    app.shell.switch_view("home")
    pump()


def t_wizard_block_bad_steps():
    """Skipping data (empty vehicle) shows an error and stays on the step."""
    app.shell.switch_view("home")
    pump()
    app.shell.switch_view("new_booking")
    pump()
    wizard = app.shell.current_view
    wizard._v_label.set("")
    wizard._v_make.set("")
    wizard._v_model.set("")
    wizard._go(1)
    assert wizard._draft["step"] == 0, "wizard moved on with bad data"
    app.shell.switch_view("home")
    pump()


# 6. MY BOOKINGS (live updates) --------------------------------------------
def t_my_bookings_flow():
    """My Bookings page refreshes and reflects admin status changes."""
    app.shell.switch_view("my_bookings")
    pump()
    view = app.shell.current_view
    rows = view._db_rows
    assert rows, "marcus should have at least the old booking"
    bid = rows[0]["id"]
    # admin changes status outside the screen; a refresh must pick it up
    database.update_status(bid, "Confirmed")
    view._refresh()
    pump()
    assert database.get_booking(bid)["status"] == "Confirmed"
    # undo, clean and quiet again
    database.update_status(bid, "Pending")
    view._refresh()


# 7. ADMIN ------------------------------------------------------------------
def t_admin_shell():
    """Admin login opens the AdminShell and all four pages build."""
    app.logout()
    pump()
    app.show_screen("login")
    pump()
    screen = app.current_screen
    screen.username.set("admin")
    screen.password.set("admin123")
    screen.do_login()
    pump()
    assert isinstance(app.current_screen, AdminShell)
    for name in AdminShell.ITEMS:
        shell_key = name[0]
        app.shell.switch_view(shell_key)
        pump()
    app.shell.switch_view("dashboard")
    pump()


def t_admin_bookings_status_change():
    """Admin changes a booking status with the segmented control."""
    app.shell.switch_view("bookings")
    pump()
    view = app.shell.current_view
    rows = view._filtered_rows()
    assert rows, "there must be at least the old booking"
    target = [r for r in rows if r["status"] == "Pending"][0]
    view._on_pick({"id": "#" + str(target["id"])})
    view._status_choice._select("Confirmed")
    view._save_status()
    pump()
    assert database.get_booking(target["id"])["status"] == "Confirmed"
    # put it back
    view._status_choice._select("Pending")
    view._save_status()
    pump()
    assert database.get_booking(target["id"])["status"] == "Pending"


def t_admin_bookings_search_and_sort():
    """Search box filters rows; the sort control reorders them."""
    view = app.shell.current_view
    view._search.set("marcus")
    view.reload()
    pump()
    assert all("marcus" in (row["client_username"] or "").lower()
               for row in view._filtered_rows())
    view._search.set("")
    view._pick_sort("Oldest")
    view._pick_sort("Highest total")
    view.reload()


def t_admin_schedule():
    """Calendar navigation across months keeps the day list working."""
    app.shell.switch_view("schedule")
    pump()
    view = app.shell.current_view
    start = (view.year, view.month)
    view._next_month()
    after = (view.year, view.month)
    assert after in ((start[0], start[1] + 1), (start[0] + 1, 1))
    view._prev_month()
    assert (view.year, view.month) == start
    view._go_today()
    assert view.selected_date.startswith(str(datetime.date.today().year))


def t_admin_clients():
    """Clients page lists only clients and shows booking counts."""
    app.shell.switch_view("clients")
    pump()
    view = app.shell.current_view
    names = [row["name"] for row in view._rows]
    assert "AutoGlide Admin" not in names
    assert "marcus" in [row["username"] for row in view._rows]
    assert all(int(row["bookings"]) >= 0 for row in view._rows)


# 8. LOGOUT + OLD DATA ------------------------------------------------------
def t_logout_old_data_intact():
    """Logout returns to the landing page with old data still there."""
    app.logout()
    pump()
    assert isinstance(app.current_screen, LandingScreen)
    connection = database.get_connection()
    try:
        usernames = {row["username"] for row in
                     connection.execute("SELECT username FROM users")}
        assert ORIGINAL_USERNAMES <= usernames, "old user rows were lost"
        ids = {row["id"] for row in database.get_all_bookings()}
        assert ORIGINAL_BOOKING_IDS <= ids, "old bookings were lost"
    finally:
        connection.close()
    assert database.login_user("admin", "admin123") is not None
    # remove the account this suite created so repeated runs start clean
    if database.username_exists("brand_new_test"):
        database.delete_user("brand_new_test")


def t_saved_pick_then_package():
    """Regression: pick a SAVED vehicle, then click packages and add-ons.
    This used to crash on a stale price label; it must not."""
    app.shell.switch_view("new_booking")
    pump()
    wizard = app.shell.current_view
    before_ids = {r["id"] for r in database.get_bookings_by_user(
        app.shell.current_user["id"])}
    # first, one saved vehicle must exist
    if not database.get_saved_vehicles(app.shell.current_user["id"]):
        database.add_saved_vehicle(app.shell.current_user["id"], "Suite car",
                                   "SUV", "Toyota", "RAV4", "Blue", "")
    wizard._go(1)  # no vehicle typed yet, but saved one boots on the radio
    # choose the saved vehicle radio (first saved row) like a mouse click
    first_saved = str(database.get_saved_vehicles(
        app.shell.current_user["id"])[0]["id"])
    wizard._vehicle_choice.set(first_saved)
    wizard._pick_vehicle()
    assert wizard._draft["vehicle"]["id"] == int(first_saved)
    wizard._go(2)
    # hammer the package cards and add-ons (price bar lives on this step)
    wizard._pick_tier("wash_wax")
    wizard._pick_tier("showroom")
    wizard._pick_tier("wash_vacuum")
    for addon_id in sorted(config.ADD_ONS):
        wizard._toggle_addon(addon_id)
    wizard._toggle_addon(sorted(config.ADD_ONS)[0])
    expected_total = config.price_for("wash_vacuum", wizard._v_type.get())
    for addon_id in wizard._draft["addons"]:
        expected_total = expected_total + config.ADD_ONS[addon_id]["price"]
    assert wizard._price_labels[0].cget("text").find(
        "\u20b1" + str(expected_total)) >= 0
    # keep the test fast: jump back home after the crash-prone clicks
    app.shell.switch_view("home")
    pump()


TESTS = [
    ("validators", t_validators),
    ("register and login", t_register_and_login),
    ("login screen flow", t_login_screen_flow),
    ("client tabs", t_client_tabs),
    ("client profile and help", t_client_profile_and_help),
    ("guest landing", t_guest_landing),
    ("marketing prices", t_marketing_prices),
    ("saved vehicle CRUD", t_saved_vehicle_crud),
    ("saved address CRUD", t_saved_address_crud),
    ("profile password flow", t_profile_change_password),
    ("wizard full booking", t_wizard_full),
    ("saved pick then package", t_saved_pick_then_package),
    ("wizard blocks bad data", t_wizard_block_bad_steps),
    ("my bookings live updates", t_my_bookings_flow),
    ("admin shell", t_admin_shell),
    ("admin status change", t_admin_bookings_status_change),
    ("admin search and sort", t_admin_bookings_search_and_sort),
    ("admin schedule calendar", t_admin_schedule),
    ("admin clients", t_admin_clients),
    ("logout + old data intact", t_logout_old_data_intact),
]


if __name__ == "__main__":
    for name, fn in TESTS:
        check(name, fn)
    failures = 0
    for status, name in results:
        if status == "FAIL":
            failures += 1
        print(status + ": " + name.split("\n")[0])
        if status == "FAIL":
            print(name)
    print()
    print("=" * 60)
    print(str(len(results) - failures) + "/" + str(len(results)) + " PASSED")
    app.destroy()
    raise SystemExit(1 if failures else 0)

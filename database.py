"""
database.py
=============================================================================
All SQLite work for AutoGlide lives here, and only here.

The database file is autoglide.db and is created automatically the first time
the program runs. Default data (one admin account and three detailers) is
seeded at that time.

This file also performs a SAFE migration: if an older autoglide.db already
exists, new tables and columns are added and default rows are filled in only
when they are missing, so no existing bookings or accounts are ever lost.

Screens import these functions and never write SQL themselves.
Uses only the standard library (sqlite3, os, datetime).
=============================================================================
"""

import os
import sqlite3
import datetime
import config

# The database file sits next to this Python file.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "autoglide.db")


# ---------------------------------------------------------------------------
# CONNECTION AND SETUP
# ---------------------------------------------------------------------------
def get_connection():
    """Opens and returns a new connection to the SQLite database."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    """
    Creates the database and its tables when missing, then runs a safe
    migration (new tables and columns) and seeds any missing default rows.
    """
    connection = get_connection()
    try:
        _create_tables(connection)
        _migrate(connection)
        _seed_defaults(connection)
        connection.commit()
    finally:
        connection.close()


def _create_tables(connection):
    """Creates every table the application uses (does nothing if it exists)."""
    cursor = connection.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "full_name TEXT NOT NULL, "
        "username TEXT NOT NULL, "
        "phone TEXT NOT NULL, "
        "email TEXT NOT NULL, "
        "password TEXT NOT NULL, "
        "role TEXT NOT NULL, "
        "created_at TEXT NOT NULL)"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS detailers ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT NOT NULL, "
        "active INTEGER NOT NULL DEFAULT 1)"
    )

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS bookings ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "vehicle_type TEXT NOT NULL, "
        "tier_id TEXT NOT NULL, "
        "addons TEXT, "
        "base_price INTEGER NOT NULL, "
        "addon_total INTEGER NOT NULL, "
        "travel_fee INTEGER NOT NULL, "
        "total_price INTEGER NOT NULL, "
        "booking_date TEXT NOT NULL, "
        "time_slot TEXT NOT NULL, "
        "address TEXT NOT NULL, "
        "zone_code TEXT, "
        "pin_x INTEGER, "
        "pin_y INTEGER, "
        "status TEXT NOT NULL, "
        "detailer_id INTEGER, "
        "created_at TEXT NOT NULL)"
    )

    # Editable package prices, one row per (package, vehicle type).
    connection.execute(
        "CREATE TABLE IF NOT EXISTS tier_prices ("
        "tier_id TEXT NOT NULL, "
        "vehicle_type TEXT NOT NULL, "
        "price INTEGER NOT NULL, "
        "PRIMARY KEY (tier_id, vehicle_type))"
    )

    # Editable add-ons.
    connection.execute(
        "CREATE TABLE IF NOT EXISTS addons ("
        "id TEXT PRIMARY KEY, "
        "name TEXT NOT NULL, "
        "price INTEGER NOT NULL, "
        "active INTEGER NOT NULL DEFAULT 1)"
    )

    # Editable service zones and their travel fees.
    connection.execute(
        "CREATE TABLE IF NOT EXISTS zones ("
        "code TEXT PRIMARY KEY, "
        "name TEXT NOT NULL, "
        "travel_fee INTEGER NOT NULL, "
        "active INTEGER NOT NULL DEFAULT 1)"
    )

    # Saved vehicles a client may reuse when booking.
    connection.execute(
        "CREATE TABLE IF NOT EXISTS saved_vehicles ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "label TEXT NOT NULL, "
        "vehicle_type TEXT NOT NULL, "
        "created_at TEXT NOT NULL)"
    )

    # Saved addresses a client may reuse when booking.
    connection.execute(
        "CREATE TABLE IF NOT EXISTS saved_addresses ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "label TEXT NOT NULL, "
        "address TEXT NOT NULL, "
        "zone_code TEXT, "
        "pin_x INTEGER, "
        "pin_y INTEGER, "
        "created_at TEXT NOT NULL)"
    )

    connection.commit()
    _migrate(connection)


def _has_column(connection, table, column):
    """Returns True when a table already has a column (used by migration)."""
    cursor = connection.execute("PRAGMA table_info(" + table + ")")
    for row in cursor.fetchall():
        if row["name"] == column:
            return True
    return False


def _migrate(connection):
    """
    Adds columns that a newer version needs but an older database lacks.
    Existing rows keep their data; only the missing column is added.
    """
    if not _has_column(connection, "detailers", "active"):
        connection.execute(
            "ALTER TABLE detailers ADD COLUMN active INTEGER NOT NULL DEFAULT 1")
        connection.commit()


# ---------------------------------------------------------------------------
# SEEDING (only fills in what is missing)
# ---------------------------------------------------------------------------
def _seed_defaults(connection):
    """Inserts default accounts, detailers, prices, add-ons, and zones."""
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_data = config.DEFAULT_ADMIN
        cursor.execute(
            "INSERT INTO users (full_name, username, phone, email, password, role, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (admin_data["full_name"], admin_data["username"],
             admin_data["phone"], admin_data["email"], admin_data["password"],
             admin_data["role"], _now())
        )

    cursor.execute("SELECT COUNT(*) FROM detailers")
    if cursor.fetchone()[0] == 0:
        for name in config.DEFAULT_DETAILERS:
            cursor.execute("INSERT INTO detailers (name, active) VALUES (?, 1)", (name,))

    # Package prices, from config, only when the table is empty.
    cursor.execute("SELECT COUNT(*) FROM tier_prices")
    if cursor.fetchone()[0] == 0:
        for tier in config.SERVICE_TIERS:
            for vehicle_type, price in tier["prices"].items():
                cursor.execute(
                    "INSERT INTO tier_prices (tier_id, vehicle_type, price) "
                    "VALUES (?, ?, ?)",
                    (tier["id"], vehicle_type, price)
                )

    # Add-ons, from config, only when the table is empty.
    cursor.execute("SELECT COUNT(*) FROM addons")
    if cursor.fetchone()[0] == 0:
        for addon in config.ADD_ONS:
            cursor.execute(
                "INSERT INTO addons (id, name, price, active) VALUES (?, ?, ?, 1)",
                (addon["id"], addon["name"], addon["price"])
            )

    # Zones, from config, only when the table is empty.
    cursor.execute("SELECT COUNT(*) FROM zones")
    if cursor.fetchone()[0] == 0:
        for zone in config.SERVICE_ZONES:
            cursor.execute(
                "INSERT INTO zones (code, name, travel_fee, active) VALUES (?, ?, ?, 1)",
                (zone["code"], zone["name"], zone["travel_fee"])
            )

    connection.commit()


def _now():
    """Returns the current date and time as a text timestamp."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------
def username_exists(username):
    """Returns True if a user already uses this username."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        return cursor.fetchone() is not None
    finally:
        connection.close()


def create_user(full_name, username, phone, email, password, role="client"):
    """Inserts a new user and returns the new row id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (full_name, username, phone, email, password, role, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (full_name, username, phone, email, password, role, _now())
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def login_user(username, password):
    """Returns the matching user row, or None when the login is wrong."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        )
        return cursor.fetchone()
    finally:
        connection.close()


def get_user(user_id):
    """Returns one user row by id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()
    finally:
        connection.close()


def update_user(user_id, full_name, phone, email, password=None):
    """Updates a user's profile, and the password only when one is given."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if password:
            cursor.execute(
                "UPDATE users SET full_name = ?, phone = ?, email = ?, password = ? "
                "WHERE id = ?",
                (full_name, phone, email, password, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET full_name = ?, phone = ?, email = ? WHERE id = ?",
                (full_name, phone, email, user_id)
            )
        connection.commit()
    finally:
        connection.close()


def get_clients():
    """Returns every client (non-admin) user ordered by name."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'client' ORDER BY full_name")
        return cursor.fetchall()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# DETAILERS
# ---------------------------------------------------------------------------
def get_detailers():
    """Returns every detailer row ordered by name."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM detailers ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def get_active_detailers():
    """Returns only the detailers that are marked active."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM detailers WHERE active = 1 ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def add_detailer(name):
    """Adds a new detailer and returns the new row id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO detailers (name, active) VALUES (?, 1)", (name,))
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def rename_detailer(detailer_id, name):
    """Changes a detailer's name."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE detailers SET name = ? WHERE id = ?", (name, detailer_id))
        connection.commit()
    finally:
        connection.close()


def set_detailer_active(detailer_id, active):
    """Marks a detailer active (1) or inactive (0)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE detailers SET active = ? WHERE id = ?",
                       (1 if active else 0, detailer_id))
        connection.commit()
    finally:
        connection.close()


def get_detailers_list():
    """Returns the detailer rows (alias kept for older code)."""
    return get_detailers()


# ---------------------------------------------------------------------------
# PRICES, ADD-ONS, ZONES (admin editable)
# ---------------------------------------------------------------------------
def get_tier_prices():
    """Returns all package price rows."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tier_prices")
        return cursor.fetchall()
    finally:
        connection.close()


def get_price(tier_id, vehicle_type):
    """Returns the current price for a package and vehicle type."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT price FROM tier_prices WHERE tier_id = ? AND vehicle_type = ?",
            (tier_id, vehicle_type)
        )
        row = cursor.fetchone()
        if row is None:
            tier = config.tier_by_id(tier_id)
            if tier is not None:
                return tier["prices"].get(vehicle_type, 0)
            return 0
        return row["price"]
    finally:
        connection.close()


def update_price(tier_id, vehicle_type, price):
    """Sets the price for a package and vehicle type."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE tier_prices SET price = ? WHERE tier_id = ? AND vehicle_type = ?",
            (price, tier_id, vehicle_type)
        )
        connection.commit()
    finally:
        connection.close()


def get_addons():
    """Returns all add-on rows ordered by name."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM addons ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def get_active_addons():
    """Returns only the add-ons that are marked active."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM addons WHERE active = 1 ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def get_addon(addon_id):
    """Returns one add-on row by id, or None."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM addons WHERE id = ?", (addon_id,))
        return cursor.fetchone()
    finally:
        connection.close()


def update_addon_price(addon_id, price):
    """Changes an add-on's price."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE addons SET price = ? WHERE id = ?", (price, addon_id))
        connection.commit()
    finally:
        connection.close()


def set_addon_active(addon_id, active):
    """Marks an add-on active (1) or inactive (0)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE addons SET active = ? WHERE id = ?",
                       (1 if active else 0, addon_id))
        connection.commit()
    finally:
        connection.close()


def get_zones():
    """Returns all service zone rows ordered by name."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM zones ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def get_active_zones():
    """Returns only the zones that are marked active."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM zones WHERE active = 1 ORDER BY name")
        return cursor.fetchall()
    finally:
        connection.close()


def update_zone_fee(code, travel_fee):
    """Changes a zone's travel fee."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE zones SET travel_fee = ? WHERE code = ?",
                       (travel_fee, code))
        connection.commit()
    finally:
        connection.close()


def set_zone_active(code, active):
    """Marks a zone active (1) or inactive (0)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE zones SET active = ? WHERE code = ?",
                       (1 if active else 0, code))
        connection.commit()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# SAVED VEHICLES
# ---------------------------------------------------------------------------
def get_saved_vehicles(user_id):
    """Returns a client's saved vehicles, newest first."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM saved_vehicles WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        connection.close()


def add_saved_vehicle(user_id, label, vehicle_type):
    """Saves a vehicle for a client and returns the new row id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO saved_vehicles (user_id, label, vehicle_type, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, label, vehicle_type, _now())
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def delete_saved_vehicle(vehicle_id):
    """Removes a saved vehicle."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM saved_vehicles WHERE id = ?", (vehicle_id,))
        connection.commit()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# SAVED ADDRESSES
# ---------------------------------------------------------------------------
def get_saved_addresses(user_id):
    """Returns a client's saved addresses, newest first."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM saved_addresses WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        connection.close()


def add_saved_address(user_id, label, address, zone_code, pin_x, pin_y):
    """Saves an address for a client and returns the new row id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO saved_addresses (user_id, label, address, zone_code, pin_x, "
            "pin_y, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, label, address, zone_code, pin_x, pin_y, _now())
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def delete_saved_address(address_id):
    """Removes a saved address."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM saved_addresses WHERE id = ?", (address_id,))
        connection.commit()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# BOOKINGS
# ---------------------------------------------------------------------------
def count_slot_bookings(booking_date, time_slot, exclude_id=None):
    """Counts active bookings for a date and slot (cancelled ones excluded)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = ("SELECT COUNT(*) FROM bookings WHERE booking_date = ? "
                 "AND time_slot = ? AND status != 'Cancelled'")
        values = [booking_date, time_slot]
        if exclude_id is not None:
            query = query + " AND id != ?"
            values.append(exclude_id)
        cursor.execute(query, values)
        return cursor.fetchone()[0]
    finally:
        connection.close()


def create_booking(user_id, vehicle_type, tier_id, addons, base_price,
                   addon_total, travel_fee, total_price, booking_date,
                   time_slot, address, zone_code, pin_x, pin_y, status):
    """Inserts a new booking and returns the new row id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO bookings (user_id, vehicle_type, tier_id, addons, base_price, "
            "addon_total, travel_fee, total_price, booking_date, time_slot, address, "
            "zone_code, pin_x, pin_y, status, detailer_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, vehicle_type, tier_id, addons, base_price, addon_total,
             travel_fee, total_price, booking_date, time_slot, address, zone_code,
             pin_x, pin_y, status, None, _now())
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def get_bookings_by_user(user_id):
    """Returns all bookings that belong to one client, newest first."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM bookings WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_booking(booking_id):
    """Returns one booking row by id, joined with client and detailer names."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT b.*, u.full_name AS client_name, u.phone AS client_phone, "
            "d.name AS detailer_name "
            "FROM bookings b "
            "LEFT JOIN users u ON b.user_id = u.id "
            "LEFT JOIN detailers d ON b.detailer_id = d.id "
            "WHERE b.id = ?",
            (booking_id,)
        )
        return cursor.fetchone()
    finally:
        connection.close()


def get_all_bookings():
    """Returns every booking joined with client and detailer names."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT b.*, u.full_name AS client_name, u.phone AS client_phone, "
            "d.name AS detailer_name "
            "FROM bookings b "
            "LEFT JOIN users u ON b.user_id = u.id "
            "LEFT JOIN detailers d ON b.detailer_id = d.id "
            "ORDER BY b.id DESC"
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_bookings_filtered(status=None, booking_date=None):
    """Returns bookings filtered by status and/or date (either may be None)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = (
            "SELECT b.*, u.full_name AS client_name, u.phone AS client_phone, "
            "d.name AS detailer_name "
            "FROM bookings b "
            "LEFT JOIN users u ON b.user_id = u.id "
            "LEFT JOIN detailers d ON b.detailer_id = d.id WHERE 1 = 1"
        )
        values = []
        if status:
            query = query + " AND b.status = ?"
            values.append(status)
        if booking_date:
            query = query + " AND b.booking_date = ?"
            values.append(booking_date)
        query = query + " ORDER BY b.id DESC"
        cursor.execute(query, values)
        return cursor.fetchall()
    finally:
        connection.close()


def get_bookings_on_date(booking_date):
    """Returns bookings scheduled for one date, joined with names."""
    return get_bookings_filtered(booking_date=booking_date)


def get_bookings_in_month(year, month):
    """Returns bookings whose date falls inside a given month."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        prefix = "%04d-%02d-%%" % (year, month)
        cursor.execute(
            "SELECT b.*, u.full_name AS client_name, d.name AS detailer_name "
            "FROM bookings b "
            "LEFT JOIN users u ON b.user_id = u.id "
            "LEFT JOIN detailers d ON b.detailer_id = d.id "
            "WHERE b.booking_date LIKE ? ORDER BY b.booking_date, b.time_slot",
            (prefix,)
        )
        return cursor.fetchall()
    finally:
        connection.close()


def update_status(booking_id, status):
    """Changes the status of a booking."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (status, booking_id))
        connection.commit()
    finally:
        connection.close()


def assign_detailer(booking_id, detailer_id):
    """Assigns a detailer to a booking (detailer_id may be None to clear)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE bookings SET detailer_id = ? WHERE id = ?",
                       (detailer_id, booking_id))
        connection.commit()
    finally:
        connection.close()


def reschedule_booking(booking_id, booking_date, time_slot):
    """Moves a booking to a new date and time slot (admin action)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE bookings SET booking_date = ?, time_slot = ? WHERE id = ?",
            (booking_date, time_slot, booking_id)
        )
        connection.commit()
    finally:
        connection.close()


def delete_booking(booking_id):
    """Permanently removes a booking."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        connection.commit()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# SUMMARY / STATS
# ---------------------------------------------------------------------------
def get_summary():
    """Returns (total bookings, pending count, revenue from completed)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bookings")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = ?", ("Pending",))
        pending = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(total_price) FROM bookings WHERE status = ?",
                       ("Completed",))
        revenue_row = cursor.fetchone()[0]
        revenue = revenue_row if revenue_row is not None else 0
        return (total, pending, revenue)
    finally:
        connection.close()


def get_admin_stats():
    """
    Returns a dictionary of dashboard numbers:
    total bookings, pending, completed, cancelled, revenue from completed,
    and the number of client accounts.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM bookings")
        stats["total"] = cursor.fetchone()[0]
        for status in ["Pending", "Confirmed", "On the Way", "In Progress",
                       "Completed", "Cancelled"]:
            cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = ?", (status,))
            stats[status] = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(total_price) FROM bookings WHERE status = ?",
                       ("Completed",))
        revenue_row = cursor.fetchone()[0]
        stats["revenue"] = revenue_row if revenue_row is not None else 0
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'client'")
        stats["clients"] = cursor.fetchone()[0]
        return stats
    finally:
        connection.close()


def get_client_stats(user_id):
    """Returns (total bookings, upcoming count) for one client."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()[0]
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT COUNT(*) FROM bookings WHERE user_id = ? AND booking_date >= ? "
            "AND status NOT IN ('Completed', 'Cancelled')",
            (user_id, today)
        )
        upcoming = cursor.fetchone()[0]
        return (total, upcoming)
    finally:
        connection.close()

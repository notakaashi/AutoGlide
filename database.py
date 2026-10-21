"""
database.py
=============================================================================
All SQLite work for AutoGlide lives here, and only here.

The database file is autoglide.db and is created automatically the first time
the program runs. Default data (the admin account) is seeded at that time.

This file also performs a SAFE migration: if an older autoglide.db already
exists, new columns are added and default rows are filled in only when they
are missing. Tables and rows are never dropped or deleted, so old bookings
(including ones with zone codes and travel fees) keep all their stored data.

Screens import these functions and never write SQL themselves.
Uses only the standard library (sqlite3, os, datetime).
=============================================================================
"""

import hashlib
import os
import secrets
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
    migration (new columns) and seeds any missing default rows.
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

    # Old table kept so existing databases keep working; no longer used.
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS detailers ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT NOT NULL, "
        "active INTEGER NOT NULL DEFAULT 1)"
    )

    # Note: zone_code, pin_x, pin_y, travel_fee and detailer_id are old
    # columns kept so older rows survive. New bookings leave them empty.
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
        "barangay TEXT DEFAULT '', "
        "city TEXT DEFAULT '', "
        "landmark TEXT DEFAULT '', "
        "vehicle_label TEXT DEFAULT '', "
        "vehicle_make TEXT DEFAULT '', "
        "vehicle_model TEXT DEFAULT '', "
        "vehicle_color TEXT DEFAULT '', "
        "vehicle_plate TEXT DEFAULT '', "
        "created_at TEXT NOT NULL)"
    )

    # Saved vehicles a client may reuse when booking.
    connection.execute(
        "CREATE TABLE IF NOT EXISTS saved_vehicles ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "label TEXT NOT NULL, "
        "vehicle_type TEXT NOT NULL, "
        "make TEXT DEFAULT '', "
        "model TEXT DEFAULT '', "
        "color TEXT DEFAULT '', "
        "plate TEXT DEFAULT '', "
        "created_at TEXT NOT NULL)"
    )

    # Saved addresses a client may reuse when booking.
    connection.execute(
        "CREATE TABLE IF NOT EXISTS saved_addresses ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER NOT NULL, "
        "label TEXT NOT NULL, "
        "address TEXT NOT NULL, "
        "barangay TEXT DEFAULT '', "
        "city TEXT DEFAULT '', "
        "landmark TEXT DEFAULT '', "
        "is_default INTEGER NOT NULL DEFAULT 0, "
        "zone_code TEXT, "
        "pin_x INTEGER, "
        "pin_y INTEGER, "
        "created_at TEXT NOT NULL)"
    )

    connection.commit()


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
    plans = {
        "bookings": [
            ("barangay", "TEXT DEFAULT ''"),
            ("city", "TEXT DEFAULT ''"),
            ("landmark", "TEXT DEFAULT ''"),
            ("vehicle_label", "TEXT DEFAULT ''"),
            ("vehicle_make", "TEXT DEFAULT ''"),
            ("vehicle_model", "TEXT DEFAULT ''"),
            ("vehicle_color", "TEXT DEFAULT ''"),
            ("vehicle_plate", "TEXT DEFAULT ''")
        ],
        "saved_vehicles": [
            ("make", "TEXT DEFAULT ''"),
            ("model", "TEXT DEFAULT ''"),
            ("color", "TEXT DEFAULT ''"),
            ("plate", "TEXT DEFAULT ''")
        ],
        "saved_addresses": [
            ("barangay", "TEXT DEFAULT ''"),
            ("city", "TEXT DEFAULT ''"),
            ("landmark", "TEXT DEFAULT ''"),
            ("is_default", "INTEGER NOT NULL DEFAULT 0")
        ],
        "detailers": [
            ("active", "INTEGER NOT NULL DEFAULT 1")
        ]
    }
    for table, new_columns in plans.items():
        for column, definition in new_columns:
            if not _has_column(connection, table, column):
                connection.execute(
                    "ALTER TABLE " + table + " ADD COLUMN " + column
                    + " " + definition)
        connection.commit()


# ---------------------------------------------------------------------------
# PASSWORDS (salted sha256; old plaintext rows migrate on first login)
# ---------------------------------------------------------------------------
def hash_password(password, salt=None):
    """Returns 'salt$hash' for a password, making a random salt when none."""
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt + "$" + digest


def verify_password(password, stored):
    """True when the password matches the stored 'salt$hash' text."""
    if "$" not in stored:
        return False
    salt, digest = stored.split("$", 1)
    check = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return check == digest


# ---------------------------------------------------------------------------
# SEEDING (only fills in what is missing)
# ---------------------------------------------------------------------------
def _seed_defaults(connection):
    """Inserts the default admin account when the users table is empty."""
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_data = config.DEFAULT_ADMIN
        cursor.execute(
            "INSERT INTO users (full_name, username, phone, email, password, role, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (admin_data["full_name"], admin_data["username"],
             admin_data["phone"], admin_data["email"],
             hash_password(admin_data["password"]),
             admin_data["role"], _now())
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


def delete_user(username):
    """Removes one user account by username (used by tests and cleanup)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM users WHERE username=?", (username,))
        deleted = cursor.rowcount
        connection.commit()
        return deleted
    finally:
        connection.close()


def create_user(full_name, username, phone, email, password, role="client"):
    """Inserts a new user and returns the new row id (password is hashed)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (full_name, username, phone, email, password, role, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (full_name, username, phone, email, hash_password(password), role,
             _now())
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def login_user(username, password):
    """Returns the matching user row, or None when the login is wrong.

    Old accounts still have a plaintext password; those migrate to a
    salted hash the moment they sign in successfully.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if user is None:
            return None
        stored = user["password"] or ""
        if "$" in stored:
            if not verify_password(password, stored):
                return None
        else:
            # legacy plaintext row - compare and upgrade to a salted hash
            if stored != password:
                return None
            cursor.execute("UPDATE users SET password = ? WHERE id = ?",
                           (hash_password(password), user["id"]))
            connection.commit()
        return user
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
    """Updates a user's profile, and the password (hashed) when given."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if password:
            cursor.execute(
                "UPDATE users SET full_name = ?, phone = ?, email = ?, password = ? "
                "WHERE id = ?",
                (full_name, phone, email, hash_password(password), user_id)
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
        cursor.execute("SELECT * FROM users WHERE role = 'client' "
                       "ORDER BY full_name")
        return cursor.fetchall()
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


def get_saved_vehicle(vehicle_id):
    """Returns one saved vehicle row by id, or None."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM saved_vehicles WHERE id = ?", (vehicle_id,))
        return cursor.fetchone()
    finally:
        connection.close()


def add_saved_vehicle(user_id, label, vehicle_type, make, model, color, plate):
    """Saves a vehicle for a client and returns the new row id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO saved_vehicles (user_id, label, vehicle_type, make, model, "
            "color, plate, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, label, vehicle_type, make, model, color, plate, _now())
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_saved_vehicle(vehicle_id, label, vehicle_type, make, model, color,
                         plate):
    """Updates one saved vehicle."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE saved_vehicles SET label = ?, vehicle_type = ?, make = ?, "
            "model = ?, color = ?, plate = ? WHERE id = ?",
            (label, vehicle_type, make, model, color, plate, vehicle_id)
        )
        connection.commit()
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


def vehicle_desc(*args):
    """
    Formats a vehicle as one readable line.
    Use either a saved vehicle row, or plain parts in the order
    (vehicle_type, make, model, color, plate).
    """
    if len(args) == 1:
        row = args[0]
        row = {
            "label": row["label"],
            "vehicle_type": row["vehicle_type"],
            "make": row["make"],
            "model": row["model"],
            "color": row["color"],
            "plate": row["plate"],
        }
    else:
        vehicle_type, make, model, color, plate = args
        row = {"label": "", "vehicle_type": vehicle_type, "make": make,
               "model": model, "color": color, "plate": plate}
    parts = []
    if row["make"] or row["model"]:
        parts.append((row["make"] + " " + row["model"]).strip())
    if row["color"]:
        parts.append(row["color"])
    text = " ".join(p for p in ([row["vehicle_type"]] + parts) if p)
    if row["plate"]:
        text = text + " (" + row["plate"] + ")"
    elif row["label"]:
        text = row["label"] + " - " + text
    return text


# ---------------------------------------------------------------------------
# SAVED ADDRESSES
# ---------------------------------------------------------------------------
def get_saved_addresses(user_id):
    """Returns a client's saved addresses, default first then newest."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM saved_addresses WHERE user_id = ? "
            "ORDER BY is_default DESC, id DESC", (user_id,)
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_saved_address(address_id):
    """Returns one saved address row by id, or None."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM saved_addresses WHERE id = ?",
                       (address_id,))
        return cursor.fetchone()
    finally:
        connection.close()


def add_saved_address(user_id, label, address, barangay, city, landmark,
                      is_default=False):
    """Saves an address for a client and returns the new row id."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        if is_default:
            cursor.execute("UPDATE saved_addresses SET is_default = 0 "
                           "WHERE user_id = ?", (user_id,))
        cursor.execute(
            "INSERT INTO saved_addresses (user_id, label, address, barangay, city, "
            "landmark, is_default, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, label, address, barangay, city, landmark,
             1 if is_default else 0, _now())
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def update_saved_address(address_id, label, address, barangay, city, landmark):
    """Updates one saved address (does not change the default flag)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE saved_addresses SET label = ?, address = ?, barangay = ?, "
            "city = ?, landmark = ? WHERE id = ?",
            (label, address, barangay, city, landmark, address_id)
        )
        connection.commit()
    finally:
        connection.close()


def set_default_address(address_id, user_id):
    """Marks one address as the default and clears the old default."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE saved_addresses SET is_default = 0 "
                       "WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE saved_addresses SET is_default = 1 "
                       "WHERE id = ?", (address_id,))
        connection.commit()
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


def address_lines(*args):
    """
    Formats an address as one readable line.
    Use either a saved address row, or plain parts in the order
    (address, barangay, city, landmark).
    """
    if len(args) == 1:
        row = args[0]
        row = {"address": row["address"], "barangay": row["barangay"],
               "city": row["city"], "landmark": row["landmark"]}
    else:
        address, barangay, city, landmark = args
        row = {"address": address, "barangay": barangay, "city": city,
               "landmark": landmark}
    parts = [row["address"]]
    if row["barangay"]:
        parts.append("Brgy. " + row["barangay"])
    if row["city"]:
        parts.append(row["city"])
    text = ", ".join(p for p in parts if p)
    if row["landmark"]:
        text = text + " (near " + row["landmark"] + ")"
    return text


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
                   addon_total, total_price, booking_date, time_slot,
                   address, barangay, city, landmark, vehicle_label,
                   vehicle_make, vehicle_model, vehicle_color, vehicle_plate,
                   status):
    """
    Inserts a new booking and returns the new row id.
    Old columns (zone_code, pin_x, pin_y, travel_fee, detailer_id) are left
    empty because bookings no longer use zones or travel fees.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO bookings (user_id, vehicle_type, tier_id, addons, "
            "base_price, addon_total, travel_fee, total_price, booking_date, "
            "time_slot, address, barangay, city, landmark, vehicle_label, "
            "vehicle_make, vehicle_model, vehicle_color, vehicle_plate, "
            "zone_code, pin_x, pin_y, detailer_id, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "NULL, NULL, NULL, NULL, ?, ?)",
            (user_id, vehicle_type, tier_id, addons, base_price, addon_total,
             0, total_price, booking_date, time_slot, address, barangay,
             city, landmark, vehicle_label, vehicle_make, vehicle_model,
             vehicle_color, vehicle_plate, status, _now())
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


_BOOKING_JOIN = (
    "SELECT b.*, u.full_name AS client_name, u.phone AS client_phone, "
    "u.email AS client_email, u.username AS client_username "
    "FROM bookings b "
    "LEFT JOIN users u ON b.user_id = u.id "
)


def get_bookings_last_days(days):
    """
    Counts bookings per day for the last N days, oldest first.
    Returns a dict like {'2026-10-13': 2, ...} for the dashboard chart.
    """
    import datetime
    today = datetime.date.today()
    first_day = today - datetime.timedelta(days=days - 1)
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT booking_date, COUNT(*) AS total FROM bookings "
            "WHERE booking_date >= ? AND booking_date <= ? "
            "GROUP BY booking_date",
            (first_day.isoformat(), today.isoformat()))
        rows = cursor.fetchall()
    finally:
        connection.close()
    return {row["booking_date"]: row["total"] for row in rows}


def get_bookings_by_user(user_id):
    """Returns all bookings that belong to one client, newest first."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(_BOOKING_JOIN + " WHERE b.user_id = ? ORDER BY b.id DESC",
                       (user_id,))
        return cursor.fetchall()
    finally:
        connection.close()


def get_booking(booking_id):
    """Returns one booking row by id, joined with the client's details."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(_BOOKING_JOIN + " WHERE b.id = ?", (booking_id,))
        return cursor.fetchone()
    finally:
        connection.close()


def get_all_bookings():
    """Returns every booking joined with client details, newest first."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(_BOOKING_JOIN + " ORDER BY b.id DESC")
        return cursor.fetchall()
    finally:
        connection.close()


def get_bookings_filtered(status=None, booking_date=None):
    """Returns bookings filtered by status and/or date (either may be None)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        query = _BOOKING_JOIN + " WHERE 1 = 1"
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
    """Returns bookings scheduled for one date, sorted by day order."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            _BOOKING_JOIN + " WHERE b.booking_date = ? "
            "ORDER BY b.time_slot",
            (booking_date,)
        )
        return cursor.fetchall()
    finally:
        connection.close()


def get_bookings_in_month(year, month):
    """Returns bookings whose date falls inside a given month, by date."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        prefix = "%04d-%02d-%%" % (year, month)
        cursor.execute(
            _BOOKING_JOIN + " WHERE b.booking_date LIKE ? "
            "ORDER BY b.booking_date, b.time_slot",
            (prefix,)
        )
        return cursor.fetchall()
    finally:
        connection.close()


def update_status(booking_id, status):
    """Changes the status of a booking (admin action or client cancel)."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE bookings SET status = ? WHERE id = ?",
                       (status, booking_id))
        connection.commit()
        cursor.execute("SELECT user_id FROM bookings WHERE id = ?",
                       (booking_id,))
        return cursor.fetchone()
    finally:
        connection.close()


def delete_booking(booking_id):
    """Permanently removes a booking (admin only, confirms first)."""
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
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = ?",
                       ("Pending",))
        pending = cursor.fetchone()[0]
        cursor.execute(
            "SELECT SUM(total_price) FROM bookings WHERE status = ?",
            ("Completed",))
        revenue_row = cursor.fetchone()[0]
        revenue = revenue_row if revenue_row is not None else 0
        return (total, pending, revenue)
    finally:
        connection.close()


def get_admin_stats():
    """
    Returns dashboard numbers: bookings per status, revenue from completed
    bookings only, and the count of client accounts.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        stats = {}
        import datetime
        today = datetime.date.today()
        week_start = (today - datetime.timedelta(days=today.weekday())
                      ).isoformat()
        today_text = today.isoformat()
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_date=?",
                       (today_text,))
        stats["today"] = cursor.fetchone()[0]
        cursor.execute(
            "SELECT COUNT(*) FROM bookings WHERE booking_date>=?",
            (week_start,))
        stats["week"] = cursor.fetchone()[0]
        active_list = ["Pending", "Confirmed", "On the Way", "In Progress"]
        cursor.execute("SELECT COUNT(*) FROM bookings WHERE status IN "
                       + "(" + ",".join("?" for _ in active_list) + ")",
                       active_list)
        stats["active"] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bookings")
        stats["total"] = cursor.fetchone()[0]
        for status in config.BOOKING_STATUSES:
            cursor.execute("SELECT COUNT(*) FROM bookings WHERE status = ?",
                           (status,))
            stats[status] = cursor.fetchone()[0]
        cursor.execute(
            "SELECT SUM(total_price) FROM bookings WHERE status = 'Completed'")
        revenue_row = cursor.fetchone()[0]
        stats["revenue"] = revenue_row if revenue_row is not None else 0
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'client'")
        stats["clients"] = cursor.fetchone()[0]
        return stats
    finally:
        connection.close()


def count_user_bookings(user_id):
    """Counts how many bookings a client has made in total."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) AS total FROM bookings WHERE user_id=?",
                       (user_id,))
        return cursor.fetchone()["total"]
    finally:
        connection.close()


def get_next_booking(user_id):
    """Returns the client's closest upcoming active booking, or None."""
    """
    Returns the client's next upcoming active booking (soonest by date),
    or None when there is nothing coming up.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT * FROM bookings WHERE user_id = ? AND booking_date >= ? "
            "AND status NOT IN ('Completed', 'Cancelled') "
            "ORDER BY booking_date, time_slot LIMIT 1",
            (user_id, today)
        )
        return cursor.fetchone()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# CLIENTS FOR THE ADMIN SCREEN
# ---------------------------------------------------------------------------
def get_client_counts():
    """Returns a dictionary user_id -> number of bookings for every client."""
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT user_id, COUNT(*) AS c FROM bookings "
                       "GROUP BY user_id")
        counts = {}
        for row in cursor.fetchall():
            counts[row["user_id"]] = row["c"]
        return counts
    finally:
        connection.close()

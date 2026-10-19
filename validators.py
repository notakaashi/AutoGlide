"""
validators.py
=============================================================================
Input checking helpers for AutoGlide.

Each function returns a tuple: (is_valid, message). When is_valid is True the
message is empty. Screens call these before saving anything to the database,
so bad input never reaches the data layer.

Uses only the standard library (datetime) and config.py.
=============================================================================
"""

import datetime
import config


def is_empty(text):
    """Returns True when a text value is empty or only spaces."""
    return text.strip() == ""


def validate_phone(phone, label="Phone number"):
    """
    Checks a phone number: it must have 7 to 15 digits and may contain
    spaces, dashes, parentheses or a leading plus sign.
    """
    if is_empty(phone):
        return (False, label + " is required.")

    allowed = "0123456789 -()+"
    digits = 0
    for character in phone:
        if character not in allowed:
            return (False, label + " has an invalid character: " + character)
        if character.isdigit():
            digits = digits + 1

    if digits < 7:
        return (False, label + " must have at least 7 digits.")
    if digits > 15:
        return (False, label + " must have at most 15 digits.")
    return (True, "")


def validate_email(email):
    """Checks a basic email shape: one @, a dot after it, and no spaces."""
    if is_empty(email):
        return (False, "Email is required.")
    if " " in email:
        return (False, "Email must not contain spaces.")
    if email.count("@") != 1:
        return (False, "Email must contain one @ symbol.")

    name, domain = email.split("@")
    if is_empty(name):
        return (False, "Email is missing the part before @.")
    if "." not in domain:
        return (False, "Email domain looks incomplete.")
    if domain.startswith(".") or domain.endswith("."):
        return (False, "Email domain looks incomplete.")
    return (True, "")


def validate_registration(full_name, username, phone, email, password, confirm):
    """
    Checks every registration field at once.
    Does NOT check for duplicate usernames (the database does that).
    """
    if is_empty(full_name):
        return (False, "Full name is required.")
    if len(full_name.strip()) < 2:
        return (False, "Full name is too short.")

    if is_empty(username):
        return (False, "Username is required.")
    if len(username.strip()) < 3:
        return (False, "Username must be at least 3 characters.")
    for character in username:
        if not (character.isalnum() or character in "._-"):
            return (False, "Username may only use letters, numbers, . _ and -")

    phone_ok, phone_message = validate_phone(phone)
    if not phone_ok:
        return (False, phone_message)

    email_ok, email_message = validate_email(email)
    if not email_ok:
        return (False, email_message)

    if is_empty(password):
        return (False, "Password is required.")
    if len(password) < 6:
        return (False, "Password must be at least 6 characters.")
    if password != confirm:
        return (False, "Password and confirmation do not match.")

    return (True, "")


def validate_profile(full_name, phone, email):
    """Checks just the editable profile fields (no username/password)."""
    if is_empty(full_name):
        return (False, "Full name is required.")
    if len(full_name.strip()) < 2:
        return (False, "Full name is too short.")
    phone_ok, phone_message = validate_phone(phone)
    if not phone_ok:
        return (False, phone_message)
    email_ok, email_message = validate_email(email)
    if not email_ok:
        return (False, email_message)
    return (True, "")


def validate_date_format(date_text):
    """Checks only that a date uses the format YYYY-MM-DD and is a real date."""
    if is_empty(date_text):
        return (False, "Date is required.")
    try:
        datetime.datetime.strptime(date_text.strip(), "%Y-%m-%d")
    except ValueError:
        return (False, "Date must use the format YYYY-MM-DD.")
    return (True, "")


def validate_date(date_text):
    """
    Checks a booking date (YYYY-MM-DD): it must be a real date, not in the
    past, and within the allowed number of days ahead.
    """
    format_ok, format_message = validate_date_format(date_text)
    if not format_ok:
        return (False, format_message)

    chosen = datetime.datetime.strptime(date_text.strip(), "%Y-%m-%d").date()

    today = datetime.date.today()
    if chosen < today:
        return (False, "Date cannot be in the past.")
    if (chosen - today).days > config.MAX_ADVANCE_DAYS:
        return (False, "Date is too far ahead. Book within "
                       + str(config.MAX_ADVANCE_DAYS) + " days.")
    return (True, "")


def validate_vehicle(label, vehicle_type, make, model, color, plate):
    """
    Checks the saved vehicle form at once.
    Label, vehicle type, make and model are required; color and plate may
    be left empty.
    """
    if is_empty(label):
        return (False, "Vehicle nickname is required.")
    if len(label.strip()) > 30:
        return (False, "Vehicle nickname is too long.")
    if vehicle_type not in config.VEHICLE_TYPES:
        return (False, "Pick a vehicle type.")
    if is_empty(make):
        return (False, "Make is required.")
    if is_empty(model):
        return (False, "Model is required.")
    if len(color.strip()) > 30:
        return (False, "Color is too long.")
    if len(plate.strip()) > 12:
        return (False, "Plate number is too long.")
    return (True, "")


def validate_address(label, address, barangay, city, landmark):
    """
    Checks the saved address form at once.
    Label, street, barangay and city are required; landmark is optional.
    """
    if is_empty(label):
        return (False, "Label is required.")
    if len(label.strip()) > 30:
        return (False, "Label is too long.")
    if is_empty(address):
        return (False, "Street address is required.")
    if len(address.strip()) < 5:
        return (False, "Street address is too short.")
    if is_empty(barangay):
        return (False, "Barangay is required.")
    if is_empty(city):
        return (False, "City is required.")
    if len(landmark.strip()) > 120:
        return (False, "Landmark is too long.")
    return (True, "")


def validate_new_password(new_password, confirm):
    """
    Checks a password change: the new password must be long enough and must
    match its confirmation. (Correctness of the OLD password is checked
    against the database by the caller.)
    """
    if is_empty(new_password):
        return (False, "New password is required.")
    if len(new_password) < 6:
        return (False, "New password must be at least 6 characters.")
    if new_password != confirm:
        return (False, "New password and confirmation do not match.")
    return (True, "")

"""
config.py
=============================================================================
Configuration and business rules for AutoGlide Mobile Detailing.

Stores brand details, landing page copy, service packages, vehicle pricing,
add-ons, booking rules, and default seed data used by database.py.
Travel fees/zones and detailer management were removed from the product.
=============================================================================
"""

# Business Identity & Footer Information
BRAND_INFO = {
    "name": "AutoGlide",
    "service_area": "Serving Metro Manila and nearby areas.",
    "contact": "Phone: (02) 8920-4543 / 0917-890-2886 | Email: hello@autoglide.ph"
}

# Hero Section Content (Headline: 6 words or fewer; one sentence of subtext)
HERO_CONTENT = {
    "headline": "Car detailing at your doorstep.",
    "subtext": "We come to your home with our own water and equipment so you can spend your day on what matters.",
    "button_text": "Book Now"
}

# Design block shown where the old hero photo used to be (solid color + type)
HERO_BLOCK = {
    "title": "We bring the shine to you.",
    "caption": "Home service detailing"
}

# How It Works (exactly 3 short steps, few words each, no paragraphs)
HOW_IT_WORKS_STEPS = [
    "1. Choose a package",
    "2. Set time and address",
    "3. We wash at your home"
]

# Vehicle Categories
VEHICLE_TYPES = ["Sedan", "SUV", "Truck"]

# Detailing Service Tiers (3 clean tiers, prices in Philippine Pesos)
# At most 3 short bullet points per package.
SERVICE_TIERS = [
    {
        "id": "wash_vacuum",
        "name": "Wash & Vacuum",
        "accent": "#2E5A44",
        "prices": {
            "Sedan": 799,
            "SUV": 1099,
            "Truck": 1399
        },
        "bullets": [
            "Exterior hand wash",
            "Interior vacuum",
            "Windows and tire shine"
        ]
    },
    {
        "id": "wash_wax",
        "name": "Wash & Wax",
        "accent": "#1E392A",
        "prices": {
            "Sedan": 1299,
            "SUV": 1599,
            "Truck": 1899
        },
        "bullets": [
            "Wash and protective wax",
            "Vacuum and dashboard wipe",
            "Tire and rim cleaning"
        ]
    },
    {
        "id": "showroom",
        "name": "Showroom Detail",
        "accent": "#14261B",
        "prices": {
            "Sedan": 2499,
            "SUV": 2999,
            "Truck": 3399
        },
        "bullets": [
            "Deep clean and paint wax",
            "Carpet and seat shampoo",
            "Interior deodorizing"
        ]
    }
]

# Full-Width Banner Section (design block replaces the old banner photo)
BANNER_CONTENT = {
    "line": "Clean cars made simple.",
    "caption": "Book a wash in under a minute.",
    "button_text": "Book Now"
}

# Targeted Add-Ons (used on the New Booking screen), keyed by add-on id
ADD_ONS = {
    "engine_bay": {"name": "Engine bay wipe", "price": 499},
    "headlights": {"name": "Headlight cleaning", "price": 599},
    "cabin_odor": {"name": "Cabin deodorizer", "price": 399}
}

# Booking rules
TIME_SLOTS = ["8:00 AM", "10:00 AM", "12:00 PM", "2:00 PM", "4:00 PM"]
SLOT_CAPACITY = 3          # maximum active bookings allowed per time slot
MAX_ADVANCE_DAYS = 60      # how far ahead a client may book

# Booking statuses used across the app
BOOKING_STATUSES = [
    "Pending",
    "Confirmed",
    "On the Way",
    "In Progress",
    "Completed",
    "Cancelled"
]

# Statuses that may still be cancelled by the client
CANCELLABLE_STATUSES = ["Pending", "Confirmed"]

# New booking wizard steps
WIZARD_STEPS = [
    "1 Vehicle",
    "2 Package",
    "3 Schedule",
    "4 Location",
    "5 Review"
]

# Booking wizard extra copy
REVIEW_NOTE = ("We will confirm your booking shortly. You pay after the "
               "service, cash or GCash.")

# Client Home page copy
HOME_SUBTEXT = "Here is what is coming up for your car."
HOME_EMPTY_TEXT = ("You have no upcoming booking. Tap Book a Detail and we "
                   "will come to your home.")

# Default accounts seeded on first run
DEFAULT_ADMIN = {
    "full_name": "AutoGlide Admin",
    "username": "admin",
    "phone": "0917-000-0000",
    "email": "admin@autoglide.ph",
    "password": "admin123",
    "role": "admin"
}


# ---------------------------------------------------------------------------
# SMALL LOOKUP HELPERS (used by several screens so the code is not repeated)
# ---------------------------------------------------------------------------
def tier_by_id(tier_id):
    """Returns the service tier dictionary for an id."""
    for tier in SERVICE_TIERS:
        if tier["id"] == tier_id:
            return tier
    return None


def tier_name(tier_id):
    """Returns a package name for an id, or the id itself if not found."""
    tier = tier_by_id(tier_id)
    if tier is None:
        return tier_id
    return tier["name"]


def price_for(tier_id, vehicle_type):
    """Returns the package price from config for a vehicle type."""
    tier = tier_by_id(tier_id)
    if tier is None:
        return 0
    return tier["prices"].get(vehicle_type, 0)


def addon_name(addon_id):
    """Returns an add-on name for an id, or the id itself if not found."""
    info = ADD_ONS.get(addon_id)
    if info is None:
        return addon_id
    return info["name"]


def addons_text(addons):
    """Turns a stored comma-separated add-on string into readable names."""
    if addons is None or addons.strip() == "":
        return "None"
    names = []
    for addon_id in addons.split(","):
        names.append(addon_name(addon_id.strip()))
    return ", ".join(names)


def friendly_date(date_text):
    """Turns 'YYYY-MM-DD' into 'Mon, Oct 19, 2026' for the GUI."""
    import datetime
    try:
        date_value = datetime.date.fromisoformat(str(date_text))
    except (TypeError, ValueError):
        return str(date_text or "")
    return date_value.strftime("%a, %b %d, %Y")


def slot_note():
    """One-line note about slots shown beside the schedule picker."""
    return ("Each slot takes up to " + str(SLOT_CAPACITY) + " cars per day. "
            "Grey slots are already full.")

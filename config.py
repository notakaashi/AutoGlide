"""
config.py
=============================================================================
Configuration and business rules for AutoGlide Mobile Detailing.

Stores brand details, landing page copy, service packages, vehicle pricing,
add-ons, service zones (with travel fees), booking rules, and default seed
data used by database.py.
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

# Targeted Add-Ons (used on the New Booking screen)
ADD_ONS = [
    {
        "id": "engine_bay",
        "name": "Engine bay wipe",
        "price": 499
    },
    {
        "id": "headlights",
        "name": "Headlight cleaning",
        "price": 599
    },
    {
        "id": "cabin_odor",
        "name": "Cabin deodorizer",
        "price": 399
    }
]

# Service Zones with travel fees. Coordinates (x1, y1, x2, y2) place the zone
# as a rectangle on the map picker Canvas.
SERVICE_ZONES = [
    {
        "code": "QC",
        "name": "Quezon City",
        "travel_fee": 150,
        "rect": (20, 20, 240, 140)
    },
    {
        "code": "BGC",
        "name": "BGC / Makati",
        "travel_fee": 200,
        "rect": (270, 20, 500, 140)
    },
    {
        "code": "MNL",
        "name": "Manila",
        "travel_fee": 250,
        "rect": (20, 170, 240, 290)
    },
    {
        "code": "SMD",
        "name": "Parañaque / South",
        "travel_fee": 300,
        "rect": (270, 170, 500, 290)
    }
]

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

# Default accounts seeded on first run
DEFAULT_ADMIN = {
    "full_name": "AutoGlide Admin",
    "username": "admin",
    "phone": "0917-000-0000",
    "email": "admin@autoglide.ph",
    "password": "admin123",
    "role": "admin"
}

# Default detailers seeded on first run
DEFAULT_DETAILERS = [
    "Marco Reyes",
    "Dina Santos",
    "Paolo Cruz"
]


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


def zone_by_code(zone_code):
    """Returns the service zone dictionary for a code."""
    for zone in SERVICE_ZONES:
        if zone["code"] == zone_code:
            return zone
    return None


def zone_name(zone_code):
    """Returns a zone name for a code, or a dash if there is no code."""
    zone = zone_by_code(zone_code)
    if zone is None:
        return "-"
    return zone["name"]


def addon_name(addon_id):
    """Returns an add-on name for an id, or the id itself if not found."""
    for addon in ADD_ONS:
        if addon["id"] == addon_id:
            return addon["name"]
    return addon_id


def addons_text(addons):
    """Turns a stored comma-separated add-on string into readable names."""
    if addons is None or addons.strip() == "":
        return "None"
    names = []
    for addon_id in addons.split(","):
        names.append(addon_name(addon_id))
    return ", ".join(names)

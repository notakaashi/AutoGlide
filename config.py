"""
config.py
=============================================================================
Configuration file for AutoGlide Mobile Detailing.
Stores business details, landing page copy, service packages, vehicle pricing,
and reserved data for future booking and location modules.
=============================================================================
"""

# Business Identity & Footer Information
BRAND_INFO = {
    "name": "AutoGlide",
    "service_area": "Serving Metro Manila and nearby areas.",
    "contact": "Phone: (02) 8920-4543 / 0917-890-2886 | Email: hello@autoglide.ph"
}

# Hero Section Content (Headline: 6 words or fewer; exactly one sentence of subtext)
HERO_CONTENT = {
    "headline": "Car detailing at your doorstep.",
    "subtext": "We come to your home with our own water and equipment so you can spend your day on what matters.",
    "button_text": "Book Now",
    "image_path": "assets/images/hero.png"
}

# How It Works (Exactly 3 short steps, few words each, no paragraphs)
HOW_IT_WORKS_STEPS = [
    "1. Choose a package",
    "2. Set time and address",
    "3. We wash at your home"
]

# Vehicle Categories
VEHICLE_TYPES = ["Sedan", "SUV", "Truck"]

# Detailing Service Tiers (3 clean tiers with plain names, prices in Philippine Pesos)
# At most 3 short bullet points per package.
SERVICE_TIERS = [
    {
        "id": "wash_vacuum",
        "name": "Wash & Vacuum",
        "image_path": "assets/images/tier_wash.png",
        "prices": {
            "Sedan": 799,
            "SUV": 999,
            "Truck": 1199
        },
        "bullets": [
            "Hand wash and dry",
            "Interior vacuum",
            "Windows and tire dressing"
        ]
    },
    {
        "id": "wash_wax",
        "name": "Wash & Wax",
        "image_path": "assets/images/tier_wax.png",
        "prices": {
            "Sedan": 1499,
            "SUV": 1799,
            "Truck": 2099
        },
        "bullets": [
            "Foam wash and spray wax",
            "Vacuum and dashboard wipe",
            "Wheel clean and tire shine"
        ]
    },
    {
        "id": "deep_clean",
        "name": "Deep Clean",
        "image_path": "assets/images/tier_reset.png",
        "prices": {
            "Sedan": 2499,
            "SUV": 2999,
            "Truck": 3499
        },
        "bullets": [
            "Exterior wash and protective wax",
            "Shampoo seats and floor mats",
            "Interior wipe and deodorizer"
        ]
    }
]

# Full-Width Photo Banner Section
BANNER_CONTENT = {
    "line": "Clean cars made simple.",
    "button_text": "Book Now",
    "image_path": "assets/images/banner.png"
}

# ---------------------------------------------------------------------------
# RESERVED DATA FOR BOOKING FLOW (Moved off landing page to keep it clean)
# ---------------------------------------------------------------------------
# Targeted Add-Ons (will be used when building the full booking screen)
ADD_ONS = [
    {
        "id": "engine_bay",
        "name": "Engine bay wipe",
        "price": 499,
        "description": "Safe dust and grease wipe with protective finish."
    },
    {
        "id": "headlights",
        "name": "Headlight cleaning",
        "price": 599,
        "description": "Cleans yellowed plastic covers for better light."
    },
    {
        "id": "odor_treatment",
        "name": "Cabin deodorizer",
        "price": 399,
        "description": "Removes trapped food, smoke, and moisture odors."
    },
    {
        "id": "rain_repellent",
        "name": "Windshield rain treatment",
        "price": 449,
        "description": "Helps rain slide off glass for clear road view."
    }
]

# Service Zones (will be used for the map pin and location picker)
SERVICE_ZONES = [
    {"code": "QC", "name": "Quezon City and Ortigas"},
    {"code": "BGC", "name": "BGC, Makati, and Mandaluyong"},
    {"code": "SOUTH", "name": "Alabang, Parañaque, and Las Piñas"},
    {"code": "BAY", "name": "Pasay and Manila Bay"}
]

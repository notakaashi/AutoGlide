"""
theme.py
=============================================================================
Styling definitions for AutoGlide.
Defines a calm, restrained palette inspired by a dependable local business:
warm linen, deep pine green, and soft charcoal.
=============================================================================
"""

# ---------------------------------------------------------------------------
# COLOR PALETTE (Restrained 3-4 Color Palette)
# ---------------------------------------------------------------------------
BG_MAIN = "#F8F7F4"            # Warm linen / off-white (page background)
BG_SURFACE = "#FFFFFF"         # Pure clean white (cards, navigation bar)
BG_PLACEHOLDER = "#EBE9E4"     # Warm stone tone for image placeholders

BORDER_COLOR = "#E5E3DE"       # Subtle warm border and divider line

ACCENT_COLOR = "#1E392A"       # Deep pine green (primary button and brand accent)
ACCENT_HOVER = "#2A4D3B"       # Slightly lighter pine for hover states

TEXT_DARK = "#1A1D1A"          # Soft charcoal ink (headlines, main body)
TEXT_MUTED = "#5F665E"         # Muted sage slate (subtitles, secondary info)
TEXT_LIGHT = "#FFFFFF"         # Crisp white for text inside dark buttons

# ---------------------------------------------------------------------------
# TYPOGRAPHY
# ---------------------------------------------------------------------------
# Clean standard font family available on Windows with standard fallbacks
FONT_FAMILY = "Segoe UI"

FONT_BRAND = (FONT_FAMILY, 15, "bold")
FONT_HERO = (FONT_FAMILY, 24, "bold")
FONT_HERO_SUB = (FONT_FAMILY, 12, "normal")

FONT_SECTION = (FONT_FAMILY, 18, "bold")
FONT_CARD_TITLE = (FONT_FAMILY, 13, "bold")
FONT_PRICE = (FONT_FAMILY, 18, "bold")

FONT_BODY = (FONT_FAMILY, 10, "normal")
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_BUTTON = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9, "normal")

# ---------------------------------------------------------------------------
# SPACING CONSTANTS
# ---------------------------------------------------------------------------
PAD_XS = 4
PAD_SM = 8
PAD_MD = 16
PAD_LG = 24
PAD_XL = 32
PAD_HERO = 40

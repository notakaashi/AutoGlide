"""
theme.py
=============================================================================
Design tokens for AutoGlide.

One place for every color, font, and spacing value, so the whole application
looks consistent. Also sets up the ttk styles used by the tables and scroll
bars (ttk is part of the Tkinter package in the standard library).
=============================================================================
"""

from tkinter import ttk

# ---------------------------------------------------------------------------
# COLOR PALETTE
# ---------------------------------------------------------------------------
BG_APP = "#F4F2EE"          # app canvas (warm off-white)
BG_SURFACE = "#FFFFFF"      # cards and panels
BG_SOFT = "#FAF9F6"         # very light panel tint
BG_HOVER = "#F0EEE9"        # hover fill
BG_SIDEBAR = "#FBFAF7"      # sidebar background
BG_INPUT = "#FFFFFF"        # entry background

BORDER = "#E7E4DD"          # thin default border
BORDER_STRONG = "#D6D2C9"   # stronger border (focused/selected)

PRIMARY = "#1E392A"         # deep pine green (brand + primary button)
PRIMARY_HOVER = "#294C39"
PRIMARY_ACTIVE = "#152A1E"
ACCENT = "#2E5A44"          # mid pine (secondary accent)
ACCENT_SOFT = "#E4ECE6"     # pale pine fill

TEXT = "#1F231F"            # main text
TEXT_MUTED = "#6B716A"      # secondary text
TEXT_FAINT = "#9AA098"      # hints / disabled
TEXT_ON_DARK = "#FFFFFF"    # text on dark fills

DANGER = "#A8453C"
DANGER_HOVER = "#B95A50"
SUCCESS = "#1E6B43"

# Status colors as (text color, background color) pairs for pills.
STATUS = {
    "Pending": ("#8A6416", "#F6ECD6"),
    "Confirmed": ("#1E5E8A", "#DCEAF4"),
    "On the Way": ("#4A3F8A", "#E6E3F5"),
    "In Progress": ("#8A5A1F", "#F5E7D6"),
    "Completed": ("#1E6B43", "#DCEFE2"),
    "Cancelled": ("#7A4038", "#F3E1DE")
}
# Old name kept so nothing that references it breaks.
STATUS_COLORS = {name: pair[0] for name, pair in STATUS.items()}

# Design blocks (decorative solid panels)
BLOCK_DARK = PRIMARY
BLOCK_MID = ACCENT
BLOCK_LIGHT = ACCENT_SOFT

# Map picker
MAP_BG = "#EDEBE5"
MAP_ZONE_FILL = "#FFFFFF"
MAP_ZONE_HOVER = "#E9F0EA"
MAP_ZONE_SELECTED = "#D6E4DA"
MAP_ZONE_BORDER = "#CFCBC2"
MAP_PIN = "#C0453B"
MAP_PIN_SHADOW = "#00000022"

# ---------------------------------------------------------------------------
# TYPOGRAPHY (all Text using the same family and a small type scale)
# ---------------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"

FONT_BRAND = (FONT_FAMILY, 15, "bold")
FONT_HERO = (FONT_FAMILY, 30, "bold")
FONT_HERO_SUB = (FONT_FAMILY, 12, "normal")
FONT_SECTION = (FONT_FAMILY, 18, "bold")
FONT_TITLE = (FONT_FAMILY, 15, "bold")
FONT_CARD_TITLE = (FONT_FAMILY, 12, "bold")
FONT_PRICE = (FONT_FAMILY, 20, "bold")

FONT_BODY = (FONT_FAMILY, 10, "normal")
FONT_BODY_BOLD = (FONT_FAMILY, 10, "bold")
FONT_BUTTON = (FONT_FAMILY, 10, "bold")
FONT_SMALL = (FONT_FAMILY, 9, "normal")
FONT_SMALL_BOLD = (FONT_FAMILY, 9, "bold")
FONT_TINY = (FONT_FAMILY, 8, "normal")

# ---------------------------------------------------------------------------
# SPACING
# ---------------------------------------------------------------------------
PAD_XS = 4
PAD_SM = 8
PAD_MD = 16
PAD_LG = 24
PAD_XL = 32
PAD_HERO = 40

# ---------------------------------------------------------------------------
# RADII
# ---------------------------------------------------------------------------
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14

# ---------------------------------------------------------------------------
# ttk STYLE (used only by the tables and scroll bars)
# ---------------------------------------------------------------------------
def apply_ttk_style(root):
    """Sets up the ttk styles for the DataTable and thin scroll bars."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Treeview = the ttk table widget (not in the basic widget list, so noted).
    style.configure(
        "AutoGlide.Treeview",
        background=BG_SURFACE,
        fieldbackground=BG_SURFACE,
        foreground=TEXT,
        rowheight=34,
        borderwidth=0,
        font=FONT_BODY
    )
    style.configure(
        "AutoGlide.Treeview.Heading",
        background=BG_SOFT,
        foreground=TEXT_MUTED,
        relief="flat",
        font=FONT_SMALL_BOLD,
        padding=(8, 8)
    )
    style.map(
        "AutoGlide.Treeview",
        background=[("selected", ACCENT_SOFT)],
        foreground=[("selected", TEXT)]
    )
    style.map(
        "AutoGlide.Treeview.Heading",
        background=[("active", BG_HOVER)]
    )

    # Thin, modern scroll bars.
    style.configure(
        "Thin.Vertical.TScrollbar",
        background=BORDER_STRONG,
        troughcolor=BG_SOFT,
        bordercolor=BG_SOFT,
        arrowcolor=TEXT_MUTED,
        relief="flat",
        width=10
    )
    style.configure(
        "Thin.Horizontal.TScrollbar",
        background=BORDER_STRONG,
        troughcolor=BG_SOFT,
        bordercolor=BG_SOFT,
        arrowcolor=TEXT_MUTED,
        relief="flat"
    )

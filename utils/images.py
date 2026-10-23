"""
utils/images.py
=============================================================================
Tiny image helper for the AutoGlide screens.

load_image(name, size) loads photos/<name> (also tries common typo variants
like banner.jpg.jpg), crops it to exactly fill the requested size, and gives
back an ImageTk.PhotoImage ready to put on a Canvas or Label.

Two rules every caller must follow:
  - The CALLER keeps a reference (widget.image = photo) or Tkinter will
    garbage-collect the picture and it disappears.
  - A missing or unreadable file NEVER crashes the app: a flat
    theme.BG_SOFT placeholder image is returned instead.
=============================================================================
"""

import os
import sys

import theme

# say the "no Pillow" thing exactly once per program run, never twice
# include the interpreter path so it's obvious which Python needs Pillow
_pillow_warned = False


def _warn_no_pillow():
    global _pillow_warned
    if not _pillow_warned:
        print("Pillow is not installed for this Python: %s. Run: %s -m pip install pillow" % (sys.executable, sys.executable))
        _pillow_warned = True


try:
    from PIL import Image, ImageDraw, ImageOps
    from PIL import ImageTk as _PILImageTk
    PIL_OK = True
except ImportError:            # Pillow not installed - placeholders only
    PIL_OK = False
    _warn_no_pillow()

# pictures/ sits next to the project root (utils/ is one level down)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PICTURES_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "pictures"))


def _candidates(name):
    """All spelling variants we are willing to try inside pictures/."""
    stem = os.path.splitext(name)[0]
    names = [name, name + ".jpg", stem + ".jpg", stem + "..jpg"]
    seen = []
    for n in names:
        if n not in seen:
            seen.append(n)
    return seen


def _find_path(name):
    """First existing pictures/ file that matches name (tolerates typos)."""
    stem = os.path.splitext(name)[0]
    for candidate in _candidates(name):
        path = os.path.join(PICTURES_DIR, candidate)
        if os.path.isfile(path):
            return path
    # last resort: any file in pictures/ starting with the name's stem
    if os.path.isdir(PICTURES_DIR):
        for entry in os.listdir(PICTURES_DIR):
            if entry.startswith(stem):
                return os.path.join(PICTURES_DIR, entry)
    return None


def load_image(name, size, cover=True, rounded=0, color=None):
    """Returns an ImageTk.PhotoImage for pictures/<name>.

    size      - (width, height) in pixels
    cover     - crop the picture so it fills the whole size
    rounded   - corner radius in px (0 = square corners)
    color     - placeholder fill color when something goes wrong
    """
    fill = color or theme.BG_SOFT
    width, height = size
    if not PIL_OK:
        # return a plain grey PhotoImage so the canvas keeps its size
        import tkinter as tk
        img = tk.PhotoImage(width=width, height=height)
        img.put((fill,), to=(0, 0, width, height))
        return img
    try:
        path = _find_path(name)
        if path is None:
            raise FileNotFoundError(name)
        with Image.open(path) as img:
            img = img.convert("RGB")
            # cover-crop so the picture fills the box without squashing
            if cover:
                img = ImageOps.fit(img, (width, height),
                                   method=Image.LANCZOS)
            else:
                img = img.resize((width, height), Image.LANCZOS)
            if rounded > 0:                      # soft rounded corners
                mask = Image.new("L", (width, height), 0)
                ImageDraw.Draw(mask).rounded_rectangle(
                    (0, 0, width - 1, height - 1), radius=rounded, fill=255)
                img = img.convert("RGBA")
                img.putalpha(mask)
            return _PILImageTk.PhotoImage(img)
    except Exception:
        # flat block of the tame background color - never crash the app
        try:
            solid = Image.new("RGB", (width, height), fill)
            if rounded > 0:
                mask = Image.new("L", (width, height), 0)
                ImageDraw.Draw(mask).rounded_rectangle(
                    (0, 0, width - 1, height - 1), radius=rounded, fill=255)
                solid = solid.convert("RGBA")
                solid.putalpha(mask)
            return _PILImageTk.PhotoImage(solid)
        except Exception:
            return None


def attach(widget, photo):
    """Keeps a reference so Tkinter does not garbage-collect the image."""
    widget.image = photo
    return photo


def cover_photo(canvas, name):
    """Fills a whole canvas with one photo, redrawing on resize.

    Used by the auth screens for the full-height side image. The photo is
    re-cropped to the current canvas size (never squashed), and a missing
    file leaves the canvas flat-tinted instead of crashing.
    """
    def redraw(event=None):
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        canvas.delete("all")
        photo = load_image(name, (width, height), cover=True)
        attach(canvas, photo)
        if photo:
            canvas.create_image(0, 0, image=photo, anchor="nw")

    canvas.bind("<Configure>", redraw)
    canvas.after(80, redraw)
    return redraw

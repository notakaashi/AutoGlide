"""
components.py
=============================================================================
Reusable UI components for AutoGlide.
Contains:
  - HoverButton: Label-based button with consistent hover styling on all OS platforms
  - CardFrame: Clean bordered container card
  - ScrollableContainer: Responsive canvas with mousewheel scrolling
  - load_or_placeholder_image: Robust dual-engine image loader. Uses Pillow (PIL)
                               when available, falls back to native Tkinter PhotoImage
                               (PNG support), and falls back to a calm Canvas placeholder
                               if a file cannot be loaded.
=============================================================================
"""

import os
import tkinter as tk
import theme

# Pillow (PIL) enables advanced proportional cropping and JPEG decoding.
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _resolve_image_path(path):
    """
    Finds the absolute path to an image file relative to the project directory,
    and checks for alternate extensions (.png / .jpg) if needed.
    """
    if not path:
        return None

    # Base directory is the AutoGlide folder containing components.py
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # If relative, anchor to base_dir
    candidate = path if os.path.isabs(path) else os.path.normpath(os.path.join(base_dir, path))

    if os.path.exists(candidate):
        return candidate

    # Try matching filename with alternate common extensions
    root, ext = os.path.splitext(candidate)
    for alt_ext in [".png", ".jpg", ".jpeg"]:
        alt_path = root + alt_ext
        if os.path.exists(alt_path):
            return alt_path

    return None


class HoverButton(tk.Label):
    """
    A custom button built on tk.Label to ensure consistent background colors
    and hover effects across Windows, macOS, and Linux without native OS overrides.
    """
    def __init__(self, master, text="", command=None,
                 bg=theme.ACCENT_COLOR, fg=theme.TEXT_LIGHT,
                 hover_bg=theme.ACCENT_HOVER, hover_fg=theme.TEXT_LIGHT,
                 font=theme.FONT_BUTTON, padx=16, pady=8, cursor="hand2", **kwargs):
        super().__init__(
            master,
            text=text,
            bg=bg,
            fg=fg,
            font=font,
            padx=padx,
            pady=pady,
            cursor=cursor,
            **kwargs
        )
        self.command = command
        self.default_bg = bg
        self.default_fg = fg
        self.hover_bg = hover_bg
        self.hover_fg = hover_fg
        self.is_active = False

        # Bind mouse hover and click events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, event=None):
        """Changes color when mouse enters the button area."""
        if not self.is_active:
            self.configure(bg=self.hover_bg, fg=self.hover_fg)

    def _on_leave(self, event=None):
        """Restores default color when mouse leaves the button area."""
        if not self.is_active:
            self.configure(bg=self.default_bg, fg=self.default_fg)

    def _on_click(self, event=None):
        """Executes the assigned command callback when clicked."""
        if self.command:
            self.command()

    def set_active(self, is_active, active_bg=theme.ACCENT_COLOR, active_fg=theme.TEXT_LIGHT,
                   inactive_bg=theme.BG_SURFACE, inactive_fg=theme.TEXT_DARK):
        """
        Toggles an active/selected state for vehicle filter buttons and tabs.
        """
        self.is_active = is_active
        if is_active:
            self.configure(bg=active_bg, fg=active_fg)
        else:
            self.configure(bg=inactive_bg, fg=inactive_fg)


class CardFrame(tk.Frame):
    """
    A clean container card with a light surface background and subtle border.
    """
    def __init__(self, master, bg=theme.BG_SURFACE, border_color=theme.BORDER_COLOR,
                 highlightthickness=1, **kwargs):
        super().__init__(
            master,
            bg=bg,
            highlightbackground=border_color,
            highlightthickness=highlightthickness,
            **kwargs
        )


class ScrollableContainer(tk.Frame):
    """
    A scrolling container that bundles a tk.Canvas and a tk.Scrollbar.
    Handles dynamic inner width resizing and cross-platform mousewheel scrolling.
    """
    def __init__(self, master, bg=theme.BG_MAIN, **kwargs):
        super().__init__(master, bg=bg, **kwargs)

        # 1. Canvas setup
        self.canvas = tk.Canvas(
            self,
            bg=bg,
            highlightthickness=0,
            borderwidth=0
        )

        # 2. Vertical scrollbar
        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # 3. Inner scrollable frame
        self.content = tk.Frame(self.canvas, bg=bg)
        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.content,
            anchor="nw"
        )

        # Dynamic resizing listeners
        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Bind mousewheel scrolling
        self.bind_mousewheel(self)

    def _on_content_configure(self, event):
        """Updates scrollregion whenever content changes height."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Resizes the inner frame to match the canvas width upon window resize."""
        self.canvas.itemconfig(self.window_id, width=event.width)

    def _on_mousewheel(self, event):
        """Handles mousewheel events smoothly on Windows, macOS, and Linux."""
        if hasattr(event, "delta") and event.delta != 0:
            scroll_units = -1 * int(event.delta / 120) if abs(event.delta) >= 120 else -1 * int(event.delta)
            self.canvas.yview_scroll(scroll_units, "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def bind_mousewheel(self, widget):
        """
        Recursively binds mousewheel listeners to a widget and its children
        so scrolling works regardless of where the mouse is positioned.
        """
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_mousewheel, add="+")
        widget.bind("<Button-5>", self._on_mousewheel, add="+")

        for child in widget.winfo_children():
            self.bind_mousewheel(child)


def load_or_placeholder_image(master, image_path, target_width, target_height, placeholder_text=""):
    """
    Loads an image file, scales and crops it, and displays it inside a tk.Label.

    Engine priority:
      1. Pillow (PIL): High quality proportional crop & resize for JPG and PNG.
      2. Native Tkinter PhotoImage: Built-in Tk 8.6 PNG decoder (no pip required).
      3. Palette Placeholder: Quiet Canvas block with border if file cannot be found.
    """
    resolved_path = _resolve_image_path(image_path)

    # Strategy 1: Pillow is available
    if HAS_PIL and resolved_path:
        try:
            with Image.open(resolved_path) as img:
                orig_w, orig_h = img.size
                scale = max(target_width / orig_w, target_height / orig_h)
                new_w = max(1, int(orig_w * scale))
                new_h = max(1, int(orig_h * scale))

                resample_filter = getattr(Image.Resampling, "LANCZOS", getattr(Image, "ANTIALIAS", 1))
                resized = img.resize((new_w, new_h), resample_filter)

                left = (new_w - target_width) // 2
                top = (new_h - target_height) // 2
                right = left + target_width
                bottom = top + target_height
                cropped = resized.crop((left, top, right, bottom))

                photo = ImageTk.PhotoImage(cropped)
                lbl = tk.Label(master, image=photo, bg=theme.BG_PLACEHOLDER, bd=0, highlightthickness=0)
                lbl.image = photo  # Keep reference to prevent GC
                return lbl
        except Exception:
            pass

    # Strategy 2: Native Tkinter PhotoImage (supports PNG without Pillow)
    if resolved_path:
        # Check if the file is PNG or if a PNG version exists
        png_path = resolved_path if resolved_path.lower().endswith(".png") else None
        if not png_path:
            root_no_ext = os.path.splitext(resolved_path)[0]
            if os.path.exists(root_no_ext + ".png"):
                png_path = root_no_ext + ".png"

        if png_path:
            try:
                raw_photo = tk.PhotoImage(file=png_path)
                w, h = raw_photo.width(), raw_photo.height()

                # Calculate integer subsample if image is noticeably larger than target
                sub_x = max(1, round(w / target_width))
                sub_y = max(1, round(h / target_height))
                final_photo = raw_photo.subsample(sub_x, sub_y) if (sub_x > 1 or sub_y > 1) else raw_photo

                lbl = tk.Label(master, image=final_photo, bg=theme.BG_PLACEHOLDER, bd=0, highlightthickness=0)
                lbl.image = final_photo  # Keep reference to prevent GC
                return lbl
            except Exception:
                pass

    # Strategy 3: Graceful fallback placeholder in palette colors
    canvas = tk.Canvas(
        master,
        width=target_width,
        height=target_height,
        bg=theme.BG_PLACEHOLDER,
        highlightthickness=1,
        highlightbackground=theme.BORDER_COLOR,
        bd=0
    )
    margin = 8
    canvas.create_rectangle(
        margin, margin, target_width - margin, target_height - margin,
        outline=theme.BORDER_COLOR, width=1
    )

    label_msg = placeholder_text if placeholder_text else (os.path.basename(image_path) if image_path else "Image")
    canvas.create_text(
        target_width // 2,
        target_height // 2,
        text=label_msg,
        font=theme.FONT_SMALL,
        fill=theme.TEXT_MUTED
    )
    return canvas

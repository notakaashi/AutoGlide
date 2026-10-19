"""
screens/booking_wizard.py
=============================================================================
New Booking wizard (5 steps).

Steps: 1 Vehicle, 2 Package, 3 Schedule, 4 Location, 5 Review.
Each step validates before moving on. Prices come from the database so admin
edits apply to new bookings. On confirm the booking is saved as Pending and
the client is taken to My Bookings.
=============================================================================
"""

import tkinter as tk
import datetime
import theme
import config
import database
import validators
from components import (Card, SectionHeading, Button, SegmentedControl, Chip,
                        EntryField, DateField, MapPicker, Toast)


class BookingWizard(tk.Frame):
    """A five-step wizard that creates a booking."""
    def __init__(self, master, app):
        self.app = app
        super().__init__(master, bg=theme.BG_APP)
        self.pack(fill="both", expand=True)

        self.step = 1
        self.vehicle_type = self.app.booking_draft.get("vehicle_type", "Sedan")
        self.tier_id = self.app.booking_draft.get("tier_id", "wash_vacuum")
        self.addons = []
        self.booking_date = ""
        self.time_slot = ""
        self.address = ""
        self.zone_code = None
        self.travel_fee = 0
        self.pin_x = None
        self.pin_y = None

        self._dots = []
        self._price_labels = {}
        self._addon_chips = {}
        self._slot_chips = {}
        self._build_progress()
        self._build_content()
        self._show_step()

    # ------------------------------------------------------------------
    # PROGRESS BAR
    # ------------------------------------------------------------------
    def _build_progress(self):
        """Builds the step progress indicator."""
        card = Card(self, pad=theme.PAD_SM)
        card.pack(fill="x", padx=theme.PAD_LG, pady=(theme.PAD_MD, 0))
        row = tk.Frame(card.body, bg=theme.BG_SURFACE)
        row.pack(fill="x")
        for label in config.WIZARD_STEPS:
            cell = tk.Frame(row, bg=theme.BG_SURFACE)
            cell.pack(side="left", fill="x", expand=True, padx=4)
            dot = tk.Canvas(cell, width=30, height=30, bg=theme.BG_SURFACE,
                            highlightthickness=0, bd=0)
            dot.pack(anchor="center")
            text = tk.Label(cell, text=label, font=theme.FONT_TINY,
                            fg=theme.TEXT_FAINT, bg=theme.BG_SURFACE)
            text.pack(anchor="center")
            self._dots.append((dot, text))
        self._update_progress()

    def _update_progress(self):
        """Repaints each step dot for done, current, and upcoming states."""
        for index, (dot, text) in enumerate(self._dots, start=1):
            dot.delete("all")
            if index < self.step:
                dot.create_oval(3, 3, 27, 27, fill=theme.PRIMARY,
                                outline=theme.PRIMARY)
                dot.create_text(15, 15, text="\u2713", font=theme.FONT_SMALL_BOLD,
                                fill=theme.TEXT_ON_DARK)
                text.configure(fg=theme.TEXT_MUTED)
            elif index == self.step:
                dot.create_oval(3, 3, 27, 27, fill=theme.ACCENT_SOFT,
                                outline=theme.PRIMARY, width=2)
                dot.create_text(15, 15, text=str(index),
                                font=theme.FONT_BODY_BOLD, fill=theme.PRIMARY)
                text.configure(fg=theme.PRIMARY, font=theme.FONT_TINY)
            else:
                dot.create_oval(3, 3, 27, 27, fill=theme.BG_SURFACE,
                                outline=theme.BORDER)
                dot.create_text(15, 15, text=str(index),
                                font=theme.FONT_BODY, fill=theme.TEXT_FAINT)
                text.configure(fg=theme.TEXT_FAINT)

    # ------------------------------------------------------------------
    # SHELL
    # ------------------------------------------------------------------
    def _build_content(self):
        """Creates the content area for the current step."""
        self.content = tk.Frame(self, bg=theme.BG_APP)
        self.content.pack(fill="both", expand=True, padx=theme.PAD_LG,
                          pady=theme.PAD_MD)

    def _clear(self):
        """Destroys the current step's widgets."""
        for child in self.content.winfo_children():
            child.destroy()

    def _show_step(self):
        """Renders the current step."""
        self._clear()
        builders = {1: self._step_vehicle, 2: self._step_package,
                    3: self._step_schedule, 4: self._step_location,
                    5: self._step_review}
        builders[self.step]()
        self._update_progress()

    def _nav_buttons(self, body, next_text="Next"):
        """Adds Back and Next buttons at the bottom of a step."""
        nav = tk.Frame(body, bg=theme.BG_SURFACE)
        nav.pack(fill="x", pady=(theme.PAD_LG, 0))
        if self.step > 1:
            Button(nav, text="Back", command=self._back,
                   variant="ghost").pack(side="left")
        Button(nav, text=next_text, command=self._next,
               variant="primary").pack(side="right")
        return nav

    def _next(self):
        """Validates, then advances one step (or confirms on the last)."""
        if not self._validate():
            return
        if self.step == 5:
            self._confirm()
            return
        self.step += 1
        self._show_step()

    def _back(self):
        """Moves back one step."""
        if self.step > 1:
            self.step -= 1
            self._show_step()

    # ------------------------------------------------------------------
    # STEPS
    # ------------------------------------------------------------------
    def _step_vehicle(self):
        """Step 1: choose the vehicle type."""
        card = Card(self.content)
        card.pack(fill="both", expand=True)
        body = card.body
        SectionHeading(body, title="Step 1 - Vehicle",
                       subtitle="What are we washing today?").pack(anchor="w")
        self._vehicle_control = SegmentedControl(
            body, options=config.VEHICLE_TYPES, value=self.vehicle_type,
            command=self._on_vehicle)
        self._vehicle_control.pack(anchor="w", pady=theme.PAD_MD)
        self._nav_buttons(body)

    def _on_vehicle(self, value):
        """Stores the chosen vehicle type."""
        self.vehicle_type = value

    def _step_package(self):
        """Step 2: pick a package and optional add-ons (DB prices)."""
        card = Card(self.content)
        card.pack(fill="both", expand=True)
        body = card.body
        SectionHeading(body, title="Step 2 - Package",
                       subtitle="Prices shown for a " + self.vehicle_type
                       ).pack(anchor="w")

        self._price_labels = {}
        for tier in config.SERVICE_TIERS:
            row = tk.Frame(body, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=(theme.PAD_MD, 0))
            dot = tk.Canvas(row, width=18, height=18, bg=theme.BG_SURFACE,
                            highlightthickness=0, cursor="hand2")
            dot.pack(side="left")
            dot.bind("<Button-1>", lambda e, t=tier["id"]: self._pick_tier(t))
            dot._tier = tier["id"]
            row._tier_dot = dot
            left = tk.Frame(row, bg=theme.BG_SURFACE)
            left.pack(side="left", fill="x", expand=True, padx=8)
            name = tier["name"]
            base_price = database.get_price(tier["id"], self.vehicle_type)
            head = tk.Frame(left, bg=theme.BG_SURFACE)
            head.pack(fill="x")
            tk.Label(head, text=name, font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                     bg=theme.BG_SURFACE).pack(side="left")
            tk.Label(head, text="\u20b1" + str(base_price),
                     font=theme.FONT_BODY_BOLD,
                     fg=theme.PRIMARY, bg=theme.BG_SURFACE).pack(side="right")
            for bullet in tier["bullets"]:
                tk.Label(left, text="- " + bullet, font=theme.FONT_TINY,
                         fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE
                         ).pack(anchor="w")
            row._pick_part = [dot, left, head]
            for widget in [row, left, head] + list(head.winfo_children()):
                widget.bind("<Button-1>",
                            lambda e, t=tier["id"]: self._pick_tier(t))
                widget.configure(cursor="hand2")
            self._price_labels[tier["id"]] = dot
            for child in left.winfo_children():
                child.bind("<Button-1>",
                           lambda e, t=tier["id"]: self._pick_tier(t))
                child.configure(cursor="hand2")

        tk.Label(body, text="Add-on services", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE
                 ).pack(anchor="w", pady=(theme.PAD_LG, 0))
        chips = tk.Frame(body, bg=theme.BG_SURFACE)
        chips.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._addon_chips = {}
        for addon in database.get_addons():
            if not addon["active"]:
                continue
            selected = addon["id"] in self.addons
            chip = Chip(chips,
                        text=addon["name"] + " \u20b1" + str(addon["price"]),
                        command=lambda a=addon["id"]: self._toggle_addon(a),
                        state="selected" if selected else "normal",
                        bg=theme.BG_SURFACE)
            chip.pack(side="left", padx=(0, theme.PAD_SM))
            self._addon_chips[addon["id"]] = chip
        self._paint_tier_dots()
        self._nav_buttons(body)

    def _pick_tier(self, tier_id):
        """Selects one package and repaints the radio dots."""
        self.tier_id = tier_id
        self._paint_tier_dots()

    def _paint_tier_dots(self):
        """Repaints package radio dots."""
        for tier_id, dot in self._price_labels.items():
            dot.delete("all")
            selected = (tier_id == self.tier_id)
            fill = theme.PRIMARY if selected else theme.BG_SURFACE
            dot.create_oval(2, 2, 16, 16, fill=fill,
                            outline=theme.PRIMARY if selected else theme.BORDER_STRONG)
            if selected:
                dot.create_oval(6, 6, 12, 12, fill=theme.BG_SURFACE,
                                outline=theme.BG_SURFACE)

    def _toggle_addon(self, addon_id):
        """Adds or removes an add-on selection."""
        if addon_id in self.addons:
            self.addons.remove(addon_id)
            self._addon_chips[addon_id].state = "normal"
        else:
            self.addons.append(addon_id)
            self._addon_chips[addon_id].state = "selected"
        self._addon_chips[addon_id]._draw()

    def _step_schedule(self):
        """Step 3: date and time slot."""
        card = Card(self.content)
        card.pack(fill="both", expand=True)
        body = card.body
        SectionHeading(body, title="Step 3 - Schedule",
                       subtitle="When should we come over?").pack(anchor="w")
        self._date_field = DateField(body, label="Date", value=self.booking_date)
        self._date_field.pack(fill="x", pady=(theme.PAD_MD, 0))

        tk.Label(body, text="Available time slots", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE
                 ).pack(anchor="w", pady=(theme.PAD_LG, 0))
        self._slot_chips = {}
        chips = tk.Frame(body, bg=theme.BG_SURFACE)
        chips.pack(fill="x", pady=(theme.PAD_SM, 0))
        date_for_slots = self.booking_date or datetime.date.today().strftime("%Y-%m-%d")
        for slot in config.TIME_SLOTS:
            booked = database.count_slot_bookings(date_for_slots, slot)
            state = "normal"
            if booked >= config.SLOT_CAPACITY:
                state = "full"
            elif slot in self._chosen_slot():
                state = "selected"
            chip = Chip(chips, text=slot,
                        command=lambda s=slot: self._pick_slot(s),
                        state=state, bg=theme.BG_SURFACE)
            chip.pack(side="left", padx=(0, theme.PAD_SM))
            self._slot_chips[slot] = chip
        self._paint_slot_chips()
        self._nav_buttons(body)

    def _chosen_slot(self):
        """Returns the saved slot so chips can be preselected."""
        return [self.time_slot] if self.time_slot else []

    def _paint_slot_chips(self):
        """Repaints time slot chips in their saved states."""
        for slot, chip in self._slot_chips.items():
            if self.time_slot and slot == self.time_slot:
                chip.state = "selected"
            chip._draw()

    def _pick_slot(self, slot):
        """Stores the chosen time slot."""
        self.time_slot = slot
        self._paint_slot_chips()

    def _step_location(self):
        """Step 4: address and service-zone map with pin."""
        card = Card(self.content)
        card.pack(fill="both", expand=True)
        body = card.body
        SectionHeading(body, title="Step 4 - Location",
                       subtitle="Where should our detailers arrive?").pack(anchor="w")
        self._address_field = EntryField(body, label="Service address",
                                         placeholder="123 Main St, Barangay",
                                         width=40)
        self._address_field.pack(fill="x", pady=(theme.PAD_MD, 0))
        if self.address:
            self._address_field.set(self.address)
        map_holder = tk.Frame(body, bg=theme.BG_SURFACE)
        map_holder.pack(pady=(theme.PAD_MD, 0))
        self._map = MapPicker(map_holder, read_only=False,
                              on_select=self._on_zone_pick)
        self._map.pack()
        self._zone_label = tk.Label(body, text=self._zone_text(),
                                    font=theme.FONT_SMALL,
                                    fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE)
        self._zone_label.pack(anchor="w", pady=(theme.PAD_SM, 0))
        self._nav_buttons(body)

    def _zone_text(self):
        """Shows the picked zone and travel fee under the map."""
        if not self.zone_code:
            return "Pick a service zone on the map."
        name = config.zone_name(self.zone_code)
        return name + " - travel fee \u20b1" + str(self.travel_fee)

    def _on_zone_pick(self, zone, fee):
        """Stores zone and travel fee from the map click."""
        self.zone_code = zone["code"]
        self.travel_fee = fee
        coords = self._map.get_selection()
        self.pin_x, self.pin_y = coords[1], coords[2]
        self._zone_label.configure(text=self._zone_text())

    def _step_review(self):
        """Step 5: summary and confirm button."""
        card = Card(self.content)
        card.pack(fill="both", expand=True)
        body = card.body
        SectionHeading(body, title="Step 5 - Review",
                       subtitle="Check everything then book it").pack(anchor="w")
        rows = (
            ("Vehicle", self.vehicle_type),
            ("Package", config.tier_name(self.tier_id)),
            ("Add-ons", "None" if not self.addons else
             ", ".join(addon["name"] for addon in database.get_addons()
                       if addon["id"] in self.addons and addon["active"])),
            ("Date", self.booking_date),
            ("Slot", self.time_slot),
            ("Address", self.address),
            ("Zone", config.zone_name(self.zone_code)
             if self.zone_code else "Not picked"),
        )
        for label, value in rows:
            row = tk.Frame(body, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=(4, 0))
            tk.Label(row, text=label, font=theme.FONT_SMALL,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(side="left")
            tk.Label(row, text=value or "-", font=theme.FONT_BODY,
                     fg=theme.TEXT, bg=theme.BG_SURFACE,
                     justify="right").pack(side="right")
        tk.Frame(body, bg=theme.BORDER, height=1).pack(fill="x",
                                                       pady=(theme.PAD_MD, 0))
        pricing = self._compute_price()
        for label, value in (
            ("Base price", "\u20b1" + str(pricing["base"])),
            ("Add-ons", "\u20b1" + str(pricing["addons"])),
            ("Travel fee", "\u20b1" + str(pricing["travel"])),
        ):
            row = tk.Frame(body, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=(2, 0))
            tk.Label(row, text=label, font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(side="left")
            tk.Label(row, text=value, font=theme.FONT_SMALL, fg=theme.TEXT,
                     bg=theme.BG_SURFACE).pack(side="right")
        row = tk.Frame(body, bg=theme.BG_SURFACE)
        row.pack(fill="x", pady=(theme.PAD_SM, 0))
        tk.Label(row, text="Total", font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(side="left")
        tk.Label(row, text="\u20b1" + str(pricing["total"]),
                 font=theme.FONT_PRICE, fg=theme.PRIMARY,
                 bg=theme.BG_SURFACE).pack(side="right")
        self._nav_buttons(body, next_text="Confirm booking")

    # ------------------------------------------------------------------
    # PRICING
    # ------------------------------------------------------------------
    def _compute_price(self):
        """Returns a dict with base, add-ons, travel, and total prices."""
        base = database.get_price(self.tier_id, self.vehicle_type)
        addon_total = 0
        for addon in database.get_addons():
            if addon["id"] in self.addons and addon["active"]:
                addon_total += addon["price"]
        travel = self.travel_fee or 0
        return {"base": base, "addons": addon_total, "travel": travel,
                "total": base + addon_total + travel}

    # ------------------------------------------------------------------
    # VALIDATION AND CONFIRM
    # ------------------------------------------------------------------
    def _validate(self):
        """Validates the current step; shows inline errors when bad."""
        if self.step == 2:
            if not self.tier_id:
                Toast.show(self.winfo_toplevel(), "Pick a package.", "error")
                return False
            return True
        if self.step == 3:
            self.booking_date = self._date_field.get()
            ok, message = validators.validate_date(self.booking_date)
            if not ok:
                Toast.show(self.winfo_toplevel(), message, "error")
                return False
            if not self.time_slot:
                Toast.show(self.winfo_toplevel(),
                           "Pick a time slot.", "error")
                return False
            return True
        if self.step == 4:
            self.address = self._address_field.get()
            ok, message = validators.is_empty(self.address), ""
            if ok:
                Toast.show(self.winfo_toplevel(),
                           "Service address is required.", "error")
                return False
            if len(self.address.strip()) < 5:
                Toast.show(self.winfo_toplevel(),
                           "Service address is too short.", "error")
                return False
            if not self._map.selected_zone:
                Toast.show(self.winfo_toplevel(),
                           "Pick a service zone on the map.", "error")
                return False
            self.zone_code = self._map.selected_zone["code"]
            coords = self._map.get_selection()
            self.pin_x, self.pin_y = coords[1], coords[2]
            return True
        if self.step == 5:
            price = self._compute_price()
            if price["total"] <= 0:
                Toast.show(self.winfo_toplevel(), "Pricing unavailable.", "error")
                return False
            return True
        return True

    def _confirm(self):
        """Saves the booking as Pending and goes to My Bookings."""
        pricing = self._compute_price()
        database.create_booking(
            self.app.current_user["id"],
            self.vehicle_type, self.tier_id,
            ",".join(self.addons), pricing["base"], pricing["addons"],
            pricing["travel"], pricing["total"], self.booking_date,
            self.time_slot, self.address, self.zone_code,
            self.pin_x, self.pin_y, "Pending")
        Toast.show(self.winfo_toplevel(), "Booking created!", "success")
        if hasattr(self.app, "shell"):
            self.app.shell.switch_view("my_bookings")

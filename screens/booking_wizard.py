"""
screens/booking_wizard.py
=============================================================================
The New Booking wizard: five short steps.

1 Vehicle   - pick a saved vehicle or type a new one (with a save checkbox)
2 Package   - package cards plus add-on chips, live price
3 Schedule  - date picker (slots grey out when full, capacity in config)
4 Location  - pick a saved address or type a new one (with a save checkbox)
5 Review    - summary; Book Now writes a Pending booking

The student note: prices come from config.price_for(), never from the DB,
so what the client sees always matches config.py.
=============================================================================
"""

import datetime
import tkinter as tk

import theme
import config
import database
import validators

from components import (Card, Button, DateField, Chip, Toast, EntryField,
                        CheckField)


class BookingWizard(tk.Frame):
    """The five-step booking flow that saves the draft into main.session."""
    STEPS = ["Vehicle", "Package", "Schedule", "Location", "Review"]

    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = shell.current_user
        super().__init__(master, bg=theme.BG_APP)
        self._dots = []
        self._tier_cards = []
        self._vehicle_rows = []
        self._address_rows = []
        self._price_labels = []
        self._addon_chips = {}
        self._slot_chips = {}
        self._saved_vehicle_check = None
        self._saved_address_check = None
        self._refresh_job = None
        self.pack(fill="both", expand=True)

        self._draft = self.app.booking_draft
        self._draft.setdefault("vehicle_type", "Sedan")
        self._draft.setdefault("tier_id", "wash_vacuum")
        self._draft.setdefault("addons", [])
        self._draft.setdefault("place", {})
        self._load_fresh_draft()

        self.card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG)
        self.card.pack(fill="both", expand=True, padx=theme.PAD_LG,
                       pady=theme.PAD_LG)
        self.body = self.card.body
        self._build_header()
        self._build_body()
        self.render_step()

    def _load_fresh_draft(self):
        """Starts clean; prefills the picked package from the landing page."""
        tier_id = self._draft.pop("picked_tier", None)
        if tier_id:
            self._draft["tier_id"] = tier_id
        self._draft["vehicle_type"] = "Sedan"
        self._draft["addons"] = []
        self._draft["place"] = {}
        self._draft["step"] = 0
        self._saved_vehicles = database.get_saved_vehicles(self.user["id"])
        self._saved_addresses = database.get_saved_addresses(self.user["id"])
        self._draft["vehicle"] = None
        self._draft["address"] = None
        self._draft["booking_date"] = None
        self._draft["time_slot"] = None

    # ------------------------------------------------------------------
    # HEADER (steps display + dots)
    # ------------------------------------------------------------------
    def _build_header(self):
        """Small caption with the clinic-style step dots."""
        top = tk.Frame(self.body, bg=theme.BG_SURFACE)
        top.pack(fill="x")
        left = tk.Frame(top, bg=theme.BG_SURFACE)
        left.pack(side="left")
        tk.Label(left, text="New Booking", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        self._step_label = tk.Label(left, text="", font=theme.FONT_TINY,
                                    fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE)
        self._step_label.pack(anchor="w")
        dots = tk.Frame(top, bg=theme.BG_SURFACE)
        dots.pack(side="right")
        for i in range(5):
            dot = tk.Canvas(dots, width=16, height=16, bg=theme.BG_SURFACE,
                            highlightthickness=0)
            dot.pack(side="left", padx=2)
            self._dots.append(dot)

    def _paint_dots(self, step):
        """Paints one dot per step - big and filled when reached."""
        for i, dot in enumerate(self._dots):
            dot.delete("all")
            done = i <= step
            color = theme.PRIMARY if done else theme.BG_SOFT
            size = 9 if i == step else 6
            off = (16 - size) // 2
            dot.create_oval(off, off, off + size, off + size,
                            fill=color, outline=color)
            if i == step:
                dot.create_oval(off, off, off + size, off + size,
                                outline=theme.PRIMARY, width=2)

    # ------------------------------------------------------------------
    # BODY + FOOTER
    # ------------------------------------------------------------------
    def _build_body(self):
        """One plain frame per step that gets rebuilt on demand."""
        self._step_frame = tk.Frame(self.body, bg=theme.BG_SURFACE)
        self._step_frame.pack(fill="both", expand=True,
                              pady=(theme.PAD_MD, 0))

    def _build_footer(self, step):
        """Back / Continue buttons under the step content."""
        # kill the old footer first, otherwise buttons pile up per step
        if getattr(self, "_footer", None) is not None:
            try:
                self._footer.destroy()
            except Exception:
                pass
        foot = tk.Frame(self.body, bg=theme.BG_SURFACE)
        foot.pack(fill="x", side="bottom", pady=(theme.PAD_MD, 0))
        self._footer = foot
        if step > 0:
            Button(foot, text="Back",
                   command=lambda: self._go(step - 1),
                   variant="ghost").pack(side="right", padx=(8, 0))
        if step < 4:
            Button(foot, text="Continue",
                   command=lambda: self._go(step + 1),
                   variant="primary").pack(side="right")
        else:
            Button(foot, text="Book it",
                   command=self._confirm, variant="primary").pack(side="right")

    def render_step(self):
        """Shows the current step inside the card."""
        step = self._draft.get("step", 0)
        self._step_label.configure(
            text="Booking steps - step " + str(step + 1) + " of 5: "
            + self.STEPS[step])
        self._paint_dots(step)
        self._slot_chips = {}
        self._addon_chips = {}
        # Price labels belong to one step only - old ones die with the
        # step frame, so the list must be emptied on every new step.
        self._price_labels = []
        self._clear_step()
        self._slot_frame = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        self._slot_frame.pack(fill="x")
        {
            0: self._step_vehicle,
            1: self._step_package,
            2: self._step_schedule,
            3: self._step_location,
            4: self._step_review,
        }[step]()
        self._build_footer(step)

    def _clear_step(self):
        """Removes the step content but keeps the card header."""
        for wdg in self._step_frame.winfo_children():
            wdg.destroy()

    def _go(self, step):
        """Validates before moving between steps."""
        current = self._draft.get("step", 0)
        ok = True
        if step > current:
            checks = {
                0: self._validate_vehicle,
                1: self._validate_package,
                2: self._validate_schedule,
                3: self._validate_location,
            }.get(current)
            if checks:
                ok, message = checks()
                if not ok:
                    Toast(self, message, variant="error")
        if ok:
            self._draft["step"] = step
            self.render_step()

    # ------------------------------------------------------------------
    # STEP 1 - VEHICLE
    # ------------------------------------------------------------------
    def _step_vehicle(self):
        """Choose a saved vehicle or type a new one."""
        self._clear_step()
        wrap = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        wrap.pack(fill="x")
        if self._saved_vehicles:
            saved = tk.Frame(wrap, bg=theme.BG_SURFACE)
            saved.pack(fill="x")
            tk.Label(saved, text="Saved vehicles",
                     font=theme.FONT_SMALL_BOLD, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w",
                                               pady=(0, theme.PAD_XS))
            self._vehicle_choice = tk.StringVar(value=""
                                                if self._draft["vehicle"] is None
                                                else str(self._draft["vehicle"]["id"]))
            for v in self._saved_vehicles:
                item = tk.Frame(saved, bg=theme.BG_SOFT)
                item.pack(fill="x", pady=3)
                radio = tk.Radiobutton(item, variable=self._vehicle_choice,
                                       value=str(v["id"]), command=self._pick_vehicle,
                                       bg=theme.BG_SOFT, cursor="hand2")
                radio.pack(side="left", padx=(8, 4))
                desc = database.vehicle_desc(
                    v["vehicle_type"], v["make"], v["model"],
                    v["color"], v["plate"])
                tk.Label(item, text=desc, font=theme.FONT_BODY,
                         fg=theme.TEXT, bg=theme.BG_SOFT).pack(
                             side="left", pady=6)
                self._vehicle_rows.append(item)

        form = Card(self._step_frame, pad=theme.PAD_LG)
        form.pack(fill="both", expand=True, pady=(theme.PAD_MD, 0))
        tk.Label(form.body, text="Vehicle details",
                 font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")

        row = tk.Frame(form.body, bg=theme.BG_SURFACE)
        row.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._v_label = EntryField(row, label="Nickname *", width=18,
                                   placeholder="e.g. Daily car",
                                   text=self._draft["vehicle"]["label"] if
                                   self._draft["vehicle"] else "")
        self._v_label.pack(side="left")
        self._v_type = tk.StringVar(value=self._draft["vehicle_type"])
        seg = tk.Frame(row, bg=theme.BG_SURFACE)
        seg.pack(side="left", padx=(16, 0))
        for vt in config.VEHICLE_TYPES:
            b = tk.Radiobutton(seg, text=vt, variable=self._v_type,
                               value=vt, command=self._pick_vtype,
                               font=theme.FONT_BODY, bg=theme.BG_SURFACE,
                               cursor="hand2")
            b.pack(side="left", padx=(0, 8))
            self._vehicle_rows.append(b)

        grid = tk.Frame(form.body, bg=theme.BG_SURFACE)
        grid.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._v_make = EntryField(grid, width=16, label="Make *",
                                  placeholder="e.g. Toyota",
                                  text=self._draft["vehicle"]["make"]
                                  if self._draft["vehicle"] else "")
        self._v_make.grid(row=0, column=0, padx=(0, 12), sticky="w")
        self._v_model = EntryField(grid, width=16, label="Model *",
                                   text=self._draft["vehicle"]["model"]
                                   if self._draft["vehicle"] else "")
        self._v_model.grid(row=0, column=1, padx=(0, 12), sticky="w")
        self._v_color = EntryField(grid, width=12, label="Color",
                                   text=self._draft["vehicle"]["color"]
                                   if self._draft["vehicle"] else "")
        self._v_color.grid(row=0, column=2, padx=(0, 12), sticky="w")
        self._v_plate = EntryField(grid, width=12, label="Plate",
                                   text=self._draft["vehicle"]["plate"]
                                   if self._draft["vehicle"] else "")
        self._v_plate.grid(row=0, column=3, sticky="w")
        # Typing in the form means "new vehicle" - deselect any saved pick.
        for field in (self._v_label, self._v_make, self._v_model,
                      self._v_color, self._v_plate):
            field.entry.bind("<FocusIn>",
                             lambda e: self._switch_to_new_vehicle())
        tk.Label(form.body,
                 text="Fields marked * are required.",
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w",
                                           pady=(theme.PAD_XS, 0))
        show_check = True
        if getattr(self, "_vehicle_choice", None) and \
                self._vehicle_choice.get().isdigit():
            show_check = False
        if show_check:
            self._saved_vehicle_check = CheckField(
                form.body, "Save this vehicle for next time", bg=theme.BG_SURFACE)

    def _switch_to_new_vehicle(self):
        """Switches to the typed form when the user edits a vehicle field."""
        if getattr(self, "_vehicle_choice", None) and \
                self._vehicle_choice.get().isdigit():
            self._vehicle_choice.set("")
            self._saved_vehicle_check.pack(anchor="w", pady=(theme.PAD_SM, 0))
        else:
            self._saved_vehicle_check = None

    def _pick_vtype(self):
        """Vehicle type radio changed - update price labels as well."""
        self._draft["vehicle_type"] = self._v_type.get()
        self._update_prices()

    def _pick_vehicle(self):
        """A saved vehicle radio got picked - fills the form with it."""
        try:
            vid = int(self._vehicle_choice.get())
        except ValueError:
            vid = None
        vehicle = self._find_vehicle(vid)
        if vehicle is None:
            return
        self._draft["vehicle"] = dict(vehicle)
        self._v_label.set(vehicle["label"])
        self._v_type.set(vehicle["vehicle_type"])
        self._v_make.set(vehicle["make"] or "")
        self._v_model.set(vehicle["model"] or "")
        self._v_color.set(vehicle["color"] or "")
        self._v_plate.set(vehicle["plate"] or "")
        self._draft["vehicle_type"] = vehicle["vehicle_type"]
        self._update_prices()

    def _find_vehicle(self, vid):
        """Looks a saved vehicle up by id."""
        for v in self._saved_vehicles:
            if v["id"] == vid:
                return v
        return None

    def _validate_vehicle(self):
        """Reads the form back into the draft; validates it."""
        data = {
            "label": self._v_label.get().strip(),
            "vehicle_type": self._v_type.get(),
            "make": self._v_make.get().strip(),
            "model": self._v_model.get().strip(),
            "color": self._v_color.get().strip(),
            "plate": self._v_plate.get().strip(),
        }
        ok, message = validators.validate_vehicle(
            data["label"], data["vehicle_type"], data["make"],
            data["model"], data["color"], data["plate"])
        if not ok:
            return (False, message)
        picked_saved = False
        if getattr(self, "_vehicle_choice", None) and \
                self._vehicle_choice.get().isdigit():
            saved = self._find_vehicle(int(self._vehicle_choice.get()))
            if saved is not None:
                picked_saved = True
                data["id"] = saved["id"]
                data["label"] = saved["label"]
                data["vehicle_type"] = saved["vehicle_type"]
                data["make"] = saved["make"]
                data["model"] = saved["model"]
                data["color"] = saved["color"]
                data["plate"] = saved["plate"]
        if not picked_saved and self._saved_vehicle_check and \
                self._saved_vehicle_check.get():
            database.add_saved_vehicle(
                self.user["id"], data["label"], data["vehicle_type"],
                data["make"], data["model"], data["color"], data["plate"])
        self._draft["vehicle"] = data
        self._draft["vehicle_type"] = data["vehicle_type"]
        return (True, "")

    # ------------------------------------------------------------------
    # STEP 2 - PACKAGE
    # ------------------------------------------------------------------
    def _step_package(self):
        """Package cards with live prices + add-on chips."""
        self._clear_step()
        head = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        head.pack(fill="x")
        tk.Label(head, text="For a " + self._draft["vehicle_type"],
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        row = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        row.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._tier_cards = []
        for tier in config.SERVICE_TIERS:
            selected = tier["id"] == self._draft["tier_id"]
            price = config.price_for(tier["id"], self._draft["vehicle_type"])
            card = Card(row, radius=theme.RADIUS_LG, pad=theme.PAD_LG,
                        bg=theme.BG_SOFT if selected else theme.BG_SURFACE)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0, theme.PAD_SM))
            card.body.bind("<Button-1>", lambda e, t=tier["id"]: self._pick_tier(t))
            card.title = tk.Label(card.body, text=tier["name"],
                                  font=theme.FONT_CARD_TITLE,
                                  fg=theme.PRIMARY
                                  if selected else theme.TEXT,
                                  bg=card.card_bg)
            card.title.pack(anchor="w")
            card.price_label = tk.Label(card.body, text="\u20b1" + str(price),
                                        font=theme.FONT_PRICE,
                                        fg=theme.TEXT, bg=card.card_bg)
            card.price_label.pack(anchor="w", pady=(2, theme.PAD_SM))
            for bullet in tier["bullets"]:
                tk.Label(card.body, text=bullet, font=theme.FONT_SMALL,
                         fg=theme.TEXT_MUTED,
                         bg=card.card_bg).pack(anchor="w")
            self._tier_cards.append((card, tier["id"]))

        addons_row = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        addons_row.pack(fill="x", pady=(theme.PAD_LG, 0))
        tk.Label(addons_row, text="Add-ons", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        chips = tk.Frame(addons_row, bg=theme.BG_SURFACE)
        chips.pack(fill="x", pady=(theme.PAD_SM, 0))
        for addon_id in sorted(config.ADD_ONS):
            info = config.ADD_ONS[addon_id]
            picked = addon_id in self._draft["addons"]
            chip = Chip(chips, text=info["name"] + "  +" + "\u20b1"
                        + str(info["price"]),
                        state="selected" if picked else "normal",
                        command=lambda a=addon_id: self._toggle_addon(a))
            chip.pack(side="left", padx=(0, 8))
            self._addon_chips[addon_id] = chip
        bar = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        bar.pack(fill="x", pady=(theme.PAD_MD, 0))
        self._update_prices()

    def _pick_tier(self, tier_id):
        """Package card clicked - repaint cards and prices."""
        self._draft["tier_id"] = tier_id
        for card, tid in self._tier_cards:
            selected = tid == tier_id
            card.set_card_bg(theme.BG_SOFT if selected else theme.BG_SURFACE)
            card.title.configure(fg=theme.PRIMARY if selected else theme.TEXT,
                                 bg=card.card_bg)
            card.price_label.configure(bg=card.card_bg)
        self._update_prices()

    def _toggle_addon(self, addon_id):
        """Adds or removes an add-on chip click."""
        addons = self._draft["addons"]
        if addon_id in addons:
            addons.remove(addon_id)
        else:
            addons.append(addon_id)
        chip = self._addon_chips.get(addon_id)
        if chip:
            chip.set_state("selected" if addon_id in addons else "normal")
        self._update_prices()

    def _update_prices(self):
        """Recalculates the lines shown on the price bar."""
        base = config.price_for(self._draft["tier_id"],
                                self._draft["vehicle_type"])
        addon_total = 0
        for addon_id in self._draft["addons"]:
            addon_total = addon_total + config.ADD_ONS[addon_id]["price"]
        line = ("Base price   \u20b1" + str(base)
                + "        Add-ons   \u20b1" + str(addon_total)
                + "        Estimated total   \u20b1" + str(base + addon_total))
        label = self._price_labels[0] if self._price_labels else None
        if label is None or not label.winfo_exists():
            # the old label died with the previous step - paint a fresh one
            label = tk.Label(self._step_frame, font=theme.FONT_BODY_BOLD,
                             fg=theme.PRIMARY, bg=theme.BG_SURFACE)
            label.pack(anchor="e")
            self._price_labels = [label]
        label.configure(text=line)

    def _validate_package(self):
        """Package always has a valid value - nothing to check."""
        return (True, "")

    # ------------------------------------------------------------------
    # STEP 3 - SCHEDULE
    # ------------------------------------------------------------------
    def _step_schedule(self):
        """Date picker plus time-slot chips (full ones disabled)."""
        self._clear_step()
        left = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        left.pack(side="left", pady=(theme.PAD_MD, 0))
        tk.Label(left, text="Pick a date", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        initial = self._draft.get("booking_date")
        self._date_field = DateField(left, value=initial,
                                     on_change=self._paint_slots)
        self._date_field.pack(anchor="w", pady=(theme.PAD_SM, 0))
        tk.Label(self._step_frame,
                 text="We can start as early as tomorrow, up to "
                 + str(config.MAX_ADVANCE_DAYS) + " days ahead.",
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(theme.PAD_XS, 0))

        right = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        right.pack(side="right", padx=(theme.PAD_XL, 0),
                   pady=(theme.PAD_MD, 0))
        tk.Label(right, text="Pick a time", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        self._slot_grid = tk.Frame(right, bg=theme.BG_SURFACE)
        self._slot_grid.pack(anchor="w", pady=(theme.PAD_SM, 0))
        self._paint_slots()
        tk.Label(self._step_frame,
                 text=config.slot_note(),
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w",
                                           pady=(theme.PAD_SM, 0))

    def _paint_slots(self):
        """Builds the time-slot chips; full slots are disabled."""
        date_text = self._date_field.get()
        current = self._draft.get("time_slot")
        for slot in config.TIME_SLOTS:
            full = False
            if date_text:
                full = database.count_slot_bookings(date_text, slot) >= \
                    config.SLOT_CAPACITY
            if full:
                state = "full"
            elif slot == current:
                state = "selected"
            else:
                state = "normal"
            chip = Chip(self._slot_grid, text=slot, state=state,
                        command=lambda s=slot: self._pick_slot(s))
            chip.pack(side="left", padx=(0, 8), pady=2)
            self._slot_chips[slot] = chip

    def _pick_slot(self, slot):
        """A time chip was clicked; repaint selection."""
        self._draft["time_slot"] = slot
        for s, chip in self._slot_chips.items():
            if chip.state == "full":
                continue
            chip.set_state("selected" if s == slot else "normal")

    def _validate_schedule(self):
        """Date + slot both required; date must be within the allowed range."""
        date_text = self._date_field.get()
        ok, message = validators.validate_date(date_text)
        if not ok:
            return (False, message)
        today = datetime.date.today()
        chosen = datetime.date.fromisoformat(date_text)
        if chosen < today + datetime.timedelta(days=1):
            return (False, "Pick tomorrow or later.")
        if chosen > today + datetime.timedelta(days=config.MAX_ADVANCE_DAYS):
            return (False, "Pick a date within " + str(config.MAX_ADVANCE_DAYS)
                    + " days.")
        slot = self._draft.get("time_slot")
        if slot:
            if database.count_slot_bookings(date_text, slot) >= \
                    config.SLOT_CAPACITY:
                return (False, "That time slot is already full.")
        if not slot:
            return (False, "Please pick a time slot.")
        self._draft["booking_date"] = date_text
        self._draft["time_slot"] = slot
        return (True, "")

    # ------------------------------------------------------------------
    # STEP 4 - LOCATION
    # ------------------------------------------------------------------
    def _step_location(self):
        """Saved address radios or a new address form + save checkbox."""
        self._clear_step()
        preamble = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        preamble.pack(fill="x", pady=(theme.PAD_SM, 0))
        tk.Label(preamble, text="We come to you. "
                 "Tell us where to find the car.",
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        if self._saved_addresses:
            saved = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
            saved.pack(fill="x", pady=(theme.PAD_SM, 0))
            tk.Label(saved, text="Saved addresses",
                     font=theme.FONT_SMALL_BOLD, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w",
                                               pady=(0, theme.PAD_XS))
            chosen = self._draft.get("address")
            # "new" = the form below; a saved address is picked by id only
            start = "new"
            if chosen and chosen.get("saved_id"):
                start = str(chosen["saved_id"])
            self._address_choice = tk.StringVar(value=str(start))
            for a in self._saved_addresses:
                lines = " - ".join(database.address_lines(
                    a["address"], a["barangay"], a["city"], a["landmark"]))
                item = tk.Frame(saved, bg=theme.BG_SOFT)
                item.pack(fill="x", pady=3)
                radio = tk.Radiobutton(item, variable=self._address_choice,
                                       value=str(a["id"]),
                                       command=self._pick_address,
                                       bg=theme.BG_SOFT, cursor="hand2")
                radio.pack(side="left", padx=(8, 4))
                tk.Label(item, text=(a["label"] + " - " + lines),
                         font=theme.FONT_BODY, fg=theme.TEXT,
                         bg=theme.BG_SOFT).pack(side="left", pady=6)
                self._address_rows.append(item)
            # last row: use the form instead of any saved address
            fresh_row = tk.Frame(saved, bg=theme.BG_SOFT)
            fresh_row.pack(fill="x", pady=(0, 6))
            tk.Radiobutton(fresh_row, variable=self._address_choice,
                           value="new", command=self._pick_new_address,
                           text="+ Type a new address",
                           bg=theme.BG_SOFT, cursor="hand2").pack(
                               side="left", padx=(8, 4), pady=6)
            self._address_rows.append(fresh_row)

        form = Card(self._step_frame, pad=theme.PAD_LG)
        form.pack(fill="both", expand=True, pady=(theme.PAD_MD, 0))
        head = tk.Frame(form.body, bg=theme.BG_SURFACE)
        head.pack(fill="x")
        tk.Label(head, text="Address details", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(side="left")
        tk.Label(head, text="  (*. required)", font=theme.FONT_TINY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(side="left")

        grid = tk.Frame(form.body, bg=theme.BG_SURFACE)
        grid.pack(fill="x", pady=(theme.PAD_SM, 0))
        chosen = self._draft.get("address") or {}
        self._a_label = EntryField(grid, width=16, label="Label *",
                                   placeholder="Home / Office",
                                   text=chosen.get("label", ""))
        self._a_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        self._a_street = EntryField(grid, width=24, label="Street address *",
                                    placeholder="House number and street",
                                    text=chosen.get("address", ""))
        self._a_street.grid(row=0, column=1, sticky="w")
        self._a_barangay = EntryField(grid, width=14, label="Barangay *",
                                      text=chosen.get("barangay", ""))
        self._a_barangay.grid(row=1, column=0, sticky="w", pady=(6, 0))
        self._a_city = EntryField(grid, width=14, label="City *",
                                  text=chosen.get("city", ""))
        self._a_city.grid(row=1, column=1, sticky="w", pady=(6, 0))
        self._a_landmark = EntryField(grid, width=30, label="Landmark",
                                      placeholder="e.g. beside the bakery",
                                      text=chosen.get("landmark", ""))
        self._a_landmark.grid(row=2, column=0, columnspan=2, sticky="w",
                              pady=(6, 0))
        # Typing in the form means "+ Type a new address" - auto-switch.
        for field in (self._a_label, self._a_street, self._a_barangay,
                      self._a_city, self._a_landmark):
            field.entry.bind("<FocusIn>",
                             lambda e: self._switch_to_new_address())
        if getattr(self, "_address_choice", None) and \
                self._address_choice.get().isdigit():
            self._saved_address_check = None
        else:
            self._saved_address_check = CheckField(
                form.body, "Save this address for next time",
                bg=theme.BG_SURFACE)
            self._saved_address_check.pack(anchor="w", pady=(theme.PAD_SM, 0))

    def _switch_to_new_address(self):
        """Switches to the '+ Type a new address' option when the user types."""
        if getattr(self, "_address_choice", None) and \
                self._address_choice.get().isdigit():
            self._address_choice.set("new")

    def _pick_address(self):
        """A saved address radio got picked - fill the address form."""
        try:
            aid = int(self._address_choice.get())
        except ValueError:
            aid = None
        for a in self._saved_addresses:
            if a["id"] == aid:
                data = {
                    "saved_id": a["id"],
                    "label": a["label"],
                    "address": a["address"],
                    "barangay": a["barangay"],
                    "city": a["city"],
                    "landmark": a["landmark"] or "",
                }
                self._draft["address"] = data
                self._a_label.set(a["label"])
                self._a_street.set(a["address"])
                self._a_barangay.set(a["barangay"])
                self._a_city.set(a["city"])
                self._a_landmark.set(a["landmark"] or "")
                return

    def _pick_new_address(self):
        """The '+ Type a new address' radio got picked - keep what is typed."""
        pick = self._draft.get("address")
        if pick is not None:
            pick.pop("saved_id", None)
            self._draft["address"] = pick

    def _validate_location(self):
        """Reads the address form; a saved pick wins until fields are edited."""
        data = {
            "label": self._a_label.get().strip(),
            "address": self._a_street.get().strip(),
            "barangay": self._a_barangay.get().strip(),
            "city": self._a_city.get().strip(),
            "landmark": self._a_landmark.get().strip(),
        }
        if getattr(self, "_address_choice", None) and \
                self._address_choice.get().isdigit():
            for a in self._saved_addresses:
                if a["id"] == int(self._address_choice.get()):
                    data["saved_id"] = a["id"]
                    data["label"] = a["label"]
                    data["address"] = a["address"]
                    data["barangay"] = a["barangay"]
                    data["city"] = a["city"]
                    data["landmark"] = a["landmark"] or ""
                    break
        ok, message = validators.validate_address(
            data["label"], data["address"], data["barangay"],
            data["city"], data["landmark"])
        if not ok:
            return (False, message)
        picked_saved = "saved_id" in data
        if not picked_saved and self._saved_address_check and \
                self._saved_address_check.get():
            saved_id = database.add_saved_address(
                self.user["id"], data["label"], data["address"],
                data["barangay"], data["city"], data["landmark"],
                is_default=0)
            if saved_id:
                data["saved_id"] = saved_id
        self._draft["address"] = data
        return (True, "")

    # ------------------------------------------------------------------
    # STEP 5 - REVIEW
    # ------------------------------------------------------------------
    def _step_review(self):
        """Summary lines with a breakdown: base + add-ons = total."""
        self._clear_step()
        left = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        right.pack(side="right", padx=(theme.PAD_XL, 0))

        v = self._draft["vehicle"]
        a = self._draft["address"]
        lines = [
            ("Vehicle", database.vehicle_desc(v["vehicle_type"], v["make"],
                                              v["model"], v["color"],
                                              v["plate"])),
            ("Package", config.tier_name(self._draft["tier_id"])),
            ("When", config.friendly_date(self._draft["booking_date"])
             + "  -  " + self._draft["time_slot"]),
            ("Where", " - ".join(database.address_lines(
                a["address"], a["barangay"], a["city"], a["landmark"]))),
        ]
        for key, value in lines:
            tk.Label(left, text=key, font=theme.FONT_SMALL_BOLD,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                         anchor="w", pady=(theme.PAD_SM, 0))
            tk.Label(left, text=value, font=theme.FONT_BODY, fg=theme.TEXT,
                     bg=theme.BG_SURFACE, wraplength=340,
                     justify="left").pack(anchor="w")

        base = config.price_for(self._draft["tier_id"],
                                self._draft["vehicle_type"])
        addon_total = 0
        for addon_id in self._draft["addons"]:
            addon_total = addon_total + config.ADD_ONS[addon_id]["price"]
        tk.Label(right, text="Price breakdown", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        tk.Label(right, text=config.tier_name(self._draft["tier_id"])
                 + " (" + self._draft["vehicle_type"] + ")",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        table = tk.Frame(right, bg=theme.BG_SURFACE)
        table.pack(anchor="w", pady=(theme.PAD_SM, 0))
        rows = [("Base", "\u20b1" + str(base))]
        for addon_id in self._draft["addons"]:
            info = config.ADD_ONS[addon_id]
            rows.append((info["name"], "+" + "\u20b1" + str(info["price"])))
        rows.append(("Total", "\u20b1" + str(base + addon_total)))
        for i, (name, amount) in enumerate(rows):
            last = i == len(rows) - 1
            tk.Label(table, text=name, font=theme.FONT_BODY_BOLD if last
                     else theme.FONT_SMALL,
                     fg=theme.TEXT if last else theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).grid(row=i, column=0, sticky="w")
            tk.Label(table, text=amount,
                     font=theme.FONT_BODY_BOLD if last else theme.FONT_SMALL,
                     fg=theme.TEXT, bg=theme.BG_SURFACE).grid(
                         row=i, column=1, sticky="e", padx=(30, 0))
        note = tk.Frame(right, bg=theme.BG_SURFACE)
        note.pack(anchor="w", pady=(theme.PAD_MD, 0))
        tk.Label(note, text=config.REVIEW_NOTE, font=theme.FONT_TINY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE,
                 wraplength=260, justify="left").pack(anchor="w")

    def _confirm(self):
        """Validates everything, saves the booking as Pending, shows a toast."""
        for validate, step in ((self._validate_vehicle, 0),
                               (self._validate_package, 1),
                               (self._validate_schedule, 2),
                               (self._validate_location, 3)):
            ok, message = validate()
            if not ok:
                self._draft["step"] = step
                self.render_step()
                Toast(self, message, variant="error")
                return
        v = self._draft["vehicle"]
        a = self._draft["address"]
        base = config.price_for(self._draft["tier_id"],
                                self._draft["vehicle_type"])
        addon_total = 0
        for addon_id in self._draft["addons"]:
            addon_total = addon_total + config.ADD_ONS[addon_id]["price"]
        addons_csv = ",".join(self._draft["addons"])
        booking_id = database.create_booking(
            self.user["id"], v["vehicle_type"], self._draft["tier_id"],
            addons_csv, base, addon_total, base + addon_total,
            self._draft["booking_date"], self._draft["time_slot"],
            a["address"], a["barangay"], a["city"], a["landmark"],
            v["label"], v["make"], v["model"], v["color"], v["plate"],
            "Pending")
        if booking_id is None:
            Toast(self, "That time slot filled up - pick another.",
                  variant="error")
            self._draft["step"] = 2
            self.render_step()
            return

        self._draft.clear()

        # Reset the reusable fields for the next booking session.
        self._draft.update({"vehicle_type": "Sedan", "tier_id": "wash_vacuum",
                            "addons": [], "place": {}, "step": 0})
        self._saved_vehicles = database.get_saved_vehicles(self.user["id"])
        self._saved_addresses = database.get_saved_addresses(self.user["id"])

        # Show the toast on the shell (this view is about to close), then
        # jump to My Bookings where the new booking is visible at once.
        Toast(self.winfo_toplevel(),
              "Booking #" + str(booking_id) + " requested!", variant="ok")
        self.shell.switch_view("my_bookings")

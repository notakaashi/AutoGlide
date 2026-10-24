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
                        CheckField, ScrollFrame, SelectCard)


class BookingWizard(tk.Frame):
    """The five-step booking flow that saves the draft into main.session."""
    STEPS = ["Vehicle", "Package", "Schedule", "Location", "Review"]

    def __init__(self, master, shell):
        self.shell = shell
        self.app = shell.app
        self.user = shell.current_user
        super().__init__(master, bg=theme.BG_APP)
        self._tier_cards = []
        self._vehicle_rows = []
        self._address_rows = []
        self._vehicle_cards = {}
        self._address_cards = {}
        self._vtype_chips = {}
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

        # the shell already builds this view in a full-height centered
        # column; stretch makes the card fill the window top to bottom
        self.card = Card(self, radius=theme.RADIUS_LG, pad=theme.PAD_LG,
                         stretch=True)
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
    # HEADER (step indicator)
    # ------------------------------------------------------------------
    def _build_header(self):
        """Title on the left, a numbered five-step indicator on the right."""
        top = tk.Frame(self.body, bg=theme.BG_SURFACE)
        top.pack(fill="x")
        left = tk.Frame(top, bg=theme.BG_SURFACE)
        left.pack(side="left")
        tk.Label(left, text="New Booking", font=theme.FONT_SECTION,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        self._step_label = tk.Label(left, text="", font=theme.FONT_SMALL,
                                    fg=theme.TEXT_MUTED,
                                    bg=theme.BG_SURFACE)
        self._step_label.pack(anchor="w")
        # one canvas draws the circles, the joining line and the names
        self._steps = tk.Canvas(top, width=520, height=64,
                                bg=theme.BG_SURFACE, highlightthickness=0)
        self._steps.pack(side="right")

    def _paint_steps(self, step):
        """Done = green with a check, current = green ring, rest = grey."""
        c = self._steps
        c.delete("all")
        start, gap, cy = 30, 115, 22
        for i in range(len(self.STEPS)):
            x = start + i * gap
            if i:
                x_prev = start + (i - 1) * gap
                color = theme.PRIMARY if i <= step else theme.BORDER
                c.create_line(x_prev + 14, cy, x - 14, cy,
                              fill=color, width=2)
        for i, name in enumerate(self.STEPS):
            x = start + i * gap
            if i < step:
                c.create_oval(x - 12, cy - 12, x + 12, cy + 12,
                              fill=theme.PRIMARY, outline=theme.PRIMARY)
                c.create_text(x, cy, text="\u2713",
                              font=theme.FONT_SMALL_BOLD,
                              fill=theme.TEXT_ON_DARK)
            elif i == step:
                c.create_oval(x - 12, cy - 12, x + 12, cy + 12,
                              fill=theme.BG_SURFACE, outline=theme.PRIMARY,
                              width=2)
                c.create_text(x, cy, text=str(i + 1),
                              font=theme.FONT_SMALL_BOLD,
                              fill=theme.PRIMARY)
            else:
                c.create_oval(x - 12, cy - 12, x + 12, cy + 12,
                              fill=theme.BG_SOFT, outline=theme.BORDER)
                c.create_text(x, cy, text=str(i + 1),
                              font=theme.FONT_SMALL_BOLD,
                              fill=theme.TEXT_FAINT)
            c.create_text(x, 46, text=name, font=theme.FONT_TINY,
                          fill=theme.PRIMARY if i <= step
                          else theme.TEXT_FAINT)

    # ------------------------------------------------------------------
    # BODY + FOOTER
    # ------------------------------------------------------------------
    def _build_body(self):
        """One plain frame per step that gets rebuilt on demand.

        The step content lives in a scroll area, so a long saved-vehicles
        or addresses list can't push the form and buttons off-screen.
        """
        scroller = ScrollFrame(self.body, bg=theme.BG_SURFACE)
        scroller.pack(fill="both", expand=True, pady=(theme.PAD_MD, 0))
        self._step_frame = scroller.inner

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
        # Back sits on the left edge, the primary action on the right edge
        if step > 0:
            Button(foot, text="Back",
                   command=lambda: self._go(step - 1),
                   variant="ghost", height=46).pack(side="left")
        if step < 4:
            Button(foot, text="Continue",
                   command=lambda: self._go(step + 1),
                   variant="primary", height=46).pack(side="right")
        else:
            Button(foot, text="Book it",
                   command=self._confirm, variant="primary",
                   height=46).pack(side="right")

    def render_step(self):
        """Shows the current step inside the card."""
        step = self._draft.get("step", 0)
        self._step_label.configure(
            text="Step " + str(step + 1) + " of 5  -  " + self.STEPS[step])
        self._paint_steps(step)
        self._slot_chips = {}
        self._addon_chips = {}
        # Price labels belong to one step only - old ones die with the
        # step frame, so the list must be emptied on every new step.
        self._price_labels = []
        self._clear_step()
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
        """Choose a saved vehicle card or type a new one."""
        self._clear_step()
        self._vehicle_rows = []
        self._vehicle_cards = {}
        wrap = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        wrap.pack(fill="x")
        if self._saved_vehicles:
            saved = tk.Frame(wrap, bg=theme.BG_SURFACE)
            saved.pack(fill="x")
            tk.Label(saved, text="Saved vehicles",
                     font=theme.FONT_SMALL_BOLD, fg=theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(anchor="w",
                                               pady=(0, theme.PAD_XS))
            chosen = self._draft.get("vehicle") or {}
            # "new" = the form below, like the address step
            start = "new"
            if chosen.get("id"):
                start = str(chosen["id"])
            self._vehicle_choice = tk.StringVar(value=str(start))
            # selectable cards instead of the old tiny radios
            for v in self._saved_vehicles:
                desc = database.vehicle_desc(
                    v["vehicle_type"], v["make"], v["model"],
                    v["color"], v["plate"])
                card = SelectCard(
                    saved,
                    title=v["label"] + "  -  " + v["vehicle_type"],
                    subtitle=desc, height=60,
                    selected=str(v["id"]) == str(start),
                    command=lambda vid=v["id"]: self._select_vehicle(vid))
                card.pack(fill="x", pady=(0, 6))
                self._vehicle_cards[str(v["id"])] = card
                self._vehicle_rows.append(card)
            # last card: use the form instead of a saved vehicle
            new_card = SelectCard(
                saved, title="+ Type a new vehicle",
                subtitle="Enter the details below", height=60,
                selected=str(start) == "new",
                command=self._pick_new_vehicle)
            new_card.pack(fill="x", pady=(0, 6))
            self._vehicle_cards["new"] = new_card
            self._vehicle_rows.append(new_card)

        form = Card(self._step_frame, pad=theme.PAD_LG)
        form.pack(fill="both", expand=True, pady=(theme.PAD_MD, 0))
        self._vehicle_form_body = form.body
        tk.Label(form.body, text="Vehicle details",
                 font=theme.FONT_BODY_BOLD, fg=theme.TEXT,
                 bg=theme.BG_SURFACE).pack(anchor="w")

        row = tk.Frame(form.body, bg=theme.BG_SURFACE)
        row.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._v_label = EntryField(row, label="Nickname *", width=24,
                                   placeholder="e.g. Daily car",
                                   font=theme.FONT_INPUT, pad_y=10,
                                   text=self._draft["vehicle"]["label"] if
                                   self._draft["vehicle"] else "")
        self._v_label.pack(side="left")
        self._v_type = tk.StringVar(value=self._draft["vehicle_type"])
        seg = tk.Frame(row, bg=theme.BG_SURFACE)
        seg.pack(side="left", padx=(24, 0), pady=(18, 0))
        # vehicle types as pills now, not boxed radios
        for vt in config.VEHICLE_TYPES:
            chip = Chip(seg, text=vt,
                        state="selected" if vt == self._draft["vehicle_type"]
                        else "normal",
                        command=lambda v=vt: self._pick_vtype(v))
            chip.pack(side="left", padx=(0, 8))
            self._vtype_chips[vt] = chip
            self._vehicle_rows.append(chip)

        grid = tk.Frame(form.body, bg=theme.BG_SURFACE)
        grid.pack(fill="x", pady=(theme.PAD_SM, 0))
        self._v_make = EntryField(grid, width=22, label="Make *",
                                  placeholder="e.g. Toyota",
                                  font=theme.FONT_INPUT, pad_y=10,
                                  text=self._draft["vehicle"]["make"]
                                  if self._draft["vehicle"] else "")
        self._v_make.grid(row=0, column=0, padx=(0, theme.PAD_MD),
                          sticky="w")
        self._v_model = EntryField(grid, width=22, label="Model *",
                                   font=theme.FONT_INPUT, pad_y=10,
                                   text=self._draft["vehicle"]["model"]
                                   if self._draft["vehicle"] else "")
        self._v_model.grid(row=0, column=1, sticky="w")
        # Color and Plate on a second row so they don't clip at 1000px wide
        self._v_color = EntryField(grid, width=22, label="Color",
                                   font=theme.FONT_INPUT, pad_y=10,
                                   text=self._draft["vehicle"]["color"]
                                   if self._draft["vehicle"] else "")
        self._v_color.grid(row=1, column=0, padx=(0, theme.PAD_MD),
                           sticky="w", pady=(theme.PAD_MD, 0))
        self._v_plate = EntryField(grid, width=22, label="Plate",
                                   font=theme.FONT_INPUT, pad_y=10,
                                   text=self._draft["vehicle"]["plate"]
                                   if self._draft["vehicle"] else "")
        self._v_plate.grid(row=1, column=1, sticky="w",
                           pady=(theme.PAD_MD, 0))
        # Typing in the form means "new vehicle" - deselect any saved pick.
        for field in (self._v_label, self._v_make, self._v_model,
                      self._v_color, self._v_plate):
            field.entry.bind("<FocusIn>",
                             lambda e=None: self._switch_to_new_vehicle())
        tk.Label(form.body,
                 text="Fields marked * are required.",
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w",
                                           pady=(theme.PAD_XS, 0))
        # save checkbox shows in "new vehicle" mode only
        if getattr(self, "_vehicle_choice", None) and \
                self._vehicle_choice.get().isdigit():
            self._saved_vehicle_check = None
        else:
            self._saved_vehicle_check = CheckField(
                form.body, "Save this vehicle for next time", bg=theme.BG_SURFACE)
            self._saved_vehicle_check.pack(anchor="w", pady=(theme.PAD_SM, 0))

    def _select_vehicle(self, vid):
        """A saved-vehicle card was clicked - fill the form with it."""
        self._vehicle_choice.set(str(vid))
        self._paint_vehicle_cards()
        self._pick_vehicle()

    def _paint_vehicle_cards(self):
        """Highlights only the picked vehicle card."""
        choice = self._vehicle_choice.get()
        for key, card in self._vehicle_cards.items():
            card.set_selected(key == str(choice))

    def _switch_to_new_vehicle(self):
        """Switches to the typed form when the user edits a vehicle field.
        Keeps the typed text; only the explicit card clears the form."""
        if getattr(self, "_vehicle_choice", None) and \
                self._vehicle_choice.get().isdigit():
            self._vehicle_choice.set("new")
            self._draft["vehicle"] = None
            if getattr(self, "_vehicle_cards", None):
                self._paint_vehicle_cards()
            if self._saved_vehicle_check is None:
                self._saved_vehicle_check = CheckField(
                    getattr(self, "_vehicle_form_body", self._step_frame),
                    "Save this vehicle for next time", bg=theme.BG_SURFACE)
            try:
                self._saved_vehicle_check.pack(anchor="w",
                                               pady=(theme.PAD_SM, 0))
            except Exception:
                pass

    def _pick_new_vehicle(self):
        """+ Type a new vehicle picked. Clears the saved pick and the form
        so nothing feeds the typed values underneath."""
        self._vehicle_choice.set("new")
        self._draft["vehicle"] = None
        self._paint_vehicle_cards()
        self._v_label.set("")
        self._v_type.set(self._draft.get("vehicle_type", "Sedan"))
        self._paint_vtype_chips()
        self._v_make.set("")
        self._v_model.set("")
        self._v_color.set("")
        self._v_plate.set("")
        # bring back the save checkbox if a saved pick removed it
        if self._saved_vehicle_check is None:
            self._saved_vehicle_check = CheckField(
                getattr(self, "_vehicle_form_body", self._step_frame),
                "Save this vehicle for next time", bg=theme.BG_SURFACE)
        try:
            self._saved_vehicle_check.pack(anchor="w", pady=(theme.PAD_SM, 0))
        except Exception:
            pass

    def _paint_vtype_chips(self):
        """Green pill on the chosen vehicle type only."""
        for name, chip in self._vtype_chips.items():
            chip.set_state("selected" if name == self._v_type.get()
                           else "normal")

    def _pick_vtype(self, value=None):
        """Vehicle type pill changed - update price labels as well."""
        if value:
            self._v_type.set(value)
        self._paint_vtype_chips()
        self._draft["vehicle_type"] = self._v_type.get()
        self._update_prices()

    def _pick_vehicle(self):
        """A saved vehicle card got picked - fills the form with it."""
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
        self._paint_vtype_chips()
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
        # id always present (None when typed) so step-1 rerender never KeyErrors
        data = {
            "id": None,
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
        # grid with three equal columns: cards always share the row width
        # (pack would keep every canvas at its default ~378px and clip)
        for c in range(len(config.SERVICE_TIERS)):
            row.grid_columnconfigure(c, weight=1, uniform="tiers")
        self._tier_cards = []
        for col, tier in enumerate(config.SERVICE_TIERS):
            selected = tier["id"] == self._draft["tier_id"]
            price = config.price_for(tier["id"], self._draft["vehicle_type"])
            card = Card(row, radius=theme.RADIUS_LG, pad=theme.PAD_LG,
                        bg=theme.ACCENT_SOFT if selected else theme.BG_SURFACE,
                        border=theme.PRIMARY if selected else theme.BORDER,
                        border_w=2 if selected else 1)
            card.grid(row=0, column=col, sticky="nsew",
                      padx=(0, theme.PAD_SM))
            card.body.bind("<Button-1>", lambda e, t=tier["id"]: self._pick_tier(t))
            card.title = tk.Label(card.body, text=tier["name"],
                                  font=theme.FONT_CARD_TITLE,
                                  fg=theme.PRIMARY
                                  if selected else theme.TEXT,
                                  bg=card.card_bg, cursor="hand2")
            card.title.pack(anchor="w")
            card.title.bind("<Button-1>",
                            lambda e, t=tier["id"]: self._pick_tier(t))
            card.price_label = tk.Label(card.body, text="\u20b1" + str(price),
                                        font=theme.FONT_PRICE,
                                        fg=theme.TEXT, bg=card.card_bg,
                                        cursor="hand2")
            card.price_label.pack(anchor="w", pady=(2, theme.PAD_SM))
            card.price_label.bind("<Button-1>",
                                  lambda e, t=tier["id"]: self._pick_tier(t))
            for bullet in tier["bullets"]:
                bullet_label = tk.Label(card.body, text=bullet,
                                        font=theme.FONT_SMALL,
                                        fg=theme.TEXT_MUTED,
                                        bg=card.card_bg, cursor="hand2")
                bullet_label.pack(anchor="w")
                bullet_label.bind("<Button-1>",
                                  lambda e, t=tier["id"]: self._pick_tier(t))
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
            card.set_card_bg(theme.ACCENT_SOFT if selected
                             else theme.BG_SURFACE)
            # green border marks the chosen package
            card.set_border(theme.PRIMARY if selected else theme.BORDER,
                            2 if selected else 1)
            card.title.configure(fg=theme.PRIMARY if selected else theme.TEXT,
                                 bg=card.card_bg)
            card.price_label.configure(bg=card.card_bg)
            for child in card.body.winfo_children():
                try:
                    child.configure(bg=card.card_bg)
                except Exception:
                    pass
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
        """Date picker plus time-slot chips (full ones disabled).

        The chips sit in Morning / Afternoon rows and a "your booking"
        strip fills in live while you pick, so the step isn't just one
        lonely date box with empty space under it."""
        self._clear_step()
        row = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        row.pack(fill="x", pady=(theme.PAD_MD, 0))
        left = tk.Frame(row, bg=theme.BG_SURFACE)
        left.pack(side="left")
        tk.Label(left, text="Pick a date", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        initial = self._draft.get("booking_date")
        self._date_field = DateField(left, value=initial,
                                     on_change=lambda: self._on_date_changed())
        self._date_field.pack(anchor="w", pady=(theme.PAD_SM, 0))
        tk.Label(self._step_frame,
                 text="We can start as early as tomorrow, up to "
                 + str(config.MAX_ADVANCE_DAYS) + " days ahead.",
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w", pady=(theme.PAD_XS, 0))

        right = tk.Frame(row, bg=theme.BG_SURFACE)
        right.pack(side="right", padx=(theme.PAD_XL, 0))
        tk.Label(right, text="Pick a time", font=theme.FONT_BODY_BOLD,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(anchor="w")
        self._slot_grid = tk.Frame(right, bg=theme.BG_SURFACE)
        self._slot_grid.pack(anchor="w", pady=(theme.PAD_SM, 0))
        self._paint_slots()

        # the live summary strip - the fun bit that fills in as you choose
        strip = Card(self._step_frame, bg=theme.ACCENT_SOFT,
                     border=theme.ACCENT_SOFT, pad=theme.PAD_MD)
        strip.pack(fill="x", pady=(theme.PAD_LG, theme.PAD_MD))
        self._pick_label = tk.Label(
            strip.body, text="", font=theme.FONT_BODY_BOLD,
            fg=theme.PRIMARY, bg=theme.ACCENT_SOFT, justify="left")
        self._pick_label.pack(anchor="w")
        tk.Label(self._step_frame,
                 text=config.slot_note(),
                 font=theme.FONT_TINY, fg=theme.TEXT_MUTED,
                 bg=theme.BG_SURFACE).pack(anchor="w")
        self._update_pick_line()

    def _on_date_changed(self):
        """Date picked or retyped - repaint slots and the summary strip."""
        self._paint_slots()
        self._update_pick_line()

    def _slot_group(self, title, slots):
        """One caption + one row of slot chips (full ones disabled)."""
        tk.Label(self._slot_grid, text=title, font=theme.FONT_SMALL_BOLD,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE).pack(
                     anchor="w", pady=(6, 0))
        row = tk.Frame(self._slot_grid, bg=theme.BG_SURFACE)
        row.pack(anchor="w")
        date_text = self._date_field.get()
        current = self._draft.get("time_slot")
        for slot in slots:
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
            chip = Chip(row, text=slot, state=state,
                        command=lambda s=slot: self._pick_slot(s))
            chip.pack(side="left", padx=(0, 8), pady=2)
            self._slot_chips[slot] = chip

    def _paint_slots(self):
        """Rebuilds the two slot rows; Morning = before noon, Afternoon = rest."""
        for widget in self._slot_grid.winfo_children():
            widget.destroy()
        self._slot_chips = {}
        self._slot_group("Morning", config.TIME_SLOTS[:3])
        self._slot_group("Afternoon", config.TIME_SLOTS[3:])

    def _pick_slot(self, slot):
        """A time chip was clicked; repaint selection and the strip."""
        self._draft["time_slot"] = slot
        for s, chip in self._slot_chips.items():
            if chip.state == "full":
                continue
            chip.set_state("selected" if s == slot else "normal")
        self._update_pick_line()

    def _update_pick_line(self):
        """Fills the summary strip with the current date + time pick."""
        if not getattr(self, "_pick_label", None):
            return
        slot = self._draft.get("time_slot")
        # DateField.get() returns None when the box is empty
        date_text = self._date_field.get() if getattr(
            self, "_date_field", None) else ""
        if not date_text:
            date_text = ""
        try:
            day = datetime.date.fromisoformat(date_text)
        except ValueError:
            day = None
        if day is None or not slot:
            text = ("Your booking: nothing picked yet - " +
                    "choose a date, then a time.")
        else:
            used = database.count_slot_bookings(date_text, slot)
            open_left = max(0, config.SLOT_CAPACITY - used)
            text = ("Your booking: " + config.friendly_date(date_text)
                    + " at " + slot + "   -   " + str(open_left) + " open "
                    + "slot" + ("" if open_left == 1 else "s") + " left.")
        self._pick_label.configure(text=text)

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
        """Saved address cards or a new address form + save checkbox."""
        self._clear_step()
        self._address_cards = {}
        preamble = tk.Frame(self._step_frame, bg=theme.BG_SURFACE)
        preamble.pack(fill="x", pady=(theme.PAD_SM, 0))
        tk.Label(preamble, text="We come to you. "
                 "Tell us where to find the car.",
                 font=theme.FONT_SMALL, fg=theme.TEXT_MUTED,
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
            # selectable cards instead of the old tiny radios
            for a in self._saved_addresses:
                # address_lines() already returns one readable line
                lines = database.address_lines(
                    a["address"], a["barangay"], a["city"], a["landmark"])
                card = SelectCard(
                    saved, title=a["label"], subtitle=lines, height=64,
                    selected=str(a["id"]) == str(start),
                    command=lambda aid=a["id"]: self._select_address(aid))
                card.pack(fill="x", pady=(0, 6))
                self._address_cards[str(a["id"])] = card
                self._address_rows.append(card)
            # last card: use the form instead of any saved address
            new_card = SelectCard(
                saved, title="+ Type a new address",
                subtitle="Enter the details below", height=64,
                selected=str(start) == "new",
                command=self._pick_new_address)
            new_card.pack(fill="x", pady=(0, 6))
            self._address_cards["new"] = new_card
            self._address_rows.append(new_card)

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
        self._a_label = EntryField(grid, width=20, label="Label *",
                                   placeholder="Home / Office",
                                   font=theme.FONT_INPUT, pad_y=10,
                                   text=chosen.get("label", ""))
        self._a_label.grid(row=0, column=0, sticky="w",
                           padx=(0, theme.PAD_MD))
        self._a_street = EntryField(grid, width=32, label="Street address *",
                                    placeholder="House number and street",
                                    font=theme.FONT_INPUT, pad_y=10,
                                    text=chosen.get("address", ""))
        self._a_street.grid(row=0, column=1, sticky="w")
        self._a_barangay = EntryField(grid, width=20, label="Barangay *",
                                      font=theme.FONT_INPUT, pad_y=10,
                                      text=chosen.get("barangay", ""))
        self._a_barangay.grid(row=1, column=0, sticky="w",
                              pady=(theme.PAD_MD, 0))
        self._a_city = EntryField(grid, width=20, label="City *",
                                  font=theme.FONT_INPUT, pad_y=10,
                                  text=chosen.get("city", ""))
        self._a_city.grid(row=1, column=1, sticky="w",
                          pady=(theme.PAD_MD, 0))
        self._a_landmark = EntryField(grid, width=42, label="Landmark",
                                      placeholder="e.g. beside the bakery",
                                      font=theme.FONT_INPUT, pad_y=10,
                                      text=chosen.get("landmark", ""))
        self._a_landmark.grid(row=2, column=0, columnspan=2, sticky="w",
                              pady=(theme.PAD_MD, 0))
        # Typing in the form means "+ Type a new address" - auto-switch.
        for field in (self._a_label, self._a_street, self._a_barangay,
                      self._a_city, self._a_landmark):
            field.entry.bind("<FocusIn>",
                             lambda e=None: self._switch_to_new_address())
        if getattr(self, "_address_choice", None) and \
                self._address_choice.get().isdigit():
            self._saved_address_check = None
        else:
            self._saved_address_check = CheckField(
                form.body, "Save this address for next time",
                bg=theme.BG_SURFACE)
            self._saved_address_check.pack(anchor="w", pady=(theme.PAD_SM, 0))

    def _select_address(self, aid):
        """A saved-address card was clicked - fill the address form."""
        self._address_choice.set(str(aid))
        self._paint_address_cards()
        self._pick_address()

    def _paint_address_cards(self):
        """Highlights only the picked address card."""
        choice = self._address_choice.get()
        for key, card in self._address_cards.items():
            card.set_selected(key == str(choice))

    def _switch_to_new_address(self):
        """Switches to the '+ Type a new address' option when the user types."""
        if getattr(self, "_address_choice", None) and \
                self._address_choice.get().isdigit():
            self._address_choice.set("new")
            self._paint_address_cards()

    def _pick_address(self):
        """A saved address card got picked - fill the address form."""
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
        """The '+ Type a new address' card was picked - keep what is typed."""
        self._address_choice.set("new")
        self._paint_address_cards()
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
        """One tidy summary card with the bold total in green."""
        self._clear_step()
        card = Card(self._step_frame, pad=theme.PAD_LG)
        card.pack(fill="x")
        body = card.body
        tk.Label(body, text="Booking summary", font=theme.FONT_CARD_TITLE,
                 fg=theme.TEXT, bg=theme.BG_SURFACE).pack(
                     anchor="w", pady=(0, theme.PAD_SM))

        v = self._draft["vehicle"]
        a = self._draft["address"]
        lines = [
            ("Vehicle", database.vehicle_desc(v["vehicle_type"], v["make"],
                                              v["model"], v["color"],
                                              v["plate"])),
            ("Package", config.tier_name(self._draft["tier_id"])),
            ("When", config.friendly_date(self._draft["booking_date"])
             + "  -  " + self._draft["time_slot"]),
            ("Where", database.address_lines(
                a["address"], a["barangay"], a["city"], a["landmark"])),
        ]
        # label/value rows line up nicely in two columns
        for key, value in lines:
            row = tk.Frame(body, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=key, font=theme.FONT_SMALL_BOLD,
                     fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE, width=9,
                     anchor="w").pack(side="left")
            tk.Label(row, text=value, font=theme.FONT_BODY, fg=theme.TEXT,
                     bg=theme.BG_SURFACE, wraplength=520, justify="left",
                     anchor="w").pack(side="left", fill="x", expand=True)

        tk.Frame(body, bg=theme.BORDER, height=1).pack(
            fill="x", pady=(theme.PAD_MD, theme.PAD_SM))

        base = config.price_for(self._draft["tier_id"],
                                self._draft["vehicle_type"])
        addon_total = 0
        for addon_id in self._draft["addons"]:
            addon_total = addon_total + config.ADD_ONS[addon_id]["price"]
        rows = [("Base", "\u20b1" + str(base))]
        for addon_id in self._draft["addons"]:
            info = config.ADD_ONS[addon_id]
            rows.append((info["name"], "+" + "\u20b1" + str(info["price"])))
        rows.append(("Total", "\u20b1" + str(base + addon_total)))
        for i, (name, amount) in enumerate(rows):
            last = i == len(rows) - 1
            row = tk.Frame(body, bg=theme.BG_SURFACE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=name,
                     font=theme.FONT_BODY_BOLD if last else theme.FONT_SMALL,
                     fg=theme.PRIMARY if last else theme.TEXT_MUTED,
                     bg=theme.BG_SURFACE).pack(side="left")
            tk.Label(row, text=amount,
                     font=theme.FONT_BODY_BOLD if last else theme.FONT_SMALL,
                     fg=theme.PRIMARY if last else theme.TEXT,
                     bg=theme.BG_SURFACE).pack(side="right")
        tk.Label(body, text=config.REVIEW_NOTE, font=theme.FONT_TINY,
                 fg=theme.TEXT_MUTED, bg=theme.BG_SURFACE,
                 wraplength=560, justify="left").pack(
                     anchor="w", pady=(theme.PAD_SM, 0))

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

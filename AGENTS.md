# AutoGlide

Python 3 + Tkinter + SQLite auto-detailing appointment app. Everything is in `main.py`,
`screens/`, `components.py`, `theme.py`, `config.py`, `validators.py`, `database.py`,
`utils/images.py` (Pillow image helper) and `pictures/` (photos: `hero.jpg`,
`banner.jpg`, `login_side.jpg`, `pkg_*.jpg`, `step_*.jpg`). Pillow is the only
third-party install; everything else is standard library.

## Run

```powershell
py -3 main.py          # launch the app
py -3 test_headless.py # headless test suite (20 tests) - run after any change
py -3 -m py_compile <file>  # always compile-check edited files before running
```

Shell is Windows PowerShell 5.1: no grep/sed/heredocs; use Select-String, and
`cmd1; if ($?) { cmd2 }` instead of `&&`.

## Dev conventions

- Comments go above the touched code, keep them short and casual (student level).
- MessageBox only for destructive confirms (delete/cancel); everything else uses Toast.
- Peso sign is written `\u20b1` in code.
- DB safety: never DROP tables/rows; `ALTER TABLE ADD COLUMN` only. Seed users
  `admin`/`admin123` (admin) and `marcus`/`password` (client). The user may have
  real/manual test bookings in `autoglide.db` — leave them alone; the test suite
  cleans only the rows it creates itself.

## Architecture (do not regress)

- `main.py` — App/`AutoGlideApp`; `show_screen("landing"/"login"/"register"/"shell")`,
  role-based `_build_shell` (ClientShell vs AdminShell), `request_booking(tier_id)`
  hands the picked package to the wizard, `login_success` may resume a pending booking
  (draft key `"new_booking"`).
- Guest flow: landing page (marketing, packages) -> login/register -> wizard.
- `screens/marketing.py` — shared `MarketingBody(parent, app, target_width)` builds the
  hero + package cards + how-it-works + banner + footer. `landing_screen.py` (guest)
  and `client_home.py` (logged in) BOTH embed it so they look the same. Don't fork
  the design: edit MarketingBody, not the callers.
- Client shell (`app_shell.py ClientShell`): TOP navigation bar, tabs
  home / new_booking / my_bookings / vehicles / addresses / profile / help.
- Admin shell (`AdminShell`): SIDEBAR nav (dashboard = `admin_screen.py`,
  bookings = `admin_bookings.py`, schedule = `admin_schedule.py`, clients =
  `admin_clients.py`).
- NO map/zones/service fees/detailers — those were removed on purpose.
- Centered layout: `ClientShell.switch_view` / `AdminShell.switch_view` wrap every view
  (home gets `target_width` computed from the window) in `components.CenteredColumn`.
  Views must NOT create their own CenteredColumn on top of that (double centering).
- Window sizes: main.py starts the window zoomed (maximized). Layout rules as of
  this session: Home + client Vehicles/Addresses/Profile/Help pages are wrapped in a
  shell-level ScrollFrame (page scrolls); wizard and My Bookings use
  `CenteredColumn(fill_height=True)` and fill the window with stretchy cards
  (`Card(..., stretch=True)`) that scroll INSIDE (wizard steps in a ScrollFrame;
  bookings tables in DataTable; detail panels in their own ScrollFrame). Admin
  non-dashboard pages are `CenteredColumn(fill_height=True)` with target
  `max(1150, content width - padding)` — no page-level scrollbar anywhere.
  DataTable row cells use pady=10; SegmentedControl supports wrap=N (grid, N per
  row) — used with wrap=2 in the admin booking status panel; admin bookings
  auto-selects the newest booking on reload.
- Wizard (`screens/booking_wizard.py`): 5 steps vehicle -> package -> schedule ->
  location -> review. Add-ons are selected as a set of ids (`draft["addons"]`),
  joined with `","` before `database.create_booking`. Booking goes in as Pending.
  Full slots (3 per slot) are greyed out. Schedule step groups slots into
  Morning/Afternoon rows and shows a live "Your booking: ..." summary strip that
  fills in as date/time are picked (`_update_pick_line`).
- `admin_schedule.py` day cells are canvases with explicit `height = CELL_H` (72); a
  canvas without an explicit height defaults to ~265px tall and pushes the calendar
  off-screen.
- `database.py` passwords are salted SHA-256 hashes (`hash_password` / `verify_password`);
  `login_user` migrates a plaintext row to a hash on successful login. Never store or
  compare plaintext.

## Component APIs (`components.py`)

- `EntryField(master, label, placeholder="", show=None, width=30, text=None, bg=None)`
  with `.get()/.set()/.set_error()/.clear_error()`; the entry is `.entry`.
- `DateField(master, label="Date", value="", on_change=None, bg=None)` — `.set()` fires on_change.
- `Button` is canvas-based: use `.set_variant(variant)` / `.set_text()`, NOT `configure(fg=)`.
- `Card` — use `.card_bg` / `.set_card_bg(bg)`; content goes in `.body`.
  `Card(..., stretch=True)` makes the body fill the card height (tall table /
  calendar cards) instead of hugging its content — only use it on cards that
  are packed fill=both+expand.
- `Toast.show(root, msg, kind)` or `Toast(master, msg, variant="ok"/"error"/"info")`.
- `ScrollFrame` binds the mouse wheel globally on `<Enter>`/`<Leave>` so scrolling
  works anywhere over the page, not just the scrollbar.
- `CenteredColumn(master, width=...)` caps content width and auto-centers it via
  symmetric `padx`. Its `_recenter` uses a 40px hysteresis threshold + `after_idle` —
  do NOT turn it into a naive `pack_configure(padx)` on every `<Configure>`: that
  fights the scrollbar and hangs the app in an infinite relayout loop (bug 6).
  NEVER put a CenteredColumn inside a ScrollFrame page when the content's natural
  width exceeds the column width (stat-card canvases etc.): the column's padx
  grows the scroll page's requested width, which grows the measured "available"
  width, which grows padx again — unbounded loop, Tk eventually access-violates.
  Full-width dashboard-style pages must build directly into the shell content.
- `Chip`, `SegmentedControl`, `CheckField`, `Accordion`, `DataTable` also available.

## Bugs fixed in past sessions (don't reintroduce)

1. Stale price label in the wizard package step crashed the app
   ("can't go past package page"): `render_step` resets `_price_labels` and
   `_update_prices` recreates the label when `winfo_exists()` is false.
2. Duplicate Back/Continue buttons: `render_step` must destroy the old footer
   (`self._footer`) and `_clear_step` must destroy ALL children in the step frame.
3. Saved address/vehicle silently overriding typed values: radio sets have an
   explicit "+ Type a new address" option (default), and typing in any form field
   auto-switches the choice to "new" (`FocusIn` bindings).
4. Fonts sizes live in `theme.py` tokens (BODY 13, SMALL 12, TINY 11, GREETING 30,
   SECTION 24 / PRICE 22...), not per-widget.
5. Wheel scrolling only worked over the scrollbar — fixed via global capture in
   `ScrollFrame` (see above).
6. Centering via padx on every `<Configure>` hung the app in an infinite relayout
   loop (scrollbar appearing/disappearing around the threshold width) — the
   `_recenter` hysteresis in `CenteredColumn` is the fix; see Component APIs.
7. `admin_schedule.py` calendar cut off after Oct 18: day-cell canvases with no
   explicit `height` collapse to the Canvas default (~265px). Fixed via `CELL_H=72`.
8. Wizard saved-vehicle picker no longer clobbers typed values: radio defaults to
   "+ Type a new vehicle", `_switch_to_new_vehicle` doesn't overwrite the saved
   check state, typed vehicles get `data["id"] = None`.
9. Passwords were plaintext — now salted SHA-256 (see `database.py` note above).
10. Admin dashboard spacing: the CenteredColumn wrap made the scroll page's height
   follow the canvas-default (~265px) request, so the chart/pending cards were a
   thin clipped strip. Dashboard now builds straight into the shell content at
   full shell width (AdminShell only column-wraps the other three pages); the
   chart canvas repaints on `<Configure>` (after_idle) so bars start at the real
   width, not the 420px fallback.
11. Wide tables squeezed: DataTable now uses ScrollFrame(hscroll=True); the header
   lives INSIDE the scroll area (so it lines up when scrolled sideways), rows go
   in `self._rows_box`, and Shift+wheel scrolls horizontally.
12. Saved address radii letter-spaced ("2 - 3 - s - a - d..."): someone ran
   `" - ".join()` on the STRING `database.address_lines()` returns — that joins
   per-character. `address_lines` already returns one formatted line; append it
   as-is (same fix in the review step's "Where"). Also: `DateField.get()`
   returns None when the box is empty — guard with `or ""` before parsing.

## Next session (known issues to fix)

None currently.

## Lessons learned

- Reusing a draft across views meant a crashed test left the wizard mid-step and the
  next test saw the wrong screen; `_load_fresh_draft` resets `step` to 0 so every
  New Booking visit starts clean.
- When tests fail weirdly after an earlier failure, suspect shared app state —
  force a fresh view rebuild (switch home, then back) before asserting.
- `winfo_parent()` returns a string path, not a widget; when probing geometry in a
  throwaway script, walk `winfo_children()` recursively and assert on `winfo_x()`
  / `winfo_width()` after `update_idletasks()` + `update()`, not on pack options
  of the wrong nesting level (easy to misread "not centered" when you actually
  measured a parent).
- A Tk access violation (exit -1073741819, no traceback) with no Python error is
  often an unbounded geometry loop, not a code bug: instrument `_recenter`
  (log pack_info padx changes) and bisect by disabling the suspect binding/column
  until the hang goes away. Hysteresis only helps when the per-pump delta is
  smaller than the threshold (40px here; padx grew +432/pump).
- Packing order matters: pack a horizontal scrollbar (side="bottom") BEFORE the
  canvas that fills/expands, or the canvas claims the cavity and the bar never
  gets space.
- Wrapping a view in a fill="x"-only container changes its height semantics: the
  view renders at its requested height (a ScrollFrame canvas there ~ 265px
  default), not the window height. If a page must own the window, build it
  straight into the shell content.

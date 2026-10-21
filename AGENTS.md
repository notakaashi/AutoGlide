# AutoGlide

Python 3 + Tkinter + SQLite auto-detailing appointment app. Everything is in `main.py`,
`screens/`, `components.py`, `theme.py`, `config.py`, `validators.py`, `database.py`.
Standard library only — no installs needed.

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
- Client shell (`app_shell.py ClientShell`): TOP navigation bar, tabs
  home / new_booking / my_bookings / vehicles / addresses / profile / help.
- Admin shell (`AdminShell`): SIDEBAR nav (slots, bookings, clients).
- NO map/zones/service fees/detailers — those were removed on purpose.
- Wizard (`screens/booking_wizard.py`): 5 steps vehicle -> package -> schedule ->
  location -> review. Add-ons are selected as a set of ids (`draft["addons"]`),
  joined with `","` before `database.create_booking`. Booking goes in as Pending.
  Full slots (3 per slot) are greyed out.

## Component APIs (`components.py`)

- `EntryField(master, label, placeholder="", show=None, width=30, text=None, bg=None)`
  with `.get()/.set()/.set_error()/.clear_error()`; the entry is `.entry`.
- `DateField(master, label="Date", value="", on_change=None, bg=None)` — `.set()` fires on_change.
- `Button` is canvas-based: use `.set_variant(variant)` / `.set_text()`, NOT `configure(fg=)`.
- `Card` — use `.card_bg` / `.set_card_bg(bg)`; content goes in `.body`.
- `Toast.show(root, msg, kind)` or `Toast(master, msg, variant="ok"/"error"/"info")`.
- `ScrollFrame` binds the mouse wheel globally on `<Enter>`/`<Leave>` so scrolling
  works anywhere over the page, not just the scrollbar.
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
4. Fonts were too small — sizes live in `theme.py` tokens (BODY 12, SMALL 11,
   TINY 10...), not per-widget.
5. Wheel scrolling only worked over the scrollbar — fixed via global capture in
   `ScrollFrame` (see above).

## Lessons learned

- Reusing a draft across views meant a crashed test left the wizard mid-step and the
  next test saw the wrong screen; `_load_fresh_draft` resets `step` to 0 so every
  New Booking visit starts clean.
- When tests fail weirdly after an earlier failure, suspect shared app state —
  force a fresh view rebuild (switch home, then back) before asserting.

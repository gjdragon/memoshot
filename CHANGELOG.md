# Changelog

All notable changes to MemoShot are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.6.3] — UI polish

## [1.6.2] — Multi-monitor coordinate fix, logging tab, UI polish

### Fixed

- **Multi-monitor full-screen capture cuts off taskbar on non-primary screens.**
  Root cause: three separate coordinate-space mismatches in `ui/overlay.py` when
  monitors have different y-origins (e.g. a centre screen positioned 60 px higher
  than the left and right screens in Windows display settings).

  1. **`_get_valid_last_region`** — the stored rect is in local overlay coordinates,
     but the intersection check `rect.intersects(screen.geometry())` was comparing
     it against global screen coordinates. Fixed by translating the rect to global
     coords before the check: `global_rect = rect.translated(ox, oy)`.

  2. **Initial rect placement** — when no saved region exists, the rect was centred
     using `sg.left()` / `sg.top()` (global screen coords) directly as local overlay
     coords. Fixed by converting: `local_left = sg.left() - ox`,
     `local_top = sg.top() - oy`.

  3. **`_clamp_rect_to_desktop`** — used `max(ox, ...)` / `max(oy, ...)` (the raw
     overlay origin in global coords) as the minimum bound in local coords. For a
     setup where `oy = -60`, this allowed dragging the selection 60 px above all
     actual screen content into a black letterbox band, causing the taskbar to be
     cropped from the bottom of the capture. Fixed by computing the minimum local
     bounds from the actual screen geometries: `local_min_y = min(s.top() - oy
     for s in screens)`, which equals the topmost real pixel across all screens.

- **"Logging is disabled" shown even when the checkbox is ticked.**
  `settings["log_folder"]` is stored as `""` when the user has not customised it.
  `dict.get("log_folder", default)` only returns the default when the key is
  *absent*, not when it is an empty string. `os.makedirs("")` then raised
  `FileNotFoundError`, the except branch ran without setting `_current_log_path`,
  and `_refresh_current_log_label()` read `None` and showed "disabled". Fixed by
  resolving the folder before the try block:
  `log_folder = raw.strip() if raw else _default_log_folder()`.
  The except branch now also explicitly resets `_current_log_path = None` so the
  label is accurate when a genuine failure occurs.

- **Tab bar shows scroll arrows with four tabs.**
  `setExpanding(True)` on Windows with an active stylesheet compresses tabs to
  their text width instead of stretching them, causing the "Logginc" clipping.
  Removed `setExpanding`. Fixed with explicit `min-width: 88px; max-width: 88px`
  in the tab stylesheet — four equal tabs at 88 px + three 1 px gaps = 355 px,
  fitting within the 368 px available body width.

- **Browse button text clipped to "3rowse…".**
  `setFixedWidth(72)` was too narrow on Windows DPI. Widened both Browse buttons
  (Output tab and Logging tab) to `80px`.

### Added

- **Logging tab** (fourth tab in Settings). Contains:
  - *Enable logging* checkbox — master on/off switch, takes effect immediately.
  - *Log level* dropdown — INFO (key events only) or DEBUG (every interaction).
  - *Log folder* field with Browse button — defaults to `src/Logs/`; empty string
    is stored when the user has not changed it, keeping settings clean.
  - *File naming hint* — `log_memoshot_YYYYMMDD_HHMMSS.txt · 1 MB max · 5
    rotating backups`.
  - *Current session* label — shows the active log file path, or "disabled" if
    logging is off.
  - *📂 Open log folder* button — opens the log folder in the system file manager.
  - Changes apply instantly without restarting the app.

- **`utils/logger.py` — full rewrite.** Singleton root logger `memoshot.*` shared
  across all modules. `apply_log_settings(settings)` tears down existing handlers
  and rebuilds: `RotatingFileHandler` (1 MB, 5 backups) + `StreamHandler`.
  `current_log_path()` returns the active log file path. `_default_log_folder()`
  resolves to `src/Logs/` relative to the script directory with a fallback to
  `~/.memoshot/Logs/`.

- **`app.py`** — calls `apply_log_settings(settings)` before the window is created
  so hotkey registration and early startup messages are captured in the log file.

- **Verbose DEBUG logging** added across all modules:
  - `capture/screenshot.py` — sequence number resolution, filename choice, rect
    and cropped pixmap size, clipboard skip reason.
  - `core/hotkey.py` — hotkey triggered (each press), `add_hotkey` registered,
    `unhook_all` completed, `stop()` called.
  - `ui/overlay.py` — overlay geometry and screen count, active screen, initial
    rect placement, last-region restore, drag start/end with position, resize
    start/end with edge and final rect, snap-to-screen result, shortcut panel
    toggle, key actions (Enter/Esc/S/?), capture confirmed with final rect.

- **📂 Open folder button** on the Quick Capture toolbar. Opens the configured
  screenshots save folder in the system file manager. Cross-platform: `os.startfile`
  on Windows, `open` on macOS, `xdg-open` on Linux. Creates the folder if it does
  not exist yet.

### Changed

- **Quick Capture toolbar** — four equal-width buttons (Settings, Open folder,
  Tray, Exit) each with `stretch=1` in the `QHBoxLayout`, filling the full row
  evenly. The `addStretch()` separator is removed.
- **Tab stylesheet** — `documentMode(True)` removed (caused gap line on Windows).
  New border model: `QTabWidget::pane` with `top: -1px`; unselected tabs have
  `margin-top: 2px`; selected tab has `border-bottom: 1px solid {_SURFACE}` to
  erase the pane top border and merge visually with the content area.
- **`_divider()` helper** — replaced `QFrame.HLine` (renders as a raised/sunken
  line on Windows) with a plain `QWidget` of `setFixedHeight(1)` and a flat
  background colour, which renders as a clean single-pixel rule on all platforms.
- **Profile list placeholder text** on Quick panel updated to
  "go to Settings to create one".
- **`os`, `subprocess`, `sys`** imported at module level in `main_window.py`
  (previously imported inline inside methods).
- **`core/settings.py`** — three new default keys: `logging_enabled` (`True`),
  `log_folder` (`""`), `log_level` (`"INFO"`). Fixed `list[str]` return type
  annotation to `List[str]` from `typing` for Python 3.9 compatibility.
- Version string updated to `1.6.2` in `version.py`.

---

## [1.5.0] — Test capture & profile workflow

### Added

- **▶ Test capture button** in the Settings footer. Clicking it hides the window,
  opens the capture overlay with the current settings, and — once the overlay
  closes — automatically re-opens the Settings panel. The inline status label in
  the footer updates to show the captured region dimensions and position, so users
  can verify the result and save it as a profile without leaving Settings.
- **`_return_to_settings` flag** (`bool`, default `False`). Set in
  `_test_capture_from_settings()`; cleared in `_on_capture_complete()`.
- **`_refresh_settings_status_lbl()`** — updates the `"Last: W×H at (x, y)"`
  status label in the Settings footer.
- **`_reset_autosave_label()`** — named helper that restores the autosave label
  text and hides it. Replaces a fragile multi-statement tuple lambda.

### Removed

- **"+ New profile" button** from the Quick Capture panel. Profile creation now
  belongs entirely in the Settings footer.
- **`_new_profile_from_quick()`** method.

### Changed

- Settings footer redesigned from a single row into two rows: row 1 = Test capture
  button + inline status; row 2 = profile name field + Save button.
- Quick panel profile list placeholder updated to "go to Settings to create one".
- Version bumped to `1.5.0`.

---

## [1.4.0] — Profile UX redesign

### Added

- **Profile `QListWidget` on the Quick Capture panel** — replaces the `QComboBox`
  that reset to a placeholder after loading. Clicking a row loads the profile and
  keeps it highlighted in blue.
- **Profile `QListWidget` on Settings → Profiles tab** — selecting a row highlights
  it without loading. Load and Delete buttons activate only when a row is selected.
- **"Save as profile" footer** — always visible below the tab widget on all three
  tabs. Type a name and press Save or Enter.
- **`self._active_profile`** — tracks the loaded profile name and restores the
  highlight after any list rebuild.
- **`_rebuild_all_profile_lists()`** and **`_load_profile_by_name(name)`** —
  shared helpers used by both list click handlers.

### Removed

- `QComboBox` profile dropdowns on both panels.
- `_save_profile()`, `_load_profile()`, `_delete_profile()`,
  `_refresh_profile_combo()`.

### Changed

- Version bumped to `1.4.0`.

---

## [1.3.0] — UI polish, colour scheme, hotkey capture

### Fixed

- **Tab overlap** and **Python 3.9 compatibility** (`X | None` → `Optional[X]`).

### Added

- **`HotkeyCapture` widget** — click to record, press keys to commit, Escape to
  cancel. Supports F1–F15, navigation keys, printable ASCII, and modifier combos.

### Changed

- Colour scheme: purple → slate-blue (`#2563eb`). Dark slate header bar. Off-white
  window background.
- Header bar replaces bare title label. Settings panel adds "← Back" button.
- Version bumped to `1.3.0`.

---

## [1.2.0] — Two-panel GUI redesign

### Added

- Quick Capture panel (default) and Settings panel (tabbed: Capture / Output /
  Profiles). `QStackedWidget` switches between them.
- Stylesheet constants and `_section_label()` / `_divider()` helpers.

### Changed

- Window width fixed at 400 px; height auto-adjusts.
- Version bumped to `1.2.0`.

---

## [1.1.0] — Auto-save, toast improvements, keyboard shortcut overlay

### Added

- **Auto-save** — 600 ms debounce, `✔ Settings saved` indicator.
- **Keyboard shortcut overlay** — press `?` on the capture overlay.
- **"Show in Explorer" toast link**.

### Changed

- Toast redesigned (dark slate, coloured border, anchored to primary screen).
- `Esc` closes shortcut panel first, then cancels overlay.
- Settings file renamed to `.memoshot_settings.json`.
- Version bumped to `1.1.0`.

---

## [1.0.0] — Initial release

### Added

- Full-screen capture overlay spanning all connected monitors.
- Per-ratio last-region memory (9:16 and 16:9 independently).
- `S` snap to screen, `Enter` capture, `Esc` cancel.
- Global hotkey via background `QThread`.
- 9:16 / 16:9 aspect-ratio lock, custom dimensions.
- Sequential or timestamp file naming, optional clipboard copy.
- Named profiles (save / load / delete).
- System-tray integration, toast notification.
- Modular source layout, `version.py`, `~/.memoshot_settings.json`.

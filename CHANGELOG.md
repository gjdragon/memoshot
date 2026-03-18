# Changelog

All notable changes to MemoShot are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.8.0] — UX improvements & polish

## [1.7.0] — UX improvements & polish

### Added

- **Active-profile pill on Quick Capture panel.** A small blue indicator bar
  labelled "Using: \<name\>" now appears below the header whenever a profile is
  loaded. It hides itself when no profile is active, so the current context is
  always unambiguous at a glance.

- **Arrow-key nudging on the capture overlay.** Arrow keys move the selection
  rectangle 1 px per press. Holding `Shift` increases the step to 10 px. Allows
  precise positioning without a second drag attempt. The instruction bar and the
  `?` shortcut cheat-sheet both document the new keys.

- **Overwrite warning when saving a profile.** If the name in the "Save as
  profile" footer already exists, an amber inline warning appears —
  *"'\<name\>' already exists — press Save again to overwrite"* — and the save
  is blocked. Pressing Save a second time confirms the overwrite. Prevents silent
  data loss.

- **Live file-prefix example.** The Output tab shows a live preview line below
  the prefix field that updates as you type, e.g.
  `→  myshot_001.png,  myshot_002.png`. When the field is empty it shows the
  timestamp default: `→  20240315_143022.png`.

- **Camera silhouette tray icon.** The system-tray icon is now a painted camera
  shape (body, viewfinder bump, lens ring, centre highlight dot) drawn with
  `QPainter`. Recognisable at 16–32 px system-tray sizes. Replaces the
  featureless solid blue square.

### Changed

- **Consistent single-click profile loading.** Clicking a profile row in
  Settings → Profiles now loads it immediately, identical to the Quick Capture
  panel. The separate "Load" button has been removed.

- **Status card green flash.** After every successful capture or profile load,
  the status card briefly flashes green before returning to its normal style,
  giving clear visual confirmation that the action registered.

- **Exit requires no confirmation.** The "Are you sure?" dialog has been removed.
  Since settings auto-save on every change and the app reopens trivially, the
  dialog added friction with no benefit.

- **Status card cold-start hint.** When no capture has been made yet, the status
  sub-label now reads *"Press \<HOTKEY\> from any app to start your first
  capture"* instead of the unhelpful "No previous capture in this mode". The
  hotkey shown updates dynamically.

- **Settings panel minimum height.** `QTabWidget` now has
  `setMinimumHeight(280)`, preventing the window from jumping or shrinking when
  switching between tabs with different content heights.

- **Toolbar normalised.** All three primary toolbar buttons (⚙ Settings,
  📂 Open folder, ⬜ Tray) share a consistent icon-button style. Exit is demoted
  to a plain underlined text link that turns red on hover.

- **Dimension badge flips when near the top edge.** The "W × H px" badge on the
  capture overlay no longer clips off-screen when the selection is near `y = 0`.
  It renders inside the selection when there is insufficient space above.

- **File prefix placeholder simplified.** Changed from the ambiguous
  `"Empty = timestamp · myshot1.png, myshot2.png…"` to
  `"Leave empty to use timestamps"`. The live example line takes over the role of
  showing what the output will look like.

- Version bumped to `1.7.0`.

---

## [1.6.3] — UI polish

---

## [1.6.2] — Multi-monitor coordinate fix, logging tab, UI polish

### Fixed

- **Multi-monitor full-screen capture cuts off taskbar on non-primary screens.**
  Three coordinate-space mismatches corrected in `ui/overlay.py`:
  `_get_valid_last_region` now translates the stored rect to global coords before
  the screen-intersection check; initial rect placement converts global screen
  coords to local overlay coords; `_clamp_rect_to_desktop` bounds derived from
  actual screen geometries rather than the raw overlay origin.

- **"Logging is disabled" shown even when the checkbox is ticked.** Empty-string
  log folder resolved before `os.makedirs` call; except branch resets
  `_current_log_path = None` on genuine failure.

- **Tab bar scroll arrows with four tabs.** Removed `setExpanding(True)`;
  explicit `min-width: 88px; max-width: 88px` in tab stylesheet.

- **Browse button text clipped.** `setFixedWidth` widened from 72 to 80 px.

### Added

- **Logging tab** — enable/disable, log level (INFO / DEBUG), log folder with
  Browse, current session file path, 📂 Open log folder button.
- **`utils/logger.py`** full rewrite — singleton, `RotatingFileHandler` (1 MB,
  5 backups), `apply_log_settings()`, `current_log_path()`.
- **📂 Open folder button** on the Quick Capture toolbar.
- Verbose DEBUG logging across all modules.

### Changed

- Quick Capture toolbar — four equal-width buttons.
- `_divider()` helper uses plain `QWidget` instead of `QFrame.HLine`.
- Version bumped to `1.6.2`.

---

## [1.5.0] — Test capture & profile workflow

### Added

- **▶ Test capture button** in the Settings footer. Hides the window, opens the
  overlay, and re-opens Settings automatically on completion.
- `_return_to_settings` flag and `_refresh_settings_status_lbl()` helper.

### Removed

- "New profile" button from the Quick Capture panel.

### Changed

- Settings footer redesigned into two rows (test row + save-as-profile row).
- Version bumped to `1.5.0`.

---

## [1.4.0] — Profile UX redesign

### Added

- `QListWidget` profile list on the Quick Capture panel and Settings → Profiles.
- "Save as profile" footer always visible across all tabs.
- `self._active_profile` tracking with highlight restore after list rebuilds.
- `_rebuild_all_profile_lists()` and `_load_profile_by_name()` shared helpers.

### Removed

- `QComboBox` profile dropdowns on both panels.

### Changed

- Version bumped to `1.4.0`.

---

## [1.3.0] — UI polish, colour scheme, hotkey capture

### Fixed

- Tab overlap and Python 3.9 compatibility (`X | None` → `Optional[X]`).

### Added

- `HotkeyCapture` widget — click to record, Escape to cancel. Supports F1–F15,
  navigation keys, printable ASCII, and modifier combos.

### Changed

- Colour scheme: purple → slate-blue (`#2563eb`). Dark slate header bar.
- Header bar and "← Back" button added to Settings panel.
- Version bumped to `1.3.0`.

---

## [1.2.0] — Two-panel GUI redesign

### Added

- Quick Capture panel and Settings panel with `QStackedWidget`.
- Stylesheet constants and `_section_label()` / `_divider()` helpers.

### Changed

- Window width fixed at 400 px; height auto-adjusts.
- Version bumped to `1.2.0`.

---

## [1.1.0] — Auto-save, toast improvements, keyboard shortcut overlay

### Added

- Auto-save — 600 ms debounce, `✔ Settings saved` indicator.
- Keyboard shortcut overlay — press `?` on the capture overlay.
- "Show in Explorer" link in the toast notification.

### Changed

- Toast redesigned: dark slate, coloured border, anchored to primary screen.
- `Esc` closes the shortcut panel first, then cancels the overlay.
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

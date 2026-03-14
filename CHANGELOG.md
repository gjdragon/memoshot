# Changelog

All notable changes to MemoShot are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.5.0] — Test capture & profile workflow

### Added

- **▶ Test capture button** in the Settings footer. Clicking it hides the window, opens the capture overlay with the current settings, and — once the overlay closes — automatically re-opens the Settings panel. The inline status label in the footer updates immediately to show the captured region dimensions and position, so users can verify the result and decide whether to save it as a profile without leaving Settings.
- **`_return_to_settings` flag** (`bool`, default `False`). Set to `True` in `_test_capture_from_settings()`; cleared in `_on_capture_complete()`, which checks it to decide whether to return to Settings or stay on Quick Capture.
- **`_refresh_settings_status_lbl()`** — updates the `"Last: W×H at (x, y)"` status label in the Settings footer. Called on footer build and after each test capture.
- **`_reset_autosave_label()`** — named helper that restores the autosave label text and hides it. Replaces a fragile multi-statement tuple lambda.

### Removed

- **"+ New profile" button** from the Quick Capture panel. Profile creation now belongs entirely in the Settings footer. The Quick panel is for loading and capturing only.
- **`_new_profile_from_quick()`** method.

### Changed

- Settings footer redesigned from a single row into two rows: row 1 = Test capture button + inline status label; row 2 = profile name input + Save button.
- Quick panel profile list placeholder updated to "go to Settings to create one".
- Profiles tab hint text updated to describe the test-then-save workflow.
- Version bumped to `1.5.0`.

---

## [1.4.0] — Profile UX redesign

### Added

- **Profile `QListWidget` on the Quick Capture panel** — replaces the `QComboBox` that reset to a placeholder after loading. The list shows all saved profiles; clicking a row loads it immediately and keeps it highlighted in blue. When no profiles exist a muted placeholder row explains how to create one.
- **Profile `QListWidget` on the Settings → Profiles tab** — mirrors the Quick panel list. Clicking a row selects it (highlights, does not load). Load and Delete buttons below activate only when a row is selected. A status label confirms the selected name.
- **"Save as profile" footer** — permanently visible green banner at the bottom of the Settings panel, below the tab widget. Visible on all three tabs. Type a name and press Save or Enter to snapshot all current settings. A `✔ Profile "name" saved` confirmation briefly appears.
- **`self._active_profile`** (`Optional[str]`) — tracks the currently loaded profile name. Every list rebuild uses it to restore the highlight.
- **`_rebuild_all_profile_lists()`** — single call keeps both lists in sync.
- **`_load_profile_by_name(name)`** — shared implementation used by both list click handlers and the Settings Load button.

### Removed

- `QComboBox` profile dropdowns on both panels.
- `_save_profile()`, `_load_profile()`, `_delete_profile()`, `_refresh_profile_combo()` — replaced by the new list-based methods.
- `quick_profile_combo` attribute.

### Changed

- Version bumped to `1.4.0`.

---

## [1.3.0] — UI polish, colour scheme, hotkey capture

### Fixed

- **Tab overlap** — `QTabWidget` now uses `documentMode(True)` and `min-width: 90px` per tab. Tabs no longer clip or overlap at 400 px window width. Border model corrected so the selected tab connects cleanly to the pane.
- **Python 3.9 compatibility** — all `X | None` type union hints replaced with `Optional[X]` from `typing`. The app now runs on Python 3.9+.

### Added

- **`HotkeyCapture` widget** (`QLineEdit` subclass). Click to enter recording mode (blue border, "Press keys…"). Press any key combination (`F12`, `Ctrl+Shift+S`, etc.) to commit it. Press `Escape` to cancel and revert. Focus-out also cancels. Supports all function keys (F1–F15), navigation keys, printable ASCII, Space, Tab, Enter, and modifier combinations. `value()` method returns the committed string even during recording.
- **`_KEY_NAMES` mapping** — `Qt.Key_*` constants → `keyboard`-library-compatible strings.

### Changed

- **Colour scheme** — replaced purple (`#9333ea`) with slate-blue (`#2563eb / #1d4ed8`). Header bar uses dark slate `#1e293b`. Window background is off-white `#f8fafc`. Section labels are uppercase muted grey with letter-spacing.
- **Header bar** — bare title `QLabel` removed. Both panels share a 40 px dark header bar: blue dot, "MemoShot", version string. The Settings panel variant adds "← Back" on the right.
- **Profile panel** — `QComboBox` preset list replaced with a dynamic profile `QComboBox` populated from `cfg.list_profiles()`. Selecting an item loads the profile and resets the combo to the placeholder.
- **`_snapshot_ui_to_settings`** — now calls `self.hotkey_input.value()` instead of `.text()` to correctly read the committed hotkey value.
- Tray icon colour updated to match `_BLUE` (`QColor(37, 99, 235)`).
- Version bumped to `1.3.0`.

---

## [1.2.0] — Two-panel GUI redesign

### Added

- **Quick Capture panel** (default view) — full-width Capture button with hotkey label, one-line status card (last capture dimensions + position), platform preset dropdown, icon toolbar (Settings / Tray / Exit).
- **Settings panel** — opens on `⚙ Settings`, returns on `← Back`. Three tabs: Capture, Output, Profiles.
- **`QStackedWidget`** — switches between Quick and Settings panels without opening new windows.
- **Platform preset dropdown** on the Quick panel — one click sets width and height for TikTok/IG Story, YouTube Shorts, IG Feed, LinkedIn Banner, Twitter/X Header, YouTube Thumbnail. Clears ratio lock so pixels are exact.
- **Stylesheet constants** at the top of `main_window.py` (`_PURPLE`, `_SURFACE`, `_BORDER`, etc.) — all colours in one place.
- **`_section_label()` / `_divider()` static helpers** — consistent typography and spacing across tabs.
- **`_refresh_status_card()`** — updates the Quick panel status card after captures and profile loads.
- **`_sync_preset_combo()`** — keeps the preset dropdown in sync when overlay resize changes dimensions.

### Changed

- Window width fixed at 400 px; height auto-adjusts with `adjustSize()`.
- Profiles group moved to its own tab — no longer permanently visible.
- Last-region label and ratio label consolidated into the status card.
- Version bumped to `1.2.0`.

---

## [1.1.0] — Auto-save, toast improvements, keyboard shortcut overlay

### Added

- **Auto-save settings** — settings persist immediately on every change. The "Save Settings" button is removed. A 600 ms debounce timer batches rapid spin-box changes into a single disk write. A small `✔ Settings saved` indicator appears for 2.5 s after each save.
- **Keyboard shortcut overlay** — press `?` (or `/`) on the capture overlay to show a centred semi-transparent cheat-sheet panel. Press `?` again or `Esc` to dismiss.
- **"Show in Explorer" toast link** — the post-capture toast includes a clickable link that opens the save folder and highlights the file (`explorer /select,` on Windows, `open -R` on macOS, `xdg-open` on Linux).

### Changed

- **Toast redesign** — dark slate background (`#1e1e2e`) with a coloured border (green success, red error). Uses `Qt.Tool` + `Qt.WA_ShowWithoutActivating` so it never steals focus. Anchored to the bottom of the primary screen. Duration extended to 3.5 s.
- **`Esc` on overlay** — first press closes the shortcut panel if open; second press cancels the overlay.
- **Overlay instruction bar** — hint text updated to include `? = Shortcuts`.
- **Settings file** — renamed from `.portrait_screenshot_settings.json` to `.memoshot_settings.json`.
- Version bumped to `1.1.0`.

---

## [1.0.0] — Initial release

### Added

- Full-screen capture overlay spanning all connected monitors. Purple selection rectangle with draggable edges, corners, and interior.
- Per-ratio last-region memory — overlay restores the previous capture position independently for 9:16 and 16:9 modes.
- `S` key snaps the selection to fill the current screen.
- `Enter` captures, crops, and saves the region as a PNG.
- `Esc` cancels the overlay.
- Global hotkey (default `Ctrl+Shift+P`) registered in a background `QThread` so it never blocks the Qt event loop.
- 9:16 (portrait) and 16:9 (landscape) aspect-ratio lock with radio button switching.
- Custom width/height with ratio unlock.
- Sequential file naming (`<prefix>1.png`, `<prefix>2.png`, …) or timestamp-based naming when no prefix is set.
- Optional clipboard copy after each capture.
- Named profiles — save, load, and delete complete setting snapshots.
- System-tray integration: right-click for Capture / Show Window / Exit. Single-click tray icon restores the main window.
- Toast notification after each capture showing the saved filename.
- Modular source layout: `core/`, `capture/`, `ui/`, `utils/`.
- `version.py` as the single source of truth for the version string.
- Settings stored at `~/.memoshot_settings.json`.

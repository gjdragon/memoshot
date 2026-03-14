# Changelog

All notable changes to MemoShot are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.4.0] — Profile UX redesign

### Problem statement
Three issues reported with v1.3.0:
1. No obvious way to save a profile from the Capture or Output tabs.
2. The profile dropdown on the Quick panel reset to "— load profile —" after loading, giving no visual indication of what was active.
3. "Save as…" was hidden in the Profiles sub-tab which users had to navigate to first.

### Changed — Quick Capture panel
- **Replaced dropdown with a `QListWidget`** — profiles are now displayed as a persistent list. Clicking a row loads it immediately *and keeps it highlighted* in blue, so the active profile is always visible. Selecting a different profile highlights it instead.
- **Added "+ New profile" button** next to the Profiles section header. Clicking it prompts for a name and saves the current settings as a new profile without leaving the Quick panel.
- When there are no profiles, the list shows a muted placeholder row explaining how to create one.

### Changed — Settings panel
- **"Save as profile" footer** added as a permanently visible green banner at the bottom of the Settings panel, below the tab widget. It is visible regardless of which tab is active (Capture, Output, or Profiles). Type a name and press Save (or Enter) to snapshot current settings. A brief `✔ Profile "name" saved` confirmation appears in the autosave label.
- **Profiles tab redesigned** — shows the same `QListWidget` as the Quick panel. Clicking a row selects it (highlights it) without loading. "Load" and "Delete" buttons below activate only when a row is selected. A status label shows the selected profile name. No `QInputDialog` popups for loading or deleting.
- Removed "Save as…" and "Load" buttons from the old combo+buttons layout. Profile creation now goes through the footer; profile selection now goes through the list.

### Removed
- `_save_profile`, `_load_profile`, `_delete_profile`, `_refresh_profile_combo` — replaced by `_save_profile_from_footer`, `_load_selected_profile`, `_delete_selected_profile`, `_rebuild_settings_profile_list`.
- `profile_combo` QComboBox — replaced by `QListWidget` on both panels.
- `quick_profile_combo` QComboBox — removed; replaced by `profile_list` QListWidget.

### Internal
- Added `self._active_profile: Optional[str]` to track the currently loaded profile name and restore the highlight after any list rebuild.
- `_rebuild_all_profile_lists()` keeps both lists in sync (Quick panel + Settings panel Profiles tab) with a single call.
- `_load_profile_by_name(name)` is the single shared implementation used by both list click handlers.
- Version bumped to `1.4.0`.

---

## [1.3.0] — UI polish & hotkey capture

### Fixed

- **Tab overlap** — `QTabWidget` now uses `documentMode(True)` with explicit `min-width: 90px` on tabs and a proper border model (top border on tab + no-border on pane top edge). Tabs no longer clip or overlap at 400 px window width.
- **Hotkey field** — replaced the plain `QLineEdit` with `HotkeyCapture`, a custom widget. Click it to enter recording mode (blue border + "Press keys…" placeholder). Press any key combination (e.g. `F12`, `Ctrl+Shift+S`, `Alt+F4`) and the field fills automatically. Press `Escape` to cancel and revert. Focus-out also cancels. All function keys, navigation keys, and printable characters are supported.

### Changed

- **Colour scheme** — replaced purple (`#9333ea`) with professional slate-blue (`#2563eb / #1d4ed8`). Header bar uses dark slate (`#1e293b`). Window background is off-white (`#f8fafc`). Section labels are uppercase muted grey, not bold dark.
- **Preset dropdown → Profile dropdown** — the hard-coded platform preset list on the Quick panel is replaced with a dynamic profile dropdown populated from the user's saved profiles. Selecting a name immediately loads that profile (hotkey, folder, prefix, dimensions) and resets the combo to the placeholder. When no profiles exist, the combo shows "No profiles saved".
- **Window header** — bare title label removed. Both panels share a slim dark header bar showing a blue dot, "MemoShot", and the version string. The Settings panel header bar adds a "← Back" button on the right.
- **`_snapshot_ui_to_settings`** — now calls `self.hotkey_input.value()` (the `HotkeyCapture` method) instead of `.text()` so it correctly reads the committed value even if the field is mid-recording.
- **Profile save/delete** — now also calls `_rebuild_quick_profile_combo()` so the Quick panel dropdown stays in sync without needing to close and reopen settings.
- Tray icon colour updated from purple to blue (`QColor(37, 99, 235)`).
- Version bumped to `1.3.0`.

---

## [1.2.0] — GUI redesign

### Added

- **Two-panel window layout** — the app now opens to a compact *Quick Capture* panel instead of the full settings form. A `⚙ Settings` button slides to the settings panel; `← Back` returns.
- **Quick Capture panel** contains exactly three things: the Capture button (with hotkey label), a one-line status card showing last-capture dimensions and position, and a platform preset dropdown.
- **Platform preset dropdown** on the Quick Capture panel — one click sets width and height for TikTok / IG Story (1080×1920), YouTube Shorts (1080×1920), IG Feed square (1080×1080), LinkedIn Banner (1584×396), Twitter/X Header (1500×500), and YouTube Thumbnail (1280×720). Selecting a preset automatically clears the ratio lock so pixels are exact.
- **Tabbed Settings panel** with three tabs — *Capture* (hotkey, ratio mode, lock, dimensions), *Output* (save folder, file prefix, clipboard), *Profiles* (load / save / delete). Each tab is independently scrollable and expandable.
- **Stylesheet constants** (`_PURPLE`, `_SURFACE`, `_BORDER`, etc.) defined once at the top of `main_window.py` — easy to retheme without hunting through code.
- **`_section_label` / `_divider` helpers** — reusable within every tab, enforcing consistent typography and spacing.

### Changed

- Window width fixed at 380 px; height auto-adjusts to whichever panel is active (`adjustSize()`).
- `_on_capture_complete` now calls `_refresh_status_card` to update the Quick panel immediately after each capture.
- `_on_overlay_dimensions_changed` now also calls `_sync_preset_combo` and `_refresh_status_card` so the Quick panel stays in sync when the overlay resizes.
- `_flush_auto_save` updates the Capture button label live if the hotkey changed, without requiring the user to close and reopen.
- Profiles moved into their own dedicated tab — no longer occupies permanent space on every window open.
- Last-region and ratio labels consolidated into the one-line status card on the Quick panel.
- Version bumped to `1.2.0`.

---

## [1.1.0] — Pass 1 improvements

### Added

- **Keyboard shortcut overlay** — press `?` (or `/`) while the capture overlay is open to show a floating cheat-sheet panel listing every key and mouse action. Press `?` again, or `Esc`, to dismiss it.
- **"Show in Explorer" toast link** — the post-capture notification now includes a clickable link that opens the save folder in the system file manager and selects the new file (Explorer on Windows, Finder on macOS, `xdg-open` on Linux).

### Changed

- **Auto-save settings** — settings now persist immediately on every change. The "Save Settings" button has been removed. A debounce timer (600 ms) batches rapid changes (e.g. spin-box clicks) into a single write. A small green "✔ Settings saved" indicator appears briefly after each save.
- **Toast notification** — redesigned with a dark slate background and a coloured border (green for success, red for error) so it is visually distinct from both the overlay and the desktop. The toast is now anchored to the bottom of the primary screen and uses `Qt.WA_ShowWithoutActivating` so it never steals focus. Duration extended to 3.5 s to give time to click the Explorer link.
- **Overlay instruction bar** — updated hint text to include `? = Shortcuts`.
- **`Esc` behaviour** — when the shortcut panel is open, the first `Esc` closes the panel rather than exiting the overlay entirely.
- **Settings file** — renamed from `.portrait_screenshot_settings.json` to `.memoshot_settings.json` to match the new app name.
- **Version** — bumped to `1.1.0`.

---

## [1.0.0] — Initial release

### Added

- Full-screen interactive capture overlay spanning all connected monitors.
- Purple selection rectangle with draggable edges, corners, and interior.
- Per-ratio last-region memory: the overlay restores the previous capture position for 9:16 and 16:9 modes independently.
- `S` key snaps the selection to fill whichever screen the rectangle is centred on.
- `Enter` captures, crops, and saves the selected region as a PNG.
- `Esc` cancels and closes the overlay.
- Configurable global hotkey (default `Ctrl+Shift+P`) registered via a background `QThread` so it never blocks the Qt event loop.
- 9:16 (portrait) and 16:9 (landscape) aspect-ratio lock with radio-button switching.
- Custom width/height with ratio unlock.
- Sequential file naming (`<prefix>1.png`, `<prefix>2.png`, …) or timestamp-based naming when no prefix is set.
- Clipboard copy after each capture (optional, on by default).
- Named profiles — save, load, and delete complete setting snapshots.
- System-tray integration with right-click menu (Capture, Show Window, Exit).
- Single-click tray icon restores the main window when hidden.
- Toast notification after each capture showing the saved filename.
- Modular source layout: `core/`, `capture/`, `ui/`, `utils/`.
- `version.py` as the single source of truth for the version string.

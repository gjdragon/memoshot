# Changelog

All notable changes to MemoShot are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

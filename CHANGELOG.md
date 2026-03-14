# Changelog

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

# Changelog

All notable changes to MemoShot are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] — 20 Mar 2026

### Added

- **Output format selection** — choose PNG, JPEG, or WebP per profile. JPEG includes a quality slider (1–100). File extensions update accordingly (`.png`, `.jpg`, `.webp`).
- **Rename profile in-place** — double-click any profile name in the list to rename it without changing its settings or position.
- **Drag-and-drop profile reordering** — drag rows in the Profiles list to set a custom order. Order persists across sessions via a new `profile_order` field in settings.
- **Export profile** — export any selected profile to a `.json` file via the new Export button.
- **Import profiles** — import one or more profiles from a previously exported `.json` file. Existing names are skipped with a clear summary of what was imported vs skipped.
- **Capture confirmation per profile** — each profile can require Enter to confirm a capture, or fire instantly. Defaults to on (confirmation required). Test Capture always requires confirmation regardless of this setting.
- **Default profile auto-load** — if a profile named `Default` exists, it is loaded automatically on startup.
- **Global hotkey** — the hotkey is now a global setting shared across all profiles. Loading a profile never changes your hotkey.
- **Edit profile** — select a profile and click Edit to load its settings into all tabs with the name pre-filled in the footer, ready to modify and save back.
- **Profile detail card** — selecting a profile in the Profiles tab shows an inline summary of its key settings (mode, dimensions, format, save folder, prefix, clipboard, confirm).
- **`?` tooltip help system** — all inline hint paragraphs replaced with small `?` badges next to each section header. Hovering shows the guide text. Frees significant vertical space across all tabs.
- **Profile list fills available space** — the profile list in the Profiles tab now expands to use all available vertical space instead of leaving a blank gap.

### Changed

- Profiles are now stored with a user-defined order (`profile_order`) rather than sorted alphabetically.
- `screenshot.py` refactored to support multiple output formats and extensions.
- Section headers across all tabs converted from plain labels to `_section_row()` helpers that accept a tooltip.

### Fixed

- `AttributeError` on startup when profile list was populated before its dependent buttons were constructed.

---

## [1.9.0] — 20 Mar 2026

### Changed

- All inline hint paragraphs in Settings tabs converted to hover tooltips on `?` badges next to section headers. Reduces UI height and clutter while keeping guidance accessible.

---

## [1.8.1] — 20 Mar 2026

### Added

- **Default profile** — a profile named `Default` is automatically loaded on every app start.
- **Global hotkey** — hotkey removed from `PROFILE_KEYS`; loading a profile no longer overwrites the global hotkey setting.

---

## [1.8.0] — UX improvements & polish

---

## [1.7.0] — UX improvements & polish

### Added

- Active-profile pill on Quick Capture panel.
- Arrow-key nudging on the capture overlay (1 px / 10 px with Shift).
- Overwrite warning when saving a profile with an existing name.
- Live file-prefix example preview in the Output tab.
- Camera silhouette tray icon drawn with QPainter.

### Changed

- Single-click profile loading in Settings → Profiles (Load button removed).
- Status card green flash after every capture or profile load.
- Exit requires no confirmation dialog.
- Status card cold-start hint shows active hotkey.
- Settings panel minimum height set to prevent window jumping between tabs.
- Toolbar normalised; Exit demoted to text link.
- Dimension badge flips inside the selection when near the top edge.

---

## [1.6.3] — UI polish

---

## [1.6.2] — Multi-monitor coordinate fix, logging tab, UI polish

### Fixed

- Multi-monitor full-screen capture cuts off taskbar on non-primary screens.
- "Logging is disabled" shown even when checkbox is ticked.
- Tab bar scroll arrows with four tabs.
- Browse button text clipped.

### Added

- Logging tab — enable/disable, log level, log folder, current session path, Open log folder button.
- `utils/logger.py` — singleton, RotatingFileHandler (1 MB, 5 backups), `apply_log_settings()`, `current_log_path()`.
- 📂 Open folder button on Quick Capture toolbar.

---

## [1.5.0] — Test capture & profile workflow

### Added

- ▶ Test capture button in the Settings footer. Re-opens Settings automatically on completion.

---

## [1.4.0] — Profile UX redesign

### Added

- QListWidget profile list on Quick Capture panel and Settings → Profiles.
- "Save as profile" footer always visible across all tabs.

---

## [1.3.0] — UI polish, hotkey capture

### Added

- HotkeyCapture widget — click to record, Escape to cancel.

### Changed

- Colour scheme updated; dark slate header bar added.

---

## [1.2.0] — Two-panel GUI redesign

### Added

- Quick Capture panel and Settings panel with QStackedWidget.

---

## [1.1.0] — Auto-save, toast, keyboard shortcut overlay

### Added

- Auto-save with 600 ms debounce.
- Keyboard shortcut overlay on capture overlay (press `?`).
- "Show in Explorer" link in toast notification.

---

## [1.0.0] — Initial release

### Added

- Full-screen capture overlay, multi-monitor support.
- Per-ratio last-region memory (9:16 and 16:9 independently).
- Global hotkey via background QThread.
- Aspect-ratio lock, custom dimensions, sequential/timestamp file naming.
- Named profiles (save / load / delete), clipboard copy.
- System-tray integration, toast notification.

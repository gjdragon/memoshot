# MemoShot

A lightweight, always-available screenshot tool for content creators. MemoShot lives in the system tray, responds to a global hotkey, and saves properly sized captures for TikTok, YouTube Shorts, Instagram, LinkedIn, and any other platform — without interrupting your workflow.

## Screenshots

<div style="display: flex; gap: 10px;">
  <img src="res/screenshot.png" width="180"/>
  <img src="res/screenshot1.png" width="180"/>
  <img src="res/screenshot2.png" width="180"/>
  <img src="res/screenshot3.png" width="180"/>
  <img src="res/screenshot4.png" width="180"/>
</div>

---

## Features

- **Global hotkey capture** — trigger from any app. Default `Ctrl+Shift+P`; click the hotkey field and press any combination to change it. The hotkey is global and shared across all profiles.
- **Full-screen interactive overlay** — drag and resize a selection rectangle across any monitor. All edges and corners are resizable. Multi-monitor layouts handled correctly.
- **Arrow-key nudging** — fine-position the selection with arrow keys (1 px; 10 px with `Shift`).
- **Portrait & landscape modes** — 9:16 and 16:9 aspect-ratio lock, or unlock for any custom size.
- **Per-mode region memory** — the overlay remembers the last capture position separately for portrait and landscape.
- **Output format** — save as PNG, JPEG (with quality slider), or WebP. Set per profile.
- **Capture confirmation** — each profile can require pressing `Enter` to confirm before saving, or fire instantly. Test Capture always requires confirmation.
- **Named profiles** — save a complete snapshot of settings (save folder, prefix, dimensions, ratio, format, clipboard, confirmation) under a name. Switch instantly from the main window.
- **Default profile** — a profile named `Default` is loaded automatically on every startup.
- **Profile management** — create, edit, rename (double-click), reorder (drag-and-drop), delete, export to `.json`, and import from `.json`.
- **Active-profile indicator** — a pill on the Quick Capture panel shows which profile is loaded.
- **Profile detail card** — selecting a profile shows an inline summary of its key settings.
- **Test capture** — run a live capture while reviewing settings, then return to Settings to save as a profile.
- **Auto-save settings** — every change persists immediately.
- **Sequential or timestamp file naming** — set a prefix for `myshot_001.jpg`, or leave blank for `Portrait_YYYY-MM-DD_HH-MM-SS.png`. Live example updates as you type.
- **Clipboard copy** — each screenshot copied to the system clipboard (optional, per profile).
- **Toast notification** — appears at the bottom of your primary screen after every capture, with a **Show in Explorer** link.
- **Keyboard shortcut overlay** — press `?` on the capture overlay for a floating cheat-sheet.
- **Contextual help** — every settings section has a `?` badge; hover to read the guide without cluttering the UI.
- **Multi-monitor aware** — overlay spans all screens. Press `S` to snap the selection to the current screen.
- **Logging** — rotating file logging with DEBUG/INFO level, configurable folder, and a Logging tab in Settings.
- **System tray** — minimises out of your taskbar. Right-click for Capture / Show Window / Exit.

---

## Requirements

- Python **3.9 or newer**
- PyQt5
- keyboard

```
pip install PyQt5 keyboard
```

> **Windows note:** the `keyboard` library requires administrator privileges to register global hotkeys.

---

## Installation

```bash
git clone https://github.com/your-username/memoshot.git
cd memoshot
pip install PyQt5 keyboard
python src/main.py
```

No build step or installer needed.

---

## Quick start

1. Run `python src/main.py`. The app registers in the system tray.
2. Press the hotkey (default `Ctrl+Shift+P`) from any application.
3. The overlay appears. Drag the rectangle to your region. Use arrow keys to fine-tune.
4. Press `Enter` to capture. A toast confirms the save with a **Show in Explorer** link.
5. The window stays minimised to tray until you need it again.

---

## Main window

### Quick Capture panel (default)

| Element | Purpose |
|---|---|
| **Active-profile pill** | Shows the loaded profile and capture mode. Hidden when none is active. |
| **Capture button** | Starts a capture. Displays the active hotkey. |
| **Status card** | Dimensions and position of the last captured region, or a first-run hint. |
| **Profile list** | All saved profiles in your custom order. Click to load instantly. |
| **⚙ Settings** | Opens the Settings panel. |
| **📂 Open folder** | Opens the screenshots folder in the file manager. |
| **⬜ Tray** | Minimises to the system tray. |
| **Exit** | Quits the application. |

### Settings panel

Four tabs, with a persistent footer for test captures and profile saving.

| Tab | Contents |
|---|---|
| **Capture** | Hotkey (global), capture mode (Region / Window), capture confirmation, aspect ratio, ratio lock, dimensions. |
| **Output** | Save folder, file prefix with live example, clipboard copy, output format (PNG / JPEG / WebP) with JPEG quality slider. |
| **Profiles** | Profile list with drag-to-reorder and double-click rename. Edit, Delete, Export buttons. Import from file. Detail card for selected profile. |
| **Logging** | Enable/disable, log level, log folder, current session file, Open log folder button. |

**Footer:**

| Element | Purpose |
|---|---|
| **▶ Test capture** | Live capture with current settings. Returns to Settings automatically. Always requires Enter confirmation. |
| **Save as profile** | Type a name and press Save. Overwrites require a second confirmation. |

---

## Capture overlay controls

| Key / Action | Effect |
|---|---|
| `Enter` | Capture and save |
| `Esc` | Close shortcut panel if open, otherwise cancel |
| `S` | Snap selection to the current screen |
| `?` | Toggle keyboard shortcut cheat-sheet |
| `Arrow keys` | Nudge selection 1 px |
| `Shift + Arrow keys` | Nudge selection 10 px |
| Drag inside | Move the capture region |
| Drag edge | Resize from that edge |
| Drag corner | Resize from that corner |

---

## Profile workflow

1. Open **⚙ Settings** and configure Capture and Output tabs.
2. Click **▶ Test capture**, position the region, press `Enter`.
3. Settings re-opens. Type a profile name in the footer and press **Save**.
4. The profile appears in both the Quick panel and the Profiles tab.

To edit an existing profile: go to **Profiles**, select it, click **Edit**. All tabs load that profile's settings and the footer pre-fills the name — make changes and press **Save**.

To rename: double-click the profile name directly in the list.

To reorder: drag any profile row to a new position.

To share or back up: select a profile and click **Export**. To restore: click **Import profiles from file…**

A profile named **Default** is loaded automatically every time the app starts.

---

## Output formats

| Format | Extension | Notes |
|---|---|---|
| PNG | `.png` | Lossless. Best for editing and archiving. |
| JPEG | `.jpg` | Lossy, smallest file size. Quality slider 1–100 (default 90). |
| WebP | `.webp` | Modern format, smaller than PNG at comparable quality. |

Format and JPEG quality are saved per profile.

---

## Settings reference

| Setting | Scope | Description |
|---|---|---|
| Hotkey | Global | Keyboard shortcut — click to record |
| Save folder | Profile | Output directory for screenshots |
| File prefix | Profile | Empty = timestamp. Set for numbered sequences. |
| Width / Height | Profile | Capture rectangle dimensions in pixels |
| Aspect ratio | Profile | 9:16 Portrait or 16:9 Landscape |
| Lock aspect ratio | Profile | Keeps ratio fixed when adjusting spin-boxes |
| Output format | Profile | PNG, JPEG, or WebP |
| JPEG quality | Profile | 1–100 (JPEG only) |
| Copy to clipboard | Profile | Copies each screenshot to the clipboard after saving |
| Capture confirmation | Profile | Require Enter before saving; or fire instantly |
| Enable logging | Global | Write a log file for this session |
| Log level | Global | INFO or DEBUG |
| Log folder | Global | Directory for log files (default: `src/Logs/`) |

Settings are stored as JSON at `~/.memoshot_settings.json`.

---

## Project structure

```
src/
├── main.py                 Entry point
├── app.py                  QApplication setup, logging initialisation
├── version.py              Version string
├── core/
│   ├── settings.py         Load / save / profile helpers — no Qt dependency
│   └── hotkey.py           QThread wrapper around the keyboard library
├── capture/
│   └── screenshot.py       File naming, format handling, cropping, clipboard
├── ui/
│   ├── main_window.py      Two-panel main window, tray, HotkeyCapture widget
│   ├── overlay.py          Full-screen region capture overlay
│   └── window_overlay.py   Window-click capture overlay
└── utils/
    └── logger.py           Rotating file logger, apply_log_settings()
```

---

## License

MIT — do whatever you like, just keep the copyright notice.

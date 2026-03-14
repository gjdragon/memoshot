# MemoShot

A lightweight, always-available screenshot tool built for content creators who shoot vertical video. MemoShot lives in your system tray, responds to a global hotkey, and saves properly sized captures for TikTok, YouTube Shorts, Instagram, and other portrait-format platforms — without interrupting your workflow.

---

## Features

- **Global hotkey capture** — trigger a capture from any app without switching windows
- **Full-screen interactive overlay** — drag and resize a selection rectangle across any monitor
- **Portrait & landscape presets** — 9:16 and 16:9 aspect-ratio modes with locked proportions
- **Custom dimensions** — unlock the ratio and type any width/height you need
- **Auto-save settings** — every change persists immediately; no Save button required
- **Capture history** — the overlay remembers the last region per ratio mode, so repeat captures are one keypress
- **Clipboard copy** — screenshots land on the clipboard automatically (optional)
- **Named profiles** — save and switch between complete setting snapshots (hotkey, folder, dimensions, prefix)
- **Sequential file naming** — use a custom prefix for numbered sequences, or fall back to timestamps
- **Multi-monitor aware** — spans all connected screens; `S` snaps the selection to the current monitor
- **System tray** — minimises to tray and stays out of your taskbar
- **Keyboard shortcut overlay** — press `?` during capture to see every shortcut in a floating panel

---

## Requirements

- Python 3.10+
- PyQt5
- keyboard

```
pip install PyQt5 keyboard
```

> **Windows note:** the `keyboard` library requires administrator privileges (or running without UAC elevation on some systems) to register global hotkeys.

---

## Installation

```bash
git clone https://github.com/gjdragon/memoshot.git
cd memoshot
pip install PyQt5 keyboard
python src/main.py
```

No build step or installer needed. MemoShot runs directly from the source tree.

---

## Usage

### Starting a capture

| Method | Action |
|---|---|
| Global hotkey (default `Ctrl+Shift+P`) | Trigger from any app |
| **Capture Now** button | Click in the MemoShot window |
| System tray → **Capture** | Right-click the tray icon |

### Overlay controls

| Key / Action | Effect |
|---|---|
| `Enter` | Capture and save the selected region |
| `Esc` | Cancel (or close the shortcut panel first) |
| `S` | Snap selection to fill the current screen |
| `?` | Toggle the keyboard shortcut cheat-sheet |
| Drag inside | Move the capture rectangle |
| Drag edge | Resize from that edge |
| Drag corner | Resize from that corner |

### After capture

A toast notification appears at the bottom of your primary screen confirming the save path. Click **Show in Explorer** inside the toast to open the folder and highlight the file.

### Settings

All settings save automatically as soon as you change them — there is no Save button.

| Setting | Description |
|---|---|
| Hotkey | Global keyboard shortcut to trigger capture |
| Save to | Output folder for PNG files |
| File prefix | Leave blank for `MemoShot_YYYY-MM-DD_HH-MM-SS.png`, or set a prefix for `prefix1.png`, `prefix2.png`, … |
| Width / Height | Capture rectangle dimensions in pixels |
| Lock Aspect Ratio | Keep 9:16 or 16:9 proportions when resizing |
| Copy to clipboard | Also copy each screenshot to the system clipboard |

### Profiles

Save a full snapshot of your current settings under a name (e.g. "TikTok", "LinkedIn"). Load or delete profiles from the Profiles panel at the top of the window.

---

## Project structure

```
src/
├── main.py                 Entry point
├── app.py                  QApplication setup
├── version.py              Single source of truth for the version string
├── core/
│   ├── settings.py         Load / save / profile helpers (no Qt dependency)
│   └── hotkey.py           QThread wrapper around the keyboard library
├── capture/
│   └── screenshot.py       File naming, cropping, clipboard copy
├── ui/
│   ├── main_window.py      Main window and system-tray integration
│   └── overlay.py          Full-screen capture overlay
└── utils/
    └── logger.py           Thin logging helper
```

---

## Settings file

Settings are stored as JSON at `~/.memoshot_settings.json`. You can edit this file manually while MemoShot is not running.

---

## License

MIT — do whatever you like, just keep the copyright notice.

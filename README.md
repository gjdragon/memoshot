# MemoShot

A lightweight, always-available screenshot tool for content creators. MemoShot lives in the system tray, responds to a global hotkey, and saves properly sized captures for TikTok, YouTube Shorts, Instagram, LinkedIn, and any other platform — without interrupting your workflow.

---

## Features

- **Global hotkey capture** — trigger from any app without switching windows. Default is `Ctrl+Shift+P`; change it by clicking the hotkey field and pressing your preferred keys directly on the keyboard.
- **Full-screen interactive overlay** — drag and resize a selection rectangle across any monitor. Edges and corners are all resizable.
- **Portrait & landscape modes** — 9:16 and 16:9 aspect-ratio lock. Unlock the ratio for any custom pixel size.
- **Per-mode region memory** — the overlay remembers the last capture position separately for portrait and landscape, so repeat captures are one keypress.
- **Named profiles** — save a complete snapshot of all your settings (hotkey, save folder, prefix, dimensions, ratio, clipboard) under a name. Switch between profiles instantly from the main window.
- **Test capture from Settings** — run a live capture while reviewing settings, then come straight back to Settings to verify the result and save it as a profile without navigating away.
- **Auto-save settings** — every change persists immediately with no Save button. A debounce timer batches rapid spin-box changes into a single disk write.
- **Sequential or timestamp file naming** — set a file prefix for `myshot1.png, myshot2.png, …`, or leave it blank for `Portrait_YYYY-MM-DD_HH-MM-SS.png`.
- **Clipboard copy** — each screenshot is copied to the system clipboard automatically (optional).
- **Toast notification** — appears at the bottom of your primary screen after every capture. Includes a **Show in Explorer** link that opens the save folder and highlights the file.
- **Keyboard shortcut overlay** — press `?` on the capture overlay to show a floating cheat-sheet of every key and mouse action.
- **Multi-monitor aware** — the overlay spans all connected screens. Press `S` to snap the selection to the screen the rectangle is centred on.
- **System tray** — minimises out of your taskbar. Right-click for Capture / Show Window / Exit.

---

## Requirements

- Python **3.9 or newer**
- PyQt5
- keyboard

```
pip install PyQt5 keyboard
```

> **Windows note:** the `keyboard` library requires administrator privileges (or running as a standard user on a system where UAC is not restricting hook registration) to register global hotkeys.

---

## Installation

```bash
git clone https://github.com/your-username/memoshot.git
cd memoshot
pip install PyQt5 keyboard
python src/main.py
```

No build step or installer needed. MemoShot runs directly from the source tree.

---

## Quick start

1. Run `python src/main.py`. The main window opens and the app registers in the system tray.
2. Press the hotkey (default `Ctrl+Shift+P`) from any application.
3. The overlay appears. Drag the purple rectangle to your region of interest.
4. Press `Enter` to capture. A toast confirms the save location with a **Show in Explorer** link.
5. The window stays minimised to tray until you need it again.

---

## Main window

The window has two panels that switch without opening a new window.

### Quick Capture panel (default)

| Element | Purpose |
|---|---|
| **Capture button** | Starts a capture. Shows the active hotkey as a reminder. |
| **Status card** | Shows the dimensions and position of the last captured region. |
| **Profile list** | All saved profiles. Click a row to load it — the row stays highlighted so you can always see which profile is active. |
| **⚙ Settings** | Opens the Settings panel. |
| **Tray** | Minimises to the system tray. |
| **Exit** | Quits the application. |

### Settings panel

Opens from the **⚙ Settings** button. **← Back** returns to Quick Capture.

Three tabs:

| Tab | Contents |
|---|---|
| **Capture** | Hotkey recorder, aspect ratio (9:16 / 16:9), ratio lock, width & height in pixels. |
| **Output** | Save folder (with Browse button), file prefix, clipboard copy toggle. |
| **Profiles** | List of saved profiles. Select a row to activate Load and Delete buttons. |

**Footer (always visible across all tabs):**

| Element | Purpose |
|---|---|
| **▶ Test capture** | Runs a live capture with the current settings. The Settings panel re-opens automatically so you can review the result and save it as a profile. |
| **Save as profile** | Type a profile name and press Save (or Enter) to snapshot all current settings. |

---

## Capture overlay controls

| Key / Action | Effect |
|---|---|
| `Enter` | Capture and save the selected region |
| `Esc` | Close the shortcut panel if open, otherwise cancel the overlay |
| `S` | Snap the selection to fill the current screen |
| `?` | Toggle the keyboard shortcut cheat-sheet |
| Drag inside the rectangle | Move the capture region |
| Drag any edge | Resize from that edge |
| Drag any corner | Resize from that corner |

---

## Hotkey recording

Click the hotkey field in **Settings → Capture**. The field turns blue and shows "Press keys…". Press your combination — for example `F12`, `Ctrl+Shift+S`, or `Alt+F4`. The field fills immediately and recording stops. Press `Escape` to cancel and keep the previous hotkey.

Supported keys: all function keys (`F1`–`F15`), navigation keys (Home, End, Page Up/Down, arrow keys), Delete, Insert, Tab, Enter, Backspace, Space, Print Screen, Scroll Lock, Pause, Num Lock, Caps Lock, and any printable character.

---

## Profile workflow

The recommended workflow for setting up a new profile:

1. Open **⚙ Settings**.
2. Configure your desired hotkey, ratio, dimensions, save folder, and prefix across the Capture and Output tabs.
3. Click **▶ Test capture** in the footer. The overlay opens — select your region and press `Enter`.
4. The Settings panel re-opens. The footer status line shows the captured dimensions and position.
5. If the result looks right, type a profile name in the footer field and press **Save**.
6. The new profile appears immediately in both the Quick panel list and the Profiles tab.

To switch profiles, click any row in the Quick panel list. The row stays highlighted to show which profile is active.

---

## Settings

All settings save automatically on every change. There is no Save button.

| Setting | Description |
|---|---|
| Hotkey | Global keyboard shortcut — click to record |
| Save folder | Output directory for PNG files |
| File prefix | Empty = timestamp filename. Set a prefix for numbered sequences. |
| Width / Height | Capture rectangle dimensions in pixels |
| Aspect ratio | 9:16 Portrait or 16:9 Landscape |
| Lock aspect ratio | Keeps the ratio fixed when resizing spin-boxes |
| Copy to clipboard | Copies each screenshot to the system clipboard after saving |

Settings are stored as JSON at `~/.memoshot_settings.json`. You can edit this file manually while MemoShot is not running.

---

## Project structure

```
src/
├── main.py                 Entry point
├── app.py                  QApplication setup
├── version.py              Version string (single source of truth)
├── core/
│   ├── settings.py         Load / save / profile helpers — no Qt dependency
│   └── hotkey.py           QThread wrapper around the keyboard library
├── capture/
│   └── screenshot.py       File naming, cropping, clipboard copy
├── ui/
│   ├── main_window.py      Two-panel main window, tray, HotkeyCapture widget
│   └── overlay.py          Full-screen capture overlay
└── utils/
    └── logger.py           Thin logging helper
```

---

## License

MIT — do whatever you like, just keep the copyright notice.

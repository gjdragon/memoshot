# MemoShot

A PyQt5 desktop app for capturing fixed-ratio screenshot regions via a global hotkey.

## Project Structure

```
portrait_screenshot/
│
├── main.py               # Entry point — calls app.run()
├── app.py                # QApplication setup & lifecycle
├── requirements.txt
│
├── core/                 # Business logic — no UI dependency
│   ├── settings.py       # Load/save/validate settings & profiles (JSON)
│   └── hotkey.py         # HotkeyThread (QThread + keyboard library)
│
├── ui/                   # All PyQt5 widgets
│   ├── main_window.py    # PortraitScreenshotApp — main window + system tray
│   └── overlay.py        # CaptureOverlay — full-screen selection widget
│
├── capture/              # Screenshot I/O — independent of UI widgets
│   └── screenshot.py     # save_screenshot(), copy_to_clipboard(), filename logic
│
└── utils/
    └── logger.py         # Shared logging helper
```

## How to run

```bash
pip install -r requirements.txt
python main.py
```

## Adding new features

| What you want to add | Where to put it |
|---|---|
| New file format (JPEG, WebP) | `capture/screenshot.py` |
| Post-processing / annotation | `capture/` (new module) |
| New UI panel or dialog | `ui/` (new module) |
| New setting / profile key | `core/settings.py` — add to `DEFAULT_SETTINGS` and `PROFILE_KEYS` |
| Additional hotkey actions | `core/hotkey.py` |
| CLI / headless mode | Reuse `core/` and `capture/` directly |

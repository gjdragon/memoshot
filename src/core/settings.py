"""
core/settings.py
~~~~~~~~~~~~~~~~
Load, save, and manage application settings and profiles.
No PyQt5 dependency – pure Python / JSON.
"""

import json
import os
from typing import List

from utils.logger import get_logger

logger = get_logger(__name__)

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".memoshot_settings.json")

# All supported capture modes.  Adding a new mode here is the only change
# needed in this file — the UI and capture layer read this list.
CAPTURE_MODES = [
    "region",   # drag-to-select a region (original behaviour)
    "window",   # click a window to capture it
]

DEFAULT_SETTINGS: dict = {
    "hotkey": "ctrl+shift+p",
    "save_location": os.path.join(os.path.expanduser("~"), "Screenshots"),
    "portrait_width": 607,
    "portrait_height": 1080,
    "ratio_mode": "9:16",
    "lock_ratio": True,
    "last_capture_rect": None,   # kept for backwards-compatibility
    "copy_to_clipboard": True,
    "file_prefix": "",
    "profiles": {},
    # ── Capture mode ───────────────────────────────────────────────────────────
    "capture_mode": "region",    # one of CAPTURE_MODES
    # ── Confirmation ───────────────────────────────────────────────────────────
    # True  → user must press Enter to confirm each capture (safe default)
    # False → capture fires immediately when the hotkey is pressed
    "confirm_capture": True,
    # ── Logging ────────────────────────────────────────────────────────────────
    "logging_enabled": True,
    "log_folder": "",            # empty → use default (src/Logs/)
    "log_level": "INFO",         # "INFO" or "DEBUG"
}

# Keys that are stored inside a profile snapshot.
# capture_mode is intentionally included so a profile fully describes how
# to capture, not just where to save.
# NOTE: "hotkey" is intentionally excluded — it is a global setting that
# is never overridden by loading a profile.
PROFILE_KEYS = [
    "save_location",
    "file_prefix",
    "portrait_width",
    "portrait_height",
    "ratio_mode",
    "lock_ratio",
    "copy_to_clipboard",
    "capture_mode",
    "confirm_capture",
    "last_capture_rect_9:16",
    "last_capture_rect_16:9",
]


def load() -> dict:
    """Return the application settings dict, merging defaults with saved data."""
    settings = dict(DEFAULT_SETTINGS)
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
                settings.update(loaded)
    except Exception as exc:
        logger.warning(f"Error loading settings: {exc}")
    # Guarantee capture_mode is always a recognised value (backwards compat)
    if settings.get("capture_mode") not in CAPTURE_MODES:
        settings["capture_mode"] = "region"
    return settings


def save(settings: dict) -> None:
    """Persist the settings dict to disk."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2)
    except Exception as exc:
        logger.error(f"Error saving settings: {exc}")


# ── Profile helpers ────────────────────────────────────────────────────────────

def profile_snapshot(settings: dict) -> dict:
    """Return the subset of settings that belong in a profile."""
    return {k: settings[k] for k in PROFILE_KEYS if k in settings}


def save_profile(settings: dict, name: str) -> None:
    """Add / overwrite a named profile and persist settings."""
    settings.setdefault("profiles", {})[name] = profile_snapshot(settings)
    save(settings)
    logger.info(f"Profile saved: {name}")


def load_profile(settings: dict, name: str) -> bool:
    """
    Apply a stored profile onto *settings* in-place.
    Returns True on success, False if the profile doesn't exist.
    Old profiles that pre-date capture_mode default to 'region'.
    """
    profiles = settings.get("profiles", {})
    if name not in profiles:
        logger.warning(f"Profile not found: {name}")
        return False
    data = profiles[name]
    # Backwards compat: profiles saved before capture_mode existed
    if "capture_mode" not in data:
        data["capture_mode"] = "region"
    # Backwards compat: profiles saved before confirm_capture existed
    if "confirm_capture" not in data:
        data["confirm_capture"] = True
    # hotkey is a global setting — never let a profile override it
    saved_hotkey = settings.get("hotkey")
    settings.update(data)
    if saved_hotkey is not None:
        settings["hotkey"] = saved_hotkey
    # Validate the loaded mode
    if settings.get("capture_mode") not in CAPTURE_MODES:
        settings["capture_mode"] = "region"
    save(settings)
    logger.info(f"Profile loaded: {name}")
    return True


def delete_profile(settings: dict, name: str) -> bool:
    """Remove a named profile and persist settings. Returns True on success."""
    profiles = settings.get("profiles", {})
    if name not in profiles:
        return False
    del profiles[name]
    save(settings)
    logger.info(f"Profile deleted: {name}")
    return True


def list_profiles(settings: dict) -> List[str]:
    """Return sorted list of profile names."""
    return sorted(settings.get("profiles", {}).keys())

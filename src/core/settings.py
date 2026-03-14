"""
core/settings.py
~~~~~~~~~~~~~~~~
Load, save, and manage application settings and profiles.
No PyQt5 dependency – pure Python / JSON.
"""

import json
import os

from utils.logger import get_logger

logger = get_logger(__name__)

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".memoshot_settings.json")

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
}

# Keys that are stored inside a profile snapshot
PROFILE_KEYS = [
    "hotkey",
    "save_location",
    "file_prefix",
    "portrait_width",
    "portrait_height",
    "ratio_mode",
    "lock_ratio",
    "copy_to_clipboard",
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
    """
    profiles = settings.get("profiles", {})
    if name not in profiles:
        logger.warning(f"Profile not found: {name}")
        return False
    settings.update(profiles[name])
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


def list_profiles(settings: dict) -> list[str]:
    """Return sorted list of profile names."""
    return sorted(settings.get("profiles", {}).keys())

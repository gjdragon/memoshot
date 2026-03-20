"""
core/settings.py
~~~~~~~~~~~~~~~~
Load, save, and manage application settings and profiles.
No PyQt5 dependency – pure Python / JSON.
"""

import json
import os
from typing import List, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".memoshot_settings.json")

CAPTURE_MODES = [
    "region",
    "window",
]

OUTPUT_FORMATS = ["png", "jpeg", "webp"]

DEFAULT_SETTINGS: dict = {
    "hotkey": "ctrl+shift+p",
    "save_location": os.path.join(os.path.expanduser("~"), "Screenshots"),
    "portrait_width": 607,
    "portrait_height": 1080,
    "ratio_mode": "9:16",
    "lock_ratio": True,
    "last_capture_rect": None,
    "copy_to_clipboard": True,
    "file_prefix": "",
    "profiles": {},
    "profile_order": [],
    "capture_mode": "region",
    "confirm_capture": True,
    "output_format": "png",
    "jpeg_quality": 90,
    "logging_enabled": True,
    "log_folder": "",
    "log_level": "INFO",
}

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
    "output_format",
    "jpeg_quality",
    "last_capture_rect_9:16",
    "last_capture_rect_16:9",
]


def load() -> dict:
    settings = dict(DEFAULT_SETTINGS)
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
                settings.update(loaded)
    except Exception as exc:
        logger.warning(f"Error loading settings: {exc}")
    if settings.get("capture_mode") not in CAPTURE_MODES:
        settings["capture_mode"] = "region"
    if settings.get("output_format") not in OUTPUT_FORMATS:
        settings["output_format"] = "png"
    _sync_profile_order(settings)
    return settings


def save(settings: dict) -> None:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
            json.dump(settings, fh, indent=2)
    except Exception as exc:
        logger.error(f"Error saving settings: {exc}")


# ── Profile order ──────────────────────────────────────────────────────────────

def _sync_profile_order(settings: dict) -> None:
    profiles = settings.get("profiles", {})
    order = settings.get("profile_order", [])
    order = [n for n in order if n in profiles]
    for name in profiles:
        if name not in order:
            order.append(name)
    settings["profile_order"] = order


def list_profiles(settings: dict) -> List[str]:
    _sync_profile_order(settings)
    return list(settings.get("profile_order", []))


def reorder_profiles(settings: dict, new_order: List[str]) -> None:
    profiles = settings.get("profiles", {})
    settings["profile_order"] = [n for n in new_order if n in profiles]
    save(settings)
    logger.debug(f"Profile order saved: {settings['profile_order']}")


# ── CRUD ───────────────────────────────────────────────────────────────────────

def profile_snapshot(settings: dict) -> dict:
    return {k: settings[k] for k in PROFILE_KEYS if k in settings}


def save_profile(settings: dict, name: str) -> None:
    profiles = settings.setdefault("profiles", {})
    is_new = name not in profiles
    profiles[name] = profile_snapshot(settings)
    if is_new:
        settings.setdefault("profile_order", []).append(name)
    _sync_profile_order(settings)
    save(settings)
    logger.info(f"Profile saved: {name}")


def load_profile(settings: dict, name: str) -> bool:
    profiles = settings.get("profiles", {})
    if name not in profiles:
        logger.warning(f"Profile not found: {name}")
        return False
    data = profiles[name]
    if "capture_mode" not in data:
        data["capture_mode"] = "region"
    if "confirm_capture" not in data:
        data["confirm_capture"] = True
    if "output_format" not in data:
        data["output_format"] = "png"
    if "jpeg_quality" not in data:
        data["jpeg_quality"] = 90
    saved_hotkey = settings.get("hotkey")
    settings.update(data)
    if saved_hotkey is not None:
        settings["hotkey"] = saved_hotkey
    if settings.get("capture_mode") not in CAPTURE_MODES:
        settings["capture_mode"] = "region"
    if settings.get("output_format") not in OUTPUT_FORMATS:
        settings["output_format"] = "png"
    save(settings)
    logger.info(f"Profile loaded: {name}")
    return True


def rename_profile(settings: dict, old_name: str, new_name: str) -> bool:
    profiles = settings.get("profiles", {})
    if old_name not in profiles:
        logger.warning(f"Rename failed — not found: {old_name}")
        return False
    if new_name in profiles:
        logger.warning(f"Rename failed — already exists: {new_name}")
        return False
    profiles[new_name] = profiles.pop(old_name)
    order = settings.get("profile_order", [])
    try:
        order[order.index(old_name)] = new_name
    except ValueError:
        order.append(new_name)
    settings["profile_order"] = order
    save(settings)
    logger.info(f"Profile renamed: '{old_name}' -> '{new_name}'")
    return True


def delete_profile(settings: dict, name: str) -> bool:
    profiles = settings.get("profiles", {})
    if name not in profiles:
        return False
    del profiles[name]
    order = settings.get("profile_order", [])
    if name in order:
        order.remove(name)
    save(settings)
    logger.info(f"Profile deleted: {name}")
    return True


# ── Export / Import ────────────────────────────────────────────────────────────

def export_profiles(settings: dict, names: List[str], filepath: str) -> bool:
    profiles = settings.get("profiles", {})
    export_data = {
        "memoshot_profiles": {n: profiles[n] for n in names if n in profiles}
    }
    try:
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(export_data, fh, indent=2)
        logger.info(f"Exported {len(export_data['memoshot_profiles'])} profile(s) to {filepath}")
        return True
    except Exception as exc:
        logger.error(f"Export failed: {exc}")
        return False


def import_profiles(settings: dict, filepath: str) -> Tuple[List[str], List[str]]:
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if "memoshot_profiles" not in data:
            raise ValueError("Not a valid MemoShot profile export file.")
        incoming = data["memoshot_profiles"]
        profiles = settings.setdefault("profiles", {})
        imported, skipped = [], []
        for name, snapshot in incoming.items():
            if name in profiles:
                skipped.append(name)
            else:
                profiles[name] = snapshot
                imported.append(name)
        _sync_profile_order(settings)
        save(settings)
        logger.info(f"Import: {len(imported)} imported, {len(skipped)} skipped")
        return imported, skipped
    except Exception as exc:
        logger.error(f"Import failed: {exc}")
        return [], []

"""
capture/screenshot.py
~~~~~~~~~~~~~~~~~~~~~
All logic related to taking a screenshot, naming the output file,
saving it to disk, and copying it to the clipboard.
"""

import os
import re
from datetime import datetime

from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from utils.logger import get_logger

logger = get_logger(__name__)

# Maps our setting names to Qt format strings and file extensions
_FORMAT_MAP = {
    "png":  ("PNG",  ".png"),
    "jpeg": ("JPEG", ".jpg"),
    "webp": ("WEBP", ".webp"),
}


def get_next_sequence_number(save_dir: str, prefix: str, ext: str) -> int:
    """Scan save_dir for <prefix><number><ext> and return the next integer."""
    if not os.path.exists(save_dir):
        return 1
    pattern = re.compile(
        rf"^{re.escape(prefix)}(\d+){re.escape(ext)}$", re.IGNORECASE
    )
    max_number = 0
    try:
        for filename in os.listdir(save_dir):
            m = pattern.match(filename)
            if m:
                max_number = max(max_number, int(m.group(1)))
    except Exception as exc:
        logger.warning(f"Error scanning directory for sequence numbers: {exc}")
    return max_number + 1


def build_filename(save_dir: str, prefix: str, ext: str) -> str:
    """Return a full file path for the next screenshot."""
    prefix = prefix.strip()
    if not prefix:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Portrait_{timestamp}{ext}"
    else:
        seq = get_next_sequence_number(save_dir, prefix, ext)
        filename = f"{prefix}{seq}{ext}"
    logger.debug(f"Filename: {filename}")
    return os.path.join(save_dir, filename)


def save_screenshot(pixmap: QPixmap, rect: QRect, settings: dict) -> str:
    """
    Crop pixmap to rect, save to disk in the configured format,
    and optionally copy to clipboard.  Returns the saved file path.
    """
    save_dir = settings.get(
        "save_location", os.path.join(os.path.expanduser("~"), "Screenshots")
    )
    os.makedirs(save_dir, exist_ok=True)

    fmt_key = settings.get("output_format", "png")
    if fmt_key not in _FORMAT_MAP:
        fmt_key = "png"
    qt_fmt, ext = _FORMAT_MAP[fmt_key]

    prefix   = settings.get("file_prefix", "")
    filepath = build_filename(save_dir, prefix, ext)

    cropped: QPixmap = pixmap.copy(rect)
    logger.debug(f"Cropped: {cropped.width()}x{cropped.height()}  fmt={qt_fmt}  path={filepath}")

    if fmt_key == "jpeg":
        quality = int(settings.get("jpeg_quality", 90))
        ok = cropped.save(filepath, qt_fmt, quality)
    else:
        ok = cropped.save(filepath, qt_fmt)

    if not ok:
        raise IOError(f"QPixmap.save() failed for: {filepath}")

    logger.info(f"Screenshot saved: {filepath}")

    if settings.get("copy_to_clipboard", True):
        copy_to_clipboard(cropped)

    return filepath


def copy_to_clipboard(pixmap: QPixmap) -> None:
    try:
        QApplication.clipboard().setPixmap(pixmap)
        logger.info("Screenshot copied to clipboard")
    except Exception as exc:
        logger.error(f"Error copying to clipboard: {exc}")

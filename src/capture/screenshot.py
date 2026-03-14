"""
capture/screenshot.py
~~~~~~~~~~~~~~~~~~~~~
All logic related to taking a screenshot, naming the output file,
saving it to disk, and copying it to the clipboard.

No UI widgets here – this module only works with QPixmap, QRect, and
QApplication (for clipboard access).
"""

import os
import re
from datetime import datetime

from PyQt5.QtCore import QRect
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from utils.logger import get_logger

logger = get_logger(__name__)


# ── File naming ────────────────────────────────────────────────────────────────

def get_next_sequence_number(save_dir: str, prefix: str) -> int:
    """
    Scan *save_dir* for files matching ``<prefix><number>.png`` and return
    the next integer in the sequence.
    """
    if not os.path.exists(save_dir):
        return 1

    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)\.png$", re.IGNORECASE)
    max_number = 0
    try:
        for filename in os.listdir(save_dir):
            match = pattern.match(filename)
            if match:
                max_number = max(max_number, int(match.group(1)))
    except Exception as exc:
        logger.warning(f"Error scanning directory for sequence numbers: {exc}")

    return max_number + 1


def build_filename(save_dir: str, prefix: str) -> str:
    """
    Return a full file path for the next screenshot.

    * If *prefix* is empty, the filename uses a timestamp.
    * Otherwise it uses ``<prefix><seq>.png``.
    """
    prefix = prefix.strip()
    if not prefix:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"Portrait_{timestamp}.png"
    else:
        seq = get_next_sequence_number(save_dir, prefix)
        filename = f"{prefix}{seq}.png"
    return os.path.join(save_dir, filename)


# ── Core capture actions ───────────────────────────────────────────────────────

def save_screenshot(pixmap: QPixmap, rect: QRect, settings: dict) -> str:
    """
    Crop *pixmap* to *rect*, save it to disk, and (optionally) copy it to
    the clipboard.

    Returns the saved file path on success, or raises an exception on failure.
    """
    save_dir = settings.get(
        "save_location", os.path.join(os.path.expanduser("~"), "Screenshots")
    )
    os.makedirs(save_dir, exist_ok=True)

    prefix = settings.get("file_prefix", "")
    filepath = build_filename(save_dir, prefix)

    cropped: QPixmap = pixmap.copy(rect)

    if not cropped.save(filepath, "PNG"):
        raise IOError(f"QPixmap.save() returned False for path: {filepath}")

    logger.info(f"Screenshot saved: {filepath}")

    if settings.get("copy_to_clipboard", True):
        copy_to_clipboard(cropped)

    return filepath


def copy_to_clipboard(pixmap: QPixmap) -> None:
    """Copy *pixmap* to the system clipboard."""
    try:
        QApplication.clipboard().setPixmap(pixmap)
        logger.info("Screenshot copied to clipboard")
    except Exception as exc:
        logger.error(f"Error copying to clipboard: {exc}")

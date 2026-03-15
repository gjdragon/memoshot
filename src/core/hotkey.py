"""
core/hotkey.py
~~~~~~~~~~~~~~
QThread wrapper around the `keyboard` library so hotkey hooks
never block the Qt event loop.
"""

import time

import keyboard
from PyQt5.QtCore import QThread, pyqtSignal

from utils.logger import get_logger

logger = get_logger(__name__)


class HotkeyThread(QThread):
    """Run keyboard hooks in a separate thread to prevent blocking the UI."""

    hotkey_triggered = pyqtSignal()

    def __init__(self, hotkey: str) -> None:
        super().__init__()
        self.hotkey = hotkey
        self.is_running = False
        self.daemon = True

    # ------------------------------------------------------------------
    def run(self) -> None:
        try:
            self.is_running = True
            logger.info(f"Hotkey thread started for: {self.hotkey}")
            keyboard.add_hotkey(self.hotkey, self._on_hotkey)
            logger.debug(f"keyboard.add_hotkey registered: {self.hotkey}")
            while self.is_running:
                time.sleep(0.1)
        except Exception as exc:
            logger.error(f"Error in hotkey thread: {exc}")
        finally:
            logger.info("Hotkey thread ended")

    def _on_hotkey(self) -> None:
        logger.debug(f"Hotkey triggered: {self.hotkey}")
        self.hotkey_triggered.emit()

    def stop(self) -> None:
        """Gracefully stop the thread and unhook all keyboard hooks."""
        logger.debug("HotkeyThread.stop() called")
        self.is_running = False
        try:
            keyboard.unhook_all()
            logger.debug("keyboard.unhook_all() completed")
        except Exception as exc:
            logger.error(f"Error stopping hotkey thread: {exc}")
        self.wait()

"""
app.py
~~~~~~
QApplication setup and top-level lifecycle.
"""

import sys

from PyQt5.QtWidgets import QApplication

import core.settings as cfg
from utils.logger import apply_log_settings
from ui.main_window import PortraitScreenshotApp


def run() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Initialise logging before the window is created so early messages
    # (hotkey registration, settings load) are captured in the log file.
    settings = cfg.load()
    apply_log_settings(settings)

    window = PortraitScreenshotApp()
    window.show()

    sys.exit(app.exec_())

"""
app.py
~~~~~~
QApplication setup and top-level lifecycle.
"""

import sys

from PyQt5.QtWidgets import QApplication

from ui.main_window import PortraitScreenshotApp


def run() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = PortraitScreenshotApp()
    window.show()

    sys.exit(app.exec_())

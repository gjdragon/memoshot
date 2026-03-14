"""
ui/main_window.py
~~~~~~~~~~~~~~~~~
Main application window and system-tray integration.
Delegates all data concerns to core.settings and hotkey management
to core.hotkey.
"""

import core.settings as cfg
from core.hotkey import HotkeyThread
from ui.overlay import CaptureOverlay
from utils.logger import get_logger
from version import __version__
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

logger = get_logger(__name__)

APP_VERSION = __version__


class PortraitScreenshotApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = cfg.load()
        self.overlay: Optional[CaptureOverlay] = None
        self.hotkey_thread: HotkeyThread | None = None
        self.is_exiting = False

        # ── Auto-save debounce timer ───────────────────────────────────────────
        # Fires 600 ms after the last setting change so rapid spin-box clicks
        # don't hammer the disk on every step.
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._flush_auto_save)

        self.setWindowTitle(f"MemoShot v{APP_VERSION}")
        self.setGeometry(300, 300, 450, 350)

        self._init_ui()
        self._init_tray()

        QTimer.singleShot(500, self._register_hotkey)

    # ── UI construction ────────────────────────────────────────────────────────

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.setSpacing(15)

        title = QLabel("MemoShot")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(self._build_profiles_group())
        layout.addWidget(self._build_settings_group())
        layout.addLayout(self._build_action_buttons())

        info = QLabel(f"Press {self.settings['hotkey'].upper()} to capture\nRuns in system tray when minimized")
        info.setStyleSheet("color: gray; font-size: 10px;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        central.setLayout(layout)

    def _build_profiles_group(self) -> QGroupBox:
        group = QGroupBox("Profiles")
        row = QHBoxLayout()

        row.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(150)
        self.profile_combo.addItem("— select profile —")
        for name in cfg.list_profiles(self.settings):
            self.profile_combo.addItem(name)
        row.addWidget(self.profile_combo, 3)

        for label, slot in [("Load", self._load_profile),
                             ("Save as…", self._save_profile),
                             ("Delete", self._delete_profile)]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            row.addWidget(btn)

        group.setLayout(row)
        return group

    def _build_settings_group(self) -> QGroupBox:
        group = QGroupBox("Settings")
        layout = QVBoxLayout()

        # Hotkey
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Hotkey:"))
        self.hotkey_input = QLineEdit(self.settings["hotkey"])
        self.hotkey_input.setPlaceholderText("e.g., ctrl+shift+p")
        self.hotkey_input.editingFinished.connect(self._schedule_auto_save)
        hl.addWidget(self.hotkey_input)
        layout.addLayout(hl)

        # Save location
        sl = QHBoxLayout()
        sl.addWidget(QLabel("Save to:"))
        self.save_input = QLineEdit(self.settings["save_location"])
        self.save_input.editingFinished.connect(self._schedule_auto_save)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_folder)
        sl.addWidget(self.save_input, 3)
        sl.addWidget(browse_btn, 1)
        layout.addLayout(sl)

        # File prefix
        pl = QHBoxLayout()
        pl.addWidget(QLabel("File prefix:"))
        self.prefix_input = QLineEdit(self.settings.get("file_prefix", ""))
        self.prefix_input.setPlaceholderText("Leave empty for timestamp, or enter prefix")
        self.prefix_input.editingFinished.connect(self._schedule_auto_save)
        pl.addWidget(self.prefix_input)
        layout.addLayout(pl)

        # Width / Height
        dl = QHBoxLayout()
        dl.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 4000)
        self.width_spin.setValue(self.settings["portrait_width"])
        self.width_spin.valueChanged.connect(self._on_width_changed)
        self.width_spin.valueChanged.connect(self._schedule_auto_save)
        dl.addWidget(self.width_spin)
        dl.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 4000)
        self.height_spin.setValue(self.settings["portrait_height"])
        self.height_spin.valueChanged.connect(self._on_height_changed)
        self.height_spin.valueChanged.connect(self._schedule_auto_save)
        dl.addWidget(self.height_spin)
        layout.addLayout(dl)

        # Ratio lock + radio buttons
        rl = QHBoxLayout()
        self.lock_ratio_checkbox = QCheckBox("Lock Aspect Ratio")
        self.lock_ratio_checkbox.setChecked(self.settings.get("lock_ratio", True))
        self.lock_ratio_checkbox.stateChanged.connect(self._on_lock_ratio_changed)
        self.lock_ratio_checkbox.stateChanged.connect(self._schedule_auto_save)
        rl.addWidget(self.lock_ratio_checkbox)

        self.ratio_group = QButtonGroup()
        self.ratio_9_16 = QRadioButton("9:16 (Portrait)")
        self.ratio_16_9 = QRadioButton("16:9 (Landscape)")
        self.ratio_group.addButton(self.ratio_9_16)
        self.ratio_group.addButton(self.ratio_16_9)
        (self.ratio_9_16 if self.settings.get("ratio_mode", "9:16") == "9:16"
         else self.ratio_16_9).setChecked(True)
        self.ratio_9_16.toggled.connect(self._on_ratio_mode_changed)
        self.ratio_16_9.toggled.connect(self._on_ratio_mode_changed)
        self.ratio_9_16.toggled.connect(self._schedule_auto_save)
        self.ratio_16_9.toggled.connect(self._schedule_auto_save)
        rl.addWidget(self.ratio_9_16)
        rl.addWidget(self.ratio_16_9)
        rl.addStretch()
        layout.addLayout(rl)

        self.ratio_label = QLabel()
        self.ratio_label.setStyleSheet("color: #10b981; font-size: 10px; font-style: italic;")
        layout.addWidget(self.ratio_label)
        self._on_lock_ratio_changed()   # sets enabled state + updates label

        # Last region status
        self.last_region_label = QLabel()
        self.last_region_label.setStyleSheet("color: #3b82f6; font-size: 10px; font-style: italic;")
        layout.addWidget(self.last_region_label)
        self._update_last_region_label()

        # Clipboard checkbox
        cl = QHBoxLayout()
        self.copy_to_clipboard_checkbox = QCheckBox("Copy screenshot to clipboard")
        self.copy_to_clipboard_checkbox.setChecked(self.settings.get("copy_to_clipboard", True))
        self.copy_to_clipboard_checkbox.stateChanged.connect(self._schedule_auto_save)
        cl.addWidget(self.copy_to_clipboard_checkbox)
        cl.addStretch()
        layout.addLayout(cl)

        # Auto-save indicator — replaces the old "Save Settings" button.
        # Appears briefly after each save and fades automatically.
        self.autosave_label = QLabel("✔  Settings saved")
        self.autosave_label.setStyleSheet(
            "color: #10b981; font-size: 10px; font-style: italic;"
        )
        self.autosave_label.setAlignment(Qt.AlignRight)
        self.autosave_label.setVisible(False)
        layout.addWidget(self.autosave_label)

        group.setLayout(layout)
        return group

    def _build_action_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        capture_btn = QPushButton("Capture Now")
        capture_btn.setStyleSheet("padding: 10px; font-weight: bold;")
        capture_btn.clicked.connect(self.start_capture)
        row.addWidget(capture_btn)

        minimize_btn = QPushButton("Minimize to Tray")
        minimize_btn.clicked.connect(self.hide)
        row.addWidget(minimize_btn)

        exit_btn = QPushButton("Exit Application")
        exit_btn.setStyleSheet("background-color: #dc2626; color: white; padding: 8px;")
        exit_btn.clicked.connect(self._quit_app)
        row.addWidget(exit_btn)

        return row

    # ── Tray ──────────────────────────────────────────────────────────────────

    def _init_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        pm = QPixmap(64, 64)
        pm.fill(QColor(147, 51, 234))
        self.tray_icon.setIcon(QIcon(pm))

        menu = QMenu()
        for label, slot in [("Capture", self.start_capture),
                             ("Show Window", self.show)]:
            a = QAction(label, self)
            a.triggered.connect(slot)
            menu.addAction(a)
        menu.addSeparator()
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self._quit_app)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_click)
        self.tray_icon.show()
        self.tray_icon.setToolTip(f"MemoShot\nPress {self.settings['hotkey'].upper()}")

    def _on_tray_click(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger and not self.isVisible():
            self.show()
            self.activateWindow()

    # ── Hotkey management ──────────────────────────────────────────────────────

    def _register_hotkey(self) -> None:
        if self.is_exiting:
            return
        if self.hotkey_thread is not None:
            self.hotkey_thread.stop()
            self.hotkey_thread = None
        try:
            self.hotkey_thread = HotkeyThread(self.settings["hotkey"])
            self.hotkey_thread.hotkey_triggered.connect(self.start_capture)
            self.hotkey_thread.start()
            logger.info(f"Hotkey registered: {self.settings['hotkey']}")
        except Exception as exc:
            logger.error(f"Could not register hotkey: {exc}")
            QMessageBox.warning(self, "Hotkey Error",
                                f"Could not register hotkey: {self.settings['hotkey']}\n{exc}")

    # ── Capture flow ──────────────────────────────────────────────────────────

    def start_capture(self) -> None:
        if self.is_exiting:
            return
        try:
            if self.overlay is None or not self.overlay.isVisible():
                self.overlay = CaptureOverlay(self.settings)
                self.overlay.capture_signal.connect(self._on_capture_complete)
                self.overlay.update_ui_dimensions.connect(self._on_overlay_dimensions_changed)
                self.overlay.show()
                self.overlay.activateWindow()
                self.overlay.raise_()
        except Exception as exc:
            logger.error(f"Error starting capture: {exc}")

    def _on_capture_complete(self, rect) -> None:
        self._update_last_region_label()
        cfg.save(self.settings)

    def _on_overlay_dimensions_changed(self, width: int, height: int) -> None:
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self._update_ratio_label()

    # ── Auto-save ─────────────────────────────────────────────────────────────

    def _schedule_auto_save(self, *_args) -> None:
        """Restart the debounce timer on every settings change."""
        self._save_timer.start()
        self.autosave_label.setVisible(False)

    def _flush_auto_save(self) -> None:
        """Persist the current UI state to disk — no dialog, no interruption."""
        old_hotkey = self.settings["hotkey"]
        self._snapshot_ui_to_settings()
        cfg.save(self.settings)
        if old_hotkey != self.settings["hotkey"]:
            self._register_hotkey()
        self.tray_icon.setToolTip(f"MemoShot\nPress {self.settings['hotkey'].upper()}")
        logger.info("Settings auto-saved")
        # Brief confirmation — visible for 2.5 s then disappears
        self.autosave_label.setVisible(True)
        QTimer.singleShot(2500, lambda: self.autosave_label.setVisible(False))

    # ── Settings panel helpers ─────────────────────────────────────────────────

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder:
            self.save_input.setText(folder)
            self._schedule_auto_save()

    def _on_width_changed(self, value: int) -> None:
        if self.settings.get("lock_ratio", True):
            self.height_spin.blockSignals(True)
            ratio = 16 / 9 if self.settings.get("ratio_mode", "9:16") == "9:16" else 9 / 16
            self.height_spin.setValue(int(value * ratio))
            self.height_spin.blockSignals(False)
            self._update_ratio_label()

    def _on_height_changed(self, value: int) -> None:
        if self.settings.get("lock_ratio", True):
            self.width_spin.blockSignals(True)
            ratio = 9 / 16 if self.settings.get("ratio_mode", "9:16") == "9:16" else 16 / 9
            self.width_spin.setValue(int(value * ratio))
            self.width_spin.blockSignals(False)
            self._update_ratio_label()

    def _on_lock_ratio_changed(self) -> None:
        locked = self.lock_ratio_checkbox.isChecked()
        self.settings["lock_ratio"] = locked
        self.ratio_9_16.setEnabled(locked)
        self.ratio_16_9.setEnabled(locked)
        if locked:
            self._on_width_changed(self.width_spin.value())
        self._update_ratio_label()

    def _on_ratio_mode_changed(self, checked: bool) -> None:
        if not checked:
            return
        was_locked = self.settings.get("lock_ratio", True)
        self.settings["lock_ratio"] = False
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        if self.ratio_9_16.isChecked():
            self.settings["ratio_mode"] = "9:16"
            w, h = 607, 1080
        else:
            self.settings["ratio_mode"] = "16:9"
            w, h = 1920, 1080
        self.width_spin.setValue(w)
        self.height_spin.setValue(h)
        self.settings["portrait_width"] = w
        self.settings["portrait_height"] = h
        self.settings["lock_ratio"] = was_locked
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self._update_ratio_label()

    def _update_ratio_label(self) -> None:
        if self.settings.get("lock_ratio", True):
            mode = self.settings.get("ratio_mode", "9:16")
            if mode == "9:16":
                self.ratio_label.setText("Ratio: 9:16 (Portrait – YouTube Shorts/TikTok/Instagram)")
            else:
                self.ratio_label.setText("Ratio: 16:9 (Landscape – YouTube/Standard Video)")
        else:
            w, h = self.width_spin.value(), self.height_spin.value()
            self.ratio_label.setText(f"Custom dimensions: {w} × {h} px (ratio unlocked)")

    def _update_last_region_label(self) -> None:
        parts = []
        for mode, label in [("9:16", "Portrait (9:16)"), ("16:9", "Landscape (16:9)")]:
            rect = self.settings.get(f"last_capture_rect_{mode}")
            if rect:
                parts.append(f"{label}: {rect['width']}×{rect['height']} at ({rect['x']}, {rect['y']})")
        self.last_region_label.setText(
            "Last regions: " + " | ".join(parts) if parts else "No previous capture regions saved"
        )

    # ── Profile management ─────────────────────────────────────────────────────

    def _snapshot_ui_to_settings(self) -> None:
        """Flush all UI control values into self.settings before snapshotting."""
        self.settings["hotkey"] = self.hotkey_input.text()
        self.settings["save_location"] = self.save_input.text()
        self.settings["file_prefix"] = self.prefix_input.text()
        self.settings["portrait_width"] = self.width_spin.value()
        self.settings["portrait_height"] = self.height_spin.value()
        self.settings["lock_ratio"] = self.lock_ratio_checkbox.isChecked()
        self.settings["ratio_mode"] = "9:16" if self.ratio_9_16.isChecked() else "16:9"
        self.settings["copy_to_clipboard"] = self.copy_to_clipboard_checkbox.isChecked()

    def _refresh_profile_combo(self) -> None:
        current = self.profile_combo.currentText()
        self.profile_combo.clear()
        self.profile_combo.addItem("— select profile —")
        for name in cfg.list_profiles(self.settings):
            self.profile_combo.addItem(name)
        idx = self.profile_combo.findText(current)
        self.profile_combo.setCurrentIndex(idx if idx >= 0 else 0)

    def _save_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "Save Profile", "Profile name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        self._snapshot_ui_to_settings()
        cfg.save_profile(self.settings, name)
        self._refresh_profile_combo()
        idx = self.profile_combo.findText(name)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        QMessageBox.information(self, "Profile Saved", f'Profile "{name}" saved successfully!')

    def _load_profile(self) -> None:
        name = self.profile_combo.currentText()
        if name == "— select profile —" or not name:
            QMessageBox.warning(self, "No Profile Selected", "Please select a profile first.")
            return
        if not cfg.load_profile(self.settings, name):
            QMessageBox.warning(self, "Profile Not Found", f'Profile "{name}" could not be found.')
            return
        # Refresh UI
        self.hotkey_input.setText(self.settings.get("hotkey", "ctrl+shift+p"))
        self.save_input.setText(self.settings.get("save_location", ""))
        self.prefix_input.setText(self.settings.get("file_prefix", ""))
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(self.settings.get("portrait_width", 607))
        self.height_spin.setValue(self.settings.get("portrait_height", 1080))
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self.lock_ratio_checkbox.setChecked(self.settings.get("lock_ratio", True))
        (self.ratio_9_16 if self.settings.get("ratio_mode", "9:16") == "9:16"
         else self.ratio_16_9).setChecked(True)
        self.copy_to_clipboard_checkbox.setChecked(self.settings.get("copy_to_clipboard", True))
        self._update_ratio_label()
        self._update_last_region_label()
        old_hotkey = self.settings.get("hotkey")
        cfg.save(self.settings)
        if old_hotkey != self.hotkey_input.text():
            self._register_hotkey()
        QMessageBox.information(self, "Profile Loaded", f'Profile "{name}" loaded successfully!')

    def _delete_profile(self) -> None:
        name = self.profile_combo.currentText()
        if name == "— select profile —" or not name:
            QMessageBox.warning(self, "No Profile Selected", "Please select a profile first.")
            return
        reply = QMessageBox.question(self, "Delete Profile",
                                     f'Are you sure you want to delete "{name}"?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        cfg.delete_profile(self.settings, name)
        self._refresh_profile_combo()

    # ── App lifecycle ──────────────────────────────────────────────────────────

    def _quit_app(self) -> None:
        if QMessageBox.question(self, "Exit", "Are you sure you want to exit?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.close()

    def closeEvent(self, event) -> None:
        if self.is_exiting:
            event.accept()
            return
        self.is_exiting = True
        try:
            if self.hotkey_thread is not None:
                self.hotkey_thread.stop()
                self.hotkey_thread = None
        except Exception as exc:
            logger.error(f"Error stopping hotkey thread: {exc}")
        if self.overlay and self.overlay.isVisible():
            self.overlay.close()
        try:
            self.tray_icon.hide()
        except Exception as exc:
            logger.error(f"Error hiding tray icon: {exc}")
        event.accept()
        QTimer.singleShot(100, __import__("PyQt5.QtWidgets", fromlist=["QApplication"]).QApplication.quit)

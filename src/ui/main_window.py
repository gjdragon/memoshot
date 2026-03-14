"""
ui/main_window.py
~~~~~~~~~~~~~~~~~
Main application window — two-panel design:

  Quick Capture panel  (default, compact)
    • Full-width Capture button showing the hotkey
    • One-line last-capture status card
    • Platform preset dropdown
    • Icon toolbar: ⚙ Settings  |  _ Minimize  |  ✕ Exit

  Settings panel  (opens on ⚙, replaces the Quick panel)
    Three tabs — Capture / Output / Profiles
    Close button returns to Quick panel.

All data concerns: core.settings
Hotkey management:  core.hotkey
"""

import core.settings as cfg
from core.hotkey import HotkeyThread
from ui.overlay import CaptureOverlay
from utils.logger import get_logger
from version import __version__
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAction,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
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
    QStackedWidget,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

logger = get_logger(__name__)

APP_VERSION = __version__

# ── Platform presets ───────────────────────────────────────────────────────────
# (name, width, height)
PLATFORM_PRESETS = [
    ("Custom",               None, None),
    ("TikTok / IG Story",    1080, 1920),
    ("YouTube Shorts",       1080, 1920),
    ("IG Feed (square)",     1080, 1080),
    ("LinkedIn Banner",      1584,  396),
    ("Twitter / X Header",   1500,  500),
    ("YouTube Thumbnail",    1280,  720),
]

# ── Stylesheet constants ───────────────────────────────────────────────────────
_PURPLE        = "#9333ea"
_PURPLE_DARK   = "#7e22ce"
_SURFACE       = "#f8f7ff"
_BORDER        = "#e2e0ee"
_TEXT_MUTED    = "#64748b"
_TEXT_PRIMARY  = "#1e1b4b"
_SUCCESS       = "#10b981"
_DANGER        = "#dc2626"
_DANGER_DARK   = "#b91c1c"

STYLE_CAPTURE_BTN = f"""
QPushButton {{
    background-color: {_PURPLE};
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    font-weight: bold;
    padding: 16px 24px;
}}
QPushButton:hover  {{ background-color: {_PURPLE_DARK}; }}
QPushButton:pressed {{ background-color: {_PURPLE_DARK}; padding-top: 17px; }}
"""

STYLE_ICON_BTN = f"""
QPushButton {{
    background-color: transparent;
    color: {_TEXT_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    font-size: 14px;
    padding: 5px 10px;
}}
QPushButton:hover  {{ background-color: {_SURFACE}; color: {_TEXT_PRIMARY}; }}
QPushButton:pressed {{ background-color: {_BORDER}; }}
"""

STYLE_EXIT_BTN = f"""
QPushButton {{
    background-color: transparent;
    color: {_DANGER};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    font-size: 14px;
    padding: 5px 10px;
}}
QPushButton:hover  {{ background-color: #fef2f2; border-color: {_DANGER}; }}
QPushButton:pressed {{ background-color: #fee2e2; }}
"""

STYLE_CLOSE_BTN = f"""
QPushButton {{
    background-color: transparent;
    color: {_TEXT_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    font-size: 12px;
    padding: 4px 12px;
}}
QPushButton:hover  {{ background-color: {_SURFACE}; color: {_TEXT_PRIMARY}; }}
"""

STYLE_STATUS_CARD = f"""
QFrame {{
    background-color: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 8px;
}}
"""

STYLE_TAB = f"""
QTabWidget::pane {{
    border: 1px solid {_BORDER};
    border-radius: 6px;
    background: white;
}}
QTabBar::tab {{
    padding: 6px 18px;
    color: {_TEXT_MUTED};
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
    font-size: 12px;
}}
QTabBar::tab:selected {{
    color: {_PURPLE};
    border-bottom: 2px solid {_PURPLE};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{ color: {_TEXT_PRIMARY}; }}
"""

STYLE_AUTOSAVE = f"color: {_SUCCESS}; font-size: 10px; font-style: italic;"
STYLE_LABEL_MUTED = f"color: {_TEXT_MUTED}; font-size: 10px;"
STYLE_LABEL_HINT  = f"color: {_SUCCESS}; font-size: 10px; font-style: italic;"
STYLE_SECTION_HDR = f"color: {_TEXT_PRIMARY}; font-size: 11px; font-weight: bold;"


class PortraitScreenshotApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = cfg.load()
        self.overlay: Optional[CaptureOverlay] = None
        self.hotkey_thread: Optional[HotkeyThread] = None
        self.is_exiting = False

        # Debounce timer — 600 ms after the last change
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._flush_auto_save)

        self.setWindowTitle(f"MemoShot v{APP_VERSION}")
        # Fixed width; height is determined by content
        self.setFixedWidth(380)

        self._init_ui()
        self._init_tray()

        QTimer.singleShot(500, self._register_hotkey)

    # ══════════════════════════════════════════════════════════════════════════
    # UI construction
    # ══════════════════════════════════════════════════════════════════════════

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # QStackedWidget holds Quick panel (index 0) and Settings panel (index 1)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_quick_panel())
        self.stack.addWidget(self._build_settings_panel())
        self.stack.setCurrentIndex(0)

        root.addWidget(self.stack)
        self.adjustSize()

    # ── Quick Capture panel ────────────────────────────────────────────────────

    def _build_quick_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)

        # App title
        title = QLabel("MemoShot")
        title.setStyleSheet(
            f"font-size: 17px; font-weight: bold; color: {_TEXT_PRIMARY};"
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # ── Big Capture button ─────────────────────────────────────────────────
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()
        self.capture_btn = QPushButton(f"Capture  —  {hotkey}")
        self.capture_btn.setStyleSheet(STYLE_CAPTURE_BTN)
        self.capture_btn.setMinimumHeight(58)
        self.capture_btn.clicked.connect(self.start_capture)
        layout.addWidget(self.capture_btn)

        # ── Status card ────────────────────────────────────────────────────────
        status_frame = QFrame()
        status_frame.setStyleSheet(STYLE_STATUS_CARD)
        sf_layout = QVBoxLayout(status_frame)
        sf_layout.setContentsMargins(12, 8, 12, 8)
        sf_layout.setSpacing(3)

        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 12px;")
        self.status_label.setAlignment(Qt.AlignLeft)
        sf_layout.addWidget(self.status_label)

        self.status_sub = QLabel("No previous capture")
        self.status_sub.setStyleSheet(STYLE_LABEL_MUTED)
        sf_layout.addWidget(self.status_sub)

        layout.addWidget(status_frame)
        self._refresh_status_card()

        # ── Platform preset dropdown ───────────────────────────────────────────
        preset_row = QHBoxLayout()
        preset_lbl = QLabel("Preset:")
        preset_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
        preset_row.addWidget(preset_lbl)

        self.preset_combo = QComboBox()
        self.preset_combo.setStyleSheet(f"font-size: 12px;")
        for name, w, h in PLATFORM_PRESETS:
            label = name if w is None else f"{name}  ({w}×{h})"
            self.preset_combo.addItem(label)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self._sync_preset_combo()
        preset_row.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_row)

        # ── Icon toolbar: ⚙  |  Minimize  |  Exit ─────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        settings_btn = QPushButton("⚙  Settings")
        settings_btn.setStyleSheet(STYLE_ICON_BTN)
        settings_btn.setToolTip("Open settings")
        settings_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        toolbar.addWidget(settings_btn)

        toolbar.addStretch()

        minimize_btn = QPushButton("_ Tray")
        minimize_btn.setStyleSheet(STYLE_ICON_BTN)
        minimize_btn.setToolTip("Minimize to system tray")
        minimize_btn.clicked.connect(self.hide)
        toolbar.addWidget(minimize_btn)

        exit_btn = QPushButton("✕ Exit")
        exit_btn.setStyleSheet(STYLE_EXIT_BTN)
        exit_btn.setToolTip("Exit MemoShot")
        exit_btn.clicked.connect(self._quit_app)
        toolbar.addWidget(exit_btn)

        layout.addLayout(toolbar)

        return panel

    # ── Settings panel ─────────────────────────────────────────────────────────

    def _build_settings_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # Header row: "Settings" title + ← Back button
        hdr = QHBoxLayout()
        hdr_title = QLabel("Settings")
        hdr_title.setStyleSheet(
            f"font-size: 15px; font-weight: bold; color: {_TEXT_PRIMARY};"
        )
        hdr.addWidget(hdr_title)
        hdr.addStretch()

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(STYLE_CLOSE_BTN)
        back_btn.clicked.connect(self._close_settings)
        hdr.addWidget(back_btn)
        layout.addLayout(hdr)

        # ── Tab widget ─────────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(STYLE_TAB)
        self.tabs.addTab(self._build_tab_capture(), "Capture")
        self.tabs.addTab(self._build_tab_output(),  "Output")
        self.tabs.addTab(self._build_tab_profiles(), "Profiles")
        layout.addWidget(self.tabs)

        # Auto-save indicator
        self.autosave_label = QLabel("✔  Settings saved")
        self.autosave_label.setStyleSheet(STYLE_AUTOSAVE)
        self.autosave_label.setAlignment(Qt.AlignRight)
        self.autosave_label.setVisible(False)
        layout.addWidget(self.autosave_label)

        return panel

    # ── Tab: Capture ──────────────────────────────────────────────────────────

    def _build_tab_capture(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Hotkey
        layout.addWidget(self._section_label("Hotkey"))
        self.hotkey_input = QLineEdit(self.settings["hotkey"])
        self.hotkey_input.setPlaceholderText("e.g., ctrl+shift+p")
        self.hotkey_input.editingFinished.connect(self._schedule_auto_save)
        layout.addWidget(self.hotkey_input)

        layout.addWidget(self._divider())

        # Aspect ratio
        layout.addWidget(self._section_label("Aspect ratio"))
        ratio_row = QHBoxLayout()
        self.ratio_group = QButtonGroup()
        self.ratio_9_16 = QRadioButton("9:16  Portrait")
        self.ratio_16_9 = QRadioButton("16:9  Landscape")
        self.ratio_group.addButton(self.ratio_9_16)
        self.ratio_group.addButton(self.ratio_16_9)
        (self.ratio_9_16 if self.settings.get("ratio_mode", "9:16") == "9:16"
         else self.ratio_16_9).setChecked(True)
        self.ratio_9_16.toggled.connect(self._on_ratio_mode_changed)
        self.ratio_16_9.toggled.connect(self._on_ratio_mode_changed)
        self.ratio_9_16.toggled.connect(self._schedule_auto_save)
        self.ratio_16_9.toggled.connect(self._schedule_auto_save)
        ratio_row.addWidget(self.ratio_9_16)
        ratio_row.addWidget(self.ratio_16_9)
        ratio_row.addStretch()
        layout.addLayout(ratio_row)

        # Lock ratio checkbox
        self.lock_ratio_checkbox = QCheckBox("Lock aspect ratio")
        self.lock_ratio_checkbox.setChecked(self.settings.get("lock_ratio", True))
        self.lock_ratio_checkbox.stateChanged.connect(self._on_lock_ratio_changed)
        self.lock_ratio_checkbox.stateChanged.connect(self._schedule_auto_save)
        layout.addWidget(self.lock_ratio_checkbox)

        layout.addWidget(self._divider())

        # Dimensions
        layout.addWidget(self._section_label("Dimensions"))
        dim_row = QHBoxLayout()
        dim_row.setSpacing(8)
        dim_row.addWidget(QLabel("W:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 4000)
        self.width_spin.setValue(self.settings["portrait_width"])
        self.width_spin.valueChanged.connect(self._on_width_changed)
        self.width_spin.valueChanged.connect(self._schedule_auto_save)
        dim_row.addWidget(self.width_spin)
        dim_row.addWidget(QLabel("H:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 4000)
        self.height_spin.setValue(self.settings["portrait_height"])
        self.height_spin.valueChanged.connect(self._on_height_changed)
        self.height_spin.valueChanged.connect(self._schedule_auto_save)
        dim_row.addWidget(self.height_spin)
        dim_row.addWidget(QLabel("px"))
        dim_row.addStretch()
        layout.addLayout(dim_row)

        self.ratio_label = QLabel()
        self.ratio_label.setStyleSheet(STYLE_LABEL_HINT)
        layout.addWidget(self.ratio_label)
        self._on_lock_ratio_changed()   # sets enabled state + initial label

        layout.addStretch()
        return tab

    # ── Tab: Output ───────────────────────────────────────────────────────────

    def _build_tab_output(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Save folder
        layout.addWidget(self._section_label("Save folder"))
        folder_row = QHBoxLayout()
        self.save_input = QLineEdit(self.settings["save_location"])
        self.save_input.editingFinished.connect(self._schedule_auto_save)
        browse_btn = QPushButton("Browse…")
        browse_btn.setStyleSheet(STYLE_ICON_BTN)
        browse_btn.setFixedWidth(72)
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.save_input, 1)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)

        layout.addWidget(self._divider())

        # File prefix
        layout.addWidget(self._section_label("File prefix"))
        self.prefix_input = QLineEdit(self.settings.get("file_prefix", ""))
        self.prefix_input.setPlaceholderText("Empty = timestamp  |  prefix1.png, prefix2.png…")
        self.prefix_input.editingFinished.connect(self._schedule_auto_save)
        layout.addWidget(self.prefix_input)

        layout.addWidget(self._divider())

        # Clipboard
        layout.addWidget(self._section_label("Clipboard"))
        self.copy_to_clipboard_checkbox = QCheckBox("Copy each screenshot to clipboard")
        self.copy_to_clipboard_checkbox.setChecked(self.settings.get("copy_to_clipboard", True))
        self.copy_to_clipboard_checkbox.stateChanged.connect(self._schedule_auto_save)
        layout.addWidget(self.copy_to_clipboard_checkbox)

        layout.addStretch()
        return tab

    # ── Tab: Profiles ─────────────────────────────────────────────────────────

    def _build_tab_profiles(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        layout.addWidget(self._section_label("Saved profiles"))

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("— select profile —")
        for name in cfg.list_profiles(self.settings):
            self.profile_combo.addItem(name)
        layout.addWidget(self.profile_combo)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for label, slot in [("Load", self._load_profile),
                             ("Save as…", self._save_profile),
                             ("Delete", self._delete_profile)]:
            btn = QPushButton(label)
            btn.setStyleSheet(STYLE_ICON_BTN)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        hint = QLabel(
            "Profiles save a complete snapshot of all settings —\n"
            "hotkey, folder, prefix, dimensions, ratio, clipboard."
        )
        hint.setStyleSheet(STYLE_LABEL_MUTED)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch()
        return tab

    # ── Helper widgets ─────────────────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(STYLE_SECTION_HDR)
        return lbl

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {_BORDER};")
        return line

    # ══════════════════════════════════════════════════════════════════════════
    # Panel navigation
    # ══════════════════════════════════════════════════════════════════════════

    def _close_settings(self) -> None:
        """Return to Quick Capture and refresh anything the user may have changed."""
        self._refresh_status_card()
        self._sync_preset_combo()
        # Update the Capture button label in case the hotkey changed
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()
        self.capture_btn.setText(f"Capture  —  {hotkey}")
        self.stack.setCurrentIndex(0)
        self.adjustSize()

    # ══════════════════════════════════════════════════════════════════════════
    # Status card & preset helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_status_card(self) -> None:
        """Update the one-line status card on the Quick Capture panel."""
        mode = self.settings.get("ratio_mode", "9:16")
        w = self.settings.get("portrait_width", 607)
        h = self.settings.get("portrait_height", 1080)
        mode_label = "Portrait (9:16)" if mode == "9:16" else "Landscape (16:9)"

        rect = self.settings.get(f"last_capture_rect_{mode}")
        if rect:
            self.status_label.setText(
                f"{rect['width']} × {rect['height']} px  ·  {mode_label}"
            )
            self.status_sub.setText(
                f"Last region at ({rect['x']}, {rect['y']})"
            )
        else:
            self.status_label.setText(f"{w} × {h} px  ·  {mode_label}")
            self.status_sub.setText("No previous capture")

    def _sync_preset_combo(self) -> None:
        """Set the preset combo to match current width/height, or 'Custom'."""
        w = self.settings.get("portrait_width")
        h = self.settings.get("portrait_height")
        for i, (_, pw, ph) in enumerate(PLATFORM_PRESETS):
            if pw == w and ph == h:
                self.preset_combo.blockSignals(True)
                self.preset_combo.setCurrentIndex(i)
                self.preset_combo.blockSignals(False)
                return
        # No match → Custom
        self.preset_combo.blockSignals(True)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.blockSignals(False)

    def _on_preset_changed(self, index: int) -> None:
        _, w, h = PLATFORM_PRESETS[index]
        if w is None:
            return  # Custom — don't touch dimensions
        # Push dimensions into settings and spin-boxes
        self.settings["portrait_width"]  = w
        self.settings["portrait_height"] = h
        self.settings["lock_ratio"] = False   # preset sets exact pixels; ratio free
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(w)
        self.height_spin.setValue(h)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self.lock_ratio_checkbox.blockSignals(True)
        self.lock_ratio_checkbox.setChecked(False)
        self.lock_ratio_checkbox.blockSignals(False)
        self._update_ratio_label()
        self._refresh_status_card()
        self._schedule_auto_save()

    # ══════════════════════════════════════════════════════════════════════════
    # Tray
    # ══════════════════════════════════════════════════════════════════════════

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
        self.tray_icon.setToolTip(
            f"MemoShot\nPress {self.settings['hotkey'].upper()}"
        )

    def _on_tray_click(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger and not self.isVisible():
            self.show()
            self.activateWindow()

    # ══════════════════════════════════════════════════════════════════════════
    # Hotkey management
    # ══════════════════════════════════════════════════════════════════════════

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
            QMessageBox.warning(
                self, "Hotkey Error",
                f"Could not register hotkey: {self.settings['hotkey']}\n{exc}"
            )

    # ══════════════════════════════════════════════════════════════════════════
    # Capture flow
    # ══════════════════════════════════════════════════════════════════════════

    def start_capture(self) -> None:
        if self.is_exiting:
            return
        try:
            if self.overlay is None or not self.overlay.isVisible():
                self.overlay = CaptureOverlay(self.settings)
                self.overlay.capture_signal.connect(self._on_capture_complete)
                self.overlay.update_ui_dimensions.connect(
                    self._on_overlay_dimensions_changed
                )
                self.overlay.show()
                self.overlay.activateWindow()
                self.overlay.raise_()
        except Exception as exc:
            logger.error(f"Error starting capture: {exc}")

    def _on_capture_complete(self, rect) -> None:
        self._refresh_status_card()
        cfg.save(self.settings)

    def _on_overlay_dimensions_changed(self, width: int, height: int) -> None:
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self._update_ratio_label()
        self._sync_preset_combo()
        self._refresh_status_card()

    # ══════════════════════════════════════════════════════════════════════════
    # Auto-save
    # ══════════════════════════════════════════════════════════════════════════

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
            hotkey = self.settings["hotkey"].upper()
            self.capture_btn.setText(f"Capture  —  {hotkey}")
        self.tray_icon.setToolTip(
            f"MemoShot\nPress {self.settings['hotkey'].upper()}"
        )
        logger.info("Settings auto-saved")
        self.autosave_label.setVisible(True)
        QTimer.singleShot(2500, lambda: self.autosave_label.setVisible(False))

    # ══════════════════════════════════════════════════════════════════════════
    # Settings helpers
    # ══════════════════════════════════════════════════════════════════════════

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
        self.settings["portrait_width"]  = w
        self.settings["portrait_height"] = h
        self.settings["lock_ratio"] = was_locked
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self._update_ratio_label()

    def _update_ratio_label(self) -> None:
        if self.settings.get("lock_ratio", True):
            mode = self.settings.get("ratio_mode", "9:16")
            text = (
                "9:16  —  YouTube Shorts / TikTok / Instagram"
                if mode == "9:16"
                else "16:9  —  YouTube / standard video"
            )
        else:
            w = self.width_spin.value()
            h = self.height_spin.value()
            text = f"Custom  {w} × {h} px  (ratio unlocked)"
        self.ratio_label.setText(text)

    # ══════════════════════════════════════════════════════════════════════════
    # Profile management
    # ══════════════════════════════════════════════════════════════════════════

    def _snapshot_ui_to_settings(self) -> None:
        """Flush all UI control values into self.settings."""
        self.settings["hotkey"]           = self.hotkey_input.text()
        self.settings["save_location"]    = self.save_input.text()
        self.settings["file_prefix"]      = self.prefix_input.text()
        self.settings["portrait_width"]   = self.width_spin.value()
        self.settings["portrait_height"]  = self.height_spin.value()
        self.settings["lock_ratio"]       = self.lock_ratio_checkbox.isChecked()
        self.settings["ratio_mode"]       = "9:16" if self.ratio_9_16.isChecked() else "16:9"
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
        QMessageBox.information(
            self, "Profile Saved", f'Profile "{name}" saved successfully!'
        )

    def _load_profile(self) -> None:
        name = self.profile_combo.currentText()
        if name == "— select profile —" or not name:
            QMessageBox.warning(self, "No Profile Selected", "Please select a profile first.")
            return
        if not cfg.load_profile(self.settings, name):
            QMessageBox.warning(
                self, "Profile Not Found", f'Profile "{name}" could not be found.'
            )
            return
        # Push profile values back into every UI control
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
        self.copy_to_clipboard_checkbox.setChecked(
            self.settings.get("copy_to_clipboard", True)
        )
        self._update_ratio_label()
        self._refresh_status_card()
        self._sync_preset_combo()
        old_hotkey = self.settings.get("hotkey")
        cfg.save(self.settings)
        if old_hotkey != self.hotkey_input.text():
            self._register_hotkey()
        QMessageBox.information(
            self, "Profile Loaded", f'Profile "{name}" loaded successfully!'
        )

    def _delete_profile(self) -> None:
        name = self.profile_combo.currentText()
        if name == "— select profile —" or not name:
            QMessageBox.warning(self, "No Profile Selected", "Please select a profile first.")
            return
        reply = QMessageBox.question(
            self, "Delete Profile",
            f'Are you sure you want to delete "{name}"?',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        cfg.delete_profile(self.settings, name)
        self._refresh_profile_combo()

    # ══════════════════════════════════════════════════════════════════════════
    # App lifecycle
    # ══════════════════════════════════════════════════════════════════════════

    def _quit_app(self) -> None:
        if (
            QMessageBox.question(
                self, "Exit", "Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
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
        QTimer.singleShot(
            100,
            __import__("PyQt5.QtWidgets", fromlist=["QApplication"]).QApplication.quit,
        )

"""
ui/main_window.py
~~~~~~~~~~~~~~~~~
Main application window — two-panel design.
All 13 UX improvements applied.
"""

import os
import subprocess
import sys

import core.settings as cfg
from core.settings import CAPTURE_MODES
from core.hotkey import HotkeyThread
from ui.overlay import CaptureOverlay
from ui.window_overlay import WindowCaptureOverlay, grab_desktop_pixmap, get_window_list, _get_memoshot_hwnd
from utils.logger import get_logger, apply_log_settings, current_log_path
from version import __version__
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap
from PyQt5.QtWidgets import (
    QAction, QButtonGroup, QCheckBox, QComboBox, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMenu, QMessageBox, QPushButton, QRadioButton, QSpinBox, QStackedWidget,
    QSystemTrayIcon, QTabWidget, QVBoxLayout, QWidget,
)

logger = get_logger(__name__)
APP_VERSION = __version__

# ── Design system ─────────────────────────────────────────────────────────────
# Tone: refined utilitarian. Dark graphite header, warm off-white body,
# ink-blue primary, hairline borders. Every radius is 4 px — sharp but
# not harsh. Typography leans slightly small and tight for a tool aesthetic.

_ACCENT       = "#1a56db"   # ink blue — primary action
_ACCENT_HOVER = "#1648c0"   # slightly darker on hover
_ACCENT_LIGHT = "#eef2ff"   # very pale blue tint for selections / pills
_ACCENT_BORDER= "#c7d7fc"   # border on blue-tinted surfaces

_HDR_BG       = "#18202e"   # deep graphite — header bar
_HDR_BORDER   = "#252f42"   # subtle rule below header
_HDR_TEXT     = "#e8edf5"   # near-white header text
_HDR_MUTED    = "#5a6a85"   # version / secondary header text

_WIN_BG       = "#f5f6f8"   # warm off-white window background
_SURFACE      = "#ffffff"   # card / input surfaces
_SURFACE_ALT  = "#f0f2f5"   # alternating / hover surface

_BORDER       = "#dde1e9"   # default hairline border
_BORDER_MED   = "#c4cad6"   # slightly stronger border on hover

_TEXT_PRIMARY = "#111827"   # near-black body text
_TEXT_MUTED   = "#4b5563"   # secondary text
_TEXT_HINT    = "#9ca3af"   # placeholder / hint text

_SUCCESS      = "#0d7e4a"   # success green (darker, more serious)
_SUCCESS_BG   = "#f0fdf6"
_SUCCESS_BDR  = "#a7f3cf"

_WARN         = "#92580a"   # amber warning text
_WARN_BG      = "#fffbeb"
_WARN_BDR     = "#fde68a"

_DANGER       = "#b91c1c"   # muted red — less alarming than #dc2626

# Keep these aliases so existing references resolve without change
_BLUE         = _ACCENT
_BLUE_HOVER   = _ACCENT_HOVER
_BLUE_LIGHT   = _ACCENT_LIGHT
_BLUE_BORDER  = _ACCENT_BORDER

STYLE_WINDOW = f"background-color: {_WIN_BG};"

STYLE_HEADER = f"""
QWidget {{
    background-color: {_HDR_BG};
    border-bottom: 1px solid {_HDR_BORDER};
}}
"""

STYLE_CAPTURE_BTN = f"""
QPushButton {{
    background-color: {_ACCENT};
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 600;
    padding: 13px 20px;
    letter-spacing: 0.2px;
}}
QPushButton:hover   {{ background-color: {_ACCENT_HOVER}; }}
QPushButton:pressed {{ background-color: {_ACCENT_HOVER}; padding-top: 14px; }}
"""

STYLE_ICON_BTN = f"""
QPushButton {{
    background-color: {_SURFACE};
    color: {_TEXT_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 4px;
    font-size: 12px;
    padding: 5px 11px;
}}
QPushButton:hover  {{ background-color: {_SURFACE_ALT}; color: {_TEXT_PRIMARY};
                      border-color: {_BORDER_MED}; }}
QPushButton:pressed {{ background-color: {_BORDER}; }}
"""

STYLE_PRIMARY_SM = f"""
QPushButton {{
    background-color: {_ACCENT};
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 12px;
    padding: 5px 14px;
    font-weight: 500;
}}
QPushButton:hover   {{ background-color: {_ACCENT_HOVER}; }}
QPushButton:pressed {{ background-color: {_ACCENT_HOVER}; }}
QPushButton:disabled {{ background-color: {_BORDER}; color: {_TEXT_HINT}; }}
"""

STYLE_DANGER_SM = f"""
QPushButton {{
    background-color: transparent;
    color: {_DANGER};
    border: 1px solid {_BORDER};
    border-radius: 4px;
    font-size: 12px;
    padding: 5px 12px;
}}
QPushButton:hover  {{ background-color: #fef2f2; border-color: #fca5a5; }}
QPushButton:pressed {{ background-color: #fee2e2; }}
QPushButton:disabled {{ color: {_TEXT_HINT}; border-color: {_BORDER}; }}
"""

STYLE_EXIT_LINK = f"""
QPushButton {{
    background-color: transparent;
    color: {_TEXT_HINT};
    border: none;
    font-size: 12px;
    padding: 5px 8px;
}}
QPushButton:hover  {{ color: {_DANGER}; }}
QPushButton:pressed {{ color: {_DANGER}; }}
"""

STYLE_PROFILE_LIST = f"""
QListWidget {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 4px;
    outline: none;
    padding: 2px;
    font-size: 12px;
    color: {_TEXT_PRIMARY};
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: 3px;
    border: none;
}}
QListWidget::item:hover {{
    background: {_SURFACE_ALT};
}}
QListWidget::item:selected {{
    background: {_ACCENT_LIGHT};
    color: {_ACCENT};
    font-weight: 600;
}}
"""

STYLE_TAB = f"""
QTabWidget {{ background: transparent; }}
QTabWidget::pane {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 0px 0px 4px 4px;
    top: -1px;
}}
QTabBar::tab {{
    background: {_WIN_BG};
    color: {_TEXT_HINT};
    border: 1px solid {_BORDER};
    border-bottom: 1px solid {_BORDER};
    border-radius: 4px 4px 0 0;
    padding: 6px 0px;
    min-width: 84px;
    max-width: 84px;
    margin-right: 1px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.3px;
    qproperty-alignment: AlignCenter;
}}
QTabBar::tab:selected {{
    background: {_SURFACE};
    color: {_ACCENT};
    font-weight: 600;
    border-color: {_BORDER};
    border-bottom: 2px solid {_ACCENT};
}}
QTabBar::tab:!selected {{ margin-top: 2px; }}
QTabBar::tab:hover:!selected {{
    color: {_TEXT_MUTED};
    background: {_SURFACE_ALT};
}}
"""

STYLE_SECTION_HDR = (
    f"color: {_TEXT_HINT}; font-size: 10px; font-weight: 600; letter-spacing: 0.8px;"
)

STYLE_SAVE_FOOTER = f"""
QFrame {{
    background-color: {_WIN_BG};
    border: none;
    border-top: 1px solid {_BORDER};
    border-radius: 0px;
}}
"""

STYLE_LABEL_MUTED = f"color: {_TEXT_HINT}; font-size: 11px;"
STYLE_LABEL_HINT  = f"color: {_SUCCESS}; font-size: 11px;"
STYLE_AUTOSAVE    = f"color: {_SUCCESS}; font-size: 10px; font-style: italic;"

STYLE_HOTKEY_IDLE = f"""
QLineEdit {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 4px;
    padding: 7px 10px;
    font-size: 12px;
    color: {_TEXT_PRIMARY};
}}
QLineEdit:hover {{ border-color: {_BORDER_MED}; }}
"""

STYLE_HOTKEY_RECORDING = f"""
QLineEdit {{
    background: {_ACCENT_LIGHT};
    border: 2px solid {_ACCENT};
    border-radius: 4px;
    padding: 7px 10px;
    font-size: 12px;
    color: {_ACCENT_HOVER};
    font-weight: 600;
}}
"""

_MODIFIER_KEYS = {
    Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta,
    Qt.Key_AltGr, Qt.Key_Super_L, Qt.Key_Super_R,
}
_KEY_NAMES = {
    Qt.Key_F1:"f1", Qt.Key_F2:"f2", Qt.Key_F3:"f3", Qt.Key_F4:"f4",
    Qt.Key_F5:"f5", Qt.Key_F6:"f6", Qt.Key_F7:"f7", Qt.Key_F8:"f8",
    Qt.Key_F9:"f9", Qt.Key_F10:"f10", Qt.Key_F11:"f11", Qt.Key_F12:"f12",
    Qt.Key_F13:"f13", Qt.Key_F14:"f14", Qt.Key_F15:"f15",
    Qt.Key_Escape:"esc", Qt.Key_Tab:"tab",
    Qt.Key_Return:"enter", Qt.Key_Enter:"enter",
    Qt.Key_Backspace:"backspace", Qt.Key_Delete:"delete",
    Qt.Key_Insert:"insert", Qt.Key_Home:"home", Qt.Key_End:"end",
    Qt.Key_PageUp:"page up", Qt.Key_PageDown:"page down",
    Qt.Key_Left:"left", Qt.Key_Right:"right", Qt.Key_Up:"up", Qt.Key_Down:"down",
    Qt.Key_Print:"print screen", Qt.Key_ScrollLock:"scroll lock",
    Qt.Key_Pause:"pause", Qt.Key_NumLock:"num lock",
    Qt.Key_CapsLock:"caps lock", Qt.Key_Space:"space",
}


class HotkeyCapture(QLineEdit):
    def __init__(self, initial: str, parent=None) -> None:
        super().__init__(initial, parent)
        self._recording = False
        self._saved_value = initial
        self.setReadOnly(True)
        self.setStyleSheet(STYLE_HOTKEY_IDLE)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click to record — then press your key combination")

    def mousePressEvent(self, event) -> None:
        self._cancel_recording() if self._recording else self._start_recording()

    def keyPressEvent(self, event) -> None:
        if not self._recording or event.isAutoRepeat():
            return
        key = event.key()
        if key == Qt.Key_Escape:
            self._cancel_recording(); return
        if key in _MODIFIER_KEYS:
            self.setText(self._build_combo(event, partial=True)); return
        combo = self._build_combo(event, partial=False)
        if combo:
            self._saved_value = combo
            self.setText(combo)
        self._stop_recording()

    def focusOutEvent(self, event) -> None:
        if self._recording:
            self._cancel_recording()
        super().focusOutEvent(event)

    def value(self) -> str:
        return self._saved_value if self._recording else self.text()

    def _start_recording(self) -> None:
        self._saved_value = self.text()
        self._recording = True
        self.setStyleSheet(STYLE_HOTKEY_RECORDING)
        self.setText("Press keys…")
        self.setFocus()
        self.grabKeyboard()

    def _stop_recording(self) -> None:
        self._recording = False
        self.releaseKeyboard()
        self.setStyleSheet(STYLE_HOTKEY_IDLE)
        self.clearFocus()

    def _cancel_recording(self) -> None:
        self.setText(self._saved_value)
        self._stop_recording()

    @staticmethod
    def _build_combo(event, *, partial: bool) -> str:
        parts = []
        mods = event.modifiers()
        if mods & Qt.ControlModifier: parts.append("ctrl")
        if mods & Qt.AltModifier:     parts.append("alt")
        if mods & Qt.ShiftModifier:   parts.append("shift")
        if mods & Qt.MetaModifier:    parts.append("win")
        if not partial:
            key = event.key()
            if key in _KEY_NAMES:
                parts.append(_KEY_NAMES[key])
            elif 32 <= key <= 126:
                parts.append(chr(key).lower())
            elif event.text():
                parts.append(event.text().lower())
        return "+".join(parts) if parts else ""


class PortraitScreenshotApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = cfg.load()
        self.overlay: Optional[CaptureOverlay] = None
        self.hotkey_thread: Optional[HotkeyThread] = None
        self.is_exiting = False
        self._active_profile: Optional[str] = None
        self._return_to_settings: bool = False
        self._pending_overwrite: bool = False

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._flush_auto_save)

        self.setWindowTitle("MemoShot")
        self.setFixedWidth(400)
        self.setStyleSheet(STYLE_WINDOW)

        self._init_ui()
        self._init_tray()
        QTimer.singleShot(500, self._register_hotkey)
        # Auto-load "Default" profile if it exists
        QTimer.singleShot(600, self._load_default_profile_on_startup)

    # ── UI construction ───────────────────────────────────────────────────────

    def _init_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_quick_panel())
        self.stack.addWidget(self._build_settings_panel())
        self.stack.setCurrentIndex(0)
        root.addWidget(self.stack)
        self.adjustSize()

    # ── Quick panel ───────────────────────────────────────────────────────────

    def _build_quick_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(STYLE_WINDOW)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header_bar())

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(20, 16, 20, 14)
        layout.setSpacing(6)

        # Issue #4: active-profile pill
        self.active_profile_bar = QWidget()
        self.active_profile_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {_ACCENT_LIGHT};
                border: 1px solid {_ACCENT_BORDER};
                border-radius: 4px;
            }}
        """)
        pill_row = QHBoxLayout(self.active_profile_bar)
        pill_row.setContentsMargins(10, 5, 10, 5)
        pill_row.setSpacing(6)
        pill_icon = QLabel("◈")
        pill_icon.setStyleSheet(f"color: {_BLUE}; font-size: 11px; background: transparent;")
        pill_row.addWidget(pill_icon)
        self.active_profile_lbl = QLabel()
        self.active_profile_lbl.setStyleSheet(
            f"color: {_BLUE}; font-size: 11px; font-weight: 600; background: transparent;"
        )
        pill_row.addWidget(self.active_profile_lbl, 1)
        layout.addWidget(self.active_profile_bar)
        self._refresh_active_profile_bar()

        # Capture button
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()
        self.capture_btn = QPushButton(f"  Capture  —  {hotkey}")
        self.capture_btn.setStyleSheet(STYLE_CAPTURE_BTN)
        self.capture_btn.setMinimumHeight(52)
        self.capture_btn.clicked.connect(self.start_capture)
        layout.addWidget(self.capture_btn)

        # Status card
        self._status_card_frame = QFrame()
        self._status_card_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {_SURFACE};
                border: 1px solid {_BORDER};
                border-radius: 4px;
            }}
        """)
        sf = QVBoxLayout(self._status_card_frame)
        sf.setContentsMargins(12, 8, 12, 8)
        sf.setSpacing(2)
        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 12px; font-weight: 600; letter-spacing: 0.1px;"
        )
        self.status_sub = QLabel()
        self.status_sub.setStyleSheet(STYLE_LABEL_MUTED)
        sf.addWidget(self.status_label)
        sf.addWidget(self.status_sub)
        layout.addWidget(self._status_card_frame)
        self._refresh_status_card()

        # Profile list
        prof_hdr = QLabel("PROFILES")
        prof_hdr.setStyleSheet(
            f"color: {_TEXT_HINT}; font-size: 10px; font-weight: bold; letter-spacing: 1px;"
        )
        layout.addWidget(prof_hdr)

        self.profile_list = QListWidget()
        self.profile_list.setStyleSheet(STYLE_PROFILE_LIST)
        self.profile_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.profile_list.itemClicked.connect(self._on_profile_list_clicked)
        layout.addWidget(self.profile_list, 1)
        self._rebuild_profile_list()

        # Issue #5: normalised toolbar with Exit as text link
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        for label, style, slot, tip in [
            ("⚙  Settings",    STYLE_ICON_BTN, lambda: self.stack.setCurrentIndex(1), "Open settings"),
            ("📂  Open folder", STYLE_ICON_BTN, self._open_save_folder,                "Open screenshots folder"),
            ("⬜  Tray",        STYLE_ICON_BTN, self.hide,                             "Minimize to tray"),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(style)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            toolbar.addWidget(btn, 1)
        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet(STYLE_EXIT_LINK)
        exit_btn.setToolTip("Exit MemoShot")
        exit_btn.clicked.connect(self._quit_app)
        toolbar.addWidget(exit_btn)
        layout.addLayout(toolbar)

        outer.addWidget(body)
        return panel

    # ── Settings panel ────────────────────────────────────────────────────────

    def _build_settings_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(STYLE_WINDOW)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._build_header_bar(with_back=True))

        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Issue #8: fixed min height so window doesn't jump between tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(STYLE_TAB)
        self.tabs.setMinimumHeight(280)
        self.tabs.addTab(self._build_tab_capture(),  "Capture")
        self.tabs.addTab(self._build_tab_output(),   "Output")
        self.tabs.addTab(self._build_tab_profiles(), "Profiles")
        self.tabs.addTab(self._build_tab_logging(),  "Logging")
        layout.addWidget(self.tabs)

        # Footer
        footer_frame = QFrame()
        footer_frame.setStyleSheet(STYLE_SAVE_FOOTER)
        footer_outer = QVBoxLayout(footer_frame)
        footer_outer.setContentsMargins(12, 10, 12, 10)
        footer_outer.setSpacing(8)

        test_row = QHBoxLayout()
        test_row.setSpacing(8)
        test_btn = QPushButton("▶  Test capture")
        test_btn.setStyleSheet(STYLE_PRIMARY_SM)
        test_btn.clicked.connect(self._test_capture_from_settings)
        test_row.addWidget(test_btn)
        self.settings_status_lbl = QLabel()
        self.settings_status_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 11px;")
        self.settings_status_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._refresh_settings_status_lbl()
        test_row.addWidget(self.settings_status_lbl, 1)
        footer_outer.addLayout(test_row)

        div = QWidget()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {_BORDER};")
        footer_outer.addWidget(div)

        save_row = QHBoxLayout()
        save_row.setSpacing(6)
        save_lbl = QLabel("Save as profile:")
        save_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 11px;")
        save_lbl.setFixedWidth(90)
        save_row.addWidget(save_lbl)
        self.footer_profile_name = QLineEdit()
        self.footer_profile_name.setPlaceholderText("Profile name…")
        self.footer_profile_name.setStyleSheet(f"""
            QLineEdit {{
                background: {_SURFACE}; border: 1px solid {_BORDER};
                border-radius: 4px; padding: 5px 9px; font-size: 12px; color: {_TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ border-color: {_ACCENT}; }}
        """)
        self.footer_profile_name.returnPressed.connect(self._save_profile_from_footer)
        save_row.addWidget(self.footer_profile_name, 1)
        footer_save_btn = QPushButton("Save")
        footer_save_btn.setStyleSheet(STYLE_PRIMARY_SM)
        footer_save_btn.clicked.connect(self._save_profile_from_footer)
        save_row.addWidget(footer_save_btn)
        footer_outer.addLayout(save_row)

        # Issue #9: inline overwrite warning
        self.footer_overwrite_lbl = QLabel()
        self.footer_overwrite_lbl.setStyleSheet(
            f"color: {_WARN}; font-size: 11px; background: {_WARN_BG}; "
            f"border: 1px solid {_WARN_BDR}; border-radius: 4px; padding: 3px 8px;"
        )
        self.footer_overwrite_lbl.setVisible(False)
        footer_outer.addWidget(self.footer_overwrite_lbl)

        layout.addWidget(footer_frame)

        self.autosave_label = QLabel("✔  Settings saved")
        self.autosave_label.setAlignment(Qt.AlignRight)
        # Always in layout — hidden via transparent colour, not setVisible,
        # so the window height never shifts when it appears/disappears.
        self.autosave_label.setStyleSheet("color: transparent; font-size: 10px; font-style: italic;")
        layout.addWidget(self.autosave_label)

        outer.addWidget(body)
        return panel

    # ── Header bar ────────────────────────────────────────────────────────────

    def _build_header_bar(self, with_back: bool = False) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(STYLE_HEADER)
        bar.setFixedHeight(40)
        row = QHBoxLayout(bar)
        row.setContentsMargins(14, 0, 14, 0)
        row.setSpacing(8)
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {_BLUE}; font-size: 10px; background: transparent;")
        row.addWidget(dot)
        name_lbl = QLabel("MemoShot")
        name_lbl.setStyleSheet(
            f"color: {_HDR_TEXT}; font-size: 13px; font-weight: bold;"
            f" background: transparent; letter-spacing: 0.5px;"
        )
        row.addWidget(name_lbl)
        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet(f"color: {_HDR_MUTED}; font-size: 11px; background: transparent;")
        row.addWidget(ver_lbl)
        row.addStretch()
        if with_back:
            back_btn = QPushButton("← Back")
            back_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {_HDR_MUTED};
                    border: 1px solid {_HDR_BORDER}; border-radius: 4px;
                    font-size: 11px; padding: 3px 10px;
                }}
                QPushButton:hover {{ color: {_HDR_TEXT}; border-color: #3a4a65; }}
            """)
            back_btn.clicked.connect(self._close_settings)
            row.addWidget(back_btn)
        return bar

    # ── Tab: Capture ──────────────────────────────────────────────────────────

    def _build_tab_capture(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background: {_SURFACE};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Capture mode selector ─────────────────────────────────────────────
        layout.setSpacing(0)   # manual spacing throughout for full control
        layout.addLayout(self._section_row(
            "Capture mode",
            "Region: drag to select any rectangular area on screen.\n"
            "Window: click a window to capture it — the border is detected automatically.",
        ))
        layout.addSpacing(8)
        mode_row = QHBoxLayout()
        mode_row.setSpacing(6)
        self.mode_group = QButtonGroup()
        _MODE_LABELS = {
            "region": "📐  Region",
            "window": "🪟  Window",
        }
        self._mode_buttons: dict = {}
        current_mode = self.settings.get("capture_mode", "region")
        for mode_key in CAPTURE_MODES:
            btn = QPushButton(_MODE_LABELS.get(mode_key, mode_key.title()))
            btn.setCheckable(True)
            btn.setChecked(mode_key == current_mode)
            btn.setStyleSheet(self._mode_btn_style(mode_key == current_mode))
            btn.clicked.connect(lambda checked, k=mode_key: self._on_mode_selected(k))
            self.mode_group.addButton(btn)
            self._mode_buttons[mode_key] = btn
            mode_row.addWidget(btn)
        mode_row.addStretch()
        layout.addLayout(mode_row)
        layout.addSpacing(6)

        mode_desc = QLabel()
        mode_desc.setStyleSheet(STYLE_LABEL_MUTED)
        mode_desc.setWordWrap(True)
        self._mode_desc_label = mode_desc
        layout.addWidget(mode_desc)

        layout.addSpacing(10)
        layout.addWidget(self._divider())
        layout.addSpacing(10)

        # ── Hotkey ────────────────────────────────────────────────────────────
        layout.addLayout(self._section_row(
            "Hotkey",
            "Global shortcut key — applies to all profiles.\n"
            "Click the field and press any key combination (e.g. F12, Ctrl+Shift+S).\n"
            "Changes take effect immediately and are saved automatically.",
        ))
        layout.addSpacing(8)
        self.hotkey_input = HotkeyCapture(self.settings["hotkey"])
        self.hotkey_input.installEventFilter(self)
        layout.addWidget(self.hotkey_input)

        layout.addSpacing(10)
        layout.addWidget(self._divider())
        layout.addSpacing(10)

        # ── Confirmation ──────────────────────────────────────────────────────
        layout.addLayout(self._section_row(
            "Confirmation",
            "When enabled, pressing the hotkey opens the capture box so you can\n"
            "reposition it before confirming with Enter — useful while setting up.\n"
            "Disable this on a trusted profile to capture instantly with no extra step.\n"
            "Note: Test Capture always requires confirmation regardless of this setting.",
        ))
        layout.addSpacing(8)
        self.confirm_capture_checkbox = QCheckBox("Require Enter to confirm each capture")
        self.confirm_capture_checkbox.setChecked(
            self.settings.get("confirm_capture", True)
        )
        self.confirm_capture_checkbox.stateChanged.connect(self._schedule_auto_save)
        layout.addWidget(self.confirm_capture_checkbox)

        # ── Region-only settings (hidden for other modes) ─────────────────────
        # No margins on the container itself — the outer layout's spacing (12px)
        # provides the gap above. Internal spacing matches the outer layout so
        # sections feel consistent whether region settings are visible or not.
        self._region_settings_widget = QWidget()
        rsl = QVBoxLayout(self._region_settings_widget)
        rsl.setContentsMargins(0, 0, 0, 0)
        rsl.setSpacing(0)   # manual spacing via addSpacing() for full control

        rsl.addWidget(self._divider())
        rsl.addSpacing(10)
        rsl.addLayout(self._section_row(
            "Aspect ratio",
            "9:16 Portrait — for YouTube Shorts, TikTok, Instagram Reels.\n"
            "16:9 Landscape — for standard YouTube videos and presentations.\n"
            "Lock ratio keeps width and height proportional as you resize.",
        ))
        rsl.addSpacing(8)
        ratio_row = QHBoxLayout()
        self.ratio_group = QButtonGroup()
        self.ratio_9_16 = QRadioButton("9:16  Portrait")
        self.ratio_16_9 = QRadioButton("16:9  Landscape")
        self.ratio_group.addButton(self.ratio_9_16)
        self.ratio_group.addButton(self.ratio_16_9)
        (self.ratio_9_16 if self.settings.get("ratio_mode", "9:16") == "9:16"
         else self.ratio_16_9).setChecked(True)
        for rb in (self.ratio_9_16, self.ratio_16_9):
            rb.toggled.connect(self._on_ratio_mode_changed)
            rb.toggled.connect(self._schedule_auto_save)
        ratio_row.addWidget(self.ratio_9_16)
        ratio_row.addWidget(self.ratio_16_9)
        ratio_row.addStretch()
        rsl.addLayout(ratio_row)
        rsl.addSpacing(6)

        self.lock_ratio_checkbox = QCheckBox("Lock aspect ratio")
        self.lock_ratio_checkbox.setChecked(self.settings.get("lock_ratio", True))
        self.lock_ratio_checkbox.stateChanged.connect(self._on_lock_ratio_changed)
        self.lock_ratio_checkbox.stateChanged.connect(self._schedule_auto_save)
        rsl.addWidget(self.lock_ratio_checkbox)

        rsl.addSpacing(10)
        rsl.addWidget(self._divider())
        rsl.addSpacing(10)
        rsl.addLayout(self._section_row(
            "Dimensions",
            "Width and height of the capture box in pixels.\n"
            "With ratio locked, changing one value adjusts the other automatically.\n"
            "You can also resize the box directly by dragging its edges on screen.",
        ))
        rsl.addSpacing(8)
        dim_row = QHBoxLayout()
        dim_row.setSpacing(8)
        for lbl_text, attr, on_change in [
            ("W", "width_spin",  self._on_width_changed),
            ("H", "height_spin", self._on_height_changed),
        ]:
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
            spin = QSpinBox()
            spin.setRange(100, 4000)
            spin.setValue(
                self.settings["portrait_width"]
                if lbl_text == "W" else self.settings["portrait_height"]
            )
            spin.valueChanged.connect(on_change)
            spin.valueChanged.connect(self._schedule_auto_save)
            setattr(self, attr, spin)
            dim_row.addWidget(lbl)
            dim_row.addWidget(spin)
        px_lbl = QLabel("px")
        px_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
        dim_row.addWidget(px_lbl)
        dim_row.addStretch()
        rsl.addLayout(dim_row)
        rsl.addSpacing(4)

        self.ratio_label = QLabel()
        self.ratio_label.setStyleSheet(STYLE_LABEL_HINT)
        rsl.addWidget(self.ratio_label)

        layout.addWidget(self._region_settings_widget)
        layout.addStretch()

        # Initialise display for current mode
        self._on_lock_ratio_changed()
        self._refresh_mode_ui(current_mode)
        return tab

    @staticmethod
    def _mode_btn_style(active: bool) -> str:
        if active:
            return f"""
                QPushButton {{
                    background-color: {_BLUE}; color: white;
                    border: none; border-radius: 5px;
                    font-size: 12px; padding: 5px 14px;
                    font-weight: bold;
                }}
            """
        return f"""
            QPushButton {{
                background-color: {_SURFACE}; color: {_TEXT_MUTED};
                border: 1px solid {_BORDER}; border-radius: 5px;
                font-size: 12px; padding: 5px 14px;
            }}
            QPushButton:hover {{ background-color: {_WIN_BG}; color: {_TEXT_PRIMARY};
                                 border-color: {_BORDER_MED}; }}
        """

    def _on_mode_selected(self, mode_key: str) -> None:
        """Called when the user clicks a mode button in the Capture tab."""
        self.settings["capture_mode"] = mode_key
        for k, btn in self._mode_buttons.items():
            btn.setStyleSheet(self._mode_btn_style(k == mode_key))
            btn.setChecked(k == mode_key)
        self._refresh_mode_ui(mode_key)
        self._refresh_active_profile_bar()
        self._schedule_auto_save()

    def _refresh_mode_ui(self, mode_key: str) -> None:
        """Show/hide mode-specific settings and update the description label."""
        _MODE_DESCRIPTIONS = {
            "region": "Drag to select any rectangular area on screen.",
            "window": "Click a window to capture it — the window border is detected automatically.",
        }
        self._mode_desc_label.setText(_MODE_DESCRIPTIONS.get(mode_key, ""))
        # Region-specific settings only shown in region mode
        self._region_settings_widget.setVisible(mode_key == "region")

    # ── Tab: Output ───────────────────────────────────────────────────────────

    def _build_tab_output(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background: {_SURFACE};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(self._section_row(
            "Save folder",
            "Folder where screenshots are saved.\n"
            "Each profile can have its own save location.",
        ))
        folder_row = QHBoxLayout()
        self.save_input = QLineEdit(self.settings["save_location"])
        self.save_input.editingFinished.connect(self._schedule_auto_save)
        browse_btn = QPushButton("Browse…")
        browse_btn.setStyleSheet(STYLE_ICON_BTN)
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(self.save_input, 1)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)
        layout.addWidget(self._divider())

        # Issue #12: clearer prefix field with live example preview
        layout.addLayout(self._section_row(
            "File prefix",
            "Optional prefix added to the start of every saved filename.\n"
            "Leave empty to use timestamps (e.g. 20240315_143022.png).\n"
            "With a prefix: myshot_001.png, myshot_002.png, …",
        ))
        self.prefix_input = QLineEdit(self.settings.get("file_prefix", ""))
        self.prefix_input.setPlaceholderText("Leave empty to use timestamps")
        self.prefix_input.editingFinished.connect(self._schedule_auto_save)
        self.prefix_input.textChanged.connect(self._refresh_prefix_example)
        layout.addWidget(self.prefix_input)
        self.prefix_example_lbl = QLabel()
        self.prefix_example_lbl.setStyleSheet(f"color: {_TEXT_HINT}; font-size: 11px;")
        layout.addWidget(self.prefix_example_lbl)
        self._refresh_prefix_example(self.prefix_input.text())

        layout.addWidget(self._divider())
        layout.addLayout(self._section_row(
            "Clipboard",
            "When enabled, each screenshot is also copied to the clipboard\n"
            "so you can paste it directly into any app straight after capture.",
        ))
        self.copy_to_clipboard_checkbox = QCheckBox("Copy each screenshot to clipboard")
        self.copy_to_clipboard_checkbox.setChecked(
            self.settings.get("copy_to_clipboard", True)
        )
        self.copy_to_clipboard_checkbox.stateChanged.connect(self._schedule_auto_save)
        layout.addWidget(self.copy_to_clipboard_checkbox)
        layout.addStretch()
        return tab

    def _refresh_prefix_example(self, text: str) -> None:
        """Live example label (issue #12)."""
        if not hasattr(self, "prefix_example_lbl"):
            return
        if text.strip():
            self.prefix_example_lbl.setText(
                f"→  e.g.  {text.strip()}_001.png,  {text.strip()}_002.png"
            )
        else:
            self.prefix_example_lbl.setText(
                "→  e.g.  20240315_143022.png  (timestamp default)"
            )

    # ── Tab: Profiles ─────────────────────────────────────────────────────────

    def _build_tab_profiles(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background: {_SURFACE};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addLayout(self._section_row(
            "Your profiles",
            "Profiles save your capture settings so you can switch between setups instantly.\n"
            "Click a profile to load it. To create one: adjust settings, type a name\n"
            "in the footer box and press Save. A profile named 'Default' loads automatically\n"
            "every time the app starts.",
        ))
        layout.addSpacing(4)

        # Profile list — stretch=1 so it fills all available vertical space
        self.settings_profile_list = QListWidget()
        self.settings_profile_list.setStyleSheet(STYLE_PROFILE_LIST)
        self.settings_profile_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.settings_profile_list.itemClicked.connect(
            self._on_settings_profile_list_clicked
        )
        layout.addWidget(self.settings_profile_list, 1)

        # Action row: Delete + Edit buttons + selection label
        action_row = QHBoxLayout()
        action_row.setSpacing(6)
        self.sp_delete_btn = QPushButton("Delete")
        self.sp_delete_btn.setStyleSheet(STYLE_DANGER_SM)
        self.sp_delete_btn.setEnabled(False)
        self.sp_delete_btn.clicked.connect(self._delete_selected_profile)
        action_row.addWidget(self.sp_delete_btn)

        self.sp_edit_btn = QPushButton("✏  Edit")
        self.sp_edit_btn.setStyleSheet(STYLE_PRIMARY_SM)
        self.sp_edit_btn.setEnabled(False)
        self.sp_edit_btn.setToolTip(
            "Load this profile's settings into all tabs so you can modify them,\n"
            "then save back under the same name using the footer Save button."
        )
        self.sp_edit_btn.clicked.connect(self._edit_selected_profile)
        action_row.addWidget(self.sp_edit_btn)

        action_row.addStretch()
        self.sp_status_lbl = QLabel()
        self.sp_status_lbl.setStyleSheet(STYLE_LABEL_MUTED)
        action_row.addWidget(self.sp_status_lbl)
        layout.addLayout(action_row)

        # Inline detail card — shown when a profile is selected
        self.sp_detail_card = QFrame()
        self.sp_detail_card.setStyleSheet(f"""
            QFrame {{
                background: {_SURFACE_ALT};
                border: 1px solid {_BORDER};
                border-radius: 4px;
            }}
        """)
        detail_layout = QVBoxLayout(self.sp_detail_card)
        detail_layout.setContentsMargins(10, 8, 10, 8)
        detail_layout.setSpacing(3)
        self.sp_detail_lbl = QLabel()
        self.sp_detail_lbl.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; background: transparent;"
        )
        self.sp_detail_lbl.setWordWrap(True)
        detail_layout.addWidget(self.sp_detail_lbl)
        self.sp_detail_card.setVisible(False)
        layout.addWidget(self.sp_detail_card)

        # Populate list now that all dependent widgets exist
        self._rebuild_settings_profile_list()

        return tab

    # ── Tab: Logging ──────────────────────────────────────────────────────────

    def _build_tab_logging(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background: {_SURFACE};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        layout.addLayout(self._section_row(
            "Logging",
            "When enabled, MemoShot writes a log file recording key events.\n"
            "Useful for diagnosing issues. Logs are stored in the Log folder below.",
        ))
        self.logging_enabled_checkbox = QCheckBox("Enable logging to file")
        self.logging_enabled_checkbox.setChecked(
            self.settings.get("logging_enabled", True)
        )
        self.logging_enabled_checkbox.stateChanged.connect(self._on_logging_setting_changed)
        layout.addWidget(self.logging_enabled_checkbox)
        layout.addWidget(self._divider())
        layout.addLayout(self._section_row(
            "Log level",
            "INFO: records key events (captures, profile loads, errors).\n"
            "DEBUG: records every interaction — much more verbose, use when diagnosing a bug.",
        ))
        level_row = QHBoxLayout()
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["INFO", "DEBUG"])
        saved_level = self.settings.get("log_level", "INFO").upper()
        self.log_level_combo.setCurrentText(
            saved_level if saved_level in ("INFO", "DEBUG") else "INFO"
        )
        self.log_level_combo.setFixedWidth(100)
        self.log_level_combo.currentTextChanged.connect(self._on_logging_setting_changed)
        level_row.addWidget(self.log_level_combo)
        level_row.addStretch()
        layout.addLayout(level_row)
        layout.addWidget(self._divider())
        layout.addLayout(self._section_row(
            "Log folder",
            "Where log files are written.\n"
            "Files are named log_memoshot_YYYYMMDD_HHMMSS.txt\n"
            "Max 1 MB per file — 5 rotating backups kept automatically.\n"
            "Leave empty to use the default Logs/ folder inside the app directory.",
        ))
        log_folder_row = QHBoxLayout()
        default_folder = self._default_log_folder_display()
        self.log_folder_input = QLineEdit(
            self.settings.get("log_folder", "") or default_folder
        )
        self.log_folder_input.editingFinished.connect(self._on_logging_setting_changed)
        log_browse_btn = QPushButton("Browse…")
        log_browse_btn.setStyleSheet(STYLE_ICON_BTN)
        log_browse_btn.setFixedWidth(80)
        log_browse_btn.clicked.connect(self._browse_log_folder)
        log_folder_row.addWidget(self.log_folder_input, 1)
        log_folder_row.addWidget(log_browse_btn)
        layout.addLayout(log_folder_row)
        layout.addWidget(self._divider())
        layout.addLayout(self._section_row(
            "Current session",
            "The log file being written for this session.\n"
            "Click the path to select and copy it.",
        ))
        self.current_log_lbl = QLabel()
        self.current_log_lbl.setStyleSheet(STYLE_LABEL_MUTED)
        self.current_log_lbl.setWordWrap(False)
        self.current_log_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._refresh_current_log_label()
        layout.addWidget(self.current_log_lbl)
        open_log_btn = QPushButton("📂  Open log folder")
        open_log_btn.setStyleSheet(STYLE_ICON_BTN)
        open_log_btn.clicked.connect(self._open_log_folder)
        layout.addWidget(open_log_btn)
        layout.addStretch()
        return tab

    @staticmethod
    def _inline_hint(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {_TEXT_HINT}; font-size: 11px;")
        return lbl

    @staticmethod
    def _default_log_folder_display() -> str:
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(base)
            return os.path.join(src_dir, "Logs")
        except Exception:
            return os.path.join(os.path.expanduser("~"), ".memoshot", "Logs")

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(STYLE_SECTION_HDR)
        return lbl

    @staticmethod
    def _help_badge(tooltip: str) -> QLabel:
        """Small circled ? that shows a tooltip on hover. Zero layout cost."""
        badge = QLabel("?")
        badge.setFixedSize(14, 14)
        badge.setAlignment(Qt.AlignCenter)
        badge.setStyleSheet(f"""
            QLabel {{
                color: {_TEXT_HINT};
                background: {_SURFACE_ALT};
                border: 1px solid {_BORDER};
                border-radius: 7px;
                font-size: 9px;
                font-weight: 600;
            }}
            QLabel:hover {{
                color: {_ACCENT};
                border-color: {_ACCENT};
                background: {_ACCENT_LIGHT};
            }}
        """)
        badge.setToolTip(tooltip)
        return badge

    @classmethod
    def _section_row(cls, text: str, tooltip: str = "") -> QHBoxLayout:
        """Section header row: label + optional help badge, no bottom spacing."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(5)
        row.addWidget(cls._section_label(text))
        if tooltip:
            row.addWidget(cls._help_badge(tooltip))
        row.addStretch()
        return row

    @staticmethod
    def _inline_hint(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {_TEXT_HINT}; font-size: 11px;")
        return lbl

    @staticmethod
    def _divider() -> QWidget:
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {_BORDER};")
        return line

    def eventFilter(self, obj, event) -> bool:
        from PyQt5.QtCore import QEvent
        if obj is self.hotkey_input and event.type() == QEvent.FocusOut:
            if not self.hotkey_input._recording:
                self._schedule_auto_save()
        return super().eventFilter(obj, event)

    # ── Active-profile pill (issue #4) ────────────────────────────────────────

    def _refresh_active_profile_bar(self) -> None:
        if not hasattr(self, "active_profile_bar"):
            return
        if self._active_profile:
            mode = self.settings.get("capture_mode", "region")
            mode_badge = {"region": "📐", "window": "🪟"}.get(mode, mode)
            self.active_profile_lbl.setText(
                f"Using: {self._active_profile}  ·  {mode_badge} {mode}"
            )
            self.active_profile_bar.setVisible(True)
        else:
            self.active_profile_bar.setVisible(False)

    # ── Profile list helpers ──────────────────────────────────────────────────

    def _rebuild_profile_list(self) -> None:
        self.profile_list.blockSignals(True)
        self.profile_list.clear()
        profiles = cfg.list_profiles(self.settings)
        if profiles:
            for name in profiles:
                item = QListWidgetItem(name)
                self.profile_list.addItem(item)
                if name == self._active_profile:
                    item.setSelected(True)
                    self.profile_list.setCurrentItem(item)
        else:
            placeholder = QListWidgetItem("No profiles yet — go to Settings to create one")
            placeholder.setFlags(Qt.NoItemFlags)
            placeholder.setForeground(QColor(_TEXT_HINT))
            self.profile_list.addItem(placeholder)
        self.profile_list.blockSignals(False)

    def _rebuild_settings_profile_list(self) -> None:
        self.settings_profile_list.blockSignals(True)
        self.settings_profile_list.clear()
        profiles = cfg.list_profiles(self.settings)
        if profiles:
            for name in profiles:
                item = QListWidgetItem(name)
                self.settings_profile_list.addItem(item)
                if name == self._active_profile:
                    item.setSelected(True)
                    self.settings_profile_list.setCurrentItem(item)
        else:
            placeholder = QListWidgetItem("No profiles yet")
            placeholder.setFlags(Qt.NoItemFlags)
            placeholder.setForeground(QColor(_TEXT_HINT))
            self.settings_profile_list.addItem(placeholder)
        self._update_settings_profile_buttons()
        # Refresh detail card for the currently selected item (if any)
        selected = self.settings_profile_list.currentItem()
        if selected and (selected.flags() & Qt.ItemIsSelectable):
            self._refresh_profile_detail_card(selected.text())
        else:
            if hasattr(self, "sp_detail_card"):
                self.sp_detail_card.setVisible(False)
        self.settings_profile_list.blockSignals(False)

    def _rebuild_all_profile_lists(self) -> None:
        self._rebuild_profile_list()
        self._rebuild_settings_profile_list()

    def _update_settings_profile_buttons(self) -> None:
        selected = self.settings_profile_list.currentItem()
        has_selection = bool(selected and selected.flags() & Qt.ItemIsSelectable)
        self.sp_delete_btn.setEnabled(has_selection)
        self.sp_edit_btn.setEnabled(has_selection)
        if has_selection:
            name = selected.text()
            self.sp_status_lbl.setText(f"Selected: {name}")
            self._refresh_profile_detail_card(name)
        else:
            self.sp_status_lbl.setText("")
            self.sp_detail_card.setVisible(False)

    def _refresh_profile_detail_card(self, name: str) -> None:
        """Populate and show the inline detail card for the named profile."""
        data = self.settings.get("profiles", {}).get(name)
        if not data:
            self.sp_detail_card.setVisible(False)
            return
        mode     = data.get("capture_mode", "region").title()
        folder   = data.get("save_location", "—")
        w        = data.get("portrait_width", "?")
        h        = data.get("portrait_height", "?")
        prefix   = data.get("file_prefix", "") or "—"
        confirm  = "Yes" if data.get("confirm_capture", True) else "No (instant)"
        clipboard = "Yes" if data.get("copy_to_clipboard", True) else "No"
        # Shorten long folder paths for display
        max_len = 38
        if len(folder) > max_len:
            folder = "…" + folder[-(max_len - 1):]
        lines = [
            f"Mode: {mode}   ·   Size: {w} × {h} px",
            f"Save to: {folder}",
            f"Prefix: {prefix}   ·   Clipboard: {clipboard}   ·   Confirm: {confirm}",
        ]
        self.sp_detail_lbl.setText("\n".join(lines))
        self.sp_detail_card.setVisible(True)

    # ── Profile actions ───────────────────────────────────────────────────────

    def _on_profile_list_clicked(self, item: QListWidgetItem) -> None:
        if not (item.flags() & Qt.ItemIsSelectable):
            return
        self._load_profile_by_name(item.text())

    def _on_settings_profile_list_clicked(self, item: QListWidgetItem) -> None:
        """Issue #1: Settings list now loads immediately like the Quick panel."""
        if not (item.flags() & Qt.ItemIsSelectable):
            return
        self._update_settings_profile_buttons()
        self._load_profile_by_name(item.text())

    def _delete_selected_profile(self) -> None:
        item = self.settings_profile_list.currentItem()
        if not item or not (item.flags() & Qt.ItemIsSelectable):
            return
        name = item.text()
        reply = QMessageBox.question(
            self, "Delete profile",
            f'Delete "{name}"?  This cannot be undone.',
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        cfg.delete_profile(self.settings, name)
        if self._active_profile == name:
            self._active_profile = None
        self._rebuild_all_profile_lists()
        self._refresh_active_profile_bar()
        self.sp_status_lbl.setText("")

    def _edit_selected_profile(self) -> None:
        """Load the selected profile into all settings tabs and pre-fill the
        footer name box so the user can modify settings and save back in one click."""
        item = self.settings_profile_list.currentItem()
        if not item or not (item.flags() & Qt.ItemIsSelectable):
            return
        name = item.text()
        # Load the profile so all tab widgets reflect its values
        self._load_profile_by_name(name)
        # Pre-fill the footer save box with the profile name so Save overwrites it
        self.footer_profile_name.setText(name)
        # Switch to the Capture tab so the user sees the settings immediately
        self.tabs.setCurrentIndex(0)
        # Show an inline prompt in the autosave label area
        self.autosave_label.setText(f'✏  Editing "{name}" — make changes then press Save')
        self.autosave_label.setStyleSheet(
            f"color: {_WARN}; font-size: 10px; font-style: italic;"
        )
        QTimer.singleShot(6000, self._reset_autosave_label)

    # ── Save as profile (issue #9: overwrite warning) ─────────────────────────

    def _save_profile_from_footer(self) -> None:
        name = self.footer_profile_name.text().strip()
        if not name:
            self.footer_profile_name.setFocus()
            return
        existing_profiles = cfg.list_profiles(self.settings)
        if name in existing_profiles:
            if not self._pending_overwrite:
                self._pending_overwrite = True
                self.footer_overwrite_lbl.setText(
                    f'⚠  "{name}" already exists — press Save again to overwrite'
                )
                self.footer_overwrite_lbl.setVisible(True)
                QTimer.singleShot(4000, self._clear_overwrite_warning)
                return
        self._pending_overwrite = False
        self.footer_overwrite_lbl.setVisible(False)
        self._snapshot_ui_to_settings()
        cfg.save_profile(self.settings, name)
        self._active_profile = name
        self._rebuild_all_profile_lists()
        self._refresh_active_profile_bar()
        self.footer_profile_name.clear()
        self.autosave_label.setText(f'✔  Profile "{name}" saved')
        self._autosave_show()
        QTimer.singleShot(3000, self._reset_autosave_label)

    def _clear_overwrite_warning(self) -> None:
        self._pending_overwrite = False
        self.footer_overwrite_lbl.setVisible(False)

    # ── Core profile load ─────────────────────────────────────────────────────

    def _load_profile_by_name(self, name: str) -> None:
        if not cfg.load_profile(self.settings, name):
            QMessageBox.warning(self, "Not found", f'Profile "{name}" could not be loaded.')
            return
        self.hotkey_input.setText(self.settings.get("hotkey", "ctrl+shift+p"))
        self.hotkey_input._saved_value = self.settings.get("hotkey", "ctrl+shift+p")
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
        self.confirm_capture_checkbox.setChecked(
            self.settings.get("confirm_capture", True)
        )
        # Restore capture mode — sync buttons in the Capture tab
        loaded_mode = self.settings.get("capture_mode", "region")
        for k, btn in self._mode_buttons.items():
            btn.setChecked(k == loaded_mode)
            btn.setStyleSheet(self._mode_btn_style(k == loaded_mode))
        self._refresh_mode_ui(loaded_mode)
        self._update_ratio_label()
        self._refresh_status_card()
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()
        self.capture_btn.setText(f"  Capture  —  {hotkey}")
        cfg.save(self.settings)
        self._register_hotkey()
        self._active_profile = name
        self._rebuild_all_profile_lists()
        self._refresh_active_profile_bar()
        # Issue #2: flash status card to confirm the load
        self._flash_status_card()

    # ── Panel navigation ──────────────────────────────────────────────────────

    def _close_settings(self) -> None:
        self._refresh_status_card()
        self._rebuild_profile_list()
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()
        self.capture_btn.setText(f"  Capture  —  {hotkey}")
        self.stack.setCurrentIndex(0)
        self.adjustSize()

    # ── Status card (issue #2: flash; issue #7: first-run hint) ──────────────

    def _refresh_status_card(self) -> None:
        capture_mode = self.settings.get("capture_mode", "region")
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()

        if capture_mode == "window":
            self.status_label.setText("Window capture mode")
            self.status_sub.setText(
                f"Press {hotkey} then click a window to capture it"
            )
            return

        # Region mode (default)
        mode  = self.settings.get("ratio_mode", "9:16")
        w     = self.settings.get("portrait_width",  607)
        h     = self.settings.get("portrait_height", 1080)
        mlbl  = "Portrait (9:16)" if mode == "9:16" else "Landscape (16:9)"
        rect  = self.settings.get(f"last_capture_rect_{mode}")
        if rect:
            self.status_label.setText(
                f"{rect['width']} × {rect['height']} px  ·  {mlbl}"
            )
            self.status_sub.setText(f"Last region at ({rect['x']}, {rect['y']})")
        else:
            self.status_label.setText(f"{w} × {h} px  ·  {mlbl}")
            self.status_sub.setText(
                f"Press {hotkey} from any app to start your first capture"
            )

    def _flash_status_card(self) -> None:
        """Brief green flash to confirm an action (issue #2)."""
        try:
            card = self._status_card_frame
            if card is None:
                return
            original_style = card.styleSheet()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {_SUCCESS_BG};
                    border: 1px solid {_SUCCESS_BDR};
                    border-radius: 4px;
                }}
            """)
            QTimer.singleShot(
                600,
                lambda: card.setStyleSheet(original_style) if card else None,
            )
        except Exception:
            pass

    # ── Tray (issue #13: camera silhouette icon) ──────────────────────────────

    def _init_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._build_tray_icon())
        menu = QMenu()
        for label, slot in [("Capture", self.start_capture), ("Show Window", self.show)]:
            a = QAction(label, self)
            a.triggered.connect(slot)
            menu.addAction(a)
        menu.addSeparator()
        qa = QAction("Exit", self)
        qa.triggered.connect(self._quit_app)
        menu.addAction(qa)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._on_tray_click)
        self.tray_icon.show()
        self.tray_icon.setToolTip(
            f"MemoShot\nPress {self.settings['hotkey'].upper()}"
        )

    @staticmethod
    def _build_tray_icon() -> QIcon:
        """Camera silhouette recognisable at 16-32 px (issue #13)."""
        size = 64
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        blue  = QColor(37, 99, 235)
        white = QColor(255, 255, 255)
        # Camera body
        p.setBrush(blue)
        p.setPen(Qt.NoPen)
        body = QPainterPath()
        body.addRoundedRect(4, 18, 56, 38, 6, 6)
        p.drawPath(body)
        # Viewfinder bump
        bump = QPainterPath()
        bump.addRoundedRect(22, 12, 20, 10, 4, 4)
        p.drawPath(bump)
        # Lens outer ring (white)
        p.setBrush(white)
        p.drawEllipse(20, 24, 24, 24)
        # Lens inner (blue)
        p.setBrush(blue)
        p.drawEllipse(25, 29, 14, 14)
        # Lens highlight
        p.setBrush(white)
        p.drawEllipse(30, 34, 4, 4)
        p.end()
        return QIcon(pm)

    def _on_tray_click(self, reason) -> None:
        if reason == QSystemTrayIcon.Trigger and not self.isVisible():
            self.show()
            self.activateWindow()

    # ── Hotkey management ─────────────────────────────────────────────────────

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
                f"Could not register hotkey: {self.settings['hotkey']}\n{exc}",
            )

    def _load_default_profile_on_startup(self) -> None:
        """If a profile named 'Default' exists, load it automatically at startup."""
        DEFAULT_PROFILE_NAME = "Default"
        if DEFAULT_PROFILE_NAME in self.settings.get("profiles", {}):
            logger.info("Auto-loading 'Default' profile on startup")
            self._load_profile_by_name(DEFAULT_PROFILE_NAME)

    # ── Capture flow ──────────────────────────────────────────────────────────

    def start_capture(self) -> None:
        if self.is_exiting:
            return
        try:
            if self.overlay is not None and self.overlay.isVisible():
                return
            mode = self.settings.get("capture_mode", "region")
            if mode == "window":
                # ── Window mode ───────────────────────────────────────────────
                # Capture the desktop and enumerate windows NOW, while the
                # MemoShot window is still visible — this ensures:
                #   1. The background screenshot does not contain the overlay.
                #   2. The window list does not contain the overlay HWND.
                # We hide MemoShot immediately after so it's absent from the
                # background image we already captured.
                memoshot_hwnd = _get_memoshot_hwnd()
                exclude = {memoshot_hwnd} if memoshot_hwnd else set()
                screen_pixmap, desktop_offset = grab_desktop_pixmap()
                window_list = get_window_list(exclude_hwnds=exclude)
                self.hide()
                self.overlay = WindowCaptureOverlay(
                    self.settings, screen_pixmap, desktop_offset, window_list
                )
            else:
                # ── Region mode (default) ─────────────────────────────────────
                self.overlay = CaptureOverlay(
                    self.settings,
                    force_confirm=self._return_to_settings,
                )
            self.overlay.capture_signal.connect(self._on_capture_complete)
            self.overlay.update_ui_dimensions.connect(
                self._on_overlay_dimensions_changed
            )
            self.overlay.show()
            self.overlay.activateWindow()
            self.overlay.raise_()
            logger.info(f"Capture started — mode={mode}")
        except Exception as exc:
            logger.error(f"Error starting capture: {exc}")

    def _on_capture_complete(self, rect) -> None:
        self._refresh_status_card()
        # Issue #2: flash the status card to confirm the capture
        self._flash_status_card()
        cfg.save(self.settings)
        if self._return_to_settings:
            self._return_to_settings = False
            self._refresh_settings_status_lbl()
            self.stack.setCurrentIndex(1)
            self.show()
            self.activateWindow()

    def _test_capture_from_settings(self) -> None:
        self._snapshot_ui_to_settings()
        self._return_to_settings = True
        self.hide()
        QTimer.singleShot(120, self.start_capture)

    def _refresh_settings_status_lbl(self) -> None:
        if not hasattr(self, "settings_status_lbl"):
            return
        mode = self.settings.get("ratio_mode", "9:16")
        rect = self.settings.get(f"last_capture_rect_{mode}")
        if rect:
            self.settings_status_lbl.setText(
                f"Last: {rect['width']}×{rect['height']} at ({rect['x']}, {rect['y']})"
            )
        else:
            self.settings_status_lbl.setText("No capture yet")

    def _on_overlay_dimensions_changed(self, width: int, height: int) -> None:
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)
        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)
        self._update_ratio_label()
        self._refresh_status_card()

    # ── Auto-save ─────────────────────────────────────────────────────────────

    def _autosave_show(self) -> None:
        self.autosave_label.setStyleSheet(STYLE_AUTOSAVE)

    def _autosave_hide(self) -> None:
        self.autosave_label.setStyleSheet(
            "color: transparent; font-size: 10px; font-style: italic;"
        )

    def _reset_autosave_label(self) -> None:
        self.autosave_label.setText("✔  Settings saved")
        self._autosave_hide()

    def _schedule_auto_save(self, *_args) -> None:
        self._save_timer.start()
        self._autosave_hide()

    def _flush_auto_save(self) -> None:
        old_hotkey = self.settings["hotkey"]
        self._snapshot_ui_to_settings()
        cfg.save(self.settings)
        if old_hotkey != self.settings["hotkey"]:
            self._register_hotkey()
            self.capture_btn.setText(
                f"  Capture  —  {self.settings['hotkey'].upper()}"
            )
        self.tray_icon.setToolTip(
            f"MemoShot\nPress {self.settings['hotkey'].upper()}"
        )
        logger.info("Settings auto-saved")
        self._autosave_show()
        QTimer.singleShot(2500, lambda: self._autosave_hide())

    # ── Settings helpers ──────────────────────────────────────────────────────

    def _open_save_folder(self) -> None:
        folder = self.settings.get(
            "save_location", os.path.join(os.path.expanduser("~"), "Screenshots")
        )
        os.makedirs(folder, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as exc:
            logger.warning(f"Could not open folder: {exc}")
            QMessageBox.warning(self, "Cannot open folder", f"Could not open:\n{folder}\n\n{exc}")

    def _open_log_folder(self) -> None:
        folder = self.settings.get("log_folder", "") or self._default_log_folder_display()
        os.makedirs(folder, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
        except Exception as exc:
            logger.warning(f"Could not open log folder: {exc}")
            QMessageBox.warning(self, "Cannot open folder", f"Could not open:\n{folder}\n\n{exc}")

    def _browse_log_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Log Folder")
        if folder:
            self.log_folder_input.setText(folder)
            self._on_logging_setting_changed()

    def _on_logging_setting_changed(self, *_args) -> None:
        self.settings["logging_enabled"] = self.logging_enabled_checkbox.isChecked()
        self.settings["log_level"]       = self.log_level_combo.currentText()
        raw_folder = self.log_folder_input.text().strip()
        self.settings["log_folder"] = (
            "" if raw_folder == self._default_log_folder_display() else raw_folder
        )
        cfg.save(self.settings)
        apply_log_settings(self.settings)
        self._refresh_current_log_label()

    def _refresh_current_log_label(self) -> None:
        if not hasattr(self, "current_log_lbl"):
            return
        path = current_log_path()
        if path:
            self.current_log_lbl.setText(f"Active: {os.path.basename(path)}")
            self.current_log_lbl.setToolTip(path)
        else:
            self.current_log_lbl.setText("Logging is disabled — no file is being written.")
            self.current_log_lbl.setToolTip("")

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Save Location")
        if folder:
            self.save_input.setText(folder)
            self._schedule_auto_save()

    def _on_width_changed(self, value: int) -> None:
        if self.settings.get("lock_ratio", True):
            self.height_spin.blockSignals(True)
            ratio = (16/9 if self.settings.get("ratio_mode","9:16")=="9:16" else 9/16)
            self.height_spin.setValue(int(value * ratio))
            self.height_spin.blockSignals(False)
        self._update_ratio_label()

    def _on_height_changed(self, value: int) -> None:
        if self.settings.get("lock_ratio", True):
            self.width_spin.blockSignals(True)
            ratio = (9/16 if self.settings.get("ratio_mode","9:16")=="9:16" else 16/9)
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
                if mode == "9:16" else "16:9  —  YouTube / standard video"
            )
        else:
            text = (
                f"Custom  {self.width_spin.value()} × "
                f"{self.height_spin.value()} px  (ratio unlocked)"
            )
        self.ratio_label.setText(text)

    # ── Snapshot ──────────────────────────────────────────────────────────────

    def _snapshot_ui_to_settings(self) -> None:
        self.settings["hotkey"]            = self.hotkey_input.value()
        self.settings["save_location"]     = self.save_input.text()
        self.settings["file_prefix"]       = self.prefix_input.text()
        self.settings["portrait_width"]    = self.width_spin.value()
        self.settings["portrait_height"]   = self.height_spin.value()
        self.settings["lock_ratio"]        = self.lock_ratio_checkbox.isChecked()
        self.settings["ratio_mode"]        = (
            "9:16" if self.ratio_9_16.isChecked() else "16:9"
        )
        self.settings["copy_to_clipboard"] = self.copy_to_clipboard_checkbox.isChecked()
        self.settings["confirm_capture"]   = self.confirm_capture_checkbox.isChecked()
        # capture_mode is already kept live in self.settings by _on_mode_selected;
        # record it here too so _snapshot always captures the full state.
        for k, btn in self._mode_buttons.items():
            if btn.isChecked():
                self.settings["capture_mode"] = k
                break

    # ── App lifecycle (issue #3: no exit confirmation) ────────────────────────

    def _quit_app(self) -> None:
        """Exit immediately — no confirmation dialog needed (issue #3)."""
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
            __import__(
                "PyQt5.QtWidgets", fromlist=["QApplication"]
            ).QApplication.quit,
        )

"""
ui/main_window.py
~~~~~~~~~~~~~~~~~
Main application window — two-panel design.

  Quick Capture panel  (default)
    • Header bar
    • Full-width Capture button (hotkey label updates live)
    • Last-capture status card
    • Profile list  — shows all saved profiles as a persistent list.
      Clicking a row loads that profile and keeps it highlighted.
      A "+ New profile" button below creates from current settings.
    • Toolbar: Settings | Tray | Exit

  Settings panel  (⚙ Settings)
    Three tabs: Capture / Output / Profiles
    • "Save as profile…" footer button visible on ALL tabs so users
      can always snapshot their current settings without hunting.
    • Profiles tab: create new profile (inline name field + Save button),
      then a list to rename/delete existing ones. No QInputDialog popups.
    ← Back returns to Quick panel.
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
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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

# ── Colour palette ────────────────────────────────────────────────────────────
_BLUE         = "#2563eb"
_BLUE_HOVER   = "#1d4ed8"
_BLUE_LIGHT   = "#eff6ff"
_BLUE_BORDER  = "#bfdbfe"
_HDR_BG       = "#1e293b"
_HDR_TEXT     = "#f1f5f9"
_WIN_BG       = "#f8fafc"
_SURFACE      = "#ffffff"
_BORDER       = "#e2e8f0"
_BORDER_MED   = "#cbd5e1"
_TEXT_PRIMARY = "#0f172a"
_TEXT_MUTED   = "#64748b"
_TEXT_HINT    = "#94a3b8"
_SUCCESS      = "#16a34a"
_SUCCESS_BG   = "#f0fdf4"
_SUCCESS_BDR  = "#bbf7d0"
_DANGER       = "#dc2626"

# ── Stylesheet constants ──────────────────────────────────────────────────────

STYLE_WINDOW = f"background-color: {_WIN_BG};"

STYLE_HEADER = f"""
QWidget {{
    background-color: {_HDR_BG};
    border-bottom: 1px solid #334155;
}}
"""

STYLE_CAPTURE_BTN = f"""
QPushButton {{
    background-color: {_BLUE};
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
    padding: 14px 20px;
    letter-spacing: 0.3px;
}}
QPushButton:hover   {{ background-color: {_BLUE_HOVER}; }}
QPushButton:pressed {{ background-color: {_BLUE_HOVER}; padding-top: 15px; }}
"""

STYLE_ICON_BTN = f"""
QPushButton {{
    background-color: {_SURFACE};
    color: {_TEXT_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 5px;
    font-size: 12px;
    padding: 5px 12px;
}}
QPushButton:hover  {{ background-color: {_WIN_BG}; color: {_TEXT_PRIMARY};
                      border-color: {_BORDER_MED}; }}
QPushButton:pressed {{ background-color: {_BORDER}; }}
"""

STYLE_PRIMARY_SM = f"""
QPushButton {{
    background-color: {_BLUE};
    color: white;
    border: none;
    border-radius: 5px;
    font-size: 12px;
    padding: 5px 14px;
}}
QPushButton:hover   {{ background-color: {_BLUE_HOVER}; }}
QPushButton:pressed {{ background-color: {_BLUE_HOVER}; }}
QPushButton:disabled {{ background-color: {_BORDER}; color: {_TEXT_HINT}; }}
"""

STYLE_DANGER_SM = f"""
QPushButton {{
    background-color: transparent;
    color: {_DANGER};
    border: 1px solid {_BORDER};
    border-radius: 5px;
    font-size: 12px;
    padding: 5px 12px;
}}
QPushButton:hover  {{ background-color: #fef2f2; border-color: #fca5a5; }}
QPushButton:pressed {{ background-color: #fee2e2; }}
QPushButton:disabled {{ color: {_TEXT_HINT}; border-color: {_BORDER}; }}
"""

STYLE_EXIT_BTN = f"""
QPushButton {{
    background-color: {_SURFACE};
    color: {_DANGER};
    border: 1px solid {_BORDER};
    border-radius: 5px;
    font-size: 12px;
    padding: 5px 12px;
}}
QPushButton:hover  {{ background-color: #fef2f2; border-color: #fca5a5; }}
QPushButton:pressed {{ background-color: #fee2e2; }}
"""

STYLE_STATUS_CARD = f"""
QFrame {{
    background-color: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 6px;
}}
"""

# Profile list on Quick panel
STYLE_PROFILE_LIST = f"""
QListWidget {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    outline: none;
    padding: 2px;
    font-size: 12px;
    color: {_TEXT_PRIMARY};
}}
QListWidget::item {{
    padding: 7px 10px;
    border-radius: 4px;
    border: none;
}}
QListWidget::item:hover {{
    background: {_WIN_BG};
}}
QListWidget::item:selected {{
    background: {_BLUE_LIGHT};
    color: {_BLUE};
    font-weight: bold;
}}
"""

STYLE_TAB = f"""
QTabWidget::pane {{
    border: 1px solid {_BORDER};
    border-top: none;
    background: {_SURFACE};
    border-radius: 0px 0px 6px 6px;
}}
QTabBar {{
    background: transparent;
}}
QTabBar::tab {{
    background: {_WIN_BG};
    color: {_TEXT_MUTED};
    border: 1px solid {_BORDER};
    border-bottom: none;
    border-radius: 5px 5px 0 0;
    padding: 7px 0px;
    min-width: 90px;
    margin-right: 3px;
    font-size: 12px;
    qproperty-alignment: AlignCenter;
}}
QTabBar::tab:selected {{
    background: {_SURFACE};
    color: {_BLUE};
    font-weight: bold;
    border-color: {_BORDER};
    border-bottom-color: {_SURFACE};
}}
QTabBar::tab:hover:!selected {{
    color: {_TEXT_PRIMARY};
    background: {_WIN_BG};
}}
"""

# "Save as profile" footer banner in Settings panel
STYLE_SAVE_FOOTER = f"""
QFrame {{
    background-color: {_SUCCESS_BG};
    border: 1px solid {_SUCCESS_BDR};
    border-radius: 6px;
}}
"""

STYLE_SECTION_HDR = (
    f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: bold; "
    f"letter-spacing: 0.8px;"
)
STYLE_LABEL_MUTED = f"color: {_TEXT_HINT}; font-size: 11px;"
STYLE_LABEL_HINT  = f"color: {_SUCCESS}; font-size: 11px;"
STYLE_AUTOSAVE    = f"color: {_SUCCESS}; font-size: 10px; font-style: italic;"

STYLE_HOTKEY_IDLE = f"""
QLineEdit {{
    background: {_SURFACE};
    border: 1px solid {_BORDER};
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 13px;
    color: {_TEXT_PRIMARY};
}}
QLineEdit:hover {{ border-color: {_BORDER_MED}; }}
"""

STYLE_HOTKEY_RECORDING = f"""
QLineEdit {{
    background: {_BLUE_LIGHT};
    border: 2px solid {_BLUE};
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 13px;
    color: {_BLUE_HOVER};
    font-weight: bold;
}}
"""

# ── HotkeyCapture widget ──────────────────────────────────────────────────────

_MODIFIER_KEYS = {
    Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta,
    Qt.Key_AltGr, Qt.Key_Super_L, Qt.Key_Super_R,
}

_KEY_NAMES = {
    Qt.Key_F1: "f1",   Qt.Key_F2: "f2",   Qt.Key_F3: "f3",
    Qt.Key_F4: "f4",   Qt.Key_F5: "f5",   Qt.Key_F6: "f6",
    Qt.Key_F7: "f7",   Qt.Key_F8: "f8",   Qt.Key_F9: "f9",
    Qt.Key_F10: "f10", Qt.Key_F11: "f11", Qt.Key_F12: "f12",
    Qt.Key_F13: "f13", Qt.Key_F14: "f14", Qt.Key_F15: "f15",
    Qt.Key_Escape: "esc",
    Qt.Key_Tab: "tab",
    Qt.Key_Return: "enter", Qt.Key_Enter: "enter",
    Qt.Key_Backspace: "backspace",
    Qt.Key_Delete: "delete",
    Qt.Key_Insert: "insert",
    Qt.Key_Home: "home",   Qt.Key_End: "end",
    Qt.Key_PageUp: "page up", Qt.Key_PageDown: "page down",
    Qt.Key_Left: "left", Qt.Key_Right: "right",
    Qt.Key_Up: "up",     Qt.Key_Down: "down",
    Qt.Key_Print: "print screen",
    Qt.Key_ScrollLock: "scroll lock",
    Qt.Key_Pause: "pause",
    Qt.Key_NumLock: "num lock",
    Qt.Key_CapsLock: "caps lock",
    Qt.Key_Space: "space",
}


class HotkeyCapture(QLineEdit):
    """
    Click to enter recording mode.  Press any key combination to set it.
    Escape cancels. Focus-out cancels.
    """
    def __init__(self, initial: str, parent=None) -> None:
        super().__init__(initial, parent)
        self._recording = False
        self._saved_value = initial
        self.setReadOnly(True)
        self.setStyleSheet(STYLE_HOTKEY_IDLE)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Click to record — then press your key combination (e.g. F12, Ctrl+Shift+S)")

    def mousePressEvent(self, event) -> None:
        self._cancel_recording() if self._recording else self._start_recording()

    def keyPressEvent(self, event) -> None:
        if not self._recording or event.isAutoRepeat():
            return
        key = event.key()
        if key == Qt.Key_Escape:
            self._cancel_recording()
            return
        if key in _MODIFIER_KEYS:
            self.setText(self._build_combo(event, partial=True))
            return
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


# ══════════════════════════════════════════════════════════════════════════════
# Main window
# ══════════════════════════════════════════════════════════════════════════════

class PortraitScreenshotApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = cfg.load()
        self.overlay: Optional[CaptureOverlay] = None
        self.hotkey_thread: Optional[HotkeyThread] = None
        self.is_exiting = False
        self._active_profile: Optional[str] = None   # tracks which profile is loaded

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(600)
        self._save_timer.timeout.connect(self._flush_auto_save)

        self.setWindowTitle(f"MemoShot v{APP_VERSION}")
        self.setFixedWidth(400)
        self.setStyleSheet(STYLE_WINDOW)

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

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_quick_panel())
        self.stack.addWidget(self._build_settings_panel())
        self.stack.setCurrentIndex(0)
        root.addWidget(self.stack)
        self.adjustSize()

    # ── Quick Capture panel ───────────────────────────────────────────────────

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
        layout.setSpacing(10)

        # Capture button
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()
        self.capture_btn = QPushButton(f"  Capture  —  {hotkey}")
        self.capture_btn.setStyleSheet(STYLE_CAPTURE_BTN)
        self.capture_btn.setMinimumHeight(52)
        self.capture_btn.clicked.connect(self.start_capture)
        layout.addWidget(self.capture_btn)

        # Status card
        status_frame = QFrame()
        status_frame.setStyleSheet(STYLE_STATUS_CARD)
        sf = QVBoxLayout(status_frame)
        sf.setContentsMargins(12, 8, 12, 8)
        sf.setSpacing(2)
        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 12px; font-weight: bold;"
        )
        self.status_sub = QLabel()
        self.status_sub.setStyleSheet(STYLE_LABEL_MUTED)
        sf.addWidget(self.status_label)
        sf.addWidget(self.status_sub)
        layout.addWidget(status_frame)
        self._refresh_status_card()

        # ── Profile list ───────────────────────────────────────────────────────
        prof_hdr = QHBoxLayout()
        prof_hdr.addWidget(self._section_label("Profiles"))
        prof_hdr.addStretch()

        self.new_profile_btn = QPushButton("+ New profile")
        self.new_profile_btn.setStyleSheet(STYLE_PRIMARY_SM)
        self.new_profile_btn.setToolTip(
            "Save current settings as a new named profile"
        )
        self.new_profile_btn.clicked.connect(self._new_profile_from_quick)
        prof_hdr.addWidget(self.new_profile_btn)
        layout.addLayout(prof_hdr)

        self.profile_list = QListWidget()
        self.profile_list.setStyleSheet(STYLE_PROFILE_LIST)
        self.profile_list.setMaximumHeight(110)
        self.profile_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.profile_list.itemClicked.connect(self._on_profile_list_clicked)
        layout.addWidget(self.profile_list)
        self._rebuild_profile_list()

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        settings_btn = QPushButton("⚙  Settings")
        settings_btn.setStyleSheet(STYLE_ICON_BTN)
        settings_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        toolbar.addWidget(settings_btn)

        toolbar.addStretch()

        min_btn = QPushButton("Tray")
        min_btn.setStyleSheet(STYLE_ICON_BTN)
        min_btn.setToolTip("Minimize to system tray")
        min_btn.clicked.connect(self.hide)
        toolbar.addWidget(min_btn)

        exit_btn = QPushButton("Exit")
        exit_btn.setStyleSheet(STYLE_EXIT_BTN)
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

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet(STYLE_TAB)
        self.tabs.addTab(self._build_tab_capture(),  "Capture")
        self.tabs.addTab(self._build_tab_output(),   "Output")
        self.tabs.addTab(self._build_tab_profiles(), "Profiles")
        layout.addWidget(self.tabs)

        # ── "Save as profile" footer — always visible in settings ──────────────
        # This is the key discoverability fix: users on any tab can see
        # and use this without navigating to the Profiles tab first.
        footer_frame = QFrame()
        footer_frame.setStyleSheet(STYLE_SAVE_FOOTER)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(12, 8, 12, 8)
        footer_layout.setSpacing(8)

        footer_lbl = QLabel("Save current settings as a profile:")
        footer_lbl.setStyleSheet(f"color: {_SUCCESS}; font-size: 11px;")
        footer_layout.addWidget(footer_lbl, 1)

        self.footer_profile_name = QLineEdit()
        self.footer_profile_name.setPlaceholderText("Profile name…")
        self.footer_profile_name.setFixedWidth(120)
        self.footer_profile_name.setStyleSheet(f"""
            QLineEdit {{
                background: {_SURFACE};
                border: 1px solid {_SUCCESS_BDR};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                color: {_TEXT_PRIMARY};
            }}
            QLineEdit:focus {{ border-color: {_SUCCESS}; }}
        """)
        # Enter key in name field also saves
        self.footer_profile_name.returnPressed.connect(self._save_profile_from_footer)
        footer_layout.addWidget(self.footer_profile_name)

        footer_save_btn = QPushButton("Save")
        footer_save_btn.setStyleSheet(STYLE_PRIMARY_SM)
        footer_save_btn.clicked.connect(self._save_profile_from_footer)
        footer_layout.addWidget(footer_save_btn)

        layout.addWidget(footer_frame)

        # Auto-save indicator
        self.autosave_label = QLabel("✔  Settings saved")
        self.autosave_label.setStyleSheet(STYLE_AUTOSAVE)
        self.autosave_label.setAlignment(Qt.AlignRight)
        self.autosave_label.setVisible(False)
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
        ver_lbl.setStyleSheet(
            "color: #64748b; font-size: 11px; background: transparent;"
        )
        row.addWidget(ver_lbl)

        row.addStretch()

        if with_back:
            back_btn = QPushButton("← Back")
            back_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #94a3b8;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 3px 10px;
                }
                QPushButton:hover { color: #f1f5f9; border-color: #475569; }
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

        layout.addWidget(self._section_label("Hotkey"))
        self.hotkey_input = HotkeyCapture(self.settings["hotkey"])
        self.hotkey_input.installEventFilter(self)
        layout.addWidget(self.hotkey_input)
        hint = QLabel("Click to record — press any combination (e.g. F12, Ctrl+Shift+S)")
        hint.setStyleSheet(STYLE_LABEL_MUTED)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addWidget(self._divider())

        layout.addWidget(self._section_label("Aspect ratio"))
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
        layout.addLayout(ratio_row)

        self.lock_ratio_checkbox = QCheckBox("Lock aspect ratio")
        self.lock_ratio_checkbox.setChecked(self.settings.get("lock_ratio", True))
        self.lock_ratio_checkbox.stateChanged.connect(self._on_lock_ratio_changed)
        self.lock_ratio_checkbox.stateChanged.connect(self._schedule_auto_save)
        layout.addWidget(self.lock_ratio_checkbox)

        layout.addWidget(self._divider())

        layout.addWidget(self._section_label("Dimensions"))
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
        layout.addLayout(dim_row)

        self.ratio_label = QLabel()
        self.ratio_label.setStyleSheet(STYLE_LABEL_HINT)
        layout.addWidget(self.ratio_label)
        self._on_lock_ratio_changed()

        layout.addStretch()
        return tab

    # ── Tab: Output ───────────────────────────────────────────────────────────

    def _build_tab_output(self) -> QWidget:
        tab = QWidget()
        tab.setStyleSheet(f"background: {_SURFACE};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

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

        layout.addWidget(self._section_label("File prefix"))
        self.prefix_input = QLineEdit(self.settings.get("file_prefix", ""))
        self.prefix_input.setPlaceholderText(
            "Empty = timestamp  ·  myshot1.png, myshot2.png…"
        )
        self.prefix_input.editingFinished.connect(self._schedule_auto_save)
        layout.addWidget(self.prefix_input)

        layout.addWidget(self._divider())

        layout.addWidget(self._section_label("Clipboard"))
        self.copy_to_clipboard_checkbox = QCheckBox(
            "Copy each screenshot to clipboard"
        )
        self.copy_to_clipboard_checkbox.setChecked(
            self.settings.get("copy_to_clipboard", True)
        )
        self.copy_to_clipboard_checkbox.stateChanged.connect(self._schedule_auto_save)
        layout.addWidget(self.copy_to_clipboard_checkbox)

        layout.addStretch()
        return tab

    # ── Tab: Profiles ─────────────────────────────────────────────────────────

    def _build_tab_profiles(self) -> QWidget:
        """
        Profile management tab.
        Top: list of existing profiles with Load / Delete actions per row.
        Each profile row shows its name and two small buttons.
        Selecting a profile highlights it without loading — Load button applies it.
        """
        tab = QWidget()
        tab.setStyleSheet(f"background: {_SURFACE};")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(self._section_label("Your profiles"))

        hint = QLabel(
            "Use the Save footer below to create a profile from your current settings. "
            "Select a profile here to load or delete it."
        )
        hint.setStyleSheet(STYLE_LABEL_MUTED)
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Action buttons created BEFORE the list — _rebuild_settings_profile_list
        # calls _update_settings_profile_buttons, which references these widgets.
        action_row = QHBoxLayout()
        action_row.setSpacing(6)

        self.sp_load_btn = QPushButton("Load")
        self.sp_load_btn.setStyleSheet(STYLE_PRIMARY_SM)
        self.sp_load_btn.setEnabled(False)
        self.sp_load_btn.clicked.connect(self._load_selected_profile)
        action_row.addWidget(self.sp_load_btn)

        self.sp_delete_btn = QPushButton("Delete")
        self.sp_delete_btn.setStyleSheet(STYLE_DANGER_SM)
        self.sp_delete_btn.setEnabled(False)
        self.sp_delete_btn.clicked.connect(self._delete_selected_profile)
        action_row.addWidget(self.sp_delete_btn)

        action_row.addStretch()

        self.sp_status_lbl = QLabel()
        self.sp_status_lbl.setStyleSheet(STYLE_LABEL_MUTED)
        action_row.addWidget(self.sp_status_lbl)

        # Profile list — now safe to populate since buttons are already assigned
        self.settings_profile_list = QListWidget()
        self.settings_profile_list.setStyleSheet(STYLE_PROFILE_LIST)
        self.settings_profile_list.setMinimumHeight(120)
        self.settings_profile_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )
        self.settings_profile_list.itemClicked.connect(
            self._on_settings_profile_list_clicked
        )
        layout.addWidget(self.settings_profile_list)
        self._rebuild_settings_profile_list()

        layout.addLayout(action_row)
        layout.addStretch()
        return tab

    # ── Shared helper widgets ─────────────────────────────────────────────────

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(STYLE_SECTION_HDR)
        return lbl

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(
            f"color: {_BORDER}; background: {_BORDER}; max-height: 1px;"
        )
        return line

    def eventFilter(self, obj, event) -> bool:
        from PyQt5.QtCore import QEvent
        if obj is self.hotkey_input and event.type() == QEvent.FocusOut:
            if not self.hotkey_input._recording:
                self._schedule_auto_save()
        return super().eventFilter(obj, event)

    # ══════════════════════════════════════════════════════════════════════════
    # Profile list helpers — both lists stay in sync
    # ══════════════════════════════════════════════════════════════════════════

    def _rebuild_profile_list(self) -> None:
        """Rebuild the Quick panel profile list."""
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
            placeholder = QListWidgetItem("No profiles yet — use '+ New profile' to create one")
            placeholder.setFlags(Qt.NoItemFlags)
            placeholder.setForeground(QColor(_TEXT_HINT))
            self.profile_list.addItem(placeholder)
        self.profile_list.blockSignals(False)

    def _rebuild_settings_profile_list(self) -> None:
        """Rebuild the Settings panel profile list."""
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
        self.settings_profile_list.blockSignals(False)

    def _rebuild_all_profile_lists(self) -> None:
        self._rebuild_profile_list()
        self._rebuild_settings_profile_list()

    def _update_settings_profile_buttons(self) -> None:
        selected = self.settings_profile_list.currentItem()
        has_selection = bool(
            selected
            and selected.flags() & Qt.ItemIsSelectable
        )
        self.sp_load_btn.setEnabled(has_selection)
        self.sp_delete_btn.setEnabled(has_selection)
        if has_selection:
            self.sp_status_lbl.setText(f"Selected: {selected.text()}")
        else:
            self.sp_status_lbl.setText("")

    # ══════════════════════════════════════════════════════════════════════════
    # Profile actions — Quick panel list
    # ══════════════════════════════════════════════════════════════════════════

    def _on_profile_list_clicked(self, item: QListWidgetItem) -> None:
        """Clicking a row in the Quick panel list loads that profile immediately."""
        if not (item.flags() & Qt.ItemIsSelectable):
            return
        name = item.text()
        self._load_profile_by_name(name)

    def _new_profile_from_quick(self) -> None:
        """
        '+ New profile' on Quick panel.
        Ask for a name (via a small inline input dialog) and save current settings.
        """
        # Use a simple input dialog — keeping Quick panel uncluttered
        from PyQt5.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self, "New profile", "Profile name:"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        self._snapshot_ui_to_settings()
        cfg.save_profile(self.settings, name)
        self._active_profile = name
        self._rebuild_all_profile_lists()

    # ══════════════════════════════════════════════════════════════════════════
    # Profile actions — Settings panel list
    # ══════════════════════════════════════════════════════════════════════════

    def _on_settings_profile_list_clicked(self, item: QListWidgetItem) -> None:
        """Clicking a row in the Settings list just selects it (highlights it)."""
        self._update_settings_profile_buttons()

    def _load_selected_profile(self) -> None:
        item = self.settings_profile_list.currentItem()
        if not item or not (item.flags() & Qt.ItemIsSelectable):
            return
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
        self.sp_status_lbl.setText("")

    # ══════════════════════════════════════════════════════════════════════════
    # "Save as profile" footer
    # ══════════════════════════════════════════════════════════════════════════

    def _save_profile_from_footer(self) -> None:
        """Save current settings under the name typed in the footer field."""
        name = self.footer_profile_name.text().strip()
        if not name:
            self.footer_profile_name.setFocus()
            return
        self._snapshot_ui_to_settings()
        cfg.save_profile(self.settings, name)
        self._active_profile = name
        self._rebuild_all_profile_lists()
        self.footer_profile_name.clear()
        # Brief visual confirmation in the autosave label
        self.autosave_label.setText(f'✔  Profile "{name}" saved')
        self.autosave_label.setVisible(True)
        QTimer.singleShot(
            3000,
            lambda: (
                self.autosave_label.setText("✔  Settings saved"),
                self.autosave_label.setVisible(False),
            ),
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Core profile load — used by both lists
    # ══════════════════════════════════════════════════════════════════════════

    def _load_profile_by_name(self, name: str) -> None:
        if not cfg.load_profile(self.settings, name):
            QMessageBox.warning(
                self, "Not found", f'Profile "{name}" could not be loaded.'
            )
            return
        # Sync all UI controls
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
        self._update_ratio_label()
        self._refresh_status_card()
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()
        self.capture_btn.setText(f"  Capture  —  {hotkey}")
        cfg.save(self.settings)
        self._register_hotkey()

        # Track active profile and highlight in both lists
        self._active_profile = name
        self._rebuild_all_profile_lists()

    # ══════════════════════════════════════════════════════════════════════════
    # Panel navigation
    # ══════════════════════════════════════════════════════════════════════════

    def _close_settings(self) -> None:
        self._refresh_status_card()
        self._rebuild_profile_list()
        hotkey = self.settings.get("hotkey", "ctrl+shift+p").upper()
        self.capture_btn.setText(f"  Capture  —  {hotkey}")
        self.stack.setCurrentIndex(0)
        self.adjustSize()

    # ══════════════════════════════════════════════════════════════════════════
    # Status card
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_status_card(self) -> None:
        mode  = self.settings.get("ratio_mode", "9:16")
        w     = self.settings.get("portrait_width",  607)
        h     = self.settings.get("portrait_height", 1080)
        mlbl  = "Portrait (9:16)" if mode == "9:16" else "Landscape (16:9)"
        rect  = self.settings.get(f"last_capture_rect_{mode}")
        if rect:
            self.status_label.setText(
                f"{rect['width']} × {rect['height']} px  ·  {mlbl}"
            )
            self.status_sub.setText(
                f"Last region at ({rect['x']}, {rect['y']})"
            )
        else:
            self.status_label.setText(f"{w} × {h} px  ·  {mlbl}")
            self.status_sub.setText("No previous capture in this mode")

    # ══════════════════════════════════════════════════════════════════════════
    # Tray
    # ══════════════════════════════════════════════════════════════════════════

    def _init_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        pm = QPixmap(64, 64)
        pm.fill(QColor(37, 99, 235))
        self.tray_icon.setIcon(QIcon(pm))

        menu = QMenu()
        for label, slot in [("Capture", self.start_capture),
                             ("Show Window", self.show)]:
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
                f"Could not register hotkey: {self.settings['hotkey']}\n{exc}",
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
        self._refresh_status_card()

    # ══════════════════════════════════════════════════════════════════════════
    # Auto-save
    # ══════════════════════════════════════════════════════════════════════════

    def _schedule_auto_save(self, *_args) -> None:
        self._save_timer.start()
        self.autosave_label.setVisible(False)

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
            ratio = (
                16 / 9
                if self.settings.get("ratio_mode", "9:16") == "9:16"
                else 9 / 16
            )
            self.height_spin.setValue(int(value * ratio))
            self.height_spin.blockSignals(False)
        self._update_ratio_label()

    def _on_height_changed(self, value: int) -> None:
        if self.settings.get("lock_ratio", True):
            self.width_spin.blockSignals(True)
            ratio = (
                9 / 16
                if self.settings.get("ratio_mode", "9:16") == "9:16"
                else 16 / 9
            )
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
            text = (
                f"Custom  {self.width_spin.value()} × "
                f"{self.height_spin.value()} px  (ratio unlocked)"
            )
        self.ratio_label.setText(text)

    # ══════════════════════════════════════════════════════════════════════════
    # Snapshot
    # ══════════════════════════════════════════════════════════════════════════

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
            __import__(
                "PyQt5.QtWidgets", fromlist=["QApplication"]
            ).QApplication.quit,
        )

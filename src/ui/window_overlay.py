"""
ui/window_overlay.py
~~~~~~~~~~~~~~~~~~~~
Capture-mode overlay for "window" mode.

Design notes
------------
* The desktop screenshot is taken by the CALLER before show() — this
  guarantees MemoShot's own window is absent from the background image.
* Window enumeration also runs before show() so the overlay's own HWND
  is never in the list.
* grabMouse/grabKeyboard are deferred via QTimer(0) inside showEvent —
  on Windows, Qt ignores grabs on windows that are not yet composited.
"""

import os
import subprocess
import sys
from typing import List, Optional, Tuple

from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout, QWidget

from capture.screenshot import save_screenshot
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Platform window enumeration ────────────────────────────────────────────────

def _get_windows_win32(exclude_hwnds: Optional[set] = None) -> List[Tuple[str, QRect]]:
    """
    Return (title, global QRect) for every visible, non-minimised top-level
    window.  HWNDs in *exclude_hwnds* are skipped (pass the caller's HWND to
    exclude MemoShot itself).
    """
    try:
        import ctypes
        import ctypes.wintypes as wt

        user32 = ctypes.windll.user32
        exclude_hwnds = exclude_hwnds or set()
        results: List[Tuple[str, QRect]] = []
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

        def _cb(hwnd, _lparam):
            if hwnd in exclude_hwnds:
                return True
            if not user32.IsWindowVisible(hwnd):
                return True
            if user32.IsIconic(hwnd):          # minimised
                return True
            rect = wt.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right  - rect.left
            h = rect.bottom - rect.top
            if w <= 0 or h <= 0:
                return True
            buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, buf, 256)
            if buf.value in ("Shell_TrayWnd", "Progman", "WorkerW"):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            title_buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, title_buf, length + 1)
            title = title_buf.value.strip() or "(no title)"
            results.append((title, QRect(rect.left, rect.top, w, h)))
            return True

        user32.EnumWindows(WNDENUMPROC(_cb), 0)
        logger.debug(f"EnumWindows found {len(results)} windows")
        return results
    except Exception as exc:
        logger.warning(f"EnumWindows failed: {exc}")
        return []


def _get_memoshot_hwnd() -> Optional[int]:
    """Return the HWND of the currently active Qt top-level, or None."""
    try:
        import ctypes
        for w in QApplication.topLevelWidgets():
            if w.isVisible():
                hwnd = int(w.winId())
                if hwnd:
                    return hwnd
    except Exception:
        pass
    return None


def _get_windows_xlib() -> List[Tuple[str, QRect]]:
    try:
        from Xlib import display as xdisplay, X
        d = xdisplay.Display()
        root = d.screen().root
        results = []

        def _recurse(win):
            try:
                attrs = win.get_attributes()
                if attrs.map_state != X.IsViewable:
                    return
                geo = win.get_geometry()
                translated = win.translate_coords(root, 0, 0)
                x, y = translated.x, translated.y
                w, h = geo.width, geo.height
                if w > 50 and h > 50:
                    try:
                        name = win.get_wm_name() or "(no title)"
                    except Exception:
                        name = "(no title)"
                    results.append((str(name), QRect(x, y, w, h)))
                for child in win.query_tree().children:
                    _recurse(child)
            except Exception:
                pass

        _recurse(root)
        d.close()
        logger.debug(f"Xlib found {len(results)} windows")
        return results
    except Exception as exc:
        logger.debug(f"Xlib enumeration unavailable: {exc}")
        return []


def grab_desktop_pixmap() -> Tuple[QPixmap, QPoint]:
    """
    Capture the full desktop (all screens) and return (pixmap, offset).
    Call this BEFORE hiding or showing any window so the screenshot is clean.
    """
    screens = QApplication.screens()
    min_x = min_y = float("inf")
    max_x = max_y = float("-inf")
    for s in screens:
        g = s.geometry()
        min_x = min(min_x, g.x());  min_y = min(min_y, g.y())
        max_x = max(max_x, g.x() + g.width())
        max_y = max(max_y, g.y() + g.height())
    w = int(max_x - min_x)
    h = int(max_y - min_y)
    offset = QPoint(int(min_x), int(min_y))

    pm = QPixmap(w, h)
    pm.fill(Qt.black)
    painter = QPainter(pm)
    for s in screens:
        g = s.geometry()
        shot = s.grabWindow(0)
        painter.drawPixmap(g.x() - offset.x(), g.y() - offset.y(), shot)
    painter.end()
    logger.debug(f"Desktop captured: {w}×{h} offset=({offset.x()},{offset.y()})")
    return pm, offset


def get_window_list(exclude_hwnds: Optional[set] = None) -> List[Tuple[str, QRect]]:
    """Return (title, global QRect) for every visible window."""
    if sys.platform == "win32":
        return _get_windows_win32(exclude_hwnds)
    elif sys.platform.startswith("linux"):
        return _get_windows_xlib()
    logger.debug("Window enumeration not implemented on this platform")
    return []


# ── WindowCaptureOverlay ───────────────────────────────────────────────────────

class WindowCaptureOverlay(QWidget):
    """
    Full-screen overlay for window-capture mode.

    Instantiate, then call show().  The overlay will highlight the window
    under the mouse — click to capture it, ESC to cancel.

    Parameters
    ----------
    settings       : live settings dict
    screen_pixmap  : desktop screenshot taken by the caller BEFORE this widget
                     was created (so MemoShot's own window is absent)
    desktop_offset : QPoint returned alongside screen_pixmap by grab_desktop_pixmap()
    window_list    : list of (title, global QRect) already filtered by the caller
    """

    capture_signal     = pyqtSignal(QRect)
    update_ui_dimensions = pyqtSignal(int, int)

    _HIGHLIGHT_FG = QColor(147, 51, 234)
    _DARK_OVERLAY = QColor(0, 0, 0, 80)
    _LABEL_BG     = QColor(30, 41, 59, 220)

    def __init__(
        self,
        settings: dict,
        screen_pixmap: QPixmap,
        desktop_offset: QPoint,
        window_list: List[Tuple[str, QRect]],
    ) -> None:
        super().__init__()
        self.settings       = settings
        self.screen_pixmap  = screen_pixmap
        self.full_desktop_offset = desktop_offset
        self._windows       = window_list
        self._hovered_rect: Optional[QRect]  = None   # global coords
        self._hovered_title: str = ""

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.BypassWindowManagerHint
        )
        self.setWindowState(Qt.WindowFullScreen)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.CrossCursor)

        # Size the widget to match the pre-captured pixmap
        self.setGeometry(
            desktop_offset.x(), desktop_offset.y(),
            screen_pixmap.width(), screen_pixmap.height(),
        )

        logger.debug(
            f"WindowCaptureOverlay ready — {len(self._windows)} windows  "
            f"pixmap={screen_pixmap.width()}×{screen_pixmap.height()}  "
            f"offset=({desktop_offset.x()},{desktop_offset.y()})"
        )

    # ── Coordinate helpers ─────────────────────────────────────────────────────

    def _global_to_local(self, global_rect: QRect) -> QRect:
        ox = self.full_desktop_offset.x()
        oy = self.full_desktop_offset.y()
        return QRect(
            global_rect.x() - ox,
            global_rect.y() - oy,
            global_rect.width(),
            global_rect.height(),
        )

    def _find_window_at(self, global_pos: QPoint) -> Tuple[Optional[QRect], str]:
        """Topmost window containing global_pos (reversed = topmost first)."""
        for title, rect in reversed(self._windows):
            if rect.contains(global_pos):
                return rect, title
        return None, ""

    # ── Paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        painter = QPainter(self)

        painter.drawPixmap(0, 0, self.screen_pixmap)
        painter.fillRect(0, 0, self.width(), self.height(), self._DARK_OVERLAY)

        if self._hovered_rect is not None:
            local = self._global_to_local(self._hovered_rect)

            # Un-dim the hovered window region
            painter.drawPixmap(local, self.screen_pixmap, local)

            # Purple border
            painter.setPen(QPen(self._HIGHLIGHT_FG, 3))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(local)

            # Title badge
            painter.setPen(Qt.white)
            fm = painter.fontMetrics()
            tr = fm.boundingRect(self._hovered_title)
            bx = local.center().x() - tr.width() // 2
            MARGIN = 32
            if local.top() >= MARGIN:
                by = local.top() - 8
                painter.fillRect(bx - 10, by - tr.height() - 5,
                                 tr.width() + 20, tr.height() + 10,
                                 self._HIGHLIGHT_FG)
                painter.drawText(bx, by, self._hovered_title)
            else:
                by = local.top() + tr.height() + 10
                painter.fillRect(bx - 10, local.top() + 4,
                                 tr.width() + 20, tr.height() + 10,
                                 self._HIGHLIGHT_FG)
                painter.drawText(bx, by, self._hovered_title)

        # Instruction bar
        painter.setPen(Qt.white)
        fm = painter.fontMetrics()
        inst = ("Click to capture window  |  ESC = Cancel"
                if self._windows
                else "Click to capture area  |  ESC = Cancel  (window list unavailable)")
        ir = fm.boundingRect(inst)
        ix = self.width() // 2 - ir.width() // 2
        iy = self.height() - 50
        painter.fillRect(ix - 20, iy - ir.height() - 10,
                         ir.width() + 40, ir.height() + 20, self._LABEL_BG)
        painter.drawText(ix, iy, inst)

    # ── Mouse ─────────────────────────────────────────────────────────────────

    def mouseMoveEvent(self, event) -> None:
        global_pos = event.pos() + self.full_desktop_offset
        rect, title = self._find_window_at(global_pos)
        if rect != self._hovered_rect or title != self._hovered_title:
            self._hovered_rect  = rect
            self._hovered_title = title
            self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._capture_and_save()

    # ── Keyboard ─────────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if not event.isAutoRepeat() and event.key() == Qt.Key_Escape:
            logger.debug("WindowOverlay — ESC cancelled")
            self.close()

    # ── Capture ───────────────────────────────────────────────────────────────

    def _capture_and_save(self) -> None:
        try:
            self.releaseMouse()
            self.releaseKeyboard()

            if self._hovered_rect is not None:
                capture_rect = self._global_to_local(self._hovered_rect)
                capture_rect = capture_rect.intersected(
                    QRect(0, 0, self.width(), self.height())
                )
                title = self._hovered_title
            else:
                sg = QApplication.primaryScreen().geometry()
                capture_rect = self._global_to_local(sg)
                title = "screen"

            logger.info(
                f"Window capture — '{title}'  "
                f"{capture_rect.width()}×{capture_rect.height()}  "
                f"local=({capture_rect.x()},{capture_rect.y()})  "
                f"offset=({self.full_desktop_offset.x()},{self.full_desktop_offset.y()})"
            )

            filepath = save_screenshot(self.screen_pixmap, capture_rect, self.settings)
            self.capture_signal.emit(capture_rect)
            self.update_ui_dimensions.emit(capture_rect.width(), capture_rect.height())
            self._show_toast(filepath)

        except Exception as exc:
            logger.error(f"Window capture error: {exc}")
            self._show_toast(None, error_msg=str(exc))
        finally:
            self.close()

    # ── Show / Close ──────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        """Defer grabs one event-loop tick — Qt ignores grabs on not-yet-painted windows."""
        super().showEvent(event)
        QTimer.singleShot(0, self._do_grab)

    def _do_grab(self) -> None:
        self.grabKeyboard()
        self.grabMouse()
        logger.debug("WindowCaptureOverlay — keyboard+mouse grabbed")

    def closeEvent(self, event) -> None:
        try:
            self.releaseMouse()
            self.releaseKeyboard()
        except Exception:
            pass
        super().closeEvent(event)

    # ── Toast ─────────────────────────────────────────────────────────────────

    def _show_toast(self, filepath: Optional[str], *,
                    error_msg: Optional[str] = None,
                    duration: int = 3500) -> None:
        is_error = error_msg is not None
        bg     = "#1e1e2e" if not is_error else "#2a1515"
        border = "#10b981" if not is_error else "#dc2626"

        toast = QFrame()
        toast.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        toast.setAttribute(Qt.WA_ShowWithoutActivating)
        toast.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border: 2px solid {border}; "
            f"border-radius: 10px; }}"
        )
        vbox = QVBoxLayout()
        vbox.setContentsMargins(20, 14, 20, 14)
        vbox.setSpacing(6)
        toast.setLayout(vbox)

        if is_error:
            msg = QLabel(f"❌  Capture failed\n{error_msg}")
            msg.setStyleSheet("color: #fca5a5; font-size: 13px; font-weight: bold;")
        else:
            short_name = os.path.basename(filepath) if filepath else ""
            msg = QLabel(f"✅  Screenshot saved\n{short_name}")
            msg.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: bold;")
            if filepath:
                msg.setToolTip(filepath)
        msg.setAlignment(Qt.AlignLeft)
        vbox.addWidget(msg)

        if not is_error and filepath:
            link = QLabel('<a href="open" style="color:#6ee7b7; font-size:11px;">'
                          "📂  Show in Explorer</a>")
            link.setTextInteractionFlags(Qt.TextBrowserInteraction)
            link.setOpenExternalLinks(False)
            link.linkActivated.connect(lambda _: self._open_in_explorer(filepath))
            vbox.addWidget(link)

        toast.adjustSize()
        toast.setWindowOpacity(0.97)
        sg = QApplication.primaryScreen().geometry()
        toast.move(sg.x() + (sg.width() - toast.width()) // 2,
                   sg.y() + sg.height() - toast.height() - 60)
        toast.show()

        if not hasattr(self, "_active_toasts"):
            self._active_toasts = []
        self._active_toasts.append(toast)
        QTimer.singleShot(duration, lambda: (toast.close(),
                          self._active_toasts.remove(toast)
                          if toast in self._active_toasts else None))

    @staticmethod
    def _open_in_explorer(filepath: str) -> None:
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(filepath)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", filepath])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
        except Exception as exc:
            logger.warning(f"Could not open file manager: {exc}")

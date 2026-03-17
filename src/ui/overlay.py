"""
ui/overlay.py
~~~~~~~~~~~~~
Full-screen capture overlay widget.
Handles drawing, drag/resize interaction, keyboard shortcuts,
and delegates the actual save/clipboard work to capture.screenshot.
"""

import os
import subprocess
import sys
from typing import Optional

from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QFont, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import QApplication, QFrame, QLabel, QVBoxLayout, QWidget

from capture.screenshot import save_screenshot
from utils.logger import get_logger

logger = get_logger(__name__)


class CaptureOverlay(QWidget):
    """Interactive overlay for selecting and confirming the capture region."""

    capture_signal = pyqtSignal(QRect)
    close_signal = pyqtSignal()
    update_ui_dimensions = pyqtSignal(int, int)   # width, height

    def __init__(self, settings: dict) -> None:
        super().__init__()
        self.settings = settings

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.BypassWindowManagerHint
        )
        self.setWindowState(Qt.WindowFullScreen)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.grabKeyboard()
        self.grabMouse()

        self.screens = QApplication.screens()
        self._setup_full_desktop_geometry()
        logger.debug(f"Overlay geometry: {self.geometry()}, screens: {len(self.screens)}")

        width = settings.get("portrait_width", 1080)
        height = settings.get("portrait_height", 1920)

        mouse_pos = QCursor.pos()
        screen = QApplication.screenAt(mouse_pos) or QApplication.primaryScreen()
        sg = screen.geometry()
        logger.debug(f"Active screen: {sg}, requested size: {width}×{height}")

        last_rect = self._get_valid_last_region(width, height)
        if last_rect is not None:
            self.capture_rect = last_rect
            logger.debug(f"Restored last region: {last_rect}")
        else:
            # Convert screen geometry to local overlay coordinates
            ox = self.full_desktop_offset.x()
            oy = self.full_desktop_offset.y()
            local_left = sg.left() - ox
            local_top  = sg.top()  - oy
            x = max(local_left, min(local_left + (sg.width()  - width)  // 2,
                                    local_left + sg.width()  - width))
            y = max(local_top,  min(local_top  + (sg.height() - height) // 2,
                                    local_top  + sg.height() - height))
            self.capture_rect = QRect(int(x), int(y), int(width), int(height))
            logger.debug(f"Initial capture rect (centred, local): {self.capture_rect}")

        self.dragging = False
        self.drag_offset = QPoint()
        self.resizing = False
        self.resize_edge = None
        self.resize_min_size = 100
        self._show_shortcuts = False   # toggled by the '?' key

        self._capture_screens()

    # ── Setup helpers ──────────────────────────────────────────────────────────

    def _setup_full_desktop_geometry(self) -> None:
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")
        for screen in self.screens:
            g = screen.geometry()
            min_x = min(min_x, g.x());  min_y = min(min_y, g.y())
            max_x = max(max_x, g.x() + g.width())
            max_y = max(max_y, g.y() + g.height())
        self.setGeometry(int(min_x), int(min_y), int(max_x - min_x), int(max_y - min_y))
        self.full_desktop_offset = QPoint(int(min_x), int(min_y))

    def _capture_screens(self) -> None:
        self.screen_pixmap = QPixmap(self.width(), self.height())
        self.screen_pixmap.fill(Qt.black)
        painter = QPainter(self.screen_pixmap)
        for screen in self.screens:
            g = screen.geometry()
            shot = screen.grabWindow(0)
            painter.drawPixmap(g.x() - self.full_desktop_offset.x(),
                               g.y() - self.full_desktop_offset.y(), shot)
        painter.end()

    # ── Last-region validation ─────────────────────────────────────────────────

    def _get_valid_last_region(self, width: int, height: int):
        try:
            ratio_mode = self.settings.get("ratio_mode", "9:16")
            data = self.settings.get(f"last_capture_rect_{ratio_mode}")
            if not data:
                return None
            if data.get("width") != width or data.get("height") != height:
                return None
            rect = QRect(data["x"], data["y"], data["width"], data["height"])
            # rect is in local overlay coords; convert to global to check
            # which screen it sits on, then clamp back to local coords.
            ox = self.full_desktop_offset.x()
            oy = self.full_desktop_offset.y()
            global_rect = rect.translated(ox, oy)
            for screen in self.screens:
                if global_rect.intersects(screen.geometry()):
                    return self._clamp_rect_to_desktop(rect)
        except Exception as exc:
            logger.warning(f"Error validating last region: {exc}")
        return None

    def _clamp_rect_to_desktop(self, rect: QRect) -> QRect:
        """
        Clamp *rect* (in local overlay coordinates) so it sits fully within
        the union of all screen geometries converted to local coords.
        This prevents the selection from drifting into the black letterbox
        areas above/below screens that don't share the same y-origin.
        """
        ox = self.full_desktop_offset.x()
        oy = self.full_desktop_offset.y()

        # Build the bounding box of all screens in local coords
        local_min_x = float("inf")
        local_min_y = float("inf")
        local_max_x = float("-inf")
        local_max_y = float("-inf")
        for screen in self.screens:
            g = screen.geometry()
            lx = g.x() - ox
            ly = g.y() - oy
            local_min_x = min(local_min_x, lx)
            local_min_y = min(local_min_y, ly)
            local_max_x = max(local_max_x, lx + g.width())
            local_max_y = max(local_max_y, ly + g.height())

        x = max(int(local_min_x), min(rect.x(), int(local_max_x) - rect.width()))
        y = max(int(local_min_y), min(rect.y(), int(local_max_y) - rect.height()))
        return QRect(x, y, rect.width(), rect.height())

    # ── Paint ──────────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        if hasattr(self, "screen_pixmap"):
            painter.drawPixmap(0, 0, self.screen_pixmap)
            dark = QColor(0, 0, 0, 100)
            cr = self.capture_rect
            if cr.top() > 0:
                painter.fillRect(0, 0, self.width(), cr.top(), dark)
            if cr.bottom() < self.height():
                painter.fillRect(0, cr.bottom(), self.width(), self.height() - cr.bottom(), dark)
            if cr.left() > 0:
                painter.fillRect(0, cr.top(), cr.left(), cr.height(), dark)
            if cr.right() < self.width():
                painter.fillRect(cr.right(), cr.top(), self.width() - cr.right(), cr.height(), dark)

        pen = QPen(QColor(147, 51, 234), 4)
        painter.setPen(pen)
        painter.drawRect(self.capture_rect)

        handle_size = 10
        painter.setBrush(QColor(147, 51, 234))
        cr = self.capture_rect
        for corner in [cr.topLeft(), cr.topRight(), cr.bottomLeft(), cr.bottomRight()]:
            painter.drawEllipse(corner.x() - handle_size, corner.y() - handle_size,
                                handle_size * 2, handle_size * 2)
        for edge_pt in [
            QPoint(cr.center().x(), cr.top()),
            QPoint(cr.center().x(), cr.bottom()),
            QPoint(cr.left(), cr.center().y()),
            QPoint(cr.right(), cr.center().y()),
        ]:
            painter.drawRect(edge_pt.x() - handle_size // 2, edge_pt.y() - handle_size // 2,
                             handle_size, handle_size)

        # Dimension badge — above selection normally, flips inside/below when near top edge (issue #10)
        painter.setPen(Qt.white)
        dim_text = f"{cr.width()} × {cr.height()} px"
        fm = painter.fontMetrics()
        tr = fm.boundingRect(dim_text)
        badge_h = tr.height() + 10
        MARGIN = 28  # minimum px above top edge needed to show badge above
        tx = cr.center().x() - tr.width() // 2
        if cr.top() >= MARGIN:
            # Normal: draw above the selection
            ty = cr.top() - 8
            painter.fillRect(tx - 10, ty - tr.height() - 5, tr.width() + 20, badge_h,
                             QColor(147, 51, 234))
            painter.drawText(tx, ty, dim_text)
        else:
            # Not enough room above — draw inside the selection near the top
            ty = cr.top() + badge_h
            painter.fillRect(tx - 10, cr.top() + 4, tr.width() + 20, badge_h,
                             QColor(147, 51, 234))
            painter.drawText(tx, ty, dim_text)

        # Snap hint below the selection
        snap_text = "Press S to snap to screen"
        sr = fm.boundingRect(snap_text)
        sx = cr.center().x() - sr.width() // 2
        sy = cr.bottom() + sr.height() + 15
        painter.fillRect(sx - 10, sy - sr.height() - 5, sr.width() + 20, sr.height() + 10,
                         QColor(30, 41, 59, 200))
        painter.setPen(QColor(167, 139, 250))
        painter.drawText(sx, sy, snap_text)

        # Bottom instruction bar  (? key hint added)
        painter.setPen(Qt.white)
        inst = "ENTER = Capture  |  ESC = Cancel  |  S = Snap  |  ↑↓←→ = Nudge  |  ? = Shortcuts  |  Drag to move / resize"
        ir = fm.boundingRect(inst)
        ix = self.width() // 2 - ir.width() // 2
        iy = self.height() - 50
        painter.fillRect(ix - 20, iy - ir.height() - 10, ir.width() + 40, ir.height() + 20,
                         QColor(30, 41, 59, 230))
        painter.drawText(ix, iy, inst)

        # Shortcut cheat-sheet (shown when _show_shortcuts is True)
        if self._show_shortcuts:
            self._paint_shortcut_panel(painter)

    # ── Keyboard shortcut cheat-sheet panel ───────────────────────────────────

    def _paint_shortcut_panel(self, painter: QPainter) -> None:
        """Draw a centred semi-transparent cheat-sheet panel on the overlay."""
        shortcuts = [
            ("Enter / Return", "Capture and save the screenshot"),
            ("Esc",            "Close panel if open, else cancel overlay"),
            ("S",              "Snap selection to the current screen"),
            ("?",              "Toggle this keyboard shortcut panel"),
            ("Arrow keys",     "Nudge region 1 px (hold Shift = 10 px)"),
            ("Drag (inside)",  "Move the capture region"),
            ("Drag (edge)",    "Resize from any edge"),
            ("Drag (corner)",  "Resize from any corner handle"),
        ]

        fm = painter.fontMetrics()
        line_h = fm.height() + 10
        pad_x, pad_y = 32, 20
        title_text = "Keyboard Shortcuts"
        title_h = fm.height() + 18

        max_key_w = max(fm.boundingRect(k).width() for k, _ in shortcuts)
        max_val_w = max(fm.boundingRect(v).width() for _, v in shortcuts)
        col_gap = 24
        panel_w = max_key_w + col_gap + max_val_w + pad_x * 2
        panel_h = title_h + len(shortcuts) * line_h + pad_y * 2 + 20  # +20 for dismiss hint

        px = (self.width() - panel_w) // 2
        py = (self.height() - panel_h) // 2

        # Panel background + border
        painter.setBrush(QColor(15, 15, 30, 235))
        painter.setPen(QPen(QColor(147, 51, 234), 2))
        painter.drawRoundedRect(px, py, panel_w, panel_h, 12, 12)

        # Title bar
        painter.fillRect(px + 2, py + 2, panel_w - 4, title_h - 2, QColor(147, 51, 234, 210))
        title_font = QFont(painter.font())
        title_font.setBold(True)
        title_font.setPointSize(painter.font().pointSize() + 1)
        painter.setFont(title_font)
        painter.setPen(Qt.white)
        title_w = fm.boundingRect(title_text).width()
        painter.drawText(px + (panel_w - title_w) // 2, py + title_h - 7, title_text)
        painter.setFont(QFont(title_font.family()))   # reset to default weight

        # Shortcut rows
        key_x = px + pad_x
        val_x = px + pad_x + max_key_w + col_gap
        base_y = py + title_h + pad_y
        for i, (key, desc) in enumerate(shortcuts):
            row_y = base_y + i * line_h
            # Subtle alternating row tint
            if i % 2 == 0:
                painter.fillRect(px + 2, row_y, panel_w - 4, line_h,
                                 QColor(255, 255, 255, 10))
            text_y = row_y + fm.ascent() + 4
            painter.setPen(QColor(167, 139, 250))
            painter.drawText(key_x, text_y, key)
            painter.setPen(QColor(226, 232, 240))
            painter.drawText(val_x, text_y, desc)

        # Dismiss hint at the bottom of the panel
        hint = "Press ? or Esc to close"
        hint_w = fm.boundingRect(hint).width()
        painter.setPen(QColor(148, 163, 184))
        painter.drawText(px + (panel_w - hint_w) // 2,
                         py + panel_h - 8, hint)

    # ── Mouse interaction ──────────────────────────────────────────────────────

    def _get_resize_edge(self, pos: QPoint):
        handle_size = 15
        corners = {
            "tl": self.capture_rect.topLeft(),
            "tr": self.capture_rect.topRight(),
            "bl": self.capture_rect.bottomLeft(),
            "br": self.capture_rect.bottomRight(),
        }
        for name, pt in corners.items():
            if self._distance(pos, pt) <= handle_size:
                return name
        cr = self.capture_rect
        m = 15
        if abs(pos.y() - cr.top()) <= m and cr.left() <= pos.x() <= cr.right():
            return "t"
        if abs(pos.y() - cr.bottom()) <= m and cr.left() <= pos.x() <= cr.right():
            return "b"
        if abs(pos.x() - cr.left()) <= m and cr.top() <= pos.y() <= cr.bottom():
            return "l"
        if abs(pos.x() - cr.right()) <= m and cr.top() <= pos.y() <= cr.bottom():
            return "r"
        return None

    @staticmethod
    def _distance(p1: QPoint, p2: QPoint) -> float:
        return ((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2) ** 0.5

    @staticmethod
    def _resize_cursor(edge):
        return {
            "tl": Qt.SizeFDiagCursor, "tr": Qt.SizeBDiagCursor,
            "bl": Qt.SizeBDiagCursor, "br": Qt.SizeFDiagCursor,
            "t": Qt.SizeVerCursor, "b": Qt.SizeVerCursor,
            "l": Qt.SizeHorCursor, "r": Qt.SizeHorCursor,
        }.get(edge, Qt.ArrowCursor)

    def mousePressEvent(self, event) -> None:
        edge = self._get_resize_edge(event.pos())
        if edge:
            self.resizing = True
            self.resize_edge = edge
            self.resize_start_pos = event.pos()
            self.resize_start_rect = QRect(self.capture_rect)
            self.setCursor(self._resize_cursor(edge))
            logger.debug(f"Resize started — edge={edge}")
        elif self.capture_rect.contains(event.pos()):
            self.dragging = True
            self.drag_offset = event.pos() - self.capture_rect.topLeft()
            self.setCursor(Qt.ClosedHandCursor)
            logger.debug("Drag started")

    def mouseMoveEvent(self, event) -> None:
        if self.resizing:
            dx = event.pos().x() - self.resize_start_pos.x()
            dy = event.pos().y() - self.resize_start_pos.y()
            new_rect = QRect(self.resize_start_rect)
            e = self.resize_edge
            if e == "tl": new_rect.setTopLeft(new_rect.topLeft() + QPoint(dx, dy))
            elif e == "tr": new_rect.setTopRight(new_rect.topRight() + QPoint(dx, dy))
            elif e == "bl": new_rect.setBottomLeft(new_rect.bottomLeft() + QPoint(dx, dy))
            elif e == "br": new_rect.setBottomRight(new_rect.bottomRight() + QPoint(dx, dy))
            elif e == "t": new_rect.setTop(new_rect.top() + dy)
            elif e == "b": new_rect.setBottom(new_rect.bottom() + dy)
            elif e == "l": new_rect.setLeft(new_rect.left() + dx)
            elif e == "r": new_rect.setRight(new_rect.right() + dx)
            if new_rect.width() >= self.resize_min_size and new_rect.height() >= self.resize_min_size:
                self.capture_rect = self._clamp_rect_to_desktop(new_rect)
                self.update()
        elif self.dragging:
            new_pos = event.pos() - self.drag_offset
            new_pos.setX(max(0, min(new_pos.x(), self.width() - self.capture_rect.width())))
            new_pos.setY(max(0, min(new_pos.y(), self.height() - self.capture_rect.height())))
            self.capture_rect.moveTo(new_pos)
            self.update()
        else:
            edge = self._get_resize_edge(event.pos())
            if edge:
                self.setCursor(self._resize_cursor(edge))
            elif self.capture_rect.contains(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.CrossCursor)

    def mouseReleaseEvent(self, event) -> None:
        if self.resizing:
            self.resizing = False
            self.resize_edge = None
            cr = self.capture_rect
            logger.debug(f"Resize ended — final rect: {cr.x()},{cr.y()} {cr.width()}×{cr.height()}")
            self.update_ui_dimensions.emit(cr.width(), cr.height())
        elif self.dragging:
            self.dragging = False
            cr = self.capture_rect
            logger.debug(f"Drag ended — position: {cr.x()},{cr.y()}")
        edge = self._get_resize_edge(event.pos())
        if edge:
            self.setCursor(self._resize_cursor(edge))
        elif self.capture_rect.contains(event.pos()):
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    # ── Keyboard ───────────────────────────────────────────────────────────────

    def keyPressEvent(self, event) -> None:
        if event.isAutoRepeat():
            return
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            logger.debug("Enter key — triggering capture")
            self._capture_and_save()
        elif key == Qt.Key_Escape:
            if self._show_shortcuts:
                logger.debug("Esc — closing shortcut panel")
                self._show_shortcuts = False
                self.update()
            else:
                logger.debug("Esc — cancelling overlay")
                self.close()
        elif key == Qt.Key_S:
            logger.debug("S key — snap to screen")
            self._snap_to_screen()
        elif key in (Qt.Key_Question, Qt.Key_Slash):
            self._show_shortcuts = not self._show_shortcuts
            logger.debug(f"Shortcut panel toggled: {self._show_shortcuts}")
            self.update()
        # Issue #6: arrow-key nudging (1 px, or 10 px with Shift held)
        elif key in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            step = 10 if (event.modifiers() & Qt.ShiftModifier) else 1
            dx = dy = 0
            if key == Qt.Key_Left:  dx = -step
            elif key == Qt.Key_Right: dx = step
            elif key == Qt.Key_Up:    dy = -step
            elif key == Qt.Key_Down:  dy = step
            new_x = max(0, min(self.capture_rect.x() + dx,
                               self.width() - self.capture_rect.width()))
            new_y = max(0, min(self.capture_rect.y() + dy,
                               self.height() - self.capture_rect.height()))
            self.capture_rect.moveTo(new_x, new_y)
            logger.debug(f"Nudge ({dx},{dy}) → ({new_x},{new_y})")
            self.update()

    # ── Snap to screen ─────────────────────────────────────────────────────────

    def _snap_to_screen(self) -> None:
        global_centre = self.capture_rect.center() + self.full_desktop_offset
        target = None
        for screen in self.screens:
            if screen.geometry().contains(global_centre):
                target = screen
                break
        if target is None:
            global_rect = self.capture_rect.translated(self.full_desktop_offset)
            best = 0
            for screen in self.screens:
                inter = screen.geometry().intersected(global_rect)
                area = inter.width() * inter.height()
                if area > best:
                    best = area
                    target = screen
        if target is None:
            logger.warning("Snap to screen: no target screen found")
            return
        g = target.geometry()
        lx = g.x() - self.full_desktop_offset.x()
        ly = g.y() - self.full_desktop_offset.y()
        self.capture_rect = QRect(lx, ly, g.width(), g.height())
        logger.debug(f"Snapped to screen: {g.width()}×{g.height()} at ({lx},{ly})")
        self.update()
        self.update_ui_dimensions.emit(g.width(), g.height())

    # ── Capture & save ─────────────────────────────────────────────────────────

    def _save_capture_region(self) -> None:
        try:
            cr = self.capture_rect
            ratio_mode = "9:16" if cr.width() < cr.height() else "16:9"
            self.settings[f"last_capture_rect_{ratio_mode}"] = {
                "x": cr.x(), "y": cr.y(),
                "width": cr.width(), "height": cr.height(),
            }
            logger.debug(
                f"Saved capture region ({ratio_mode}): "
                f"{cr.width()}×{cr.height()} at ({cr.x()},{cr.y()})"
            )
        except Exception as exc:
            logger.error(f"Error saving capture region: {exc}")

    def _capture_and_save(self) -> None:
        cr = self.capture_rect
        logger.info(
            f"Capture confirmed — rect: {cr.width()}×{cr.height()} at ({cr.x()},{cr.y()})"
        )
        try:
            self.releaseMouse()
            self.releaseKeyboard()

            filepath = save_screenshot(self.screen_pixmap, self.capture_rect, self.settings)
            self._save_capture_region()
            self.capture_signal.emit(self.capture_rect)
            self._show_toast(filepath)
        except Exception as exc:
            logger.error(f"Error during capture: {exc}")
            self._show_toast(None, error_msg=str(exc))
        finally:
            self.close()

    # ── Toast notification ─────────────────────────────────────────────────────

    def _show_toast(self, filepath: Optional[str], *,
                    error_msg: Optional[str] = None,
                    duration: int = 3500) -> None:
        """
        Show a notification anchored to the bottom of the *primary* screen —
        never rendered over the capture overlay itself.

        On success, includes a clickable 'Show in Explorer' link.
        """
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

        # "Show in Explorer" link — only on success
        if not is_error and filepath:
            link = QLabel('<a href="open" style="color:#6ee7b7; font-size:11px;">'
                          '📂  Show in Explorer</a>')
            link.setTextInteractionFlags(Qt.TextBrowserInteraction)
            link.setOpenExternalLinks(False)
            link.linkActivated.connect(lambda _: self._open_in_explorer(filepath))
            vbox.addWidget(link)

        toast.adjustSize()
        toast.setWindowOpacity(0.97)

        # Anchor: horizontally centred, 60 px above the bottom of the primary screen
        sg = QApplication.primaryScreen().geometry()
        toast.move(
            sg.x() + (sg.width() - toast.width()) // 2,
            sg.y() + sg.height() - toast.height() - 60,
        )
        toast.show()

        if not hasattr(self, "_active_toasts"):
            self._active_toasts = []
        self._active_toasts.append(toast)

        def _close():
            toast.close()
            if toast in self._active_toasts:
                self._active_toasts.remove(toast)

        QTimer.singleShot(duration, _close)

    @staticmethod
    def _open_in_explorer(filepath: str) -> None:
        """Open the containing folder and select/highlight the file."""
        try:
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", os.path.normpath(filepath)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", filepath])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(filepath)])
        except Exception as exc:
            logger.warning(f"Could not open file manager: {exc}")

    # ── Close ──────────────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        try:
            self.releaseMouse()
            self.releaseKeyboard()
        except Exception:
            pass
        super().closeEvent(event)

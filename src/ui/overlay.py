"""
ui/overlay.py
~~~~~~~~~~~~~
Full-screen capture overlay widget.
Handles drawing, drag/resize interaction, keyboard shortcuts,
and delegates the actual save/clipboard work to capture.screenshot.
"""

from PyQt5.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QCursor, QPainter, QPen, QPixmap
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

        width = settings.get("portrait_width", 1080)
        height = settings.get("portrait_height", 1920)

        mouse_pos = QCursor.pos()
        screen = QApplication.screenAt(mouse_pos) or QApplication.primaryScreen()
        sg = screen.geometry()

        last_rect = self._get_valid_last_region(width, height)
        if last_rect is not None:
            self.capture_rect = last_rect
        else:
            x = max(sg.left(), min(sg.left() + (sg.width() - width) // 2, sg.left() + sg.width() - width))
            y = max(sg.top(), min(sg.top() + (sg.height() - height) // 2, sg.top() + sg.height() - height))
            self.capture_rect = QRect(int(x), int(y), int(width), int(height))

        self.dragging = False
        self.drag_offset = QPoint()
        self.resizing = False
        self.resize_edge = None
        self.resize_min_size = 100

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
            for screen in self.screens:
                if rect.intersects(screen.geometry()):
                    return self._clamp_rect_to_desktop(rect)
        except Exception as exc:
            logger.warning(f"Error validating last region: {exc}")
        return None

    def _clamp_rect_to_desktop(self, rect: QRect) -> QRect:
        ox, oy = self.full_desktop_offset.x(), self.full_desktop_offset.y()
        x = max(ox, min(rect.x(), ox + self.width() - rect.width()))
        y = max(oy, min(rect.y(), oy + self.height() - rect.height()))
        return QRect(int(x), int(y), rect.width(), rect.height())

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
        for edge in [
            QPoint(cr.center().x(), cr.top()),
            QPoint(cr.center().x(), cr.bottom()),
            QPoint(cr.left(), cr.center().y()),
            QPoint(cr.right(), cr.center().y()),
        ]:
            painter.drawRect(edge.x() - handle_size // 2, edge.y() - handle_size // 2,
                             handle_size, handle_size)

        painter.setPen(Qt.white)
        dim_text = f"{cr.width()} × {cr.height()} px"
        fm = painter.fontMetrics()
        tr = fm.boundingRect(dim_text)
        tx = cr.center().x() - tr.width() // 2
        ty = cr.top() - 20
        painter.fillRect(tx - 10, ty - tr.height() - 5, tr.width() + 20, tr.height() + 10,
                         QColor(147, 51, 234))
        painter.drawText(tx, ty, dim_text)

        snap_text = "Press S to snap to screen"
        sr = fm.boundingRect(snap_text)
        sx = cr.center().x() - sr.width() // 2
        sy = cr.bottom() + sr.height() + 15
        painter.fillRect(sx - 10, sy - sr.height() - 5, sr.width() + 20, sr.height() + 10,
                         QColor(30, 41, 59, 200))
        painter.setPen(QColor(167, 139, 250))
        painter.drawText(sx, sy, snap_text)

        painter.setPen(Qt.white)
        inst = "ENTER = Capture  |  ESC = Cancel  |  S = Snap to Screen  |  Drag to move  |  Drag edges/corners to resize"
        ir = fm.boundingRect(inst)
        ix = self.width() // 2 - ir.width() // 2
        iy = self.height() - 50
        painter.fillRect(ix - 20, iy - ir.height() - 10, ir.width() + 40, ir.height() + 20,
                         QColor(30, 41, 59, 230))
        painter.drawText(ix, iy, inst)

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
        elif self.capture_rect.contains(event.pos()):
            self.dragging = True
            self.drag_offset = event.pos() - self.capture_rect.topLeft()
            self.setCursor(Qt.ClosedHandCursor)

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
            self.update_ui_dimensions.emit(self.capture_rect.width(), self.capture_rect.height())
        elif self.dragging:
            self.dragging = False
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
            self._capture_and_save()
        elif key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_S:
            self._snap_to_screen()

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
            return
        g = target.geometry()
        lx = g.x() - self.full_desktop_offset.x()
        ly = g.y() - self.full_desktop_offset.y()
        self.capture_rect = QRect(lx, ly, g.width(), g.height())
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
        except Exception as exc:
            logger.error(f"Error saving capture region: {exc}")

    def _capture_and_save(self) -> None:
        try:
            self.releaseMouse()
            self.releaseKeyboard()

            filepath = save_screenshot(self.screen_pixmap, self.capture_rect, self.settings)
            self._save_capture_region()
            self.capture_signal.emit(self.capture_rect)
            self._show_toast(f"Screenshot saved:\n{filepath}")
        except Exception as exc:
            logger.error(f"Error during capture: {exc}")
            self._show_toast(f"Capture failed: {exc}", is_error=True, duration=3000)
        finally:
            self.close()

    # ── Toast notification ─────────────────────────────────────────────────────

    def _show_toast(self, message: str, is_error: bool = False, duration: int = 2000) -> None:
        bg = "#dc2626" if is_error else "#10b981"
        toast = QFrame()
        toast.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        toast.setStyleSheet(f"QFrame {{ background-color: {bg}; border-radius: 8px; padding: 15px 25px; }}")
        label = QLabel(message)
        label.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        toast.setLayout(layout)
        toast.adjustSize()
        toast.setWindowOpacity(0.95)

        sg = QApplication.primaryScreen().geometry()
        toast.move(sg.x() + (sg.width() - toast.width()) // 2,
                   sg.y() + sg.height() - toast.height() - 50)
        toast.show()

        if not hasattr(self, "_active_toasts"):
            self._active_toasts = []
        self._active_toasts.append(toast)

        def _close():
            toast.close()
            if toast in self._active_toasts:
                self._active_toasts.remove(toast)

        QTimer.singleShot(duration, _close)

    # ── Close ──────────────────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        try:
            self.releaseMouse()
            self.releaseKeyboard()
        except Exception:
            pass
        super().closeEvent(event)

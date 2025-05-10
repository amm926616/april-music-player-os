import math

from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QFont, QWheelEvent
from PyQt6.QtWidgets import QWidget

from _utils.easy_json import EasyJson


class DonutVolumeControl(QWidget):
    volumeChanged = pyqtSignal(float)  # Emits volume between 0.0 and 1.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ej = EasyJson()
        self.setMinimumSize(100, 100)

        self._volume = self.ej.get_value("volume")

        # Customizable colors
        self._track_color = QColor(70, 50, 40, 160)  # Rich espresso tone
        self._progress_color = QColor(255, 80, 80)  # Red progress
        self._handle_color = QColor(255, 255, 255)  # White handle
        self._text_color = QColor(240, 240, 240)  # Light text
        self._bg_color = QColor(30, 30, 30)  # Dark background

        # Customizable sizes
        self._track_width = 8
        self._handle_radius = 6
        self._font_size = 12

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) / 2 - 10
        inner_radius = radius - self._track_width

        # Draw background track (full circle)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self._track_color))
        painter.drawEllipse(center, radius, radius)

        # Draw progress arc
        angle = 360 * self._volume
        painter.setBrush(QBrush(self._progress_color))
        painter.drawPie(
            int(center.x() - radius),
            int(center.y() - radius),
            int(2 * radius),
            int(2 * radius),
            90 * 16,
            -int(angle * 16)
        )

        # Cover inner circle to create the donut effect
        painter.setBrush(QBrush(self._bg_color))
        painter.drawEllipse(center, inner_radius, inner_radius)

        # Draw handle
        handle_angle = math.radians(90 - angle)
        handle_x = center.x() + (radius - self._track_width / 2) * math.cos(handle_angle)
        handle_y = center.y() - (radius - self._track_width / 2) * math.sin(handle_angle)
        painter.setBrush(QBrush(self._handle_color))
        painter.drawEllipse(QPointF(handle_x, handle_y), self._handle_radius, self._handle_radius)

        # Draw volume percentage text
        painter.setPen(self._text_color)
        font = QFont()
        font.setPointSize(self._font_size)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{int(self._volume * 100)}%")

    def mousePressEvent(self, event):
        self._update_volume_from_pos(event.position())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._update_volume_from_pos(event.position())

    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y() / 120  # Normalize wheel delta
        step = 0.02  # Volume step per scroll notch
        self._volume = max(0.0, min(1.0, self._volume + step * delta))
        self.volumeChanged.emit(self._volume)
        self.update()

    def _update_volume_from_pos(self, pos: QPointF):
        center = QPointF(self.width() / 2, self.height() / 2)
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        angle = math.degrees(math.atan2(-dy, dx)) % 360

        new_volume = (360 - angle + 90) % 360 / 360.0
        self._volume = max(0.0, min(1.0, new_volume))
        self.volumeChanged.emit(self._volume)
        self.update()

    def setVolume(self, value: float):
        self._volume = max(0.0, min(1.0, value))
        self.update()

    def volume(self) -> float:
        return self._volume


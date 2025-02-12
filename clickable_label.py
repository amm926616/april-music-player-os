from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPixmap, QPainter

class ClickableLabel(QLabel):
    doubleClicked = pyqtSignal()  # Signal to emit on double click

    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None  # Store the original pixmap

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.doubleClicked.emit()  # Emit signal on double click
            super().mouseDoubleClickEvent(event)


class ClickableImageLabel(ClickableLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Accept the event if it contains URLs (files)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.show_drag_hint()  # Show hint that file can be dropped

    def dragLeaveEvent(self, event):
        self.clear_drag_hint()  # Reset appearance if drag leaves widget

    def dropEvent(self, event: QDropEvent):
        # Get the list of URLs from the drag-and-drop event
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()  # Get the local file path of the first dropped file
            self.setText(f'File dropped: {file_path}')  # Display file path or handle it as needed
            self.parent.set_album_art_from_url(file_path)  # Optional: load and set the new image
        self.clear_drag_hint()  # Reset appearance after drop

    def show_drag_hint(self):
        # Store the original pixmap
        self.original_pixmap = self.pixmap()

        # Create a semi-transparent overlay on the current pixmap
        overlay_pixmap = QPixmap(self.size())
        overlay_pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(overlay_pixmap)
        painter.setOpacity(0.5)
        painter.drawPixmap(0, 0, self.original_pixmap)
        painter.fillRect(overlay_pixmap.rect(), Qt.GlobalColor.lightGray)

        # Set font for hint text
        painter.setFont(QFont("Komika Axis"))

        # Set opacity back to 1.0 and draw text
        painter.setOpacity(1.0)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Drop Image Here")
        painter.end()

        # Set the overlayed pixmap
        self.setPixmap(overlay_pixmap)

    def clear_drag_hint(self):
        # Restore the original pixmap
        if self.original_pixmap:
            self.setPixmap(self.original_pixmap)


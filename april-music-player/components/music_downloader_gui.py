from PyQt6.QtGui import QIcon
from zotify.app import client

from PyQt6.QtWidgets import (QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from argparse import Namespace
from contextlib import redirect_stdout

class DownloadWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, args):
        super().__init__()
        self.args = args
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    def run(self):
        try:
            with redirect_stdout(None):
                if self._cancel_requested:
                    self.finished_signal.emit(False, "Download cancelled.")
                    return
                client(self.args)  # NOTE: must support early exit based on `self._cancel_requested`
            if self._cancel_requested:
                self.finished_signal.emit(False, "Download cancelled.")
            else:
                self.finished_signal.emit(True, "Download completed successfully!")
        except Exception as e:
            self.finished_signal.emit(False, f"Download failed: {str(e)}")

class ZotifyDownloaderGui(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowIcon(QIcon(self.parent.icon_path))
        self.setWindowTitle("Zotify Music Downloader")
        self.setMinimumSize(500, 320)
        self.worker = None

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Input area
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste Spotify song/album/playlist URL here...")
        self.url_input.setClearButtonEnabled(True)
        input_layout.addWidget(self.url_input)

        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedWidth(100)
        input_layout.addWidget(self.download_btn)

        # Status
        self.status_label = QLabel("Ready to download")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        # Output
        self.results_display = QPlainTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setPlaceholderText("Download status will appear here...")

        layout.addLayout(input_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.results_display)
        self.setLayout(layout)

        # Signals
        self.download_btn.clicked.connect(self.handle_button_click)
        self.url_input.returnPressed.connect(self.handle_button_click)

        # UI Styling
        self.setStyleSheet("""
            QPushButton {
                background-color: #ff0004;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #999999;
            }
            QProgressBar {
                border-radius: 4px;
                background-color: #eeeeee;
            }
        """)

    def handle_button_click(self):
        if self.worker and self.worker.isRunning():
            # Cancel ongoing task
            self.worker.cancel()
            self.show_status("Cancelling...", "working")
            self.download_btn.setEnabled(False)
        else:
            self.start_download()

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.show_status("Please enter a Spotify URL", "error")
            return

        self.show_status("Processing your request...", "working")
        self.progress_bar.setRange(0, 0)
        self.download_btn.setText("Cancel")
        self.results_display.clear()

        args = Namespace(
            urls=[url],
            no_splash=True,
            config_location=None,
            username=None,
            password=None,
            liked_songs=False,
            followed_artists=False,
            playlist=False,
            search=None,
            download=None,
        )

        self.worker = DownloadWorker(args)
        self.worker.finished_signal.connect(self.download_completed)
        self.worker.start()

    def download_completed(self, success, message):
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Download")

        if success:
            self.show_status("Download completed!", "success")
            self.results_display.appendPlainText("✓ " + message)
        else:
            self.show_status("Download failed or cancelled", "error")
            self.results_display.appendPlainText("✗ " + message)

    def show_status(self, message, status_type):
        self.status_label.setText(message)
        color = {
            "success": "#1DB954",
            "error": "#e74c3c",
            "working": "#3498db"
        }.get(status_type, "#2c3e50")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")

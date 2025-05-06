from zotify.app import client

from PyQt6.QtWidgets import (QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout,
                            QLineEdit, QPushButton, QLabel, QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from argparse import Namespace

class DownloadWorker(QThread):
    finished_signal = pyqtSignal(bool, str)  # success, message

    def __init__(self, args):
        super().__init__()
        self.args = args

    def run(self):
        try:
            # Suppress all stdout during download
            import sys
            from contextlib import redirect_stdout
            with redirect_stdout(None):
                client(self.args)
            self.finished_signal.emit(True, "Download completed successfully!")
        except Exception as e:
            self.finished_signal.emit(False, f"Download failed: {str(e)}")

class ZotifyDownloaderGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spotify Music Downloader")
        self.setMinimumSize(500, 300)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # URL input area
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste Spotify song/album/playlist URL here...")
        self.url_input.setClearButtonEnabled(True)
        input_layout.addWidget(self.url_input)

        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedWidth(100)
        input_layout.addWidget(self.download_btn)

        # Status area
        self.status_label = QLabel("Ready to download")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        # Results display (simplified)
        self.results_display = QPlainTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setPlaceholderText("Download status will appear here...")

        # Add widgets to main layout
        layout.addLayout(input_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.results_display)

        self.setLayout(layout)

        # Connect signals
        self.download_btn.clicked.connect(self.start_download)
        self.url_input.returnPressed.connect(self.start_download)

        # Style
        self.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QProgressBar {
                border-radius: 4px;
                background-color: #eeeeee;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 4px;
            }
        """)

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.show_status("Please enter a Spotify URL", "error")
            return

        self.show_status("Processing your request...", "working")
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.download_btn.setEnabled(False)
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
        self.progress_bar.setRange(0, 1)  # Reset progress bar
        self.progress_bar.setValue(1)
        self.download_btn.setEnabled(True)

        if success:
            self.show_status("Download completed!", "success")
            self.results_display.appendPlainText("✓ " + message)
        else:
            self.show_status("Download failed", "error")
            self.results_display.appendPlainText("✗ " + message)

    def show_status(self, message, status_type):
        self.status_label.setText(message)

        if status_type == "success":
            self.status_label.setStyleSheet("color: #1DB954; font-weight: bold; font-size: 14px;")
        elif status_type == "error":
            self.status_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")
        elif status_type == "working":
            self.status_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 14px;")
        else:  # default
            self.status_label.setStyleSheet("color: #2c3e50; font-weight: bold; font-size: 14px;")

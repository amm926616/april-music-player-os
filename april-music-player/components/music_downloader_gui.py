from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                            QLineEdit, QPushButton, QListWidget)
from PyQt6.QtCore import Qt
import subprocess
import sys
import urllib.parse

class MusicDownloaderWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setWindowTitle("Music Downloader")
        self.setMinimumSize(400, 300)

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # URL input area
        input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste Spotify URL here...")
        self.url_input.setClearButtonEnabled(True)
        input_layout.addWidget(self.url_input)

        self.download_btn = QPushButton("Download")
        self.download_btn.setFixedWidth(100)
        input_layout.addWidget(self.download_btn)

        # Downloaded songs list
        self.download_list = QListWidget()
        self.download_list.setAlternatingRowColors(True)

        # Add widgets to main layout
        layout.addLayout(input_layout)
        layout.addWidget(self.download_list)

        self.setLayout(layout)

        # Connect signals
        self.download_btn.clicked.connect(self.start_download)
        self.url_input.returnPressed.connect(self.start_download)

    def start_download(self):
        pass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QFrame, QApplication
from PyQt6.QtGui import QFont

import sys

class ClockWarningDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("April Music Player - System Clock Warning")
        self.setFixedSize(500, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: #252530;
            }
            QLabel {
                color: #EEE;
                font-size: 14px;
            }
            QPushButton {
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
                min-width: 120px;
            }
        """)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Warning frame
        warning_frame = QFrame()
        warning_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(45, 45, 50, 0.9);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        warning_layout = QVBoxLayout(warning_frame)

        # Title
        title_label = QLabel("⚠ System Clock Warning")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #D62C1A;
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning_layout.addWidget(title_label)

        # Warning message
        warning_label = QLabel(
            "The system clock rewinding back in time was detected, "
            "which breaches the software's security measures.\n\n"
            "Please set your clock to the correct time "
            "or you will need to reactivate the program."
        )
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        warning_layout.addWidget(warning_label)

        main_layout.addWidget(warning_frame)

        # Button layout
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(15)

        # OK button
        ok_button = QPushButton("Fix System Time")
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #EEE;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        ok_button.clicked.connect(lambda: sys.exit())

        # Activate button
        activate_button = QPushButton("Reactivate")
        activate_button.setStyleSheet("""
            QPushButton {
                background-color: #D62C1A;
                color: white;
            }
            QPushButton:hover {
                background-color: #E04130;
            }
        """)
        activate_button.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(activate_button)
        button_layout.addStretch()

        main_layout.addWidget(button_frame)
        self.setLayout(main_layout)

        # Set font
        font = QFont()
        font.setFamily("Segoe UI")
        self.setFont(font)

        self.exec()

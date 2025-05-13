import os
import sys
import webbrowser

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor
from PyQt6.QtWidgets import (
    QDialog, QApplication, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QFrame, QRadioButton, QButtonGroup
)

from _utils.easy_json import EasyJson
from program_activation.const import *


class ProgramActivationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.ej = EasyJson()
        self.script_path = self.ej.ej_path
        self.icon_dir = os.path.join(self.script_path, 'activation_icons')
        self.successful_status = False

        self.setWindowTitle("April Music Player Activation")
        self.set_screen_ratio()

        # Set sophisticated dark background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(25, 25, 30))
        self.setPalette(palette)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # === Left Side: QR Codes and Payment Plans ===
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.Shape.StyledPanel)
        left_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(35, 35, 40, 0.9);
                border-radius: 12px;
                border: 1px solid #333;
            }
        """)

        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(15, 15, 15, 15)
        left_layout.setSpacing(15)

        # Payment Plan Selection
        plan_frame = QFrame()
        plan_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(45, 45, 50, 0.8);
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: #EEE;
                font-weight: bold;
            }
        """)
        plan_layout = QVBoxLayout(plan_frame)

        plan_title = QLabel("Select Payment Plan:")
        plan_title.setStyleSheet("color: #D62C1A; font-size: 14px;")
        plan_layout.addWidget(plan_title)

        # Radio buttons for payment plans
        self.plan_group = QButtonGroup(self)

        monthly_plan = QRadioButton("3-Month Plan (6,000 MMK/month)")
        monthly_plan.setChecked(True)
        monthly_plan.setStyleSheet("""
            QRadioButton {
                color: #EEE;
                padding: 5px;
            }
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
            }
            QRadioButton::indicator::unchecked {
                border: 2px solid #888;
                border-radius: 8px;
            }
            QRadioButton::indicator::checked {
                border: 2px solid #D62C1A;
                border-radius: 8px;
                background-color: #D62C1A;
            }
        """)

        onetime_plan = QRadioButton("One-Time Payment (15,000 MMK)")
        onetime_plan.setStyleSheet(monthly_plan.styleSheet())

        self.plan_group.addButton(monthly_plan, 1)
        self.plan_group.addButton(onetime_plan, 2)

        plan_layout.addWidget(monthly_plan)
        plan_layout.addWidget(onetime_plan)
        left_layout.addWidget(plan_frame)

        # KBZPay Section
        kbz_label = QLabel("KBZPay")
        kbz_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kbz_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px; 
            color: #D62C1A;
            padding-bottom: 5px;
        """)

        kbz_qr = QLabel()
        kbz_pixmap = QPixmap(os.path.join(self.icon_dir, "kpay.png")).scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio)
        kbz_qr.setPixmap(kbz_pixmap)
        kbz_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # WavePay Section
        wave_label = QLabel("WavePay")
        wave_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wave_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px; 
            color: #D62C1A;
            padding-bottom: 5px;
        """)

        wave_qr = QLabel()
        wave_pixmap = QPixmap(os.path.join(self.icon_dir, "wavepay.png")).scaled(250, 250,
                                                                               Qt.AspectRatioMode.KeepAspectRatio)
        wave_qr.setPixmap(wave_pixmap)
        wave_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Add to left layout
        left_layout.addWidget(kbz_label)
        left_layout.addWidget(kbz_qr)
        left_layout.addWidget(wave_label)
        left_layout.addWidget(wave_qr)
        left_layout.addStretch()

        main_layout.addWidget(left_frame)

        # === Right Side: Activation Info ===
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.Shape.StyledPanel)
        right_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(35, 35, 40, 0.9);
                border-radius: 12px;
                border: 1px solid #333;
            }
            QLabel {
                color: #EEE;
            }
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.95);
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                color: #333;
            }
        """)

        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        # Title
        title = QLabel("Welcome To April Music Player")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #D62C1A;
            padding-bottom: 10px;
        """)
        right_layout.addWidget(title)

        # Introduction text
        introduction_label = QLabel(INTRODUCTION)
        introduction_label.setWordWrap(True)
        introduction_label.setStyleSheet("font-size: 14px; line-height: 1.5;")
        right_layout.addWidget(introduction_label)

        # Instructions
        instruction_title = QLabel("Instructions")
        instruction_title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #D62C1A;
            padding-top: 10px;
        """)
        right_layout.addWidget(instruction_title)

        instruction_layout = QHBoxLayout()

        instruction_label = QLabel(INSTRUCTION)
        instruction_label.setWordWrap(True)
        instruction_label.setStyleSheet("""
            font-size: 14px; 
            background-color: rgba(45, 45, 50, 0.8);
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #D62C1A;
        """)
        instruction_layout.addWidget(instruction_label)

        telegram_qr = QLabel()
        telegram_qr_pixmap = QPixmap(os.path.join(self.icon_dir, "april_qr_code.png")).scaled(250, 250,
                                                                                            Qt.AspectRatioMode.KeepAspectRatio)
        telegram_qr.setPixmap(telegram_qr_pixmap)
        telegram_qr.setAlignment(Qt.AlignmentFlag.AlignLeft)

        instruction_layout.addWidget(telegram_qr)

        right_layout.addLayout(instruction_layout)

        # Secret Code - Combined Label with Copy Button
        secret_code = "v$9#lc@m"
        secret_code_frame = QFrame()
        secret_code_frame.setStyleSheet("""
                  background-color: rgba(45, 45, 50, 0.8);
                  border-radius: 8px;
                  padding: 10px;
                  border: 1px dashed #555;
              """)
        secret_code_layout = QHBoxLayout(secret_code_frame)

        # Combined label for "Secret Code: value"
        secret_code_combined = QLabel(
            f"Secret Code: <span style='font-family: monospace; color: #FFF;'>{secret_code}</span>")
        secret_code_combined.setStyleSheet("font-weight: bold; color: #D62C1A;")
        secret_code_combined.setTextFormat(Qt.TextFormat.RichText)

        # Copy Button with improved feedback
        self.copy_button = QPushButton("Copy")
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setStyleSheet("""
                  QPushButton {
                      background-color: #444;
                      color: #EEE;
                      border-radius: 5px;
                      padding: 4px 10px;
                      font-size: 12px;
                      min-width: 60px;
                  }
                  QPushButton:hover {
                      background-color: #555;
                  }
              """)
        self.copy_button.clicked.connect(self.copy_secret_code)

        # Telegram link
        telegram_btn = QPushButton("Contact Developer: @Adamd178")
        telegram_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #1DA1F2;
                text-align: left;
                padding: 8px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                color: #0d8bd9;
                text-decoration: underline;
            }
        """)
        telegram_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        telegram_btn.clicked.connect(lambda: webbrowser.open("https://t.me/adamd178"))

        secret_code_layout.addWidget(secret_code_combined)
        secret_code_layout.addWidget(self.copy_button)
        secret_code_layout.addStretch()
        secret_code_layout.addWidget(telegram_btn)

        right_layout.addWidget(secret_code_frame)

        # Activation Section
        activation_frame = QFrame()
        activation_frame.setStyleSheet("""
            background-color: rgba(45, 45, 50, 0.8);
            border-radius: 10px;
            padding: 15px;
        """)
        activation_layout = QVBoxLayout(activation_frame)

        code_input_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter activation code here...")
        self.code_input.setMinimumHeight(40)
        activate_button = QPushButton("ACTIVATE")
        activate_button.setMinimumSize(100, 40)
        activation_frame.setStyleSheet("""
            QFrame {
                background-color: #2D2D30;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 15px;
            }
            QLineEdit {
                background-color: #1E1E20;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px;
                color: #EEE;
                font-size: 14px;
            }
            QPushButton {
                background-color: #D62C1A;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #E04130;
            }
            QPushButton:pressed {
                background-color: #C21807;
            }
        """)
        self.code_input.returnPressed.connect(self.activate)
        activate_button.clicked.connect(self.activate)
        code_input_layout.addWidget(self.code_input)
        code_input_layout.addWidget(activate_button)

        activation_layout.addLayout(code_input_layout)

        self.status_label = QLabel("Activation Status")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            padding: 8px;
            border-radius: 5px;
            background-color: rgba(45, 45, 50, 0.7);
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activation_layout.addWidget(self.status_label)

        right_layout.addWidget(activation_frame)
        right_layout.addStretch()

        main_layout.addWidget(right_frame)

    def copy_secret_code(self):
        secret_code = "v$9#lc@m"  # Or get it from your variable/constant
        clipboard = QApplication.clipboard()
        clipboard.setText(secret_code)

        # Visual feedback
        self.copy_button.setText("Copied!")
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 12px;
                min-width: 60px;
            }
        """)

        # Reset after 1.5 seconds
        QTimer.singleShot(1500, self.reset_copy_button)

    def reset_copy_button(self):
        self.copy_button.setText("Copy")
        self.copy_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #EEE;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 12px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)

    def activate(self):
        entered_code = self.code_input.text().strip()
        if entered_code:
            self.status_label.setText("Verifying activation code...")
            self.status_label.setStyleSheet("color: #D62C1A; font-style: italic;")
            QTimer.singleShot(2000, lambda: self.verify_code(entered_code))

    def verify_code(self, code):
        if code == "j#0l#BgX31cPO3#^":
            self.status_label.setText("✓ Activation Successful!")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.successful_status = True
        else:
            self.status_label.setText("✗ Invalid Activation Code")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.successful_status = False

    def set_screen_ratio(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Get the screen's width and height
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Calculate the maximum possible 5:4 window size that fits on the screen
        # without exceeding screen bounds
        max_height = screen_height * 0.8  # e.g., use 80% of screen height
        max_width = max_height * 1.25  # 5:4 ratio

        # Apply the size
        self.resize(int(max_width), int(max_height))
        self.setMinimumSize(600, 480)  # Optional: prevent it from getting too small

    def show_ui(self) -> bool:
        self.exec()
        return self.successful_status


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set modern font
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)

    activation = ProgramActivationDialog()
    status = activation.show_ui()

    print(status)

    sys.exit(app.exec())

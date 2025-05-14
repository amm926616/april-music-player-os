import os
import sys
import webbrowser

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont, QPalette, QColor, QIcon
from PyQt6.QtWidgets import (
    QDialog, QApplication, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit, QFrame, QRadioButton, QButtonGroup
)

from _utils.easy_json import EasyJson
from program_activation.const import *


class ProgramActivationDialog(QDialog):
    def __init__(self, parent=None, fresh_activation=None):
        super().__init__(parent)
        self.payment_number = None
        self.setWindowIcon(QIcon(parent.icon_path))
        self.payment_title = QLabel()
        self.current_lang = 'ENG'
        self.fresh_activation = fresh_activation
        self.secret_code_combined = None
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

        if not self.fresh_activation:
            self.create_monthly_payment_price_layout(plan_frame)
        else:
            self.create_fresh_start_plan_layout(plan_frame)

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

        ### this block
        # Title
        main_title_layout = QHBoxLayout()
        title = QLabel("Monthly Reactivation" if not self.fresh_activation else "Welcome to April Music Player")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #D62C1A;
            padding-bottom: 10px;
        """)
        main_title_layout.addWidget(title)

        # Language toggle button (add this near the top of your UI setup)
        self.lang_button = QPushButton("BUR - မြန်မာ")
        self.lang_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: #EEE;
                border-radius: 5px;
                padding: 4px 10px;
                font-size: 12px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        self.lang_button.clicked.connect(self.toggle_language)

        main_title_layout.addStretch()
        main_title_layout.addWidget(self.lang_button)
        right_layout.addLayout(main_title_layout)

        # Introduction text
        self.introduction_label = QLabel(FRIENDLY_MONTHLY_PAY_REMINDER_ENG if not self.fresh_activation else INTRODUCTION_ENG)
        self.introduction_label.setWordWrap(True)
        self.introduction_label.setStyleSheet("font-size: 14px; line-height: 1.5;")
        right_layout.addWidget(self.introduction_label)

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

        self.instruction_label = QLabel(INSTRUCTION_ENG)
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setStyleSheet("""
            font-size: 14px; 
            background-color: rgba(45, 45, 50, 0.8);
            padding: 12px;
            border-radius: 8px;
            border-left: 3px solid #D62C1A;
        """)
        instruction_layout.addWidget(self.instruction_label)

        telegram_qr = QLabel()
        telegram_qr_pixmap = QPixmap(os.path.join(self.icon_dir, "april_qr_code.jpg")).scaled(320, 320,
                                                                                            Qt.AspectRatioMode.KeepAspectRatio)
        telegram_qr.setPixmap(telegram_qr_pixmap)
        telegram_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        instruction_layout.addWidget(telegram_qr)

        right_layout.addLayout(instruction_layout)

        # Secret Code - Combined Label with Copy Button
        self.secret_code = self.ej.get_secret_key()

        secret_code_frame = QFrame()
        secret_code_frame.setStyleSheet("""
                  background-color: rgba(45, 45, 50, 0.8);
                  border-radius: 8px;
                  padding: 10px;
                  border: 1px dashed #555;
              """)
        secret_code_layout = QHBoxLayout(secret_code_frame)

        self.secret_code_combined = QLabel()
        self.secret_code_combined.setStyleSheet("font-weight: bold; color: #D62C1A;")
        self.secret_code_combined.setTextFormat(Qt.TextFormat.RichText)

        self.update_secret_code()

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

        secret_code_layout.addWidget(self.secret_code_combined)
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

    def create_fresh_start_plan_layout(self, plan_frame):
        plan_layout = QVBoxLayout(plan_frame)
        plan_title = QLabel("Select Payment Plan:")
        plan_title.setStyleSheet("color: #D62C1A; font-size: 14px;")
        plan_layout.addWidget(plan_title)
        # Radio buttons for payment plans
        self.plan_group = QButtonGroup(self)
        onetime_plan = QRadioButton("One-Time Payment (28,000 MMK)")
        onetime_plan.setStyleSheet("""
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
        monthly_plan = QRadioButton("3-Month Plan (10,000 MMK/month)")
        monthly_plan.setStyleSheet(onetime_plan.styleSheet())
        if self.ej.get_value("payment_method") == "installment":
            monthly_plan.setChecked(True)
            self.ej.edit_value("payment_method", "installment")
        else:
            onetime_plan.setChecked(True)
            self.ej.edit_value("payment_method", "onetime")
        self.plan_group.addButton(onetime_plan, 1)
        self.plan_group.addButton(monthly_plan, 2)
        self.plan_group.buttonClicked.connect(self.set_payment_type)

        self.payment_number = QLabel("Payment Number: *******7122")
        plan_layout.addWidget(onetime_plan)
        plan_layout.addWidget(monthly_plan)
        plan_layout.addWidget(self.payment_number)

    def create_monthly_payment_price_layout(self, plan_frame):
        payment_price_layout = QVBoxLayout(plan_frame)
        self.payment_title.setText(MONTHLY_PAYMENT_PRICE_LABEL_ENG)
        self.payment_title.setStyleSheet("color: #D62C1A; font-size: 14px;")
        self.payment_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        payment_price_layout.addWidget(self.payment_title)
        payment_price_layout.addWidget(self.payment_title)

    def toggle_language(self):
        """Switch between English and Burmese languages"""
        self.current_lang = 'BUR' if self.current_lang == 'ENG' else 'ENG'
        self.lang_button.setText(LANGUAGE_LIST[0] if self.current_lang == 'BUR' else LANGUAGE_LIST[1])
        self.update_ui_text()

    def update_ui_text(self):
        """Update all text elements based on current language"""

        if not self.fresh_activation:
            print('it is inside monthly reactivation')
            self.setWindowTitle("April Music Player Reactivation" if self.current_lang == 'ENG'
                                else "April Music Player Reactivation (မြန်မာ)")
            self.introduction_label.setText(FRIENDLY_MONTHLY_PAY_REMINDER[self.current_lang])

            self.payment_title.setText(MONTHLY_PAYMENT_PRICE_LABEL[self.current_lang])
        else:
            self.setWindowTitle("Welcome to April Music Player" if self.current_lang == 'ENG'
                                else "April Music Player သို့ ကြိုဆိုပါသည်")
            self.introduction_label.setText(INTRODUCTION[self.current_lang])

            self.payment_number.setText(PAYMENT_NUMBER[self.current_lang])

        # Update instructions
        self.instruction_label.setText(INSTRUCTION[self.current_lang])

        # Update payment plan text only if it's not a monthly reactivation
        if not self.fresh_activation:
            pass
        else:
            if self.current_lang == 'ENG':
                self.plan_group.button(1).setText("One-Time Payment (28,000 MMK)")
                self.plan_group.button(2).setText("3-Month Plan (10,000 MMK/month)")
                self.code_input.setPlaceholderText("Enter activation code here...")
                self.status_label.setText("Activation Status")
            else:
                self.plan_group.button(1).setText("တစ်ကြိမ်တည်းပေးချေမှု (၂၈,၀၀၀ ကျပ်)")
                self.plan_group.button(2).setText("၃ လအရစ်ကျပေးချေမှု (တစ်လလျှင် ၁၀,၀၀၀ ကျပ်)")
                self.code_input.setPlaceholderText("activation code ထည့်ပါ...")
                self.status_label.setText("Activation အခြေအနေ")

    def update_secret_code(self):
        # Combined label for "Secret Code: value"
        label = f"Secret Code: <span style='font-family: monospace; color: #FFF;'>{self.secret_code}</span>"
        self.secret_code_combined.setText(label)

    def set_payment_type(self):
        checked_id = self.plan_group.checkedId()
        self.ej.printOrange(checked_id)
        if checked_id == 1:
            self.ej.set_payment_type("onetime")
        else:
            self.ej.set_payment_type("installment")

        self.secret_code = self.ej.get_secret_key()
        self.update_secret_code()

    def copy_secret_code(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.secret_code)

        # Visual feedback with language support
        if self.current_lang == 'ENG':
            self.copy_button.setText("Copied!")
        else:
            self.copy_button.setText("ကူးယူပြီး!")
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
            self.verify_code(entered_code)

    def verify_code(self, code):
        self.ej.printYellow(f"inside verify code: {code}")
        if code == self.ej.get_passcode():
            # Show activation success message first
            if self.current_lang == 'ENG':
                self.status_label.setText("✓ Activation Successful!")
            else:
                self.status_label.setText("✓ Activation အောင်မြင်ပါသည်!")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

            # Do the activation tasks right away
            self.ej.reset_activation_codes()
            if self.ej.is_payment_installment_type():
                self.ej.reduce_number_of_months_left_to_pay()
            else:
                self.ej.edit_value("fully_owned", True)
                self.ej.save_json()
            self.successful_status = True

            # Now start the countdown after 1 second
            countdown_messages = [
                "Starting April in 3...",
                "Starting April in 2...",
                "Starting April in 1...",
            ]

            def show_countdown(index=0):
                if index < len(countdown_messages):
                    self.status_label.setText(countdown_messages[index])
                    QTimer.singleShot(1000, lambda: show_countdown(index + 1))
                else:
                    # After "Go!", close the window
                    self.close()
            QTimer.singleShot(1000, lambda: show_countdown())
        else:
            if self.current_lang == 'ENG':
                self.status_label.setText("✗ Invalid Activation Code")
            else:
                self.status_label.setText("✗ Activation Code မှားယွင်းနေပါသည်")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
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
        max_height = screen_height * 0.9  # e.g., use 80% of screen height
        max_width = max_height * 1.5  # 5:4 ratio

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

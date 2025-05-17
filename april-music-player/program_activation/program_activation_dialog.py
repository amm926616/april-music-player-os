import os
import sys
import webbrowser

from PyQt6.QtCore import Qt, QTimer, QSize
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
        
        # Initialize scaling factors
        self.scale_factor = 1.0
        self.font_scale_factor = 1.0
        self.init_ui_scaling()
        
        self.setWindowTitle("April Music Player Activation")

        # Set sophisticated dark background
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(25, 25, 30))
        self.setPalette(palette)

        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(self.scale(20), self.scale(20), self.scale(20), self.scale(20))
        main_layout.setSpacing(self.scale(20))

        # === Left Side: QR Codes and Payment Plans ===
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.Shape.StyledPanel)
        left_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(35, 35, 40, 0.9);
                border-radius: {self.scale(12)}px;
                border: {self.scale(1)}px solid #333;
            }}
        """)

        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(self.scale(15), self.scale(15), self.scale(15), self.scale(15))
        left_layout.setSpacing(self.scale(15))

        # Payment Plan Selection
        plan_frame = QFrame()
        plan_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(45, 45, 50, 0.8);
                border-radius: {self.scale(8)}px;
                padding: {self.scale(10)}px;
            }}
            QLabel {{
                color: #EEE;
                font-weight: bold;
            }}
        """)

        if not self.fresh_activation:
            self.create_monthly_payment_price_layout(plan_frame)
        else:
            self.create_fresh_start_plan_layout(plan_frame)

        left_layout.addWidget(plan_frame)

        # KBZPay Section
        kbz_label = QLabel("KBZPay")
        kbz_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        kbz_label.setStyleSheet(f"""
            font-weight: bold; 
            font-size: {self.scale_font(16)}px; 
            color: #D62C1A;
            padding-bottom: {self.scale(5)}px;
        """)

        kbz_qr = QLabel()
        kbz_pixmap = QPixmap(os.path.join(self.icon_dir, "kpay.png"))
        kbz_pixmap = kbz_pixmap.scaled(
            self.scale(200), self.scale(200), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        kbz_qr.setPixmap(kbz_pixmap)
        kbz_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # WavePay Section
        wave_label = QLabel("WavePay")
        wave_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wave_label.setStyleSheet(f"""
            font-weight: bold; 
            font-size: {self.scale_font(16)}px; 
            color: #D62C1A;
            padding-bottom: {self.scale(5)}px;
        """)

        wave_qr = QLabel()
        wave_pixmap = QPixmap(os.path.join(self.icon_dir, "wavepay.png"))
        wave_pixmap = wave_pixmap.scaled(
            self.scale(200), self.scale(200), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
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
        right_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(35, 35, 40, 0.9);
                border-radius: {self.scale(12)}px;
                border: {self.scale(1)}px solid #333;
            }}
            QLabel {{
                color: #EEE;
            }}
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.95);
                border: {self.scale(1)}px solid #555;
                border-radius: {self.scale(5)}px;
                padding: {self.scale(8)}px;
                color: #333;
            }}
        """)

        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(
            self.scale(20), self.scale(20), self.scale(20), self.scale(20)
        )
        right_layout.setSpacing(self.scale(15))

        # Title
        main_title_layout = QHBoxLayout()
        title = QLabel("Monthly Reactivation" if not self.fresh_activation else "Welcome to April Music Player")
        title.setStyleSheet(f"""
            font-size: {self.scale_font(24)}px; 
            font-weight: bold; 
            color: #D62C1A;
            padding-bottom: {self.scale(10)}px;
        """)
        main_title_layout.addWidget(title)

        # Language toggle button
        self.lang_button = QPushButton("BUR - မြန်မာ")
        self.lang_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #444;
                color: #EEE;
                border-radius: {self.scale(5)}px;
                padding: {self.scale(4)}px {self.scale(10)}px;
                font-size: {self.scale_font(12)}px;
                min-width: {self.scale(80)}px;
            }}
            QPushButton:hover {{
                background-color: #555;
            }}
        """)
        self.lang_button.clicked.connect(self.toggle_language)

        main_title_layout.addStretch()
        main_title_layout.addWidget(self.lang_button)
        right_layout.addLayout(main_title_layout)

        # Introduction text
        self.introduction_label = QLabel(FRIENDLY_MONTHLY_PAY_REMINDER_ENG if not self.fresh_activation else INTRODUCTION_ENG)
        self.introduction_label.setWordWrap(True)
        self.introduction_label.setStyleSheet(f"""
            font-size: {self.scale_font(14)}px; 
            line-height: 1.5;
        """)
        right_layout.addWidget(self.introduction_label)

        # Instructions
        instruction_title = QLabel("Instructions")
        instruction_title.setStyleSheet(f"""
            font-size: {self.scale_font(20)}px; 
            font-weight: bold; 
            color: #D62C1A;
            padding-top: {self.scale(10)}px;
        """)
        right_layout.addWidget(instruction_title)

        instruction_layout = QHBoxLayout()

        self.instruction_label = QLabel(INSTRUCTION_ENG)
        self.instruction_label.setWordWrap(True)
        self.instruction_label.setStyleSheet(f"""
            font-size: {self.scale_font(14)}px; 
            background-color: rgba(45, 45, 50, 0.8);
            padding: {self.scale(12)}px;
            border-radius: {self.scale(8)}px;
            border-left: {self.scale(3)}px solid #D62C1A;
        """)
        instruction_layout.addWidget(self.instruction_label)

        telegram_qr = QLabel()
        telegram_qr_pixmap = QPixmap(os.path.join(self.icon_dir, "april_qr_code.jpg"))
        telegram_qr_pixmap = telegram_qr_pixmap.scaled(
            self.scale(250), self.scale(250), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        telegram_qr.setPixmap(telegram_qr_pixmap)
        telegram_qr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        instruction_layout.addWidget(telegram_qr)

        right_layout.addLayout(instruction_layout)

        # Secret Code - Combined Label with Copy Button
        self.secret_code = self.ej.get_secret_key()

        secret_code_frame = QFrame()
        secret_code_frame.setStyleSheet(f"""
            background-color: rgba(45, 45, 50, 0.8);
            border-radius: {self.scale(8)}px;
            padding: {self.scale(10)}px;
            border: {self.scale(1)}px dashed #555;
        """)
        secret_code_layout = QHBoxLayout(secret_code_frame)

        self.secret_code_combined = QLabel()
        self.secret_code_combined.setStyleSheet(f"""
            font-weight: bold; 
            color: #D62C1A;
            font-size: {self.scale_font(14)}px;
        """)
        self.secret_code_combined.setTextFormat(Qt.TextFormat.RichText)

        self.update_secret_code()

        # Copy Button with improved feedback
        self.copy_button = QPushButton("Copy")
        self.copy_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #444;
                color: #EEE;
                border-radius: {self.scale(5)}px;
                padding: {self.scale(4)}px {self.scale(10)}px;
                font-size: {self.scale_font(12)}px;
                min-width: {self.scale(60)}px;
            }}
            QPushButton:hover {{
                background-color: #555;
            }}
        """)
        self.copy_button.clicked.connect(self.copy_secret_code)

        # Telegram link
        telegram_btn = QPushButton("Contact Developer: @Adamd178")
        telegram_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #1DA1F2;
                text-align: left;
                padding: {self.scale(8)}px;
                border: none;
                font-size: {self.scale_font(14)}px;
            }}
            QPushButton:hover {{
                color: #0d8bd9;
                text-decoration: underline;
            }}
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
        activation_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #2D2D30;
                border: {self.scale(1)}px solid #444;
                border-radius: {self.scale(8)}px;
                padding: {self.scale(15)}px;
            }}
            QLineEdit {{
                background-color: #1E1E20;
                border: {self.scale(1)}px solid #555;
                border-radius: {self.scale(5)}px;
                padding: {self.scale(8)}px;
                color: #EEE;
                font-size: {self.scale_font(14)}px;
            }}
            QPushButton {{
                background-color: #D62C1A;
                color: white;
                font-weight: bold;
                border-radius: {self.scale(5)}px;
                padding: {self.scale(8)}px {self.scale(16)}px;
                font-size: {self.scale_font(14)}px;
            }}
            QPushButton:hover {{
                background-color: #E04130;
            }}
            QPushButton:pressed {{
                background-color: #C21807;
            }}
        """)
        activation_layout = QVBoxLayout(activation_frame)

        code_input_layout = QHBoxLayout()
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter activation code here...")
        self.code_input.setMinimumHeight(self.scale(40))
        activate_button = QPushButton("ACTIVATE")
        activate_button.setMinimumSize(self.scale(100), self.scale(40))
        
        self.code_input.returnPressed.connect(self.activate)
        activate_button.clicked.connect(self.activate)
        code_input_layout.addWidget(self.code_input)
        code_input_layout.addWidget(activate_button)

        activation_layout.addLayout(code_input_layout)

        self.status_label = QLabel("Activation Status")
        self.status_label.setStyleSheet(f"""
            font-size: {self.scale_font(14)}px;
            padding: {self.scale(8)}px;
            border-radius: {self.scale(5)}px;
            background-color: rgba(45, 45, 50, 0.7);
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activation_layout.addWidget(self.status_label)

        right_layout.addWidget(activation_frame)
        right_layout.addStretch()

        main_layout.addWidget(right_frame)

    def init_ui_scaling(self):
        """Initialize scaling factors based on screen resolution"""
        screen = QApplication.primaryScreen()
        if screen:
            # Calculate scaling factor based on screen DPI and resolution
            dpi = screen.logicalDotsPerInch()
            base_dpi = 96.0  # Standard DPI
            
            # Get screen dimensions
            screen_size = screen.availableSize()
            screen_width = screen_size.width()
            screen_height = screen_size.height()
            
            # Calculate scaling factors
            self.scale_factor = min(screen_width / 1920, screen_height / 1080)  # Based on 1080p reference
            self.font_scale_factor = dpi / base_dpi * 0.9  # Slightly reduce font scaling
            
            # Ensure minimum scaling
            self.scale_factor = max(0.8, min(self.scale_factor, 1.5))
            self.font_scale_factor = max(0.9, min(self.font_scale_factor, 1.3))
    
    def scale(self, value):
        """Scale a value based on the screen resolution"""
        return int(value * self.scale_factor)
    
    def scale_font(self, size):
        """Scale font size based on DPI and screen resolution"""
        return int(size * self.font_scale_factor)

    def create_fresh_start_plan_layout(self, plan_frame):
        plan_layout = QVBoxLayout(plan_frame)
        plan_title = QLabel("Select Payment Plan:")
        plan_title.setStyleSheet(f"""
            color: #D62C1A; 
            font-size: {self.scale_font(14)}px;
        """)
        plan_layout.addWidget(plan_title)
        
        # Radio buttons for payment plans
        self.plan_group = QButtonGroup(self)
        onetime_plan = QRadioButton("One-Time Payment (28,000 MMK)")
        onetime_plan.setStyleSheet(f"""
            QRadioButton {{
                color: #EEE;
                padding: {self.scale(5)}px;
                font-size: {self.scale_font(12)}px;
            }}
            QRadioButton::indicator {{
                width: {self.scale(16)}px;
                height: {self.scale(16)}px;
            }}
            QRadioButton::indicator::unchecked {{
                border: {self.scale(2)}px solid #888;
                border-radius: {self.scale(8)}px;
            }}
            QRadioButton::indicator::checked {{
                border: {self.scale(2)}px solid #D62C1A;
                border-radius: {self.scale(8)}px;
                background-color: #D62C1A;
            }}
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
        self.payment_number.setStyleSheet(f"font-size: {self.scale_font(12)}px;")
        
        plan_layout.addWidget(onetime_plan)
        plan_layout.addWidget(monthly_plan)
        plan_layout.addWidget(self.payment_number)

    def create_monthly_payment_price_layout(self, plan_frame):
        payment_price_layout = QVBoxLayout(plan_frame)
        self.payment_title.setText(MONTHLY_PAYMENT_PRICE_LABEL_ENG)
        self.payment_title.setStyleSheet(f"""
            color: #D62C1A; 
            font-size: {self.scale_font(14)}px;
        """)
        self.payment_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        payment_price_layout.addWidget(self.payment_title)

    def toggle_language(self):
        """Switch between English and Burmese languages"""
        self.current_lang = 'BUR' if self.current_lang == 'ENG' else 'ENG'
        self.lang_button.setText(LANGUAGE_LIST[0] if self.current_lang == 'BUR' else LANGUAGE_LIST[1])
        self.update_ui_text()

    def update_ui_text(self):
        """Update all text elements based on current language"""
        if not self.fresh_activation:
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
        self.copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #4CAF50;
                color: white;
                border-radius: {self.scale(5)}px;
                padding: {self.scale(4)}px {self.scale(10)}px;
                font-size: {self.scale_font(12)}px;
                min-width: {self.scale(60)}px;
            }}
        """)

        # Reset after 1.5 seconds
        QTimer.singleShot(1500, self.reset_copy_button)

    def reset_copy_button(self):
        self.copy_button.setText("Copy")
        self.copy_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #444;
                color: #EEE;
                border-radius: {self.scale(5)}px;
                padding: {self.scale(4)}px {self.scale(10)}px;
                font-size: {self.scale_font(12)}px;
                min-width: {self.scale(60)}px;
            }}
            QPushButton:hover {{
                background-color: #555;
            }}
        """)

    def activate(self):
        entered_code = self.code_input.text().strip()
        if entered_code:
            self.status_label.setText("Verifying activation code...")
            self.status_label.setStyleSheet(f"""
                color: #D62C1A; 
                font-style: italic;
                font-size: {self.scale_font(14)}px;
            """)
            self.verify_code(entered_code)

    def verify_code(self, code):
        if code == self.ej.get_passcode():
            # Show activation success message first
            if self.current_lang == 'ENG':
                self.status_label.setText("✓ Activation Successful!")
            else:
                self.status_label.setText("✓ Activation အောင်မြင်ပါသည်!")
            self.status_label.setStyleSheet(f"""
                color: #4CAF50; 
                font-weight: bold;
                font-size: {self.scale_font(14)}px;
            """)

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
            self.status_label.setStyleSheet(f"""
                color: #F44336; 
                font-weight: bold;
                font-size: {self.scale_font(14)}px;
            """)
            self.successful_status = False

    def show_ui(self) -> bool:
        self.exec()
        return self.successful_status

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set modern font with dynamic scaling
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)

    activation = ProgramActivationDialog()
    status = activation.show_ui()

    print(status)

    sys.exit(app.exec())
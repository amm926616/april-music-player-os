import webbrowser
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from password_generator.key import get_key
from password_generator.decryptor import Decryptor
from _utils.easy_json import EasyJson
import sys


def copy_to_clipboard(key):
    clipboard = QApplication.clipboard()
    clipboard.setText(key)
    feedback_label.setText("Activation code copied to clipboard!")
    feedback_label.setStyleSheet("color: green;")
    feedback_label.show()


class CopyButton(QPushButton):
    def __init__(self, key):
        super().__init__("Copy to clipboard")
        self.clicked.connect(lambda: copy_to_clipboard(key))


class Activation(QDialog):
    def __init__(self, main_ui=None):
        super().__init__()
        self.return_value = 0
        self.ej = EasyJson()
        self.setWindowIcon(QIcon(self.ej.get_value("window_icon_path")))
        self.main_ui = main_ui
        key = get_key()
        key_code = f"[{key}]"
        self.passcode = Decryptor(key).decrypt()
        self.setWindowTitle("April Music Player Subscription")
        self.setGeometry(300, 300, 450, 400)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Label
        header_label = QLabel("Subscription Renewal Required")
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header_label)

        # Activation Code Info
        code_label = QLabel(
            "Your subscription has expired.\nUse the code below to contact the developer for a new passcode."
        )
        code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        code_label.setWordWrap(True)
        layout.addWidget(code_label)

        # Activation Code Display
        activation_code_label = QLabel(key_code)
        activation_code_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        activation_code_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        activation_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(activation_code_label)

        # Copy Button
        copy_button = CopyButton(key_code)
        copy_button.setText("Copy Activation Code")
        layout.addWidget(copy_button)

        # Feedback Label (Initially Hidden)
        global feedback_label
        feedback_label = QLabel("")
        feedback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(feedback_label)

        # Instructions
        instruction_label = QLabel(
            "Steps to get a passcode:\n"
            "1. Copy the activation code.\n"
            "2. Contact the developer using the links below.\n"
            "3. Provide the code to receive your passcode."
        )
        instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction_label.setWordWrap(True)
        layout.addWidget(instruction_label)

        # Social Media Links
        social_media_layout = QHBoxLayout()
        for platform, url in [
            ("Messenger", "https://www.messenger.com/t/106815562354478/"),
            ("Telegram Chatbot", "https://t.me/amm926616_bot"),
            ("Viber", ""),
        ]:
            btn = QPushButton(platform)
            btn.clicked.connect(lambda _, u=url: webbrowser.open(u))
            social_media_layout.addWidget(btn)

        layout.addLayout(social_media_layout)

        # Passcode Input
        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Enter your passcode here")
        self.password_input.returnPressed.connect(lambda: self.check_passcode())
        layout.addWidget(self.password_input)

        # Submit Button
        submit_button = QPushButton("Activate")
        submit_button.clicked.connect(self.check_passcode)
        layout.addWidget(submit_button)

        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def keyPressEvent(self, a0):
        if a0.key() == Qt.Key.Key_Escape:
            self.close()

    def closeEvent(self, a0):
        sys.exit()

    def check_passcode(self):
        entered_passcode = (self.password_input.text()).strip()
        if entered_passcode == self.passcode:
            self.correct_validation()
            self.accept()
        elif entered_passcode == "evaluation":
            if self.ej.check_evalution_used():
                self.show_message("""You already used your evaluation period. If you can't afford for subscription, you can try contacting the developer for access grant.""")
                self.message_label.setStyleSheet("color: yellow;")
                self.message_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

            else:
                self.ej.create_evaluation_proof()
                self.correct_validation(return_value=2)
                self.accept()            
        else:
            self.show_message("Invalid passcode! Try again.")
            self.message_label.setStyleSheet("color: red;")
            self.return_value = 0

    def correct_validation(self, return_value=1):
        self.show_message("Passcode accepted! Access granted.")
        self.message_label.setStyleSheet("color: green;")
        self.main_ui.createUI()
        self.return_value = return_value

    def exec_and_return(self) -> int:
        """
        Executes the dialog and returns a boolean value:
        - True if QDialog.Accepted
        - False if QDialog.Rejected
        """
        self.exec()
        return self.return_value

    def show_message(self, text):
        self.message_label.setText(text)

class ClockWarningDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Clock Warning")
        self.setFixedSize(400, 200)

    def init_ui(self):
        layout = QVBoxLayout()

        # Warning message
        warning_label = QLabel(
            "The system clock rewinding back in time detected, "
            "which breaches the software's security. "
            "Please set your clock back to the correct time "
            "or you will need to activate the program again."
        )
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button_layout = QHBoxLayout()

        # OK button
        ok_button = QPushButton("OK, I will check\nthe system time")
        ok_button.clicked.connect(lambda: sys.exit())

        activate_button = QPushButton("I will activate\nagain")
        activate_button.clicked.connect(lambda: self.close())

        button_layout.addWidget(ok_button)
        button_layout.addWidget(activate_button)

        # Add widgets to layout
        layout.addWidget(warning_label)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.exec()

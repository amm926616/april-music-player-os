import os
import subprocess

from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QDialog, QLabel, QPushButton, QVBoxLayout,
                             QHBoxLayout, QPlainTextEdit, QProgressBar)
from _utils.colors import printGreen, printRed, printCyan, printOrange, printYellow
from _utils.easy_json import EasyJson, rewrite_credentials


class ActivationWorker(QThread):
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, ej, stop_flag):
        super().__init__()
        self.ej = ej
        self.stop_flag = stop_flag
        self.authenticator_path = os.path.join(self.ej.ej_path, "librespot-authenticator")

    def run(self):
        try:
            # Determine platform-specific activation command
            if self.ej.get_value("running_system") == "windows":
                activate_cmd = [os.path.join(self.authenticator_path, "librespot-auth.exe")]
            else:
                activate_cmd = [os.path.join(self.authenticator_path, "librespot-auth")]

            # Add the --path argument and the path to the credentials file
            activate_cmd.extend(["--path", self.ej.get_zotify_credential_file_path()])

            # Debug: Print the full command
            print(f"Running command: {' '.join(activate_cmd)}")

            result = subprocess.run(
                activate_cmd,
                check=True,
                shell=False,
                cwd=os.makedirs(self.ej.get_zotify_config_folder_path(), exist_ok=True)# Run in the target directory
            )

            if self.stop_flag():
                self.finished_signal.emit(False, "Activation cancelled")
                return

            if result.returncode == 0:
                printGreen("Process run successfully")

                printYellow("Trying to run replace.py script")
                rewrite_credentials(self.ej.get_zotify_credential_file_path())
                printGreen("After running replace.py script")

                self.finished_signal.emit(True, "Activation completed successfully!\nYou can now use the downloader.")
            else:
                self.finished_signal.emit(False, "Activation failed - please try again")

        except subprocess.CalledProcessError as e:
            self.finished_signal.emit(False, f"Activation error: {str(e)}")
        except Exception as e:
            self.finished_signal.emit(False, f"Unexpected error: {str(e)}")

class CredentialDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ej = EasyJson()
        self.parent = parent
        self.setWindowTitle("Spotify Credentials")
        self.setWindowIcon(QIcon(parent.icon_path) if parent else None)
        self.setMinimumSize(500, 400)

        # Thread control
        self._stop_flag = False
        self.worker = None

        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Instruction label
        self.instruction_label = QLabel("""
            <p style='font-size: 14px;'>
            <b>How to generate credentials:</b><br>
            1. Click the button below to start the activation process<br>
            2. Open your Spotify desktop app<br>
            3. Go to 'Connect to a device' section<br>
            4. Select the device named "Generate Credentials"<br>
            5. Wait for the process to complete
            </p>
            """)
        self.instruction_label.setWordWrap(True)

        # Status label
        self.status_label = QLabel("Ready to generate credentials")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)

        # Output console
        self.console_output = QPlainTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setPlaceholderText("Activation progress will appear here...")

        # Button layout
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("Generate Credentials")
        self.generate_button.setFixedWidth(150)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.setVisible(False)

        button_layout.addStretch()
        button_layout.addWidget(self.generate_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addStretch()

        # Add widgets to main layout
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.console_output)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Signals
        self.generate_button.clicked.connect(self.generate_credentials)
        self.cancel_button.clicked.connect(self.cancel_activation)

        # Apply styling consistent with musicdownloadergui
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
            QProgressBar::chunk {
                background-color: #ff0004;
                border-radius: 4px;
            }
            QPlainTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                font-family: monospace;
            }
        """)

    def generate_credentials(self):
        """Start the credential generation process"""
        self._stop_flag = False
        self.generate_button.setVisible(False)
        self.cancel_button.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.update_status("Starting activation...", "working")
        self.console_output.clear()

        self.worker = ActivationWorker(self.ej, lambda: self._stop_flag)
        self.worker.finished_signal.connect(self.activation_complete)
        self.worker.start()

    def cancel_activation(self):
        """Cancel the ongoing activation"""
        self._stop_flag = True
        self.update_status("Cancelling activation...", "working")
        self.cancel_button.setEnabled(False)
        if self.worker and self.worker.isRunning():
            self.worker.quit()
        self.reject()  # <-- Reject immediately if canceled

    def activation_complete(self, success, message):
        """Handle activation completion"""
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(1)
        self.cancel_button.setVisible(False)
        self.cancel_button.setEnabled(True)

        if success:
            self.update_status("Activation successful!", "success")
            self.console_output.appendPlainText("✓ " + message)

            # Change the generate button to "Go to Download" or "Close"
            self.generate_button.setText("Go to Download")
            self.generate_button.setVisible(True)
            self.generate_button.clicked.disconnect()
            self.generate_button.clicked.connect(self.accept)  # Close dialog when clicked

            # Optional: Change button color to green for success
            self.generate_button.setStyleSheet("""
                QPushButton {
                    background-color: #1DB954;  /* Spotify green */
                    color: white;
                    border: none;
                    padding: 8px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1aa34a;
                }
            """)
        else:
            self.update_status("Activation failed", "error")
            self.console_output.appendPlainText("✗ " + message)
            self.generate_button.setVisible(True)
            self.generate_button.setText("Try Again")
            self.generate_button.clicked.disconnect()
            self.generate_button.clicked.connect(self.generate_credentials)

    def update_status(self, message, status_type):
        """Update status with color coding"""
        self.status_label.setText(message)
        color = {
            "success": "#1DB954",  # Spotify green
            "error": "#e74c3c",  # Red
            "working": "#3498db"  # Blue
        }.get(status_type, "#2c3e50")  # Default dark
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")

    def closeEvent(self, event):
        """Handle window close event"""
        self._stop_flag = True
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait(1000)
        event.accept()

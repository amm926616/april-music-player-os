import os
from PyQt6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout
from PyQt6.QtGui import QMovie
import subprocess
import shutil
import threading
from _utils.easy_json import EasyJson

class CredentialDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ej = EasyJson()
        self.process_finish = None
        self.setWindowTitle("Spotify Credential Generation")

        # Stop flag for the thread
        self.stop_thread = False
        self.activation_thread = None  # Reference to the activation thread

        # Label to instruct the user
        self.instruction_label = QLabel("""
            Click the button to run the activation script. The script will listen to toggle a device list connection from Spotify.
            Firstly, you need to have the Spotify desktop app installed and be logged in to your Spotify account.
            Open Spotify Desktop app. Go to the devices connection section. There will be a device named "Generate Credentials."
            Click on it. Then the activation process is completed.
            """, self)

        # Button to start credential generation
        self.generate_button = QPushButton("Generate Credentials", self)
        self.generate_button.clicked.connect(self.generate_credentials)

        # Label to show loading animation
        self.loading_label = QLabel(self)
        self.loading_label.setVisible(False)  # Hidden initially

        # Load the loading animation (Replace with the path to your loading.gif)
        self.loading_movie = QMovie("loading.gif")  # Ensure loading.gif is in the same directory or provide a full path
        self.loading_label.setMovie(self.loading_movie)

        # Layout setup
        layout = QVBoxLayout()
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.loading_label)
        self.setLayout(layout)

    def generate_credentials(self):
        """Generating Zotify credential with auth-librespot script"""
        # Update label, hide the button, and start the loading animation
        self.instruction_label.setText("Open Spotify, go to 'Connect to a device' section, and choose 'Generate Credentials'.")
        self.generate_button.setVisible(False)
        self.loading_label.setVisible(True)
        self.loading_movie.start()

        # Run activation in a separate thread
        self.stop_thread = False
        self.activation_thread = threading.Thread(target=self.activate_zotify)
        self.activation_thread.start()

    def activate_zotify(self):
        def run_activation():
            # Determine platform-specific activation command
            if self.ej.get_value("running_system") == "windows":
                activate_cmd = [os.path.join(self.ej.script_path, "librespot-authenticator", "librespot-auth.exe")]
            else:
                activate_cmd = [os.path.join(self.ej.script_path, "librespot-authenticator", "librespot-auth")]

            try:
                # Run the activation command, checking the stop flag
                result = subprocess.run(activate_cmd, check=True, shell=True)
                if self.stop_thread:
                    return  # Exit if stop flag is set

                # If activation is successful, run replace.py
                if result.returncode == 0:
                    subprocess.run(["python", os.path.join(self.ej.script_path, "librespot-authenticator", "replace.py")], check=True)
                    self.move_credentials_file()
                    print("Activation and replace.py executed successfully.")

                # Notify user and bring dialog to the front on completion
                self.instruction_label.setText("Activation completed successfully. Credentials generated.")
                self.activateWindow()  # Bring dialog window to front
                self.raise_()  # Make sure the window stays on top

            except subprocess.CalledProcessError as e:
                # Display error message
                self.instruction_label.setText("An error occurred during activation.")
                print(f"An error occurred: {e}")

            # Stop the loading animation
            self.loading_movie.stop()
            self.loading_label.setVisible(False)

        # Start activation in a separate thread
        if not self.stop_thread:
            run_activation()

    def move_credentials_file(self):
        # Determine the operating system


        # Make sure the destination directory exists
        os.makedirs(self.ej.zotify_credential_path, exist_ok=True)

        try:
            # Move the file
            shutil.move(os.path.join(self.ej.script_path, "credentials.json"), self.ej.zotify_credential_path)
            print(f"File moved to {self.ej.zotify_credential_path}")
            
        except Exception as e:
            print(f"Error moving file: {e}")

    def closeEvent(self, event):
        """Override closeEvent to stop the thread when the dialog is closed."""
        # Set the stop flag to True
        self.stop_thread = True

        # Wait for the thread to finish if it's running
        if self.activation_thread is not None and self.activation_thread.is_alive():
            self.activation_thread.join()

        # Accept the close event to actually close the dialog
        event.accept()

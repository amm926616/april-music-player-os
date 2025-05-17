#! /usr/bin/env python

import os
import signal
import sys
import time

from PyQt6.QtCore import QSharedMemory
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication, QMessageBox

from _utils.easy_json import EasyJson
from program_activation.check_subscription_time import CheckSubscriptionTime
from main_ui.musicplayerui import MusicPlayerUI
from program_activation.program_activation_dialog import ProgramActivationDialog

APP_KEY = 'AprilMusicPlayer'
SERVER_NAME = 'MusicPlayerServer'

class SingleInstanceApp:
    _instance = None

    def __init__(self):
        self.subscription_datetime = CheckSubscriptionTime()


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.shared_memory = QSharedMemory(APP_KEY)
            cls._instance.server = None
            cls._instance.ej = EasyJson()
            cls._instance.ej.set_home_script_path(os.path.dirname(os.path.abspath(__file__)))
        return cls._instance

    def is_another_instance_running(self):
        """Check if another instance of the application is already running."""
        if self.shared_memory.attach():
            return True
        if self.shared_memory.create(1):
            return False
        else:
            print("Error creating shared memory:", self.shared_memory.errorString())
            return True

    def cleanup_stale_server(self):
        """Forcefully remove any existing server with the same name."""
        try:
            # Try to remove the server if it already exists
            QLocalServer.removeServer(SERVER_NAME)
            print(f"Server {SERVER_NAME} removed successfully.")
        except Exception as e:
            # Log error if removal fails
            print(f"Error cleaning up server: {e}")
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Error cleaning up server: {e}\n")

        # Check if the server is still listening
        if self.server and self.server.isListening():
            print(f"Server {SERVER_NAME} is still listening. Removing it...")
            self.server.close()  # Close the server if still listening

    def setup_signal_handlers(self):
        """Setup signal handlers to ensure cleanup on crash or termination."""
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def handle_signal(self, sig, frame):
        """Handle termination signals."""
        print(f"Signal {sig} received. Cleaning up and exiting.")
        self.cleanup_stale_server()
        sys.exit(1)

    def load_stylesheet(self):
        """Load the QSS file from the specified path."""
        script_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_path, "style.qss")
        with open(file_path, "r") as f:
            return f.read()

    def bring_up_main_window(self):
        """Connect to the local server and send a message to bring up the window."""
        socket = QLocalSocket()
        socket.connectToServer(SERVER_NAME)
        if socket.waitForConnected(1000):
            socket.write(b'activate_window')
            socket.flush()
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
        else:
            print("Failed to connect to server:", socket.errorString())
        socket.close()

    def create_local_server(self, ui):
        """Create a local server to allow other instances to communicate."""
        self.cleanup_stale_server()  # Ensure any stale server is cleaned up before starting a new one
        self.server = QLocalServer()
        if self.server.listen(SERVER_NAME):
            self.server.newConnection.connect(lambda: self.handle_new_connection(ui))
        else:
            print(f"Error starting server: {self.server.errorString()}")
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Error starting server: {self.server.errorString()}\n")

    def handle_new_connection(self, ui):
        """Handle new connections from other instances."""
        socket = self.server.nextPendingConnection()
        if socket and socket.waitForReadyRead(1000):
            message = socket.readAll().data().decode()
            if message == 'activate_window':
                ui.showMaximized()
                ui.activateWindow()
                ui.raise_()
        socket.disconnectFromServer()
        socket.close()

    def setup_app(self):
        """Setup and initialize the application, including UI and stylesheet."""
        app = QApplication(sys.argv)

        app.setQuitOnLastWindowClosed(False)

        # Load QSS stylesheet
        stylesheet = self.load_stylesheet()
        self.ej.printGreen("After parsing style sheet")
        app.setStyleSheet(stylesheet)

        # Set up signal handlers for cleanup
        self.setup_signal_handlers()

        # Show the MusicPlayerUI and create local server
        ui = MusicPlayerUI(app)
        self.create_local_server(ui)

        return app, ui

    def start_main_ui(self, ui):
        # Measure time for UI initialization
        start_time = time.time()  # Start time
        ui.createUI()  # Create the UI
        end_time = time.time()  # End time
        print(f"UI initialization took: {end_time - start_time:.4f} seconds")

    def has_expired_montly_usage(self) -> bool:
        if self.subscription_datetime.has_expired():
            return True
        return False

    def create_activation_dialog_and_continue(self, ui, fresh_activation=None):
        activation_dialog = ProgramActivationDialog(ui, fresh_activation)  # Assuming Activation is a dialog
        activation_status = activation_dialog.show_ui()
        if activation_status:  # Block the main window until this is closed
            if self.ej.is_payment_installment_type():
                self.subscription_datetime.set_subscription_status_and_time(30)
            else:
                self.ej.edit_value("active_subscription", True)
            self.start_main_ui(ui)
        else:
            sys.exit()

    def generate_activation_codes(self):
        if not self.ej.get_value("activation_keys"):
            self.subscription_datetime.prepare_passcodes_for_both_one_time_and_installment()

    def run(self):
        """Run the main application."""
        app, ui = self.setup_app()

        if not self.ej.is_fully_owned():
            if self.ej.check_activation_status(): # Where the program is activated
                if self.ej.is_payment_installment_type():
                    if self.has_expired_montly_usage():
                        self.ej.printYellow("Inside has expired")
                        self.create_activation_dialog_and_continue(ui, False)
                    else:
                        self.start_main_ui(ui)
            else: # not activated yet, so, start the activation process
                self.generate_activation_codes()
                self.create_activation_dialog_and_continue(ui, True)
        else:
            self.start_main_ui(ui)

        # Run the application
        exit_code = app.exec()

        # Log exit code
        if exit_code != 0:
            print(f"Application exited with error code: {exit_code}")
            with open("error_log.txt", "a") as log_file:
                log_file.write(f"Application exited with error code: {exit_code}\n")

        # Cleanup shared memory
        if self.shared_memory.isAttached():
            self.shared_memory.detach()

        sys.exit(exit_code)

# Global Exception Handler
def handle_exception(exc_type, exc_value, exc_traceback):
    # Get traceback information
    import traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    error_message = ''.join(tb_lines)

    # Log the full exception to a file
    with open("error_log.txt", "a") as log_file:
        log_file.write(error_message + "\n")

    # Show the exception details in a message box to the user
    app = QApplication.instance()  # Get the current QApplication instance
    if app:
        QMessageBox.critical(None, "April ran into an error and catched it", f"An error occurred:\n{exc_value}\n\nDetails:\n{error_message}")
    else:
        print(f"An error occurred:\n{exc_value}\n\nDetails:\n{error_message}")

    sys.exit(1)  # Exit the application with error code

sys.excepthook = handle_exception

if __name__ == "__main__":
    instance_app = SingleInstanceApp()

    if instance_app.is_another_instance_running():
        instance_app.bring_up_main_window()
        sys.exit(1)  # Exit the new instance
    else:
        instance_app.run()
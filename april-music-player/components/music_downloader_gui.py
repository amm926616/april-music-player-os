import subprocess
import sys
import urllib.parse

from PyQt6.QtCore import QProcess, Qt
from PyQt6.QtGui import QAction, QIcon, QKeyEvent
from PyQt6.QtWidgets import (
    QCheckBox, QGroupBox, QMenu, QMenuBar, QRadioButton, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QPlainTextEdit, QWidgetAction
)

from components.credential_dialog import CredentialDialog
from _utils.easy_json import EasyJson


class MusicDownloaderWidget(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.process = None
        self.ej = EasyJson()
        self.parent = parent
        self.round_line_style = f"""
            QGroupBox {{
                border: 1px solid palette(light); /* Use system palette color for border */
                border-radius: 5px; /* Rounded corners */
                margin-top: 10px; /* Space between the title and the group box */
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px; /* Space for the title */
                padding: 5px; /* Space around the title text */
                font-weight: bold; /* Make title bold */
            }}
        """

        self.toggle_reload_directories = self.parent.toggle_reload_directories
        self.lyrics_downloader_dict = self.ej.get_value("lyrics_downloaders")
        self.during_downloading = False
        self.downloaded_something = False

        # Initialize the layout
        self.setWindowTitle("Experimentation of Command Line Music Downloader Implementation")
        self.setWindowIcon(QIcon(self.parent.icon_path))
        self.setGeometry(100, 100, 600, 400)
        main_layout = QVBoxLayout()

        # Add the menubar to the main layout
        main_layout.setMenuBar(self.create_menubar())

        # self.activte_zotify_label = QLabel("You Need to generate spotify credentials to be able to download songs from spotify")
        # self.activate_zotify_button = QPushButton("Activate zotify")
        # main_layout.addWidget(self.activte_zotify_label)
        # main_layout.addWidget(self.activate_zotify_button)

        url_layout = QHBoxLayout()

        # URL input field
        self.url_input = QLineEdit()
        self.url_input.setFocus()
        self.url_input.setPlaceholderText("Paste Song Url Here...")
        self.url_input.returnPressed.connect(self.start_download)
        url_layout.addWidget(self.url_input)

        # Download button
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.start_download)
        url_layout.addWidget(self.download_button)

        link_name_toggle = QCheckBox("Search Mode")
        link_name_toggle.setChecked(True)
        # link_name_toggle.triggered.connect(self.switch_search_type)

        # Terminal-like output display
        self.output_display = QPlainTextEdit()
        self.output_display.setReadOnly(True)

        display_laytout = QVBoxLayout()
        display_laytout.addWidget(self.output_display)

        display_group_box = QGroupBox("Terminal Output", self)
        display_group_box.setStyleSheet(self.round_line_style)
        display_group_box.setLayout(display_laytout)

        main_layout.addLayout(url_layout)
        main_layout.addWidget(link_name_toggle)
        main_layout.addWidget(display_group_box)

        self.setLayout(main_layout)
        self.start_download_process()

    def start_generating_credentials(self):
        CredentialDialog().exec()

    def start_download_process(self):
        """
        Initialize QProcess for running the download commands.
        """
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyRead.connect(self.update_output)  # Unified readyRead signal
        self.process.finished.connect(self.on_download_finished)

    def create_menubar(self):
        # Create the menubar
        menubar = QMenuBar(self)
        self.create_menu_actions()

        # Create "File" menu and add actions
        configuration_menu = menubar.addMenu("Configurations")

        # Create "Help" menu and add actions
        help_menu = menubar.addMenu("Help")
        help_menu.addAction(self.about_action)

        # assigning actions and menus
        configuration_menu.addMenu(self.create_music_downloader_selection_radio_buttons())
        configuration_menu.addMenu(self.create_lyrics_downloader_menu())

        # configuration_menu.addAction(self.exit_action)

        return menubar

    def create_menu_actions(self):
        # exit action
        self.exit_action = QAction("Exit", self)
        self.exit_action.triggered.connect(self.close)

        self.about_action = QAction("About", self)
        self.about_action.triggered.connect(self.show_about_dialog)

    def create_music_downloader_selection_radio_buttons(self):
        # Create a menu to hold the radio buttons
        music_downloader_menu = QMenu("Music Downloader", self)

        # List of music downloader options
        downloader_list = ["zotify", "spotDL"]
        self.downloader_radio_buttons = {}

        # Add each downloader option as a radio button in the menu without closing on click
        for downloader in downloader_list:
            radio_button = QRadioButton(downloader)
            radio_button.toggled.connect(lambda checked, d=downloader: self.set_music_downloader(d) if checked else None)

            # Wrap the radio button in a QWidgetAction and add it to the menu
            radio_action = QWidgetAction(self)
            radio_action.setDefaultWidget(radio_button)
            music_downloader_menu.addAction(radio_action)
            self.downloader_radio_buttons[downloader] = radio_button

        # Optionally, set a default selection
        self.downloader_radio_buttons[self.ej.get_value("selected_music_downloader")].setChecked(True)

        return music_downloader_menu

    def create_lyrics_downloader_menu(self):
        # Create a menu to hold checkboxes
        lyrics_menu = QMenu("Lyrics Downloaders", self)

        # List of lyrics downloader options
        lyrics_downloader_list = ["lrcdl", "syrics"]

        # Dictionary to hold the checkboxes for easy access
        self.lyrics_checkbox_actions = {}

        # Add each downloader option as a checkbox in the menu without closing on click
        for downloader in lyrics_downloader_list:
            checkbox = QCheckBox(downloader)
            checkbox_action = QWidgetAction(self)
            checkbox_action.setDefaultWidget(checkbox)

            # Use stateChanged signal instead of triggered and capture downloader correctly
            checkbox.stateChanged.connect(lambda state, d=downloader: self.check_lyrics_downloader(state, d))

            lyrics_menu.addAction(checkbox_action)
            self.lyrics_checkbox_actions[downloader] = checkbox
            checkbox.setChecked(self.lyrics_downloader_dict[downloader])

        return lyrics_menu

    def set_music_downloader(self, downloader):
        self.ej.edit_value("selected_music_downloader", downloader)
        if downloader == "zotify":
            if not self.ej.check_zotify_credential_format():
                self.start_generating_credentials()

    def check_lyrics_downloader(self, checked: int, downloader: str):
        # Convert checked state to boolean
        is_checked = checked == 2  # True if checked (2), False if unchecked (0)

        # Update the dictionary with the boolean value
        self.lyrics_downloader_dict[downloader] = is_checked

        # Debug print to check the lyrics downloader dictionary
        print("After checking lyrics downloader:", self.lyrics_downloader_dict)

        # Persist the updated dictionary
        self.ej.edit_value("lyrics_downloaders", self.lyrics_downloader_dict)

    def show_about_dialog(self):
        self.output_display.appendPlainText("This is the only output you can see in This Music Downloader\n")

    def start_download(self):
        """
        Start the download process with the specified URL.
        """
        url = self.url_input.text().strip()
        if not url:
            self.output_display.appendPlainText("Please enter a URL.\n")
            return

        # Extract the actual Spotify link if the URL is a redirect
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Check if 'url' is present in the query parameters
        if 'url' in query_params:
            # Extract the Spotify link from the 'url' parameter
            url = query_params['url'][0]

        # Validate the URL
        if not url.startswith("https://open.spotify.com/"):
            self.output_display.appendPlainText(
                "Invalid URL. Please enter a valid Spotify URL starting with 'https://open.spotify.com/'.\n"
            )
            return

        # Proceed with the download
        self.downloaded_something = True
        self.url_input.clear()

        try:
            # Define the command
            command = [sys.executable, "-m", "zotify", "url", url]

            # Start the subprocess and capture its output
            process = subprocess.Popen(
                command,
                cwd=self.ej.script_path,  # Set working directory for the process
                stdout=subprocess.PIPE,    # Capture standard output
                stderr=subprocess.PIPE     # Capture error output
            )

            # Append initial message to the output display
            self.output_display.appendPlainText("Starting download...\n")

            # Read the process output and error, and append to the output display
            for line in iter(process.stdout.readline, b''):  # Read output line by line
                self.output_display.appendPlainText(line.decode('utf-8'))  # Decode bytes to string

            # Also capture and append error messages (if any)
            for line in iter(process.stderr.readline, b''):  # Read error line by line
                self.output_display.appendPlainText(f"ERROR: {line.decode('utf-8')}")  # Decode bytes to string

            process.stdout.close()
            process.stderr.close()
            process.wait()

        except Exception as e:
            self.output_display.appendPlainText(f"Failed to start the download process: {e}\n")

    def switch_mode(self):
        if self.during_downloading:
            self.download_button.setText("Restart")
            self.download_button.clicked.disconnect()
            self.download_button.clicked.connect(self.restart_download)
        else:
            self.download_button.setText("Download")
            self.download_button.clicked.disconnect()
            self.download_button.clicked.connect(self.start_download)

    def closeEvent(self, event):
        if self.downloaded_something:
            self.toggle_reload_directories()
        super().closeEvent(event)

    def update_output(self):
        """
        Update the output display with text from the subprocess.
        """
        output = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        if output:
            self.output_display.appendPlainText(output)

        error = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        if error:
            self.output_display.appendPlainText(error)

        # Automatically scroll to the end of the output display
        self.output_display.moveCursor(self.output_display.textCursor().MoveOperation.End)

    def on_download_finished(self):
        """
        Handle completion of the download process.
        """
        self.output_display.appendPlainText("\nDownload complete!\n")
        self.switch_mode()
        self.during_downloading = False

    def restart_download(self):
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished()

        self.output_display.appendPlainText("\nRestarting download...\n")
        self.start_download()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()


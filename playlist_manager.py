import os
import json

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QListWidget, QMessageBox, QDialog, QMenu, QVBoxLayout, QPushButton, QHBoxLayout, QAbstractItemView
)
from PyQt6.QtGui import QAction, QKeyEvent


class PlaylistDialog(QDialog):
    def __init__(self, parent=None, passed_load_playlist_method=None):
        super().__init__(parent)
        self.playlist_folder = os.path.join(parent.ej.get_value("config_path"), "playlists")
        self.passed_load_playlist_method = passed_load_playlist_method

        # Set up the layout
        self.layout = QVBoxLayout(self)

        self.playlist_list = QListWidget()
        self.playlist_list.setToolTip("Double click or press enter to load the playlist, \nPress delete key to delete")
        self.layout.addWidget(self.playlist_list)

        # Add buttons for delete and refresh functionality
        self.delete_button = QPushButton("Delete Playlist")
        self.layout.addWidget(self.delete_button)
        self.refresh_button = QPushButton("Refresh List")
        self.layout.addWidget(self.refresh_button)

        # Connect button actions
        self.delete_button.clicked.connect(self.delete_playlist)
        self.refresh_button.clicked.connect(self.load_playlists)

        # Connect double-click signal to the action
        self.playlist_list.itemDoubleClicked.connect(self.handle_double_click)

        # Context menu on right-click
        self.playlist_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_list.customContextMenuRequested.connect(self.show_context_menu)

        # Set dialog properties (optional)
        self.setWindowTitle("Double Click on the items to load the playlist")
        self.setFixedSize(400, 300)  # Set a fixed size for the dialog
        self.setModal(True)  # Make the dialog modal (blocks interaction with other windows)

        # Load playlists into the list widget
        self.load_playlists()
        self.playlist_list.setFocus()

    def load_playlists(self):
        """Load playlist JSON files into the QListWidget."""
        if not os.path.exists(self.playlist_folder):
            os.makedirs(self.playlist_folder)

        self.playlist_list.clear()
        for filename in os.listdir(self.playlist_folder):
            if filename.endswith(".json"):
                playlist_name = os.path.splitext(filename)[0]
                self.playlist_list.addItem(playlist_name)

    def handle_double_click(self, item):
        """Handle double-click on a playlist."""
        playlist_name = item.text()
        playlist_path = os.path.join(self.playlist_folder, f"{playlist_name}.json")

        # Call the passed method to handle the playlist loading
        self.passed_load_playlist_method(playlist_path)

        self.close()

        # Show a message box indicating the playlist has been loaded
        QMessageBox.information(
            self,
            "Playlist Loaded",
            f"Playlist '{playlist_name}' has been loaded from:\n{playlist_path}",
            QMessageBox.StandardButton.Ok
        )

    def delete_playlist(self):
        """Delete the selected playlist from the list and file system."""
        current_item = self.playlist_list.currentItem()
        if current_item:
            playlist_name = current_item.text()
            playlist_path = os.path.join(self.playlist_folder, f"{playlist_name}.json")

            # Confirm deletion
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete the playlist '{playlist_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                try:
                    os.remove(playlist_path)
                    self.load_playlists()  # Reload the playlist list
                    QMessageBox.information(self, "Success", f"Playlist '{playlist_name}' deleted.")
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to delete playlist '{playlist_name}':\n{e}",
                        QMessageBox.StandardButton.Ok
                    )
        else:
            QMessageBox.warning(self, "No Playlist Selected", "Please select a playlist to delete.")

    def edit_playlist(self):
        """Open the EditPlaylistDialog to edit the selected playlist."""
        current_item = self.playlist_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Playlist Selected", "Please select a playlist to edit.")
            return

        playlist_name = current_item.text()
        playlist_path = os.path.join(self.playlist_folder, f"{playlist_name}.json")

        # Open the editing dialog
        dialog = EditPlaylistDialog(self.passed_load_playlist_method, playlist_path, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload playlists after editing
            self.load_playlists()
            QMessageBox.information(self, "Playlist Updated", f"Playlist '{playlist_name}' has been updated.")

    def show_context_menu(self, pos):
        """Show a context menu when right-clicking on a playlist."""
        context_menu = QMenu(self)

        # Add actions to the context menu
        delete_action = QAction("Delete Playlist", self)
        edit_action = QAction("Edit Playlist", self)  # New action for editing
        context_menu.addAction(delete_action)
        context_menu.addAction(edit_action)

        # Connect actions to methods
        delete_action.triggered.connect(self.delete_playlist)
        edit_action.triggered.connect(self.edit_playlist)  # New method

        # Show the context menu at the right-click position
        context_menu.exec(self.playlist_list.mapToGlobal(pos))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_playlist()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        elif (event.key() == Qt.Key.Key_Return) or (event.key() == Qt.Key.Key_Enter):
            self.handle_double_click(self.playlist_list.currentItem())
        else:
            # For other keys, use the default behavior
            super().keyPressEvent(event)

class EditPlaylistDialog(QDialog):
    def __init__(self, load_table_data_method, playlist_path, parent=None):
        super().__init__(parent)
        self.load_table_data = load_table_data_method
        self.playlist_path = playlist_path
        self.setWindowTitle("Edit Playlist")
        self.setMinimumSize(600, 400)

        # Layout
        self.layout = QVBoxLayout(self)

        # Add buttons
        self.button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Entry")
        self.delete_button = QPushButton("Delete Entry")
        self.save_button = QPushButton("Save Changes")
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.delete_button)
        self.button_layout.addWidget(self.save_button)
        self.layout.addLayout(self.button_layout)

        # Connect buttons
        self.add_button.clicked.connect(self.add_entry)
        self.delete_button.clicked.connect(self.delete_entry)
        self.save_button.clicked.connect(self.save_changes)

        # Load initial data using the provided method
        self.load_table_data(self.playlist_path)

    def add_entry(self):
        """Add a new entry to the playlist."""
        new_entry = {
            "items": [""] * 9,  # Create a default empty row
            "row_type": "normal",
            "font": None,
            "colspan": None
        }

        # Load existing data
        with open(self.playlist_path, 'r') as file:
            data = json.load(file)

        # Add the new entry
        data.append(new_entry)

        # Save back to file
        with open(self.playlist_path, 'w') as file:
            json.dump(data, file, indent=4)

        # Reload the table
        self.load_table_data(self.playlist_path)
        QMessageBox.information(self, "Entry Added", "A new entry has been added to the playlist.")

    def delete_entry(self):
        """Delete the selected entry from the playlist."""
        # Load existing data
        with open(self.playlist_path, 'r') as file:
            data = json.load(file)

        if not data:
            QMessageBox.warning(self, "No Entries", "The playlist is empty.")
            return

        # Let the user confirm the deletion
        reply = QMessageBox.question(
            self,
            "Delete Entry",
            "Are you sure you want to delete the last entry?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Remove the last entry (or specify another selection method)
            removed_entry = data.pop()

            # Save back to file
            with open(self.playlist_path, 'w') as file:
                json.dump(data, file, indent=4)

            # Reload the table
            self.load_table_data(self.playlist_path)
            QMessageBox.information(
                self,
                "Entry Deleted",
                f"Removed the following entry:\n{removed_entry['items']}"
            )

    def save_changes(self):
        """Save changes and close the dialog."""
        QMessageBox.information(self, "Saved", "All changes have been saved.")
        self.accept()

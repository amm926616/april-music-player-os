from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QCheckBox, QScrollArea, QWidget, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt
from _utils.easy_json import EasyJson


class AddNewDirectory(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ej = EasyJson()
        self.parent = parent
        self.directories = self.ej.get_value("music_directories") or {}

        self.scroll_area_widget = QWidget()
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_widget)
        self.scroll_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.setWindowTitle("Manage Music Directories")
        self.resize(500, 400)

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.button_layout = QHBoxLayout()

        # Info label and Add button
        self.info_label = QLabel("Choose directories to load music from:")
        self.add_button = QPushButton("Add New Directory")

        # Select All checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.clicked.connect(self.select_all_directories)

        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_area_widget)

        # Build layout
        self.main_layout.addWidget(self.info_label)
        self.main_layout.addWidget(self.select_all_checkbox)
        self.main_layout.addWidget(self.scroll_area)
        self.button_layout.addWidget(self.add_button)
        self.main_layout.addLayout(self.button_layout)

        # Signals
        self.add_button.clicked.connect(self.add_directory)

        # Load existing directories
        self.load_saved_directory()
        self.are_all_checkboxes_checked()

    def create_directory_row(self, directory: str, is_checked: bool):
        """Create a single row for a directory entry."""
        item_widget = QWidget()
        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(4, 2, 4, 2)

        # Checkbox (without long label)
        checkbox = QCheckBox()
        checkbox.setChecked(is_checked)
        checkbox.stateChanged.connect(self.update_folder_status)

        # Directory label
        dir_label = QLabel()
        dir_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        dir_label.setToolTip(directory)
        dir_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        dir_label.setMinimumWidth(200)
        dir_label.setMaximumHeight(25)
        dir_label.setText(directory if len(directory) < 60 else f"...{directory[-60:]}")

        # Remove button
        remove_btn = QPushButton("-")
        remove_btn.setMaximumWidth(30)
        remove_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        remove_btn.clicked.connect(lambda _, d=directory, cb=checkbox: self.remove_single_directory(d, cb))

        # Add to layout
        item_layout.addWidget(checkbox)
        item_layout.addWidget(dir_label)
        item_layout.addStretch()
        item_layout.addWidget(remove_btn)

        # Add to scroll area
        self.scroll_area_layout.addWidget(item_widget)

    def load_saved_directory(self):
        for directory, value in self.directories.items():
            self.create_directory_row(directory, value)

    def add_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            if directory not in self.directories:
                self.directories[directory] = True
                self.ej.edit_value("music_directories", self.directories)

                self.create_directory_row(directory, True)
                self.are_all_checkboxes_checked()
            else:
                QMessageBox.information(self, "Directory Exists", "This directory is already added.")

    def remove_single_directory(self, directory, checkbox):
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove directory:\n{directory}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if directory in self.directories:
                del self.directories[directory]

            parent_widget = checkbox.parent()
            if parent_widget:
                self.scroll_area_layout.removeWidget(parent_widget)
                parent_widget.deleteLater()

            self.ej.edit_value("music_directories", self.directories)
            self.are_all_checkboxes_checked()

    def are_all_checkboxes_checked(self):
        if not self.directories:
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.setEnabled(False)
            return

        checkboxes = self.scroll_area_widget.findChildren(QCheckBox)
        all_checked = all(cb.isChecked() for cb in checkboxes if cb != self.select_all_checkbox)

        self.select_all_checkbox.blockSignals(True)
        self.select_all_checkbox.setChecked(all_checked)
        self.select_all_checkbox.setEnabled(True)
        self.select_all_checkbox.blockSignals(False)

    def select_all_directories(self, state):
        checkboxes = [cb for cb in self.scroll_area_widget.findChildren(QCheckBox)
                      if cb != self.select_all_checkbox]

        for checkbox in checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(state)
            checkbox.blockSignals(False)

        for directory in self.directories:
            self.directories[directory] = state

        self.ej.edit_value("music_directories", self.directories)

    def update_folder_status(self):
        sender = self.sender()
        directory = None

        # Find associated label to get directory text
        for widget in self.scroll_area_widget.findChildren(QWidget):
            layout = widget.layout()
            if layout and layout.itemAt(0).widget() is sender:
                label = layout.itemAt(1).widget()
                if isinstance(label, QLabel):
                    directory = label.toolTip()  # Original full path
                    break

        if directory:
            self.directories[directory] = sender.isChecked()
            self.ej.edit_value("music_directories", self.directories)
            self.are_all_checkboxes_checked()

    def load_all_directories(self):
        selected_dirs = [cb.text() for cb in self.scroll_area_widget.findChildren(QCheckBox)
                         if cb.isChecked() and cb != self.select_all_checkbox]

        if selected_dirs:
            self.parent.albumTreeWidget.loadSongsToCollection(self.directories, loadAgain=True)
        else:
            QMessageBox.warning(self, "No Directory Selected", "Please select at least one directory to load.")

    def closeEvent(self, event):
        self.load_all_directories()
        event.accept()

from PyQt6.QtWidgets import (
    QFileDialog, QLabel, QPushButton,
    QVBoxLayout, QDialog, QSpinBox, QHBoxLayout, QGroupBox
)
from PyQt6.QtGui import QFontDatabase, QIcon, QKeyEvent
from fontTools.ttLib import TTFont
from PyQt6.QtCore import Qt
from _utils.easy_json import EasyJson

def create_language_layout(language_label, font_label, example_label, change_button):
    """ Helper function to create a horizontal layout for each language section """
    layout = QHBoxLayout()
    layout.addWidget(language_label)
    layout.addWidget(font_label)
    layout.addWidget(example_label)  # Add the example label next to the font label
    layout.addStretch(1)  # Stretch to push the button to the right
    layout.addWidget(change_button)
    return layout


def get_font_name_from_file(font_path):
    try:
        font = TTFont(font_path)
        name_records = font['name'].names
        for record in name_records:
            if record.nameID == 4:  # Name ID 4 usually contains the full font name
                return record.toStr()
    except Exception:
        pass
    return "Unknown Font"  # Default if nameID 4 is not found or there is an error


class FontSettingsWindow(QDialog):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(parent)  # Initialize the parent QDialog

        self.ej = EasyJson()

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

        self.setGeometry(200, 200, 500, 300)
        self.setWindowTitle("Font Settings")
        self.setWindowIcon(QIcon(parent.icon_path))
        self.setStyleSheet("QPushButton { padding: 5px; }")

        # List of languages
        self.languages = ["English", "Korean", "Japanese", "Chinese"]
        self.translations = {
            "English": "[I love music]",
            "Korean": "[나는 음악을 사랑해요]",
            "Japanese": "[私は音楽が大好きです]",
            "Chinese": "[我爱音乐]"
        }

        # Dictionary to store widgets for each language
        self.font_labels = {}  # Ensure that this dictionary is populated properly
        self.change_buttons = {}

        # Dictionary to store example labels for each language
        self.example_labels = {}

        # Dictionary to store the current font for each language
        self.fonts = {language: None for language in self.languages}

        # Main layout
        main_layout = QVBoxLayout()

        # Header label
        label = QLabel("<b>Current Configured Fonts by Language</b>", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(label)

        # Create font group box for each language
        font_group_box = QGroupBox("Language Fonts", self)
        font_group_box.setStyleSheet(self.round_line_style)

        font_layout = QVBoxLayout()

        for language in self.languages:
            current_font = self.ej.get_value(f"{language.lower()}_font")
            font_name = get_font_name_from_file(current_font)

            # Language and font name labels
            language_label = QLabel(f"{language}:", self)
            font_label = QLabel(f"{font_name}", self)

            # Store the font label for later updates
            self.font_labels[language] = font_label  # Add the font_label to the dictionary

            # Example label with translated text
            example_label = QLabel(self.translations[language], self)
            if current_font:
                example_font = QFontDatabase.font(font_name, '', 12)
                example_label.setFont(example_font)

            # Store the example label in the dictionary for future updates
            self.example_labels[language] = example_label

            # Change font button
            change_button = QPushButton("Change Font", self)
            change_button.clicked.connect(lambda checked, lang=language: self.load_font(lang))

            # Add the layout with the example label to the font_layout
            font_layout.addLayout(create_language_layout(language_label, font_label, example_label, change_button))

        font_group_box.setLayout(font_layout)
        main_layout.addWidget(font_group_box)

        # LRC Font size configuration
        size_group_box = QGroupBox("LRC Lyrics Display", self)
        size_group_box.setStyleSheet(self.round_line_style)
        size_layout = QHBoxLayout()

        self.lrc_font_size_label = QLabel("LRC Font Size:", self)
        self.lrc_font_size_spinbox = QSpinBox(self)
        self.lrc_font_size_spinbox.setRange(10, 100)
        self.lrc_font_size_spinbox.setValue(self.ej.get_value("lrc_font_size"))  # Default font size
        self.lrc_font_size_spinbox.valueChanged.connect(self.update_lrc_font_size)

        # Connect the editingFinished signal to a function
        self.lrc_font_size_spinbox.editingFinished.connect(self.close)

        size_layout.addWidget(self.lrc_font_size_label)
        size_layout.addWidget(self.lrc_font_size_spinbox)
        size_group_box.setLayout(size_layout)

        main_layout.addWidget(size_group_box)

        # Add the save label to inform the user
        save_label = QLabel("Press [Ctrl + S] to save configurations and exit.")
        save_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(save_label)

        # Set the main layout
        self.setLayout(main_layout)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.close()

    def update_lrc_font_size(self, value):
        self.ej.edit_value("lrc_font_size", value)
        self.parent.lrcPlayer.lrc_font.font_size = value
        self.parent.lrcPlayer.lrc_font.reloadFont()

    def load_font(self, language):
        """ Open a file dialog and load a font for the selected language """
        font_file, _ = QFileDialog.getOpenFileName(
            self, "Open Font File", "", "Font Files (*.ttf *.otf)"
        )
        if font_file:
            self.fonts[language] = get_font_name_from_file(font_file)
            self.update_font_display(language)

            # Update the example label with the selected font
            example_font = QFontDatabase.font(self.fonts[language], '', 12)
            self.example_labels[language].setFont(example_font)  # Ensure the example label font is updated

            # Update the stored font file
            self.ej.edit_value(f"{language.lower()}_font", font_file)

            # Reload the fonts in the parent if necessary
            self.parent.lrcPlayer.media_font.reloadFont()
            self.parent.lrcPlayer.lrc_font.reloadFont()

    def update_font_display(self, language):
        """ Update the QLabel for the selected language with the chosen font """
        if language in self.font_labels:
            self.font_labels[language].setText(f"{self.fonts[language]}")

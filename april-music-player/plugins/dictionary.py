import inspect
import os
import platform
import sqlite3
from PyQt6.QtCore import Qt  # for shortcuts
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (QMessageBox, QVBoxLayout, QLineEdit, QPushButton, QFormLayout,
                             QTextEdit, QDialog)

from _utils.easy_json import EasyJson


class VocabularyManager(QDialog):
    def __init__(self, parent=None):
        super().__init__()
        self.cursor = None
        self.conn = None
        self.result_text = None
        self.view_button = None
        self.delete_button = None
        self.add_button = None
        self.search_button = None
        self.meaning_input = None
        self.word_input = None
        self.icon_path = None
        self.os_name = None
        self.db_path = None
        self.parent = parent
        self.ej = EasyJson()
        self.setup()
        self.initUI()

    def setup(self):
        self.os_name = platform.system()

        self.icon_path = os.path.join(self.ej.script_path, "icons", "dictionary.png")
        db_dir = ""
        if self.os_name == "Linux":
            db_dir = os.path.join(os.environ['HOME'], '.config', 'april-music-player')
            os.makedirs(db_dir, exist_ok=True)

        elif self.os_name == "Windows":
            print("inside os windows else if")
            db_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'April Music Player')
            os.makedirs(db_dir, exist_ok=True)
            print(db_dir)

        self.db_path = os.path.join(db_dir, 'databases', 'vocabulary.db')
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initDB()        

    def initUI(self):
        self.setWindowTitle('Personal Dictionary')

        # The icon
        self.setWindowIcon(QIcon(self.icon_path))

        # Make the window always on top
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        # Layouts
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Widgets
        self.word_input = QLineEdit()
        self.meaning_input = QLineEdit()
        self.add_button = QPushButton('Add Entry')
        self.search_button = QPushButton('Search Entry')
        self.delete_button = QPushButton('Delete Entry')
        self.view_button = QPushButton('View All Entries')
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)

        # Layouts
        form_layout.addRow('Word:', self.word_input)
        form_layout.addRow('Meaning:', self.meaning_input)
        layout.addLayout(form_layout)
        layout.addWidget(self.add_button)
        layout.addWidget(self.search_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.view_button)
        layout.addWidget(self.result_text)

        self.setLayout(layout)

        # Connect buttons
        self.add_button.clicked.connect(self.add_entry)
        self.search_button.clicked.connect(self.search_entry)
        self.delete_button.clicked.connect(self.delete_entry)
        self.view_button.clicked.connect(self.view_all_entries)

        # # Connect returnPressed signal to the search_entry method
        # self.word_input.returnPressed.connect(self.search_entry)
        # self.meaning_input.returnPressed.connect(self.add_entry)

    def initDB(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocabulary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL,
            meaning TEXT
        )
        ''')
        self.conn.commit()

    def add_entry(self):
        print("inside add entry")
        # Get the frame of the caller
        caller_frame = inspect.currentframe().f_back
        # Get file name and line number of the caller
        caller_info = inspect.getframeinfo(caller_frame)
        print(f"Called from File: {caller_info.filename}, Line: {caller_info.lineno}")

        word = self.word_input.text().strip()
        meaning = self.meaning_input.text().strip()

        if word and meaning:
            # Check if the exact word and meaning combination already exists
            self.cursor.execute('SELECT 1 FROM vocabulary WHERE word = ? AND meaning = ?', (word, meaning))
            result = self.cursor.fetchone()
            if result:
                # If the meaning exists, notify the user
                self.result_text.setText(
                    f'The meaning "{meaning}" for the word "{word}" already exists in the dictionary.')
                print(result)
                print(type(result))
            else:
                # If the entry does not exist, add it to the database
                self.cursor.execute('INSERT INTO vocabulary (word, meaning) VALUES (?, ?)', (word, meaning))
                self.conn.commit()
                self.result_text.setText(f'Added: {word} - {meaning}')
        else:
            # Notify the user if either the word or meaning is empty
            self.result_text.setText('Please provide both word and meaning.')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.search_entry()

        elif event.key() == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.delete_entry()

        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.word_input.hasFocus():
                self.search_entry()
            elif self.meaning_input.hasFocus():
                self.add_entry()

        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            print("pressed ctrl + w")
            self.close()  # You can use sys.exit() here if you want to exit the entire app

        elif event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_W:
            self.close()

        # Handle Exit key (example: Esc key)
        elif event.key() == Qt.Key.Key_Escape:
            print("Escape pressed, exiting application")
            self.close()  
        else:
            super().keyPressEvent(event)

    def delete_entry(self):
        word = self.word_input.text().strip()
        meaning = self.meaning_input.text().strip()
        if word and meaning:
            reply = QMessageBox.question(
                self,
                'Delete Entry',
                f'Are you sure you want to delete the meaning "{meaning}" from the word "{word}"?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.cursor.execute('DELETE FROM vocabulary WHERE word = ? AND meaning = ?', (word, meaning))
                if self.cursor.rowcount > 0:
                    self.conn.commit()
                    self.result_text.setText(f'Deleted meaning "{meaning}" from word "{word}"')
                else:
                    self.result_text.setText('No matching meaning found for deletion.')
        else:
            self.result_text.setText('Please provide both word and meaning.')

    def search_entry(self):
        print("inside search entry")
        word = self.word_input.text().strip()

        if not word:
            return

        self.cursor.execute('SELECT meaning FROM vocabulary WHERE word = ?', (word,))
        base_results = self.cursor.fetchall()

        syllables = [word[i:i + 1] for i in range(len(word))]  # Each character as a syllable
        related_results = {syllable: [] for syllable in syllables}

        combinations = []
        if len(syllables) > 2:
            for i in range(1, len(syllables)):
                combination = ''.join(syllables[:i + 1])
                combinations.append(combination)

        remove_list = [" ", "하", "다", "하다", "를", "을"]

        for syllable in syllables + combinations:
            for remove in remove_list:
                syllable = syllable.replace(remove, "")

            if syllable:
                self.cursor.execute('SELECT word, meaning FROM vocabulary WHERE word LIKE ?', (f'%{syllable}%',))
                results = self.cursor.fetchall()

                filtered_results = [(w, m) for w, m in results if w != word]
                related_results[syllable] = filtered_results

        display_text = ""

        if base_results:
            display_text += f"Base Meaning for '{word}':\n"
            display_text += '\n'.join([f'- {meaning[0]}' for meaning in base_results])
            display_text += "\n\n"
        else:
            display_text += f"No exact match found for '{word}'.\n\n"

        if any(related_results.values()):
            display_text += "Related Meanings:"
            for syllable, results in related_results.items():
                if results:
                    display_text += f"\nSyllable/Combination '{syllable}':\n"
                    display_text += '\n'.join([f'{w}: {m}' for w, m in results])
                    display_text += "\n"
        else:
            display_text += "No related meanings found."

        self.result_text.setText(display_text)
        self.meaning_input.clear()

    def view_all_entries(self):
        self.cursor.execute('SELECT word, meaning FROM vocabulary')
        entries = self.cursor.fetchall()
        display_text = '\n'.join([f'{i + 1}. {word}: {meaning}' for i, (word, meaning) in enumerate(entries)])
        self.result_text.setText(display_text)

    def closeEvent(self, event):
        self.parent.music_player.play_pause_music()
        # Clear the text box
        self.word_input.clear()
        self.meaning_input.clear()
        event.accept()

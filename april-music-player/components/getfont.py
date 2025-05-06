from fontTools.ttLib import TTFont
import os
from PyQt6.QtGui import QFont, QFontDatabase, QTextCharFormat, QTextDocument, QTextCursor
from _utils.easy_json import EasyJson

"""
preformatted fonts for different languages
method will get text. return html text which is accessible by QLabel

in GetFont class
setup fonts with language, setup QDatabase, QFont
apply format, return html text
"""


def create_text_format(font_name, font_size):
    font = QFont(font_name, font_size)
    text_format = QTextCharFormat()
    text_format.setFont(font)
    return text_format


class GetFont:
    def __init__(self, font_size=14):
        self.ej = EasyJson()
        self.language_dict = None
        self.font_size = font_size
        self.load_font_settings()  # Initialize the font settings
        self.fonts_loaded = False
        self.formats = {}

        self.LANGUAGE_RANGES = {
            "english": (0x0041, 0x007A),  # A-Z, a-z
            "korean": (0xAC00, 0xD7A3),
            "japanese": [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x4E00, 0x9FFF)],
            "chinese": (0x4e00, 0x9fff)
        }

    def load_font_settings(self):
        english_font = self.ej.get_value("english_font")
        korean_font = self.ej.get_value("korean_font")
        japanese_font = self.ej.get_value("japanese_font")
        chinese_font = self.ej.get_value("chinese_font")

        self.language_dict = {
            "korean": {"font_name": self.get_font_name(korean_font), "file_path": korean_font, "size": self.font_size},
            "english": {"font_name": self.get_font_name(english_font), "file_path": english_font,
                        "size": self.font_size},
            "japanese": {"font_name": self.get_font_name(japanese_font), "file_path": japanese_font,
                         "size": self.font_size},
            "chinese": {"font_name": self.get_font_name(chinese_font), "file_path": chinese_font,
                        "size": self.font_size}
        }

    def loadFonts(self):
        QFontDatabase.addApplicationFont(os.path.join(self.ej.script_path, "fonts/KOMIKAX_.ttf"))

        loaded_fonts = set()
        for lang, font_info in self.language_dict.items():
            if font_info["file_path"] and font_info["file_path"] not in loaded_fonts:
                try:
                    QFontDatabase.addApplicationFont(font_info["file_path"])
                    loaded_fonts.add(font_info["file_path"])
                except Exception as e:
                    print(f"Error loading font {font_info['font_name']}: {e}")
            self.formats[lang] = create_text_format(font_info["font_name"], font_info["size"])
        self.fonts_loaded = True

    def detect_language(self, char):
        code = ord(char)
        if self.LANGUAGE_RANGES["english"][0] <= code <= self.LANGUAGE_RANGES["english"][1]:
            return "english"
        elif self.LANGUAGE_RANGES["korean"][0] <= code <= self.LANGUAGE_RANGES["korean"][1]:
            return "korean"
        elif self.LANGUAGE_RANGES["chinese"][0] <= code <= self.LANGUAGE_RANGES["chinese"][1]:
            return "chinese"
        for range_set in self.LANGUAGE_RANGES["japanese"]:
            if isinstance(range_set, tuple) and range_set[0] <= code <= range_set[1]:
                return "japanese"
        return None

    # def apply_fonts_to_text(self, text):  # new method, still needs fixes
    #     if not self.fonts_loaded:
    #         self.loadFonts()

    #     doc = QTextDocument()
    #     cursor = QTextCursor(doc)

    #     word = ''
    #     for char in text:
    #         if char.isalnum():  # If it's alphanumeric, treat it as part of a word
    #             word += char
    #         elif char in string.punctuation:  # Include punctuation as part of the word
    #             word += char
    #         else:  # If it's a space or separator, process the word
    #             if word:
    #                 # Detect language using the first character of the word
    #                 language = self.detect_language(word[0]) or "english"
    #                 cursor.setCharFormat(self.formats.get(language, self.formats["english"]))
    #                 cursor.insertText(word)
    #                 word = ''  # Reset the word variable
    #             cursor.insertText(char)  # Insert the separator (like space)

    #     # Process any remaining word after the loop ends
    #     if word:
    #         # Detect language using the first character of the word
    #         language = self.detect_language(word[0]) or "english"
    #         cursor.setCharFormat(self.formats.get(language, self.formats["english"]))
    #         cursor.insertText(word)

    #     return doc.toHtml()

    def apply_fonts_to_text(self, text):
        text = str(text)
        if not self.fonts_loaded:
            self.loadFonts()

        doc = QTextDocument()
        cursor = QTextCursor(doc)

        for char in text:
            language = self.detect_language(char) or "english"
            cursor.setCharFormat(self.formats.get(language, self.formats["english"]))
            cursor.insertText(char)

        return doc.toHtml()

    def get_formatted_text(self, text):
        return self.apply_fonts_to_text(text)

    def reloadFont(self):
        """Reloads the font settings and applies them again."""
        self.load_font_settings()  # Re-fetch font settings from EasyJson
        self.fonts_loaded = False  # Mark fonts as not loaded
        self.loadFonts()  # Reload the fonts with the new settings

    @staticmethod
    def get_font_name(font_path):
        font = TTFont(font_path)
        name_records = font['name'].names
        for record in name_records:
            if record.nameID == 4:  # Full font name
                font_name = record.toStr()
                return font_name
        return None

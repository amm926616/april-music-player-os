import bisect
import re
import os
from PyQt6.QtWidgets import QLabel, QDialog, QVBoxLayout, QApplication, QSizePolicy, QWIDGETSIZE_MAX
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation
from PyQt6.QtGui import QIcon, QKeyEvent
import pyperclip
from easy_json import EasyJson
from getfont import GetFont
from notetaking import NoteTaking
from clickable_label import ClickableLabel
import threading
from dictionary import VocabularyManager
from queue import Queue, Empty
from PIL import Image, ImageDraw, ImageFont

def extract_time_and_lyric(line):
    match = re.match(r'\[(\d{2}:\d{2}\.\d+)](.*)', line)
    if match:
        time_str = match.group(1)
        lyric = match.group(2).strip()
        return time_str, lyric
    return None, None


def convert_time_to_seconds(time_str):
    minutes, seconds = map(float, time_str.split(":"))
    return minutes * 60 + seconds


class LRCSync:
    def __init__(self, parent, music_player, config_path, on_off_lyrics=None, ui_show_maximized=None):
        # Get the screen geometry
        self.ej = EasyJson()
        self.lyrics_interaction = None
        app = QApplication.instance() or QApplication([])
        screen_geometry = app.primaryScreen().geometry()

        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()

        self.animation_direction = "down"
        self.animation_holder_list = None
        self.lyrics_color = None
        self.first_time_lyric = True
        self.parent = parent
        self.labels = []
        self.main_layout = None
        self.previous_index = 0
        self.animation_speed = 200
        self.initial_positions = None
        self.uiShowMaximized = ui_show_maximized
        self.on_off_lyrics = on_off_lyrics
        self.config_path = config_path
        self.lrc_display = None
        self.file = None
        self.music_file = None
        self.music_player = music_player
        self.BLUE = '\033[34m'
        self.RESET = '\033[0m'

        # lyrics labels
        self.lyric_label0 = None
        self.lyric_label1 = None
        self.lyric_label2 = None
        self.lyric_label3 = None
        self.lyric_label4 = None

        self.lyrics = None
        self.lyrics_time_keys = None
        self.current_time = 0.0
        self.media_font = GetFont(13)
        self.media_lyric = ClickableLabel()
        self.media_lyric.setToolTip("Double click to activate lyrics display")
        self.media_lyric.setWordWrap(True)
        self.font_size = self.ej.get_value("lrc_font_size")
        self.larger_font_size = int(self.font_size + 20)
        self.lrc_font = GetFont(int(self.font_size))
        self.show_lyrics = self.ej.get_value("show_lyrics")
        self.dictionary = None

        self.first_lyric_text = ""
        self.current_lyric_text = ""
        self.next_lyric_text = ""
        self.previous_lyric_text = ""
        self.last_lyric_text = ""

        if self.show_lyrics:
            self.current_lyric_text = "April Music Player"
        else:
            self.current_lyric_text = "Lyrics Syncing Disabled"

        self.media_lyric.setText(self.media_font.get_formatted_text(self.current_lyric_text))

        self.lyric_sync_connected = False
        self.media_sync_connected = False
        self.current_lyrics_time = 0.0
        self.last_update_time = 0.0  # Initialize with 0 or None
        self.update_interval = float(self.ej.get_value("sync_threshold"))  # Minimum interval in seconds
        self.script_path = self.ej.get_value("script_path")
        self.current_index = 0

        # Construct the full path to the icon file
        self.icon_path = os.path.join(self.script_path, 'icons', 'april-icon.png')
        self.notetaking = NoteTaking(self)
        self.started_player = False

        self.lock = threading.Lock()  # To ensure thread safety
        self.task_queue = Queue()  # Task queue for threading

        # Start a background thread to process tasks
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def disconnect_syncing(self):
        if self.lyric_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_display_lyric)
            self.lyric_sync_connected = False
        if self.media_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_media_lyric)
            self.media_sync_connected = False

        self.current_lyric_text = "April Music Player"

    def update_file_and_parse(self, file):
        if file is None:
            self.file = None
            self.lyrics = None
            return
        else:
            self.file = file

        self.parse_lrc()

    def resizeBackgroundImage(self, image_path):
        print("In resize Image method")
        image = Image.open(image_path)

        # # Calculate the new dimensions to maintain the aspect ratio
        aspect_ratio = image.width / image.height
        new_width = int(self.screen_height * aspect_ratio)

        # Resize the image
        resized_image = image.resize((new_width, self.screen_height), Image.LANCZOS)

        # Create a new image with the screen dimensions and background color
        background_color = "black"  # Set your background color here
        final_image = Image.new("RGB", (self.screen_width, self.screen_height), background_color)

        # Calculate the position to paste the resized image onto the background
        x_position = (self.screen_width - new_width) // 2
        y_position = 0  # Keep the image vertically centered

        # Paste the resized image onto the background
        final_image.paste(resized_image, (x_position, y_position))

        # Add copyright text to the final image
        draw = ImageDraw.Draw(final_image)

        # Load a custom font with a specific size
        font_size = int(self.parent.height() * 0.06)  # Set your desired font size here
        font_path = os.path.join(self.script_path, "fonts",
                                 "Sexy Beauty.ttf")  # Replace with the path to your .ttf font file
        font = ImageFont.truetype(font_path, font_size)  # Load the font with the specified size

        # Define the text
        text = "April Music Player"

        # Get text size using text-box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Define the position for the text (bottom-right corner with padding)
        text_position = (self.screen_width - text_width - 10, self.screen_height - text_height - 10)

        # Define the stroke width and stroke color
        stroke_width = 2  # Adjust the stroke width as needed
        stroke_color = "black"  # Stroke color (outline)

        # Draw the stroke by drawing the text multiple times with a slight offset
        for offset in range(-stroke_width, stroke_width + 1):
            if offset == 0:
                continue
            draw.text((text_position[0] + offset, text_position[1]), text, font=font, fill=stroke_color)
            draw.text((text_position[0], text_position[1] + offset), text, font=font, fill=stroke_color)
            draw.text((text_position[0] + offset, text_position[1] + offset), text, font=font, fill=stroke_color)

        # Draw the main text
        draw.text(text_position, text, font=font, fill="white")  # Main text color

        # Save the final image
        final_image_path = os.path.join(self.config_path, "resized_image.png")
        final_image.save(final_image_path)

        return final_image_path

    def startUI(self, parent, file):
        self.lrc_display = QDialog(parent)
        self.lrc_display.setWindowTitle(file)
        # if file is None:
        #     self.lrc_display.setWindowTitle("LRC Display")

        resized_image_path = os.path.join(self.config_path, "resized_image.png")
        resized_image_path = os.path.normpath(resized_image_path).replace("\\", "/")  # python's default method to check if the path exists.

        if not os.path.exists(resized_image_path):
            self.resizeBackgroundImage(self.ej.setupBackgroundImage())

        # Check if the OS is Windows
        if self.ej.get_value("running_system") == "windows":  # 'nt' stands for Windows
            resized_image_path = resized_image_path.replace("\\", "/")  # တော်တော်သောက်လုပ်ရှပ်တဲ့ window

        # unknown resize image size error fix for windows
        self.lrc_display.setStyleSheet(f"""
            QDialog {{
                border-image: url({resized_image_path}) 0 0 0 0 stretch stretch;
                background-repeat: no-repeat;
                background-position: center;
            }}
        """)

        self.lrc_display.setWindowIcon(QIcon(self.icon_path))

        # Calculate the width and height of the dialog
        dialog_width = int(parent.width() * 0.9)
        dialog_height = int(parent.height() * 0.8)

        # Calculate the top-left position off the dialog relative to the parent widget
        relative_x = int((parent.width() - dialog_width) / 2)
        relative_y = int((parent.height() - dialog_height) / 2)

        # Convert the relative position to global screen coordinates
        global_position = parent.mapToGlobal(parent.rect().topLeft())

        # Add the relative position to the global position to get the final coordinates
        position_x = global_position.x() + relative_x
        position_y = global_position.y() + relative_y

        # Set the geometry of the dialog
        self.lrc_display.setGeometry(position_x, position_y, dialog_width, dialog_height)
        self.lrc_display.setFixedSize(dialog_width, dialog_height)

        # fix for windows
        self.lrc_display.setMinimumSize(dialog_width, dialog_height)
        self.lrc_display.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)

        self.main_layout = QVBoxLayout(self.lrc_display)
        self.setup_lyrics_labels()

        if self.show_lyrics:
            if self.started_player:
                self.find_lyrics()
                self.update_labels_text()
            else:
                self.lyric_label2.setText(self.lrc_font.get_formatted_text("April Music Player"))

            self.music_player.player.positionChanged.connect(self.update_display_lyric)
            self.lyric_sync_connected = True
        else:
            self.lyric_label2.setText(self.lrc_font.get_formatted_text("Lyrics Syncing Disabled"))

        # Properly connect the close event
        self.lrc_display.closeEvent = self.closeEvent
        self.lrc_display.keyPressEvent = self.keyPressEvent

        self.lrc_display.exec()

    def closeEvent(self, event):
        print("QDialog closed")
        self.lyric_label1 = None
        self.lyric_label2 = None
        self.lyric_label3 = None
        self.lrc_display = None

        if self.lyric_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_display_lyric)
            self.lyric_sync_connected = False

        if self.parent.is_fullscreen:
            self.parent.showFullScreen()
        else:
            self.uiShowMaximized()

        event.accept()  # To accept the close event

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Left:
            print("left key pressed")
            self.music_player.seek_backward()

        elif event.key() == Qt.Key.Key_Minus and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("ctrl minus")
            self.lrc_font.font_size -= 1

        elif event.key() == Qt.Key.Key_Right and event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.parent.play_next_song()

        elif event.key() == Qt.Key.Key_Y and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.create_lyrics_animation()

        elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.music_player.pause()  # pause the music first
            if self.dictionary is None:
                self.dictionary = VocabularyManager(parent=self)
            self.dictionary.exec()
            self.dictionary.word_input.setFocus()

        elif event.key() == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.parent.exit_app()

        elif event.key() == Qt.Key.Key_Right:
            print("right key pressed")
            self.music_player.seek_forward()

        elif event.key() == Qt.Key.Key_Space:
            print("Space key pressed")
            self.music_player.play_pause_music()

        elif event.key() == Qt.Key.Key_Up:
            if self.lyrics_interaction:
                print("UP key pressed")
                self.go_to_previous_lyric()

        elif event.key() == Qt.Key.Key_Down:
            if self.lyrics_interaction:
                print("down key pressed")
                self.go_to_next_lyric()

        elif event.key() == Qt.Key.Key_D:
            if self.music_player.in_pause_state:
                self.music_player.play_pause_music()
                self.music_player.in_pause_state = False
            self.go_to_the_start_of_current_lyric()

        elif event.key() == Qt.Key.Key_E:
            print("pressing e")
            self.music_player.pause()
            self.createNoteTakingWindow()

        elif event.key() == Qt.Key.Key_Escape:
            self.lrc_display.close()

        elif event.key() == Qt.Key.Key_R:
            self.restart_music()

        elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            pyperclip.copy(self.current_lyric_text)

        elif event.key() == Qt.Key.Key_F:
            print("pressed F")
            if self.is_full_screen():
                self.lrc_display.showNormal()  # Restore to normal mode
            else:
                self.lrc_display.showFullScreen()  # Enter full-screen mode

        elif event.key() == Qt.Key.Key_Left and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.parent.play_previous_song()

        elif event.key() == Qt.Key.Key_Left and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.parent.play_next_song()

        elif event.key() == Qt.Key.Key_I and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("disabled lyrics")
            if self.show_lyrics:
                self.on_off_lyrics(False)
                self.music_player.player.positionChanged.disconnect(self.update_display_lyric)
                self.lyric_label2.setText(self.lrc_font.get_formatted_text("Lyrics Disabled"))
                self.lyric_sync_connected = False
            else:
                self.on_off_lyrics(True)
                self.music_player.player.positionChanged.connect(self.update_display_lyric)
                self.lyric_sync_connected = True

    def restart_music(self):
        if not self.music_player.started_playing:
            return

        print("restart music hits")
        if self.music_player.in_pause_state:
            self.music_player.play_pause_musis_full_screenic()
            self.music_player.in_pause_state = False
        self.music_player.player.setPosition(0)
        self.current_lyrics_time = self.lyrics_time_keys[0]

    def createNoteTakingWindow(self):
        self.notetaking.createUI()

    def is_full_screen(self):
        # Check if the dialog is in full-screen mode

        current_window_state = self.lrc_display.windowState()

        # Define the full-screen flag
        full_screen_flag = Qt.WindowState.WindowFullScreen

        # Check if the current window state incupdate_lyrics_after_animationludes the full-screen flag
        is_full_screen_mode = (current_window_state & full_screen_flag) == full_screen_flag

        # Return the result
        return is_full_screen_mode

    def setup_lyrics_labels(self):
        # Create and configure self.lyric_label1
        self.lyric_label0 = QLabel()
        self.lyric_label0.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label0.setWordWrap(True)
        self.lyric_label0.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label0.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create and configure self.lyric_label1
        self.lyric_label1 = QLabel()
        self.lyric_label1.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label1.setWordWrap(True)
        self.lyric_label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create and configure self.lyric_label2
        self.lyric_label2 = QLabel()
        self.lyric_label2.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label2.setWordWrap(True)
        self.lyric_label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Create and configure self.lyric_label3
        self.lyric_label3 = QLabel()
        self.lyric_label3.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label3.setWordWrap(True)
        self.lyric_label3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label3.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # Create and configure self.lyric_label3
        self.lyric_label4 = QLabel()
        self.lyric_label4.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.lyric_label4.setWordWrap(True)
        self.lyric_label4.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lyric_label4.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.labels.extend(
            [self.lyric_label0, self.lyric_label1, self.lyric_label2, self.lyric_label3, self.lyric_label4])

        # Add the labels to the layout
        self.main_layout.addWidget(self.lyric_label0)
        self.main_layout.addWidget(self.lyric_label1)
        self.main_layout.addWidget(self.lyric_label2)
        self.main_layout.addWidget(self.lyric_label3)
        self.main_layout.addWidget(self.lyric_label4)

        # Set alignment for the entire layout
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        #  for lyrics color
        self.lyrics_color = self.ej.get_value("lyrics_color")
        print("The lyrics color currently is ", self.lyrics_color)

        if not self.lyrics_color:
            self.ej.setupLyricsColor()
            self.lyrics_color = self.ej.get_value("lyrics_color")

        #  setting colors for each lyric label
        self.lyric_label0.setStyleSheet("color: gray")
        self.lyric_label1.setStyleSheet("color: gray")
        self.lyric_label2.setStyleSheet(f"color: {self.lyrics_color};")
        self.lyric_label3.setStyleSheet("color: gray")
        self.lyric_label4.setStyleSheet("color: gray")

    def update_lyrics_after_animation(self):
        """
        Update the lyrics after the animation has finished.
        """
        # Adjust styles based on the direction of movement
        if self.animation_direction == "up":
            self.lyric_label1.setStyleSheet(f"color: gray; font-size: {self.font_size}px;")  # Remove highlight from
            # above label
        else:
            self.lyric_label3.setStyleSheet(f"color: gray; font-size: {self.font_size}px;")  # Remove highlight from
            # below label

        # Reapply highlight to the current label
        self.lyric_label2.setStyleSheet(f"color: {self.lyrics_color}; font-size: {self.font_size}px;"
                                        f" font-weight: bold;")
        self.update_labels_text()
        self.animation_direction = "down"

    def go_to_previous_lyric(self):
        self.animation_direction = "up"
        if self.lyrics and self.lyric_sync_connected:
            if self.current_index == 0:
                print("inside instrumental intro")
                previous_lyric_index = len(self.lyrics_time_keys) - 1

            elif self.current_index == 1:
                self.restart_music()
                return

            else:
                previous_lyric_index = self.current_index - 2

            previous_lyrics_key = self.lyrics_time_keys[previous_lyric_index]
            self.music_player.player.setPosition(int(previous_lyrics_key * 1000))

            # fix the late to set current time due to slower sync time
            self.current_lyrics_time = self.lyrics_time_keys[previous_lyric_index]
            self.current_lyric_text = self.lyrics[self.current_lyrics_time]

            if self.current_index == 2:
                self.first_lyric_text = ""

    def go_to_next_lyric(self):
        self.animation_direction = "down"
        if self.lyrics and self.lyric_sync_connected:
            if self.current_index == len(self.lyrics_time_keys): 
                self.restart_music()
                return 
            else:
                next_lyric_index = self.current_index

            next_lyrics_key = self.lyrics_time_keys[next_lyric_index]
            self.music_player.player.setPosition(int(next_lyrics_key * 1000))

            # fix the late to set current time due to slower sync time
            self.current_lyrics_time = self.lyrics_time_keys[next_lyric_index]
            self.current_lyric_text = self.lyrics[self.current_lyrics_time]


    def go_to_the_start_of_current_lyric(self):
        self.music_player.player.setPosition(int(self.current_lyrics_time * 1000))

    def parse_lrc(self):
        # Add parsing task to the queue
        self.task_queue.put(self.file)

    def parse_lrc_base(self, file_path):
        lyrics_dict = {}
        if file_path is None:
            return None

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                for line in file:
                    time_str, lyric = extract_time_and_lyric(line)
                    if time_str and lyric:
                        time_in_seconds = convert_time_to_seconds(time_str)
                        lyrics_dict[time_in_seconds] = lyric

            if lyrics_dict:
                return {
                    "lyrics": lyrics_dict,
                    "lyrics_time_keys": sorted(lyrics_dict.keys()),
                }

        except Exception as e:
            print(f"Error occurred while parsing lrc file: {e}")
            return None

    def _worker(self):
        while True:
            try:
                file_path = self.task_queue.get(timeout=1)  # Wait for a task
                if file_path is None:
                    continue

                # Process the file in the background
                result = self.parse_lrc_base(file_path)
                with self.lock:  # Safely update shared attributes
                    if result:
                        self.lyrics = result["lyrics"]
                        self.lyrics_time_keys = result["lyrics_time_keys"]
                        self.lyrics_interaction = True
                    else:
                        self.lyrics = None
                        self.lyrics_time_keys = []
                        self.lyrics_interaction = False

            except Empty:
                pass  # No tasks to process, continue waiting

    def get_lyric_text(self, index, offset):
        """
        Retrieve lyric text safely based on index and offset.

        :param index: The current index in lyrics_time_keys.
        :param offset: The offset from the current index.
        :return: The lyric text or an empty string if out of bounds.
        """
        target_index = index + offset
        if 0 <= target_index < len(self.lyrics_time_keys):
            time_key = self.lyrics_time_keys[target_index]
            return self.lyrics.get(time_key, "")
        return ""

    def find_lyrics(self):
        if not self.file and not self.lyrics:
            print("skipped find_lyrics method")
            return
        else:
            self.current_time = self.music_player.get_current_time()

            # Only update if the current time has moved beyond the update interval
            if abs(self.current_time - self.last_update_time) < self.update_interval:
                return  # Skip updating if within the interval

            self.last_update_time = self.current_time  # Update the last updated time

            # Use binary search to find the correct lyrics time
            index = bisect.bisect_right(self.lyrics_time_keys, self.current_time)

            # Determine surrounding lyrics based on index
            if index == 0:
                # Before the first lyric
                self.current_lyric_text = "(Instrumental Intro)"

                if self.lrc_display:
                    self.previous_lyric_text = ""
                    self.first_lyric_text = ""
                    self.next_lyric_text = self.get_lyric_text(index, 0)
                    self.last_lyric_text = self.get_lyric_text(index, 1)

            elif index == len(self.lyrics_time_keys):
                # After the last lyric
                self.current_lyric_text = self.get_lyric_text(index, -1)

                if self.lrc_display:
                    self.first_lyric_text = self.get_lyric_text(index, -3)
                    self.previous_lyric_text = self.get_lyric_text(index, -2)
                    self.next_lyric_text = "---The End Of Lyrics---"
                    self.last_lyric_text = ""

            else:
                # In the range of lyrics
                self.current_lyric_text = self.get_lyric_text(index, -1)

                if self.lrc_display:
                    self.next_lyric_text = self.get_lyric_text(index, 0)
                    self.last_lyric_text = self.get_lyric_text(index, 1)
                    self.first_lyric_text = self.get_lyric_text(index, -3)
                    self.previous_lyric_text = self.get_lyric_text(index, -2)

            self.current_index = index
            print("self.current_index: ", self.current_index)

            # Update lyric label styling
            if self.lyric_label3 is not None:
                if self.next_lyric_text == "---The End Of Lyrics---":
                    self.lyric_label3.setStyleSheet("color: red;")
                else:
                    self.lyric_label3.setStyleSheet("color: gray;")

    def update_media_lyric(self):
        self.find_lyrics()
        self.media_lyric.setText(self.media_font.get_formatted_text(self.current_lyric_text))

    def update_display_lyric(self):
        if self.previous_index == self.current_index:
            if self.first_time_lyric:
                self.first_time_lyric = False
                self.update_labels_text()
            else:
                return
        else:
            self.create_lyrics_animation()

        self.previous_index = self.current_index

    def update_labels_text(self):
        if self.lyric_label0 is not None:
            self.lyric_label0.setText(self.lrc_font.get_formatted_text(self.first_lyric_text))
        if self.lyric_label2 is not None:
            self.lyric_label2.setText(self.lrc_font.get_formatted_text(self.current_lyric_text))
        if self.lyric_label1 is not None:
            self.lyric_label1.setText(self.lrc_font.get_formatted_text(self.previous_lyric_text))
        if self.lyric_label3 is not None:
            self.lyric_label3.setText(self.lrc_font.get_formatted_text(self.next_lyric_text))
        if self.lyric_label4 is not None:
            self.lyric_label4.setText(self.lrc_font.get_formatted_text(self.last_lyric_text))

    def clean_labels_text(self):
        self.first_lyric_text = ""
        self.previous_lyric_text = ""
        self.current_lyric_text = "April Music Player"
        self.next_lyric_text = ""
        self.last_lyric_text = ""

    def create_lyrics_animation(self):
        print("inside create lyrics animation")
        print("The variable self.animation_direction is ", self.animation_direction)
        """Create and start animations for the labels moving up or down."""

        # Create animations for all 5 labels
        self.animation_holder_list = []  # clean the animation list

        anim_label0 = QPropertyAnimation(self.lyric_label0, b"pos")
        anim_label1 = QPropertyAnimation(self.lyric_label1, b"pos")
        anim_label2 = QPropertyAnimation(self.lyric_label2, b"pos")
        anim_label3 = QPropertyAnimation(self.lyric_label3, b"pos")
        anim_label4 = QPropertyAnimation(self.lyric_label4, b"pos")

        # Set the start positions for all labels
        anim_label0.setStartValue(self.lyric_label0.pos())
        anim_label1.setStartValue(self.lyric_label1.pos())
        anim_label2.setStartValue(self.lyric_label2.pos())
        anim_label3.setStartValue(self.lyric_label3.pos())
        anim_label4.setStartValue(self.lyric_label4.pos())

        # Define animation durations
        anim_label0.setDuration(self.animation_speed)
        anim_label1.setDuration(self.animation_speed)
        anim_label2.setDuration(self.animation_speed)
        anim_label3.setDuration(self.animation_speed)
        anim_label4.setDuration(self.animation_speed)

        # Define the end positions based on direction
        if self.animation_direction == "up":
            self.lyric_label2.setStyleSheet("color: gray;")  # Remove highlight from current
            self.lyric_label1.setStyleSheet(f"color: {self.lyrics_color}; font-size: {self.larger_font_size}px;")  # Highlight below label

            print("in animation direction up")
            # Move labels up
            anim_label0.setEndValue(self.lyric_label1.pos())
            anim_label1.setEndValue(self.lyric_label2.pos())
            anim_label2.setEndValue(self.lyric_label3.pos())
            anim_label3.setEndValue(self.lyric_label4.pos())
            anim_label4.setEndValue(QPoint(0, self.screen_height + self.animation_speed))  # Move label5 off the view

            # Connect animation completion to update labels
            anim_label4.finished.connect(lambda: self.update_lyrics_after_animation())

        elif self.animation_direction == "down":
            self.lyric_label2.setStyleSheet("color: gray;")  # Remove highlight from current
            self.lyric_label3.setStyleSheet(f"color: {self.lyrics_color}; font-size: {self.larger_font_size}px;")  # Highlight below label

            # Move labels down
            anim_label0.setEndValue(QPoint(0, - self.animation_speed))  # Move label1 off the view
            anim_label1.setEndValue(self.lyric_label0.pos())
            anim_label2.setEndValue(self.lyric_label1.pos())
            anim_label3.setEndValue(self.lyric_label2.pos())
            anim_label4.setEndValue(self.lyric_label3.pos())

            # Connect animation completion to update labels
            anim_label2.finished.connect(lambda: self.update_lyrics_after_animation())

        # Add animations to the list and start them
        self.animation_holder_list.extend([anim_label0, anim_label1, anim_label2, anim_label3, anim_label4])
        for anim in self.animation_holder_list:
            anim.start()

    def activate_sync_lyric_connection(self, file):
        self.update_file_and_parse(file)
        if self.media_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.update_media_lyric)
            self.media_sync_connected = False

        self.music_player.player.positionChanged.connect(self.update_media_lyric)
        self.media_sync_connected = True

    def reset_labels(self):
        if self.lyric_label2 is None:
            return

        self.current_lyrics_time = 0.0
        # Handle the case when the index is at the beginning
        if self.current_time < self.lyrics_time_keys[0]:  # For instrumental section before first lyric
            self.current_lyric_text = "April Music Player"
            self.first_lyric_text = ""
            self.previous_lyric_text = ""
            self.next_lyric_text = self.lyrics.get(self.lyrics_time_keys[0], "")
            self.last_lyric_text = self.lyrics.get(self.lyrics_time_keys[1], "")
April Music Player
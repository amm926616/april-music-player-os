import os
import sys
from base64 import b64decode
from random import choice
from urllib import request

from PyQt6.QtCore import Qt, QCoreApplication, QRectF
from PyQt6.QtGui import QIcon, QFont, QAction, QCursor, QKeyEvent, QActionGroup, QColor, \
    QPainter, QPixmap, QPainterPath, QTextDocument, QTextOption
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QSystemTrayIcon, QMenu, QWidgetAction,
    QLabel, QPushButton, QSlider, QLineEdit, QFileDialog, QScrollArea, QSizePolicy, QDialog, QStyle,
    QTextEdit
)
from PyQt6.QtWidgets import QStyleFactory
from mutagen import File
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC
from mutagen.id3 import ID3, ID3NoHeaderError
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.wave import WAVE

from _utils.easy_json import EasyJson
from _utils.lrc_downloader import LyricsDownloader
from components.addnewdirectory import AddNewDirectory
from components.album_image_window import AlbumImageWindow
from components.clickable_label import ClickableImageLabel
from components.fontsettingdialog import FontSettingsWindow
from components.lrcDisplay import LRCSync
from components.playlist_manager import PlaylistDialog
from components.splitter import ColumnSplitter
from components.tag_dialog import TagDialog
from components.zotify_downloader_gui import ZotifyDownloaderGui
from consts.help_menu_consts import SHORTCUTS_TRANSLATIONS, PREPARATION_TRANSLATIONS, FROMME_TRANSLATIONS
from main_ui.albumtreewidget import AlbumTreeWidget
from consts.main_ui_consts import LYRICS_NOT_FOUND, LYRICS_NOT_FOUND_TITLE, DOWNLOAD_WITH_LRC, COPY_SONG_PATH, EDIT_META_DATA, \
    SELECT_AN_IMAGE_FOR_BACKGROUND_TITLE, LOAD_BACKGROUND_IMAGE_TITLE, NO_FILE_SELECTED_TITLE, \
    DID_NOT_SELECT_IMAGE_FILE, FILTER_SONGS_FROM_PLAYLIST, FILTER_SONGS_FROM_PLAYLIST_TOOLTIP, APRIL_WINDOW_TITLE, \
    SEARCH_SONG_BY_NAME, SONG_SEARCHBAR_TOOLTIP
from main_ui.songtablewidget import SongTableWidget, PlaylistNameDialog
from music_player.musicplayer import MusicPlayer


def html_to_plain_text(html):
    doc = QTextDocument()
    doc.setHtml(html)
    return doc.toPlainText()

def extract_mp3_album_art(audio_file):
    """Extract album art from an MP3 file."""
    if audio_file.tags is None:
       return None

    for tag in audio_file.tags.values():
        if isinstance(tag, APIC):
            return tag.data
    return None


def extract_mp4_album_art(audio_file):
    """Extract album art from an MP4 file."""
    covers = audio_file.tags.get('covr')
    if covers:
        return covers[0] if isinstance(covers[0], bytes) else covers[0].data
    return None


def extract_flac_album_art(audio_file):
    """Extract album art from a FLAC file."""
    if audio_file.pictures:
        return audio_file.pictures[0].data
    return None


def extract_ogg_album_art(audio_file):
    """Extract album art from an OGG file."""
    if 'metadata_block_picture' in audio_file:
        picture_data = audio_file['metadata_block_picture'][0]
        picture = Picture(b64decode(picture_data))
        return picture.data
    return None

def format_time(seconds):
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"

def extract_track_number(track_number):
    """
    Extracts the track number from a string, handling cases like "1/6" or "02/12".
    Returns the integer part before the slash, or the whole number if there's no slash.
    """
    if '/' in track_number:
        return int(track_number.split('/')[0])
    elif track_number.isdigit():
        return int(track_number)
    return float('inf')  # For non-numeric track numbers, place them at the end

def getRoundedCornerPixmap(scaled_pixmap, target_width, target_height):
    # Create a transparent pixmap with the same size as the scaled image
    rounded_pixmap = QPixmap(target_width, target_height)
    rounded_pixmap.fill(Qt.GlobalColor.transparent)  # Transparent background

    # Start painting the image with QPainter
    painter = QPainter(rounded_pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Create a QPainterPath for the rounded rectangle
    path = QPainterPath()
    radius = 20  # Adjust this for more or less roundness
    path.addRoundedRect(QRectF(0, 0, target_width, target_height), radius, radius)

    # Clip the image to the rounded rectangle
    painter.setClipPath(path)

    # Draw the scaled pixmap into the rounded shape
    painter.drawPixmap(0, 0, scaled_pixmap)
    painter.end()

    return rounded_pixmap


class MusicPlayerUI(QMainWindow):

    def __init__(self, app, music_files=None):
        super().__init__()
        self.shortcut_search_bar = None
        self.add_new_directory = None
        self.album_tree_widget = None
        self.lrc_player = None
        self.music_player = None
        self.song_table_widget = None
        self.time_slider = None
        self.media_control_layout = None
        self.main_media_horizontal_layout = None
        self.volume_control = None
        self.zotify_gui = None
        self.activate_lyrics_display_action = None
        self.mediaLayout = None
        self.app = app
        self.playlist_widget = None
        self.ej = EasyJson()  # ej initializing
        self.ej.ensure_config_file()

        self.system_language = self.ej.get_value("system_language")

        self.is_fullscreen = None

        self.config_path = self.ej.get_value("config_path")

        self.running_platform = self.ej.get_value("running_system")

        if self.running_platform == "windows":
            if "windows11" in QStyleFactory.keys():
                app.setStyle("windows11")
            else:
                app.setStyle("Fusion")
            print(app.style().objectName())

        elif self.running_platform == "unix":
            if "Breeze" in QStyleFactory.keys():
                app.setStyle("Breeze")
            else:
                app.setStyle("Fusion")
            print(app.style().objectName())

        # Define the config path
        self.play_song_at_startup = None
        self.threshold_actions = None
        self.search_bar_layout = None
        self.script_path = self.ej.get_value("script_path")

        print("SCRIPT_PATH IS ", self.script_path)

        # Construct the full path to the icon file
        self.icon_folder_path = os.path.join(self.ej.ej_path, 'icons', 'configuration_icons')
        self.icon_path = os.path.join(self.ej.ej_path, "icons", "april-icon.png")
        print("The icon path is, " + self.icon_path)

        self.media_control_slider_playback_control_layout = None
        self.metadata = None
        self.duration_label = None
        self.passing_image = None
        self.next_song_button = None
        self.prev_song_button = None
        self.playback_management_layout = None
        self.color_actions = None
        self.font_settings_window = None
        self.font_settings_action = None
        self.show_lyrics_action = None
        self.tray_menu = None
        self.tray_icon = None
        self.central_widget = None
        self.filter_search_bar = None
        self.track_display = None
        self.song_details = None
        self.image_display = None
        self.prev_button = None
        self.click_count = 0
        self.forward_button = None
        self.app = app
        self.file_path = None
        self.hidden_rows = False
        self.play_pause_button = QPushButton()
        self.play_pause_button.setToolTip("Play/Pause")
        self.loop_playlist_button = QPushButton()
        self.loop_playlist_button.setToolTip("Loop Playlist [Ctrl + 1]")
        self.repeat_button = QPushButton()
        self.repeat_button.setToolTip("Toggle Repeat [Ctrl + 2]")
        self.shuffle_button = QPushButton()
        self.shuffle_button.setToolTip("Toggle Shuffle [Ctrl + 3]")
        self.item = None
        self.media_files = []
        self.current_playing_random_song_index = 0
        self.random_song = None
        self.saved_position = None

        # Screen size
        self.screen_size = self.app.primaryScreen().geometry()

        # Getting image size from primary screen geometry
        self.image_size = int(self.screen_size.width() / 5)  # extract image size from main window

        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        self.directories = self.ej.get_value("music_directories")

        self.music_file = None
        self.lrc_file = None

        self.init_main_classes(music_files)

        self.last_updated_position = 0.0
        self.update_interval_millisecond = 1000

        # Get a standard "settings-like" icon (use a custom one for better visuals)
        self.settings_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)
        self.colors_icon = QIcon(os.path.join(self.icon_folder_path, "colors.ico"))
        self.default_wallpaper_icon = QIcon(os.path.join(self.icon_folder_path, "default_wallpaper.ico"))

        self.lyrics_downloader = LyricsDownloader(
            parent=self,
            song_table_widget=self.song_table_widget,
            app=self.app,
            get_path_callback=self.get_music_file_from_click
        )

        self.language_map = {
            "English": "ENG",
            "Burmese": "BUR",
            # "Korean": "KOR",
            # "Japanese": "JAP"
        }

        self.createSyncThresholdMenu()

    def init_main_classes(self, music_files=None):
        self.music_player = MusicPlayer(self, self.play_pause_button, self.loop_playlist_button, self.repeat_button,
                                        self.shuffle_button)

        self.lrc_player = LRCSync(self, self.music_player, self.config_path, self.on_off_lyrics, self.showMaximized)

        # Initialize the table widget
        self.song_table_widget = SongTableWidget(self, self.handle_row_double_click, self.music_player.seek_forward,
                                                 self.music_player.seek_backward, self.play_pause, self.screen_size.height())

        self.album_tree_widget = AlbumTreeWidget(self, self.song_table_widget)

        self.add_new_directory = AddNewDirectory(self)

        print(music_files)
        if music_files:
            for file in music_files:
                print(file)
                self.album_tree_widget.add_song_by_file_path(file)

    @staticmethod
    def get_metadata(song_file: object):
        print("get_metadata method called")
        if song_file is None:
            return

        file_extension = song_file.lower().split('.')[-1]

        metadata = {
            'title': 'Unknown Title',
            'artist': 'Unknown Artist',
            'album': 'Unknown Album',
            'year': 'Unknown Year',
            'genre': 'Unknown Genre',
            'track_number': 'Unknown Track Number',
            'comment': 'No Comment',
            'duration': 0,  # Initialize duration as integer,
            'file_type': file_extension,
        }

        try:
            if file_extension == "mp3":
                # Extract duration and file_type before crash
                mp3_audio = MP3(song_file)
                metadata['duration'] = int(mp3_audio.info.length)
                metadata['file_type'] = str(file_extension)

                audio = ID3(song_file)
                metadata['title'] = audio.get('TIT2', 'Unknown Title').text[0] if audio.get('TIT2') else 'Unknown Title'
                metadata['artist'] = audio.get('TPE1', 'Unknown Artist').text[0] if audio.get(
                    'TPE1') else 'Unknown Artist'
                metadata['album'] = audio.get('TALB', 'Unknown Album').text[0] if audio.get('TALB') else 'Unknown Album'
                metadata['year'] = audio.get('TDRC', 'Unknown Year').text[0] if audio.get('TDRC') else 'Unknown Year'
                metadata['genre'] = audio.get('TCON', 'Unknown Genre').text[0] if audio.get('TCON') else 'Unknown Genre'
                metadata['track_number'] = audio.get('TRCK', 'Unknown Track Number').text[0] if audio.get(
                    'TRCK') else 'Unknown Track Number'
                metadata['comment'] = audio.get('COMM', 'No Comment').text[0] if audio.get('COMM') else 'No Comment'

            elif file_extension == 'm4a':
                audio = MP4(song_file)

                metadata['title'] = audio.tags.get('\xa9nam', ['Unknown Title'])[0]
                metadata['artist'] = audio.tags.get('\xa9ART', ['Unknown Artist'])[0]
                metadata['album'] = audio.tags.get('\xa9alb', ['Unknown Album'])[0]
                metadata['year'] = audio.tags.get('\xa9day', ['Unknown Year'])[0]
                metadata['genre'] = audio.tags.get('\xa9gen', ['Unknown Genre'])[0]
                metadata['track_number'] = audio.tags.get('trkn', [('Unknown Track Number',)])[0][0]
                metadata['comment'] = audio.tags.get('\xa9cmt', ['No Comment'])[0]

                # Extract duration
                metadata['duration'] = int(audio.info.length)
                metadata['file_type'] = str(file_extension)

            elif file_extension == 'ogg':
                audio = OggVorbis(song_file)
                metadata['title'] = audio.get('title', ['Unknown Title'])[0]
                metadata['artist'] = audio.get('artist', ['Unknown Artist'])[0]
                metadata['album'] = audio.get('album', ['Unknown Album'])[0]
                metadata['year'] = audio.get('date', ['Unknown Year'])[0]
                metadata['genre'] = audio.get('genre', ['Unknown Genre'])[0]
                metadata['track_number'] = audio.get('tracknumber', ['Unknown Track Number'])[0]
                metadata['comment'] = audio.get('comment', ['No Comment'])[0]

                # Extract duration
                metadata['duration'] = int(audio.info.length)
                metadata['file_type'] = str(file_extension)

            elif file_extension == 'flac':
                audio = FLAC(song_file)
                metadata['title'] = audio.get('title', ['Unknown Title'])[0]
                metadata['artist'] = audio.get('artist', ['Unknown Artist'])[0]
                metadata['album'] = audio.get('album', ['Unknown Album'])[0]
                metadata['year'] = audio.get('date', ['Unknown Year'])[0]
                metadata['genre'] = audio.get('genre', ['Unknown Genre'])[0]
                metadata['track_number'] = audio.get('tracknumber', ['Unknown Track Number'])[0]
                metadata['comment'] = audio.get('description', ['No Comment'])[0]

                # Extract duration
                metadata['duration'] = int(audio.info.length)
                metadata['file_type'] = str(file_extension)

            elif file_extension == 'wav':
                audio = WAVE(song_file)
                try:
                    metadata['title'] = audio.get('title', 'Unknown Title')
                    metadata['artist'] = audio.get('artist', 'Unknown Artist')
                    metadata['album'] = audio.get('album', 'Unknown Album')
                    metadata['year'] = audio.get('date', 'Unknown Year')
                    metadata['genre'] = audio.get('genre', 'Unknown Genre')
                    metadata['track_number'] = audio.get('tracknumber', 'Unknown Track Number')
                    metadata['comment'] = audio.get('comment', 'No Comment')
                except KeyError:
                    pass  # WAV files may not contain these tags

                # Extract duration
                metadata['duration'] = int(audio.info.length)
                metadata['file_type'] = str(file_extension)

            else:
                raise ValueError("Unsupported file format")

        except Exception as e:
            print(f"Error reading metadata: {e}")
            print("There might not be metadata tagged in the music file")

        return metadata

    def play_last_played_song(self):
        print("inside play_last_played_song method")
        if not self.ej.get_value("play_song_at_startup"):
            print("to play song got rejected")
            return

        last_play_file_data = self.ej.get_value("last_played_song")
        print("last_play_file_data is", last_play_file_data)

        if last_play_file_data:
            for file, position in last_play_file_data.items():
                self.music_file = file
                self.saved_position = position

            last_played_item_list = self.song_table_widget.findItems(self.music_file, Qt.MatchFlag.MatchExactly)

            if last_played_item_list:
                print("This is the song from item loaded")
                self.handle_row_double_click(last_played_item_list[0])

                # One-time connection for mediaStatusChanged signal
                self.music_player.player.mediaStatusChanged.connect(self.on_single_media_loaded)

                # Set the flag to indicate playback started by this method
                self.is_playing_last_song = True
                self.simulate_keypress(self.song_table_widget, Qt.Key.Key_G)

            print("Current position:", self.music_player.player.position())

        else:
            print("No last played file data found")

    def on_single_media_loaded(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self.is_playing_last_song:
            print("Media loaded, setting position.")
            self.music_player.player.setPosition(int(self.saved_position * 1000))

            # Disconnect after setting position
            self.music_player.player.mediaStatusChanged.disconnect(self.on_single_media_loaded)
            self.is_playing_last_song = False  # Reset the flag

    def toggle_reload_directories(self):
        self.album_tree_widget.loadSongsToCollection(loadAgain=True)

    def createUI(self):
        self.setWindowTitle(APRIL_WINDOW_TITLE[self.system_language])
        self.setGeometry(100, 100, 800, 400)

        self.setWindowIcon(QIcon(self.icon_path))
        self.createMenuBar()
        self.create_widgets_and_layouts()

        self.showMaximized()
        self.setupTrayIcon()

    def setupTrayIcon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(self.icon_path))
        self.tray_icon.setToolTip("April Music Player")  # Set the tooltip text
        self.tray_icon.setVisible(True)

        self.tray_menu = QMenu()

        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show)
        self.tray_menu.addAction(open_action)

        exit_action = QAction("Exit [Ctrl + Q]", self)
        exit_action.triggered.connect(QCoreApplication.instance().quit)
        self.tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_clicked)

    def on_tray_icon_clicked(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Handle the left-click (Trigger) event here
            print("Tray icon was left-clicked!")
            if self.isHidden():
                self.show()
            else:
                self.hide()  # Optionally, you can toggle between showing and hiding

    def closeEvent(self, event):
        print("hiding window")
        self.hide()
        if self.lrc_player.lrc_display is not None:
            self.lrc_player.lrc_display.close()
        event.ignore()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_I and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("disabled lyrics")
            if self.lrc_player.show_lyrics:
                self.on_off_lyrics(False)
            else:
                self.on_off_lyrics(True)

        elif event.key() == Qt.Key.Key_O and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.toggle_playlist_widget()

        elif event.key() == Qt.Key.Key_Right and event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.play_next_song()

        elif event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()

        elif event.key() == Qt.Key.Key_H and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if self.music_player.thread and self.music_player.thread.isRunning():
                print("Music player's QThread is running.")
            else:
                print("Music player's QThread is not running.")

        elif event.key() == Qt.Key.Key_P and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.stop_song()

        elif event.key() == Qt.Key.Key_Left:
            print("left key pressed")
            self.seek_backward()

        elif event.key() == Qt.Key.Key_Right:
            print("right key pressed")
            self.seek_forward()

        elif event.key() == Qt.Key.Key_Space:
            print("Space key pressed")
            self.play_pause()

        elif event.key() == Qt.Key.Key_L and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.activate_lrc_display()

        elif event.key() == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.exit_app()

        elif (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_F:
            self.filter_search_bar.setFocus()
            self.filter_search_bar.setCursorPosition(len(self.filter_search_bar.text()))

        elif event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.album_tree_widget.filter_search_bar.setFocus()
            self.album_tree_widget.filter_search_bar.setCursorPosition(len(self.filter_search_bar.text()))
            self.album_tree_widget.filter_search_bar.clear()

        elif (event.modifiers() & Qt.KeyboardModifier.AltModifier) and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and (event.key() == Qt.Key.Key_R):
            print("shift alt r pressed")
            self.lrc_player.restart_music()

        elif (event.modifiers() & Qt.KeyboardModifier.AltModifier) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_R:
            self.toggle_reload_directories()

        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_R:
            print("playing random song")
            self.song_table_widget.setFocus()
            self.play_random_song(user_clicking=True, from_shortcut=True)

        elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.restore_table()

        elif event.key() == Qt.Key.Key_T and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.song_table_widget.setFocus()  # set focus on table
            self.play_the_song_at_the_top()

        elif event.key() == Qt.Key.Key_J and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.song_table_widget.setFocus()  # set focus on table

        elif event.key() == Qt.Key.Key_1 and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("F1 button pressed")
            self.music_player.toggle_loop_playlist()

        elif event.key() == Qt.Key.Key_2 and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("F2 button pressed")
            self.music_player.toggle_repeat()

        elif event.key() == Qt.Key.Key_3 and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("F3 button pressed")
            self.music_player.toggle_shuffle()

        elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("pressed ctrl + c")
            self.copy_current_row_path()

        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("pressed ctrl + S")
            self.save_playlist()

        else:
            # For other keys, use the default behavior
            super().keyPressEvent(event)

    def save_playlist(self):
        # Show the dialog to get the playlist name
        dialog = PlaylistNameDialog()
        if dialog.exec():
            playlist_name = dialog.get_playlist_name().strip()

            if not playlist_name:
                print("No playlist name provided!")
                return

            playlist_path = os.path.join(self.config_path, "playlists")
            os.makedirs(playlist_path, exist_ok=True)
            playlist_file = os.path.join(playlist_path, playlist_name + ".json")

            # Save the table data
            self.song_table_widget.save_table_data(playlist_file)
            print(f"Playlist saved as: {playlist_file}")
        else:
            print("Save canceled.")

    def exit_app(self):
        self.song_table_widget.save_table_data()
        # self.music_player.save_playback_control_state()
        print(self.ej.get_value("playback_states"))
        self.ej.save_data_when_quit()
        sys.exit()

    def toggle_add_directories(self):
        self.add_new_directory.exec()

    def set_default_background_image(self):
        self.ej.setupBackgroundImage()
        self.lrc_player.resize_background_image(self.ej.get_value("background_image"))
        QMessageBox.about(self, "Default Background Image", "Default lyric background image is restored")

    def on_off_lyrics(self, checked):
        if checked:
            self.ej.edit_value("show_lyrics", True)
            self.lrc_player.show_lyrics = True
            self.show_lyrics_action.setChecked(True)
            if self.lrc_file:
                self.lrc_player.activate_sync_lyric_connection(self.lrc_file)

            if not self.lrc_player.started_player:
                self.lrc_player.media_lyric.setText(self.lrc_player.media_font.get_formatted_text("April Music Player"))
                return

            self.lrc_player.media_lyric.setText(
                self.lrc_player.media_font.get_formatted_text(self.lrc_player.current_lyric_text))

        else:
            print("in disabling")
            self.ej.edit_value("show_lyrics", False)
            self.lrc_player.show_lyrics = False
            self.show_lyrics_action.setChecked(False)
            if self.lrc_player.media_sync_connected:
                self.music_player.player.positionChanged.disconnect(self.lrc_player.update_media_lyric)
                self.lrc_player.media_sync_connected = False
            self.lrc_player.media_lyric.setText(self.lrc_player.media_font.get_formatted_text("Lyrics Syncing Disabled"))
            self.lrc_player.current_index = 0

    def toggle_on_off_lyrics(self, checked):
        self.on_off_lyrics(checked)

    def show_font_settings(self):
        self.font_settings_window.exec()

    def trigger_play_song_at_startup(self, checked):
        print(checked)
        if checked:
            self.ej.edit_value("play_song_at_startup", True)
        else:
            self.ej.edit_value("play_song_at_startup", False)

    def toggle_playlist_widget(self):
        print("self toggle_playlist_widget method called")
        self.playlist_widget = PlaylistDialog(self, self.song_table_widget.load_table_data)
        self.playlist_widget.exec()

    def createMenuBar(self):
        menubar = self.menuBar()

        # File Menu (common KDE applications start with File)
        file_menu = menubar.addMenu("&File")

        # Create actions (grouped by functionality)
        # File actions
        close_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton),
                               "&Exit", self)
        close_action.setShortcut("Ctrl+Q")
        close_action.triggered.connect(self.exit_app)

        # Music actions
        reload_directories_action = QAction("&Reload Music Library", self)
        reload_directories_action.setShortcut("Ctrl+Alt+R")
        reload_directories_action.triggered.connect(self.toggle_reload_directories)

        add_directories_action = QAction("&Manage Music Directories...", self)
        add_directories_action.triggered.connect(self.toggle_add_directories)

        self.start_zotify_gui_action = QAction("&Download Music...", self)
        self.start_zotify_gui_action.triggered.connect(self.start_zotify_gui)

        self.start_playlist_widget_action = QAction("&Manage Playlists...", self)
        self.start_playlist_widget_action.triggered.connect(self.toggle_playlist_widget)

        # View actions
        self.show_lyrics_action = QAction("&Enable/Disable Lyrics", self)
        self.show_lyrics_action.setShortcut("Ctrl+I")
        self.show_lyrics_action.setCheckable(True)
        self.show_lyrics_action.setChecked(self.lrc_player.show_lyrics)
        self.show_lyrics_action.triggered.connect(self.toggle_on_off_lyrics)

        self.activate_lyrics_display_action = QAction("&Show Lyrics Display", self)
        self.activate_lyrics_display_action.setShortcut("Ctrl+L")
        self.activate_lyrics_display_action.triggered.connect(self.activate_lrc_display)

        # Settings actions
        self.play_song_at_startup = QAction("&Play on Startup", self)
        self.play_song_at_startup.setCheckable(True)
        self.play_song_at_startup.setChecked(self.ej.get_value("play_song_at_startup"))
        self.play_song_at_startup.triggered.connect(self.trigger_play_song_at_startup)

        self.font_settings_action = QAction(self.settings_icon, "&Font Settings...", self)
        self.font_settings_action.triggered.connect(self.show_font_settings)
        self.font_settings_window = FontSettingsWindow(self)

        # Lyrics display actions
        add_lrc_background = QAction("&Set Custom Background...", self)
        add_lrc_background.triggered.connect(self.ask_for_background_image)

        set_default_background = QAction(self.default_wallpaper_icon, "&Default Background", self)
        set_default_background.triggered.connect(self.set_default_background_image)

        # Help actions
        show_shortcuts_action = QAction("&Keyboard Shortcuts", self)
        show_shortcuts_action.triggered.connect(self.show_shortcuts)

        preparation_tips = QAction("&File Preparation Tips", self)
        preparation_tips.triggered.connect(self.show_preparation)

        fromMe = QAction("&About", self)
        fromMe.triggered.connect(self.show_fromMe)

        # Submenus
        lyrics_color_menu = QMenu("&Lyrics Color", self)
        lyrics_color_menu.setIcon(self.colors_icon)
        self.create_lyrics_color_actions(lyrics_color_menu)

        sync_threshold_menu = QMenu("&Sync Threshold", self)
        self.sync_threshold_menu_actions(sync_threshold_menu)
        self.threshold_actions[self.ej.get_value("sync_threshold")].setChecked(True)

        # Build the menu structure
        # File menu
        file_menu.addAction(self.start_zotify_gui_action)
        file_menu.addAction(self.start_playlist_widget_action)
        file_menu.addSeparator()
        file_menu.addAction(close_action)

        # View menu
        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self.show_lyrics_action)
        view_menu.addAction(self.activate_lyrics_display_action)

        # Settings menu
        settings_menu = menubar.addMenu("&Settings")

        # Music settings
        music_settings_menu = settings_menu.addMenu("&Music")
        music_settings_menu.addAction(self.play_song_at_startup)
        music_settings_menu.addSeparator()
        music_settings_menu.addAction(add_directories_action)
        music_settings_menu.addAction(reload_directories_action)

        # Lyrics settings
        lyrics_settings_menu = settings_menu.addMenu("&Lyrics")
        lyrics_settings_menu.addAction(self.font_settings_action)
        lyrics_settings_menu.addMenu(lyrics_color_menu)
        lyrics_settings_menu.addMenu(self.sync_threshold_menu)
        lyrics_settings_menu.addSeparator()
        lyrics_settings_menu.addAction(add_lrc_background)
        lyrics_settings_menu.addAction(set_default_background)

        # Language settings
        language_settings_menu = settings_menu.addMenu("&UI Language")

        # Create an action group for exclusive selection
        language_group = QActionGroup(self)
        language_group.setExclusive(True)

        # Add language options with mapping
        for lang_name, lang_code in self.language_map.items():
            lang_action = QAction(lang_name, self)
            lang_action.setCheckable(True)
            if lang_code == self.ej.get_value("system_language"):
                lang_action.setChecked(True)  # default language
            # Pass the code to the function instead of the display name
            lang_action.triggered.connect(lambda checked, code=lang_code: self.change_language(code))
            language_group.addAction(lang_action)
            language_settings_menu.addAction(lang_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(show_shortcuts_action)
        help_menu.addAction(preparation_tips)
        help_menu.addSeparator()
        help_menu.addAction(fromMe)

    def change_language(self, language_code):
        print(f"Switching language to: [{language_code}]")
        self.system_language = language_code
        self.ej.change_language(self.system_language)
        self.update_language_in_ui()

    def update_language_in_ui(self):
        self.setWindowTitle(APRIL_WINDOW_TITLE[self.system_language])
        self.album_tree_widget.search_bar.setPlaceholderText(SEARCH_SONG_BY_NAME[self.system_language])
        self.album_tree_widget.search_bar.setToolTip(SONG_SEARCHBAR_TOOLTIP[self.system_language])
        self.filter_search_bar.setPlaceholderText(FILTER_SONGS_FROM_PLAYLIST[self.system_language])
        self.filter_search_bar.setToolTip(FILTER_SONGS_FROM_PLAYLIST_TOOLTIP[self.system_language])

    def createSyncThresholdMenu(self):
        self.sync_threshold_menu = QMenu("&Sync Threshold", self)
        self.sync_threshold_menu_actions(self.sync_threshold_menu)
        self.threshold_actions[self.ej.get_value("sync_threshold")].setChecked(True)

    def sync_threshold_menu_actions(self, sync_threshold_menu):
        # Clear existing actions if any
        sync_threshold_menu.clear()

        # Add explanatory label
        label = QLabel(
            "This is basically the refresh rate. Shorter interval provides \n"
            "smoother syncing but uses more CPU.", self)
        label.setMargin(5)  # Add some padding
        label_action = QWidgetAction(self)
        label_action.setDefaultWidget(label)
        sync_threshold_menu.addAction(label_action)
        sync_threshold_menu.addSeparator()

        # Create action group
        threshold_group = QActionGroup(self)
        threshold_group.setExclusive(True)

        thresholds = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
        self.threshold_actions = {}
        for threshold in thresholds:
            action = QAction(f"{threshold} seconds", self)
            action.setCheckable(True)
            action.setActionGroup(threshold_group)
            action.triggered.connect(lambda checked, t=threshold: self.set_sync_threshold(t))
            sync_threshold_menu.addAction(action)
            self.threshold_actions[threshold] = action

    def create_lyrics_color_actions(self, lyrics_color_menu):
        # Create an action group to enforce a single selection (radio button behavior)
        color_group = QActionGroup(self)
        color_group.setExclusive(True)

        # Add color options with radio buttons
        colors = [
            "white", "black", "blue", "yellow", "red", "cyan", "magenta", "orange", "green", "purple",
            "light gray", "dark gray", "turquoise", "brown", "pink", "navy", "teal", "olive", "maroon",
            "lime", "indigo", "violet", "gold", "silver", "beige", "coral", "crimson", "khaki",
            "lavender", "salmon", "sienna", "tan", "plum", "peach", "chocolate"
        ]

        self.color_actions = {}

        for COLOR in colors:
            action = QAction(COLOR, self)
            action.setCheckable(True)

            # Create a colored pixmap for the color sample
            pixmap = QPixmap(20, 20)  # 20x20 is a reasonable size for an icon
            pixmap.fill(QColor(COLOR))  # Fill the pixmap with the color

            # Set the pixmap as the action icon
            icon = QIcon(pixmap)
            action.setIcon(icon)

            self.color_actions[COLOR] = action
            action.setActionGroup(color_group)

            action.triggered.connect(self.get_selected_color)  # Connect to method
            lyrics_color_menu.addAction(action)
            self.color_actions[COLOR] = action

        self.color_actions[self.ej.get_value("lyrics_color")].setChecked(True)

    def start_zotify_gui(self):
        self.zotify_gui = ZotifyDownloaderGui(self)
        self.zotify_gui.raise_()  # Bring to front
        self.zotify_gui.activateWindow()  # Set focus
        self.zotify_gui.url_input.setFocus()

    def get_selected_color(self):
        selected_color = self.ej.get_value("lyrics_color")
        for color, action in self.color_actions.items():
            if action.isChecked():
                selected_color = color
                break
        print(f"Selected color: {selected_color}")
        self.ej.data["lyrics_color"] = selected_color.lower()
        print("self.data from ej", self.ej.data)
        self.ej.edit_value("lyrics_color", selected_color.lower())

        QMessageBox.information(self, "Lyrics Color", f"Lyrics Color is set to {color}")

    # Method to update sync threshold
    def set_sync_threshold(self):
        selected_threshold = self.ej.get_value("sync_threshold")
        for threshold, action in self.threshold_actions.items():
            if action.isChecked():
                selected_threshold = threshold
                break
        print(f"Selected Threshold: {selected_threshold}")
        self.ej.edit_value("sync_threshold", selected_threshold)
        self.lrc_player.update_interval = selected_threshold

    def show_fromMe(self):
        text = FROMME_TRANSLATIONS[self.system_language]
        QMessageBox.information(self, "Thank you for using April", text)

    def show_preparation(self):
        text = PREPARATION_TRANSLATIONS[self.system_language]
        QMessageBox.information(self, "Preparation of files", text)

    def show_shortcuts(self):
        # Create a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Shortcuts")
        dialog.resize(600, 600)

        # Create a layout for the entire dialog
        main_layout = QVBoxLayout(dialog)

        # Create a search bar
        self.shortcut_search_bar = QLineEdit()
        self.shortcut_search_bar.setPlaceholderText(f"{SEARCH_SONG_BY_NAME[self.system_language]}")
        main_layout.addWidget(self.shortcut_search_bar)

        # Create a scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Create a widget to hold the shortcuts text
        self.shortcuts_widget = QTextEdit()
        self.shortcuts_widget.setHtml(SHORTCUTS_TRANSLATIONS[self.system_language])
        self.shortcuts_widget.setReadOnly(True)

        # Set text formatting options
        self.shortcuts_widget.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.shortcuts_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # Add the widget to the scroll area
        scroll_area.setWidget(self.shortcuts_widget)

        # Store original HTML for search functionality
        self.original_html = self.shortcuts_widget.toHtml()

        # Connect the search bar's textChanged signal
        self.shortcut_search_bar.textChanged.connect(self.filter_shortcuts)

        # Add a close button
        button_layout = QHBoxLayout()
        close_button = QPushButton("Close", dialog)
        close_button.clicked.connect(dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        main_layout.addLayout(button_layout)

        dialog.exec()

    def filter_shortcuts(self, text):
        pass
        if not text:
            self.shortcuts_widget.setHtml(self.original_html)
            return

        # Get clean HTML without previous highlights
        html = self.original_html.replace('<mark>', '').replace('</mark>', '')

        # Case-insensitive search and highlight
        search_text = text.lower()
        start_tag = '<mark>'
        end_tag = '</mark>'
        highlighted_html = html
        index = 0

        while True:
            # Find the text (case-insensitive)
            text_start = highlighted_html.lower().find(search_text, index)
            if text_start == -1:
                break

            text_end = text_start + len(text)

            # Insert highlight tags
            highlighted_html = (highlighted_html[:text_start] + start_tag +
                                highlighted_html[text_start:text_end] + end_tag +
                                highlighted_html[text_end:])

            # Move index past the end of the current match plus the length of the tags we added
            index = text_end + len(start_tag) + len(end_tag)

        self.shortcuts_widget.setHtml(highlighted_html)

    def ask_for_background_image(self):
        # Set default directory based on the operating system
        if self.running_platform == "Windows":
            default_directory = os.path.expanduser("~\\Pictures")
        elif self.running_platform == "Darwin":  # macOS
            default_directory = os.path.expanduser("~/Pictures")
        else:  # Linux and other Unix-like OS
            default_directory = os.path.expanduser("~/Pictures")

        # Open a file dialog with the default directory set
        file_path, _ = QFileDialog.getOpenFileName(self, f"{SELECT_AN_IMAGE_FOR_BACKGROUND_TITLE[self.system_language]}", default_directory)

        if file_path:
            self.ej.edit_value("background_image", file_path)
            self.lrc_player.resize_background_image(file_path)
            # Show the selected file path in a QMessageBox
            QMessageBox.information(self, f"{LOAD_BACKGROUND_IMAGE_TITLE[self.system_language]}", f"You selected: {file_path}")
        else:
            QMessageBox.warning(self, f"{NO_FILE_SELECTED_TITLE[self.system_language]}", f"{DID_NOT_SELECT_IMAGE_FILE[self.system_language]}")

    def show_context_menu(self, pos):
        # Get the item at the clicked position
        item = self.song_table_widget.itemAt(pos)

        if item and "Album Title:" not in item.text():
            # Create the context menu
            context_menu = QMenu(self)

            # Smart download: single or multiple
            download_lyrics_action = context_menu.addAction(f"ᯓ {DOWNLOAD_WITH_LRC[self.system_language]}")
            download_lyrics_action.triggered.connect(self.lyrics_downloader.start_download_from_selection)

            # Add an action to copy the file path
            copy_action = context_menu.addAction(f"➡️ {COPY_SONG_PATH[self.system_language]}")

            # Connect the action to a method
            copy_action.triggered.connect(lambda: self.copy_item_path(item))

            file_tagger_action = context_menu.addAction(f"ⓘ {EDIT_META_DATA[self.system_language]}")
            file_tagger_action.triggered.connect(self.activate_file_tagger)

            # Show the context menu at the cursor position
            context_menu.exec(QCursor.pos())

    def copy_current_row_path(self):
        current_item = self.song_table_widget.currentItem()
        self.copy_item_path(current_item)

    def copy_item_path(self, item):
        file = self.get_music_file_from_click(item)
        if file:
            self.app.clipboard().setText(file)
        print("the file path ", file)

    def get_music_file_from_click(self, item):
        """Returns self.music_file. If the recorded path doesn't exist, self.file_path and self.music_file will be none"""
        if "Album Title:" in item.text():
            return None

        row = item.row()
        self.file_path = self.song_table_widget.item(row, 7).text()  # Retrieve the file path from the hidden column

        if not os.path.isfile(self.file_path):
            # File does not exist
            QMessageBox.warning(self, 'File Not Found', f"The file located at '{self.file_path}' cannot be found. It may have been deleted or moved.")
            self.file_path = None
            self.music_file = None
            return None
        else:
            self.music_file = self.file_path

        return self.file_path

    def activate_file_tagger(self):
        currentRow = self.song_table_widget.currentRow()
        music_file = self.song_table_widget.item(currentRow, 7).text()
        tagger = TagDialog(self, music_file, self.song_table_widget, self.album_tree_widget, self.album_tree_widget.cursor,
                           self.album_tree_widget.conn)
        tagger.exec()

    def create_widgets_and_layouts(self):
        """ The main layout of the music player UI with accurate splitter ratios """
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Create the song collection widget
        self.album_tree_widget.loadSongsToCollection(self.directories)

        # Create the playlist widget
        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout(playlist_widget)
        playlist_layout.addWidget(self.song_table_widget)

        # Create the media widget
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        self.mediaLayout = media_layout  # Keep reference to mediaLayout for later use

        # Create a horizontal splitter for adjustable layouts
        splitter = ColumnSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)  # Make the splitter handle thinner

        # Add the widgets to the splitter
        splitter.addWidget(self.album_tree_widget)
        splitter.addWidget(playlist_widget)
        splitter.addWidget(media_widget)

        # # Set sizes dynamically (account for handles)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)
        splitter.setStretchFactor(2, 1)

        # Add the splitter to the main layout
        main_layout = QHBoxLayout(self.central_widget)
        main_layout.addWidget(splitter)

        # Setup the additional widgets
        self.setup_playlist_widget(playlist_layout)
        self.setupMediaPlayerWidget(media_layout)

    def setup_playlist_widget(self, playlist_layout):
        # volume control to add
        self.filter_search_bar = QLineEdit()
        self.filter_search_bar.setPlaceholderText(f"{FILTER_SONGS_FROM_PLAYLIST[self.system_language]}")
        self.filter_search_bar.setToolTip(f"{FILTER_SONGS_FROM_PLAYLIST_TOOLTIP[self.system_language]}")
        self.filter_search_bar.setFocus()  # Place the cursor in the search bar

        # Connect search bar returnPressed signal to the search method
        self.filter_search_bar.returnPressed.connect(self.filterSongs)

        self.search_bar_layout = QHBoxLayout()
        self.search_bar_layout.addWidget(self.filter_search_bar)
        self.search_bar_layout.addLayout(self.playback_management_layout)

        playlist_layout.addLayout(self.search_bar_layout)
        if self.ej.get_value("music_directories") is None:
            self.add_new_directory.add_directory()

    def click_on_playback_button(self, state):
        if state == "shuffle":
            self.music_player.toggle_shuffle()
        elif state == "loop":
            self.music_player.toggle_loop_playlist()
        elif state == "repeat":
            self.music_player.toggle_repeat()

    def attachMediaWidget(self):
        if self.media_widget and self.mediaLayout:
            self.floating_window.close()  # Close the floating window
            self.floating_window = None  # Remove the reference

            # Re-add the widget to mediaLayout
            self.mediaLayout.addWidget(self.media_widget)
            self.media_widget.setParent(self)  # Re-parent it to the main window

    def floatMediaWidget(self):
        if self.media_widget and self.mediaLayout:
            self.mediaLayout.removeWidget(self.media_widget)
            self.media_widget.setParent(None)

            # Create a new floating window for the media widget
            self.floating_window = QMainWindow()
            self.floating_window.setWindowTitle("Media Player")
            self.floating_window.setCentralWidget(self.media_widget)
            self.floating_window.resize(600, 400)  # Adjust the size if needed
            self.floating_window.show()

    def detachMediaWidget(self):
        if self.media_widget and self.mediaLayout:
            self.mediaLayout.removeWidget(self.media_widget)  # Detach from the layout
            self.media_widget.setParent(None)  # Remove from its parent to make it independent

    def setupMediaPlayerWidget(self, right_layout):
        # Create a widget to hold the media player components
        self.media_widget = QWidget()

        # Override the keyPressEvent in media_widget to propagate to QMainWindow
        def media_keyPressEvent(event: QKeyEvent):
            # Propagate the event to the QMainWindow's keyPressEvent
                self.keyPressEvent(event)

        # Assign the custom keyPressEvent to the media_widget
        self.media_widget.keyPressEvent = media_keyPressEvent        # Assign the keyPressEvent handler to the media_widget

        # Create and configure the layout for the media widget
        mediaLayout = QVBoxLayout(self.media_widget)

        # Create and configure the track display label
        self.track_display = QLabel("No Track Playing")
        self.track_display.setFont(QFont("Komika Axis"))
        self.track_display.setWordWrap(True)
        self.track_display.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.track_display.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.track_display.setStyleSheet("font-size: 20px")

        # Create and configure the image display label
        self.image_display = ClickableImageLabel(self)
        self.image_display.doubleClicked.connect(self.double_click_on_image)

        # Create and configure the song details label
        self.song_details = QLabel()
        self.song_details.setWordWrap(True)  # Ensure the text wraps within the label

        # Create a QWidget to hold the layout
        container_widget = QWidget()
        # container_widget.setStyleSheet("""background-color: #1b1e20""")

        # Create a QVBoxLayout and add self.song_details to it
        layout = QVBoxLayout(container_widget)
        layout.addWidget(self.song_details)
        layout.addStretch()  # This will push self.song_details to the top

        # Set the layout as the widget of the scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(container_widget)

        # Add widgets to the vertical layout
        mediaLayout.addWidget(self.track_display)
        mediaLayout.addWidget(self.image_display)
        mediaLayout.addWidget(scroll_area)  # Add the scroll area instead of the label directly
        mediaLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add the media_widget to the right_layout
        right_layout.addWidget(self.media_widget)

        # Set up the media player controls panel
        self.setupMediaPlayerControlsPanel(right_layout)

    def slider_key_event(self, event):
        # to catch key event on slider.
        if event.key() == Qt.Key.Key_Left:
            print("left key pressed")
            self.seek_backward()

        elif event.key() == Qt.Key.Key_Right:
            print("right key pressed")
            self.seek_forward()

        elif event.key() == Qt.Key.Key_Space:
            print("Space key pressed")
            self.play_pause()

    def slider_mouse_press_event(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Calculate the position relative to the slider length
            slider_length = self.time_slider.width() if self.time_slider.orientation() == Qt.Orientation.Horizontal else self.time_slider.height()
            click_pos = event.position().x() if self.time_slider.orientation() == Qt.Orientation.Horizontal else event.position().y()

            # Map click position to slider range
            ratio = click_pos / slider_length
            new_value = self.time_slider.minimum() + ratio * (self.time_slider.maximum() - self.time_slider.minimum())
            self.time_slider.setValue(int(new_value))
            self.music_player.player.setPosition(int(new_value))
            self.last_updated_position = float(new_value)

            if self.music_player.in_pause_state:
                self.music_player.paused_position = int(new_value)

        # Call the original mousePressEvent from the base class to retain dragging functionality
        QSlider.mousePressEvent(self.time_slider, event)

    def activate_lrc_display(self):
        if self.lrc_player.lrc_display:
            return

        # Check if the LRC file is available
        if self.lrc_player.file:
            # Check if lyrics are enabled for display
            if self.lrc_player.show_lyrics:
                self.lrc_player.start_ui(self)  # Start the lyrics display
            else:
                # Show a warning if the lyrics display is disabled
                QMessageBox.warning(
                    self,
                    "Lyrics Display Disabled",
                    "The lyrics display is currently turned off.\n"
                    "You can enable/disable it by pressing Ctrl + I."
                )
        else:
            if not self.lrc_player.show_lyrics:
                # Show a warning if no lyrics file is linked
                QMessageBox.warning(
                    self,
                    "Lyrics Disabled",
                    "Please enable lyrics display to view the lyrics."
                )

            else:
                if self.music_player.started_playing:
                    # Show a warning if no lyrics file is linked
                    QMessageBox.warning(
                        self,
                        LYRICS_NOT_FOUND_TITLE[self.system_language],
                        LYRICS_NOT_FOUND[self.system_language]
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "No Song Playing",
                        "Please start a song first."
                    )

    def update_progress_label(self, position):
        # Calculate current time and total time
        current_time = format_time(position // 1000)  # Convert from ms to seconds
        total_time = format_time(self.music_player.get_duration() // 1000)  # Total duration in seconds

        duration_string = f"[{current_time}/{total_time}]"
        self.duration_label.setText(duration_string)

    def setupMediaPlayerControlsPanel(self, right_layout):
        self.setup_central_media_control_layout()

        self.lrc_player.media_lyric.setStyleSheet("""
            QLabel {
                padding: 12px 16px;
                border: 2px solid transparent;
                border-left: 4px solid #d32f2f;
                border-right: 4px solid #d32f2f;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
            }
        """)

        self.lrc_player.media_lyric.doubleClicked.connect(self.activate_lrc_display)
        right_layout.addWidget(self.lrc_player.media_lyric)

        self.lrc_player.media_lyric.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        right_layout.addLayout(self.main_media_horizontal_layout)

        controls_layout = QHBoxLayout()
        self.prev_button = QPushButton()
        self.prev_button.setToolTip("seek backward(-1s)")
        self.forward_button = QPushButton()
        self.forward_button.setToolTip("seek forward(+1s)")
        self.prev_song_button = QPushButton()
        self.prev_song_button.setToolTip("Previous Song")
        self.next_song_button = QPushButton()
        self.next_song_button.setToolTip("Next Song")

        # Set size policy for the buttons to ensure consistent height
        size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.prev_button.setSizePolicy(size_policy)
        self.forward_button.setSizePolicy(size_policy)
        self.play_pause_button.setSizePolicy(size_policy)
        self.prev_song_button.setSizePolicy(size_policy)
        self.next_song_button.setSizePolicy(size_policy)

        self.prev_button.setIcon(QIcon(os.path.join(self.ej.icon_path, "seek-backward.ico")))
        self.play_pause_button.setIcon(QIcon(os.path.join(self.ej.icon_path, "play.ico")))
        self.forward_button.setIcon(QIcon(os.path.join(self.ej.icon_path, "seek-forward.ico")))
        self.prev_song_button.setIcon(QIcon(os.path.join(self.ej.icon_path, "previous-song.ico")))
        self.next_song_button.setIcon(QIcon(os.path.join(self.ej.icon_path, "next-song.ico")))

        self.prev_button.clicked.connect(self.seek_backward)
        self.play_pause_button.clicked.connect(self.play_pause)
        self.forward_button.clicked.connect(self.seek_forward)
        self.prev_song_button.clicked.connect(self.play_previous_song)
        self.next_song_button.clicked.connect(self.play_next_song)

        controls_layout.addWidget(self.prev_song_button)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.forward_button)
        controls_layout.addWidget(self.next_song_button)


        self.media_control_slider_playback_control_layout.addLayout(controls_layout)
        self.play_last_played_song()
        self.music_player.setup_playback_buttons()

    def setup_central_media_control_layout(self):
        # Main layout containers
        self.main_media_horizontal_layout = QHBoxLayout()
        self.media_control_slider_playback_control_layout = QVBoxLayout()
        self.media_control_layout = QHBoxLayout()

        # Volume control
        self.volume_control = self.music_player.player.get_volume_control()

        # Duration label - minimal styling
        self.duration_label = QLabel("00:00/00:00")
        self.duration_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)
        self.duration_label.setStyleSheet("font-size: 11px")

        # Playback control buttons
        buttons = [
            ("loop", "loop-default.ico", self.loop_playlist_button),
            ("repeat", "repeat-default.ico", self.repeat_button),
            ("shuffle", "shuffle-default.ico", self.shuffle_button)
        ]

        self.playback_management_layout = QHBoxLayout()
        self.playback_management_layout.setContentsMargins(0, 0, 0, 0)
        self.playback_management_layout.setSpacing(10)

        for action, icon, button in buttons:
            button.setIcon(QIcon(os.path.join(self.ej.icon_path, icon)))
            button.clicked.connect(lambda _, a=action: self.click_on_playback_button(a))
            self.playback_management_layout.addWidget(button)

        # Assemble media controls
        self.media_control_layout.addLayout(self.playback_management_layout)
        self.media_control_layout.addStretch()
        self.media_control_layout.addWidget(self.duration_label)

        # Slider with minimal styling
        self.time_slider = QSlider(Qt.Orientation.Horizontal)

        self.time_slider.keyPressEvent = self.slider_key_event
        self.time_slider.mousePressEvent = self.slider_mouse_press_event
        self.time_slider.setRange(0, self.music_player.get_duration() or 100)
        self.time_slider.setValue(0)

        # Build layout hierarchy
        self.media_control_slider_playback_control_layout.addLayout(self.media_control_layout)
        self.media_control_slider_playback_control_layout.addWidget(self.time_slider)
        self.main_media_horizontal_layout.addLayout(self.media_control_slider_playback_control_layout)
        self.main_media_horizontal_layout.addWidget(self.volume_control)

        # Connections
        self.music_player.player.positionChanged.connect(self.update_slider)
        self.music_player.player.durationChanged.connect(self.update_slider_range)
        self.time_slider.sliderMoved.connect(self.update_player_from_slider)

    def update_slider(self, position):
        time_difference = abs(self.music_player.player.position() - self.last_updated_position)
        if self.update_interval_millisecond > time_difference:
            return
        else:
            self.update_progress_label(self.music_player.player.position())
            self.time_slider.setValue(position)
            self.last_updated_position = self.music_player.player.position()

    def update_slider_range(self, duration):
        print("update duration range called")
        self.time_slider.setRange(0, duration)

    def updateDisplayData(self):
        self.metadata = self.get_metadata(self.music_file)
        updated_text = f'{self.metadata["artist"]} - {self.metadata["title"]}'
        self.track_display.setText(updated_text)

    def updateSongDetails(self, song_file):
        minutes = self.metadata["duration"] // 60
        seconds = self.metadata["duration"] % 60
        # Define the bold HTML tag
        BOLD = '<b>'
        END = '</b>'

        updated_text = (
            f'<div>{BOLD}[Track Details]{END}</div>'
            f'<div>{BOLD}Title{END}: {self.metadata["title"]}</div>'
            f'<div>{BOLD}Artist{END}: {self.metadata["artist"]}</div>'
            f'<div>{BOLD}Album{END}: {self.metadata["album"]}</div>'
            f'<div>{BOLD}Release Date{END}: {self.metadata["year"]}</div>'
            f'<div>{BOLD}Genre{END}: {self.metadata["genre"]}</div>'
            f'<div>{BOLD}Track Number{END}: {self.metadata["track_number"]}</div>'
            f'<div>{BOLD}Comment{END}: {self.metadata["comment"]}</div>'
            f'<div>{BOLD}Duration{END}: {minutes}:{seconds:02d}</div>'
            f'<div>{BOLD}File Path{END}: {song_file}</div>'
        )

        self.song_details.setText(updated_text)
        # Set text interaction to allow text selection
        self.song_details.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.song_details.setWordWrap(True)

    def clear_song_details_and_image(self):
        self.song_details.clear()
        self.track_display.clear()
        self.image_display.clear()

    def restore_table(self):
        for row in range(self.song_table_widget.rowCount()):
            self.song_table_widget.setRowHidden(row, False)

    def filterSongs(self):
        self.hidden_rows = True
        self.song_table_widget.clearSelection()  # Clear previous selections (highlighting)
        if self.filter_search_bar.hasFocus():
            search_text = self.filter_search_bar.text().lower()

            if search_text == "":  # If the search text is empty, reset the table view
                self.restore_table()

            elif search_text == "random":  # If the search text is "random", play a random song
                self.play_random_song()

            elif search_text == "load background":
                self.song_table_widget.setup_backgroundimage_logo()

            # elif search_text == "detach":
            #     self.detachMediaWidget()
            #
            # elif search_text == "float":
            #     self.floatMediaWidget()
            #
            # elif search_text == "attach":
            #     self.attachMediaWidget()

            # elif search_text == "crash":
            #     raise ValueError("This is a ValueError for testing purposes.")

            else:
                found_at_least_one = False  # Flag to track if at least one match is found
                for row in range(self.song_table_widget.rowCount()):
                    match = False
                    item = self.song_table_widget.item(row, 0)  # Check the first column of each row

                    # Hide album title rows (rows containing 'Album Title:')
                    if item and "Album Title:" in item.text():
                        self.song_table_widget.setRowHidden(row, True)
                        continue  # Skip further processing for album title rows

                    # Now filter regular song rows
                    for column in range(2):  # Check first two columns for a match
                        item = self.song_table_widget.item(row, column)
                        if item and search_text in item.text().lower():
                            match = True
                            found_at_least_one = True  # Set flag to True if at least one match is found
                            break

                    # Highlight matched rows and hide unmatched rows if at least one match is found
                    if found_at_least_one:
                        self.song_table_widget.setRowHidden(row, not match)
                        # if match:
                        #     self.songTableWidget.selectRow(row)  # Highlight the row if it matches
                        #     self.songTableWidget.scroll_to_current_row()
                    else:
                        self.song_table_widget.setRowHidden(row, True)  # Hide the other rows

            # Clear the search bar and reset the placeholder text
            self.filter_search_bar.clear()
            self.filter_search_bar.setPlaceholderText("Filter Songs From the Playlist...")

    def cleanDetails(self):
        # clear the remaining from previous play
        self.lrc_player.file = None
        self.music_player.player.stop()
        self.track_display.setText("No Track Playing")
        self.image_display.clear()
        self.song_details.clear()

    def update_information(self):
        if self.music_file:
            self.updateDisplayData()
            self.extract_and_set_album_art()
            self.updateSongDetails(self.music_file)
        else:
            return

    def find_row(self, target_file_path):
        # Loop through each row in the table
        for row in range(self.song_table_widget.rowCount()):
            item = self.song_table_widget.item(row, 7)
            if item:
                current_file_path = self.song_table_widget.item(row, 7).text()

                # Check if the current file path matches the target file path
                if current_file_path == target_file_path:
                    print(f"File found in row: {row}")
                    # Perform any action you want with the found row, such as selecting it
                    self.song_table_widget.selectRow(row)
                    return row
        else:
            print("File path not found.")

    def song_initializing_stuff(self):
        self.update_information()
        self.get_lrc_file()
        self.lrc_player.reset_labels()
        self.music_player.update_music_file(self.music_file)
        self.music_player.default_pause_state()
        self.update_slider_range(self.music_player.get_duration())

    def play_previous_song(self):
        if self.music_player.playback_states["shuffle"]:
            self.current_playing_random_song_index -= 1
            if self.current_playing_random_song_index < 1:
                self.current_playing_random_song_index = len(self.song_table_widget.random_song_list) - 1
            self.play_random_song(user_clicking=True)
            self.song_table_widget.setFocus()
        else:
            previous_song = self.song_table_widget.get_previous_song_object()
            self.handle_row_double_click(previous_song)
            self.song_table_widget.setFocus()

    def play_next_song(self, fromStart=None):
        self.song_table_widget.clearSelection()
        if fromStart:
            next_song = self.song_table_widget.get_next_song_object(fromstart=True)
            self.handle_row_double_click(next_song)
            return

        if self.music_player.playback_states['shuffle']:
            self.current_playing_random_song_index += 1
            if self.current_playing_random_song_index > len(self.song_table_widget.random_song_list) - 1:
                self.current_playing_random_song_index = 0
            self.play_random_song(user_clicking=True)
            self.song_table_widget.setFocus()
        else:
            next_song = self.song_table_widget.get_next_song_object(fromstart=False)
            self.handle_row_double_click(next_song)
            self.song_table_widget.setFocus()

    def play_the_song_at_the_top(self):
        print("inside play the song at the top method")
        if self.song_table_widget.files_on_playlist:
            self.song_table_widget.clearSelection()
            print("Files on playlist")
            print(self.song_table_widget.files_on_playlist)
            self.music_file = self.song_table_widget.files_on_playlist[0]
            self.song_table_widget.song_playing_row = self.find_row(self.music_file)
            self.song_initializing_stuff()
            self.play_song()

    def play_random_song(self, user_clicking=False, from_shortcut=False):
        if not self.song_table_widget.files_on_playlist:
            return

        self.song_table_widget.clearSelection()

        print(self.current_playing_random_song_index, "current index")

        if not user_clicking:  # without user clicking next/previous
            self.current_playing_random_song_index += 1

            if self.current_playing_random_song_index > len(self.song_table_widget.random_song_list) - 1:
                self.lrc_player.media_lyric.setText(
                    self.lrc_player.media_font.get_formatted_text(self.music_player.eop_text))
                self.ej.edit_value("last_played_song", value={})
                return

        if from_shortcut:
            self.music_file = choice(self.song_table_widget.files_on_playlist)
        else:
            self.music_file = self.song_table_widget.random_song_list[self.current_playing_random_song_index]

        random_song_row = self.find_row(self.music_file)
        self.song_table_widget.song_playing_row = random_song_row

        # Here is to start doing the normal stuff of preparation and playing song.
        self.song_initializing_stuff()
        self.play_song()

    def handle_row_double_click(self, item=None):
        # Check if the item exists and is valid
        if item is None:
            return

        row = item.row()  # Get the row of the clicked item

        the_text = item.text()

        if the_text:
            if "Album Title: " in the_text:
                pass
            else:
                self.item = item
                self.song_table_widget.song_playing_row = row
                self.lrc_player.started_player = True

                # Check if a valid music file was clicked
                if self.get_music_file_from_click(item):
                    self.song_initializing_stuff()  # Initialize player
                    self.play_song()  # Play the song

                    # Update shuffle state if shuffle is enabled
                    if self.ej.get_value("playback_states")["shuffle"]:
                        print(self.song_table_widget.random_song_list)
                        self.current_playing_random_song_index = int(self.song_table_widget.random_song_list.index(self.music_file))
                else:
                    self.lrc_player.disconnect_syncing()
                    return

        elif the_text == "":
            # Handle case where the clicked item is empty
            print("Empty cell clicked!")
            return

        # Handling hidden rows and restoration logic
        if self.hidden_rows:
            self.restore_table()

            # self.songTableWidget.clearSelection()
            self.song_table_widget.setFocus()

            # Reset hidden rows flag
            self.hidden_rows = False
            self.simulate_keypress(self.song_table_widget, Qt.Key.Key_G)  # Simulate keypres

    def stop_song(self):
        if self.music_player.started_playing:
            self.music_player.player.stop()
            self.lrc_player.started_player = False
            self.lrc_player.disconnect_syncing()
            self.play_pause_button.setIcon(QIcon(os.path.join(self.ej.icon_path, "play.ico")))
            self.lrc_player.media_lyric.setText(self.lrc_player.media_font.get_formatted_text("April Music Player"))
            self.duration_label.setText("")
            self.music_player.started_playing = False
            self.clear_song_details_and_image()

    def play_song(self):
        self.last_updated_position = 0.0
        # current for checking lrc on/off state and then play song
        self.play_pause_button.setIcon(QIcon(os.path.join(self.ej.icon_path, "pause.ico")))

        self.music_player.started_playing = True
        self.music_player.play()

        if self.saved_position:
            self.music_player.player.setPosition(int(self.saved_position))
        else:
            self.music_player.player.setPosition(int(0))

        self.reset_lyrics_connection()

        if self.lrc_file:
            self.init_lyrics_connection()
        else:
            self.lrc_player.media_lyric.setText(self.lrc_player.media_font.get_formatted_text("April Music Player"))

    def reset_lyrics_connection(self):
        if self.lrc_player.media_sync_connected:
            self.music_player.player.positionChanged.disconnect(self.lrc_player.update_media_lyric)
            self.lrc_player.media_sync_connected = False

    def init_lyrics_connection(self):
        if self.lrc_player.show_lyrics:
            self.lrc_player.activate_sync_lyric_connection(self.lrc_file)
        else:
            if self.lrc_player.media_sync_connected:
                self.lrc_player.media_lyric.setText(self.lrc_player.media_font.get_formatted_text("April Music Player"))
                self.lrc_player.media_sync_connected = False

            self.lrc_player.media_lyric.setText(self.lrc_player.media_font.get_formatted_text("April Music Player"))
            self.music_player.player.positionChanged.disconnect(self.lrc_player.update_media_lyric)

    def seek_backward(self):
        self.music_player.seek_backward()

    def seek_forward(self):
        self.music_player.seek_forward()

    def play_pause(self):
        # for checking eop then calling button changing method for play/pause
        current_text = html_to_plain_text(self.lrc_player.media_lyric.text())
        if current_text == self.music_player.eop_text:
            if self.music_player.playback_states["shuffle"]:
                # self.get_random_song_list = self.song_table_widget.random_song_list
                self.current_playing_random_song_index = 0
                self.play_random_song(user_clicking=True)
            else:
                self.play_next_song(True)
        else:
            self.music_player.play_pause_music()

    def update_player_from_slider(self, position):
        print("update player from slider method called")
        # Set the media player position when the slider is moved
        if self.music_player.in_pause_state:
            self.music_player.paused_position = position

        self.music_player.player.setPosition(position)

    def get_lrc_file(self):
        music_file_ext = (".ogg", ".mp3", ".wav", ".m4a", ".flac")

        base, ext = os.path.splitext(self.music_file)

        if ext.lower() in music_file_ext:
            lrc = f"{base}.lrc"
        else:
            lrc = None

        if lrc and os.path.exists(lrc):
            self.lrc_file = lrc
            print(self.lrc_file)
        else:
            self.lrc_file = None
            self.lrc_player.file = None

        if self.lrc_file is None:
            self.lrc_player.media_lyric.setText("What the fuck is wrong here?")

    def double_click_on_image(self):
        if self.music_file is None:
            return
        elif self.image_display.text() == "No Album Art Found":
            return
        else:
            album_window = AlbumImageWindow(self, self.passing_image, self.icon_path, self.music_file,
                                            self.screen_size.height())
            album_window.exec()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showMaximized()
            self.is_fullscreen = False
        else:
            self.showFullScreen()
            self.is_fullscreen = True

    def extract_and_set_album_art(self):
        audio_file = File(self.music_file)

        if isinstance(audio_file, MP3):
            album_image_data = extract_mp3_album_art(audio_file)
        elif isinstance(audio_file, OggVorbis):
            album_image_data = extract_ogg_album_art(audio_file)
        elif isinstance(audio_file, FLAC):
            album_image_data = extract_flac_album_art(audio_file)
        elif isinstance(audio_file, MP4) or audio_file.mime[0] == 'video/mp4':  # Handle both MP4 and M4A
            album_image_data = extract_mp4_album_art(audio_file)
        elif audio_file.mime[0] == 'audio/x-wav':
            try:
                id3_tags = ID3(self.music_file)
                apic = id3_tags.getall('APIC')  # APIC frames contain album art in ID3
                album_image_data = apic[0].data if apic else None
            except ID3NoHeaderError:
                album_image_data = None  # Handle cases where there's no ID3 tag or image
        else:
            album_image_data = None

        if album_image_data:
            pixmap = QPixmap()
            pixmap.loadFromData(album_image_data)
        else:
            # Load a default image if no album art is found
            pixmap = QPixmap(os.path.join(self.script_path, "icons/april-logo.png"))

        self.passing_image = pixmap  # for album art double-clicking

        # Set the final rounded image to QLabel
        self.image_display.setPixmap(self.get_scaled_rounded_pixmap(pixmap))
        self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)

    def set_album_art_from_url(self, image_path):
        """Set album art from a given image URL."""
        pixmap = QPixmap(image_path)
        if pixmap.loadFromData(request.get(image_path).content):
            self.passing_image = pixmap  # for album art double-clicking
            self.image_display.setPixmap(self.get_scaled_rounded_pixmap(pixmap))
            self.image_display.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignHCenter)
        else:
            print("Failed to load image from URL")

    def get_scaled_rounded_pixmap(self, pixmap):
        # Continue with the process of resizing, rounding, and setting the pixmap
        scaled_pixmap = pixmap.scaled(self.image_size, self.image_size,
                                      aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                      transformMode=Qt.TransformationMode.SmoothTransformation)

        rounded_pixmap = getRoundedCornerPixmap(scaled_pixmap, self.image_size, self.image_size)
        return rounded_pixmap

    def simulate_keypress(self, widget, key):
        """Simulate keypress for the given widget."""
        key_event = QKeyEvent(QKeyEvent.Type.KeyPress, key, Qt.KeyboardModifier.ControlModifier)
        QCoreApplication.postEvent(widget, key_event)

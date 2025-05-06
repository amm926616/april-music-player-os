
from base64 import b64decode
import os
from random import choice
import sys
from urllib import request
from PyQt6.QtGui import QIcon, QFont, QFontDatabase, QAction, QCursor, QKeyEvent, QActionGroup, QColor, \
    QPainter, QPixmap, QPainterPath, QTextDocument, QTextOption
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox, QSystemTrayIcon, QMenu, QWidgetAction,
    QLabel, QPushButton, QSlider, QLineEdit, QFileDialog, QScrollArea, QSizePolicy, QDialog, QStyle,
    QTextEdit
)

from PyQt6.QtCore import Qt, QCoreApplication, QRectF
from PyQt6.QtWidgets import QStyleFactory
from mutagen import File
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC
from mutagen.id3 import ID3, ID3NoHeaderError
from mutagen.oggvorbis import OggVorbis
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.wave import WAVE

from components.album_image_window import AlbumImageWindow
from consts.HTML_LABELS import SHORTCUTS, PREPARATION, FROMME
from components.lrcDisplay import LRCSync
from music_player.musicplayer import MusicPlayer
from components.clickable_label import ClickableImageLabel
from _utils.easy_json import EasyJson
from main_ui.songtablewidget import SongTableWidget, PlaylistNameDialog
from main_ui.albumtreewidget import AlbumTreeWidget
from components.fontsettingdialog import FontSettingsWindow
from components.tag_dialog import TagDialog
from components.addnewdirectory import AddNewDirectory
from components.music_downloader_gui import MusicDownloaderWidget
from components.playlist_manager import PlaylistDialog
from components.splitter import ColumnSplitter
from _utils.lrc_downloader import LyricsDownloader


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
        self.mediaLayout = None
        self.app = app
        self.playlist_widget = None
        self.ej = EasyJson()  # ej initializing
        self.ej.ensure_config_file()

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
        self.icon_folder_path = os.path.join(self.script_path, 'icons', 'configuration_icons')
        self.icon_path = os.path.join(self.script_path, "icons", "april-icon.png")
        print("The icon path is, " + self.icon_path)

        QFontDatabase.addApplicationFont(os.path.join(self.script_path, "fonts/KOMIKAX_.ttf"))

        self.slider_layout = None
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
        self.search_bar = None
        self.track_display = None
        self.song_details = None
        self.image_display = None
        self.slider = QSlider(Qt.Orientation.Horizontal, self)
        self.slider.mousePressEvent = self.slider_mousePressEvent

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
            song_table_widget=self.songTableWidget,
            app=self.app,
            get_path_callback=self.get_music_file_from_click
        )

    def init_main_classes(self, music_files=None):
        self.music_player = MusicPlayer(self, self.play_pause_button, self.loop_playlist_button, self.repeat_button,
                                        self.shuffle_button)

        self.lrcPlayer = LRCSync(self, self.music_player, self.config_path, self.on_off_lyrics, self.showMaximized)

        # Initialize the table widget
        self.songTableWidget = SongTableWidget(self, self.handleRowDoubleClick, self.music_player.seek_forward,
                                               self.music_player.seek_backward, self.play_pause, self.screen_size.height())

        self.albumTreeWidget = AlbumTreeWidget(self, self.songTableWidget)

        self.addnewdirectory = AddNewDirectory(self)

        print(music_files)
        if music_files:
            for file in music_files:
                print(file)
                self.albumTreeWidget.add_song_by_file_path(file)

        # self.simulate_keypress(self.songTableWidget, Qt.Key.Key_7)

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

            last_played_item_list = self.songTableWidget.findItems(self.music_file, Qt.MatchFlag.MatchExactly)

            if last_played_item_list:
                print("This is the song from item loaded")
                self.handleRowDoubleClick(last_played_item_list[0])

                # One-time connection for mediaStatusChanged signal
                self.music_player.player.mediaStatusChanged.connect(self.on_single_media_loaded)

                # Set the flag to indicate playback started by this method
                self.is_playing_last_song = True
                self.simulate_keypress(self.songTableWidget, Qt.Key.Key_G)

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
        self.albumTreeWidget.loadSongsToCollection(loadAgain=True)

    def createUI(self):
        self.setWindowTitle("April Music Player - Digest Lyrics")
        self.setGeometry(100, 100, 800, 400)

        self.setWindowIcon(QIcon(self.icon_path))
        self.createMenuBar()
        self.createWidgetsAndLayouts()

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
        if self.lrcPlayer.lrc_display is not None:
            self.lrcPlayer.lrc_display.close()
        event.ignore()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_I and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            print("disabled lyrics")
            if self.lrcPlayer.show_lyrics:
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
            self.seekBack()

        elif event.key() == Qt.Key.Key_Right:
            print("right key pressed")
            self.seekForward()

        elif event.key() == Qt.Key.Key_Space:
            print("Space key pressed")
            self.play_pause()

        elif event.key() == Qt.Key.Key_L and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.activate_lrc_display()

        elif event.key() == Qt.Key.Key_Q and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.exit_app()

        elif (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_F:
            self.search_bar.setFocus()
            self.search_bar.setCursorPosition(len(self.search_bar.text()))

        elif event.key() == Qt.Key.Key_F and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.albumTreeWidget.search_bar.setFocus()
            self.albumTreeWidget.search_bar.setCursorPosition(len(self.search_bar.text()))
            self.albumTreeWidget.search_bar.clear()

        elif (event.modifiers() & Qt.KeyboardModifier.AltModifier) and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) and (event.key() == Qt.Key.Key_R):
            print("shift alt r pressed")
            self.lrcPlayer.restart_music()

        elif (event.modifiers() & Qt.KeyboardModifier.AltModifier) and (event.modifiers() & Qt.KeyboardModifier.ControlModifier) and event.key() == Qt.Key.Key_R:
            self.toggle_reload_directories()

        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_R:
            print("playing random song")
            self.songTableWidget.setFocus()
            self.play_random_song(user_clicking=True, from_shortcut=True)

        elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.restore_table()

        elif event.key() == Qt.Key.Key_T and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.songTableWidget.setFocus()  # set focus on table
            self.play_the_song_at_the_top()

        elif event.key() == Qt.Key.Key_J and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.songTableWidget.setFocus()  # set focus on table

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
            self.songTableWidget.save_table_data(playlist_file)
            print(f"Playlist saved as: {playlist_file}")
        else:
            print("Save canceled.")

    def exit_app(self):
        self.songTableWidget.save_table_data()
        # self.music_player.save_playback_control_state()
        print(self.ej.get_value("playback_states"))
        self.ej.save_data_when_quit()
        sys.exit()

    def toggle_add_directories(self):
        self.addnewdirectory.exec()

    def set_default_background_image(self):
        self.ej.setupBackgroundImage()
        self.lrcPlayer.resizeBackgroundImage(self.ej.get_value("background_image"))
        QMessageBox.about(self, "Default Background Image", "Default lyric background image is restored")

    def on_off_lyrics(self, checked):
        if checked:
            self.ej.edit_value("show_lyrics", True)
            self.lrcPlayer.show_lyrics = True
            self.show_lyrics_action.setChecked(True)
            if self.lrc_file:
                self.lrcPlayer.activate_sync_lyric_connection(self.lrc_file)

            if not self.lrcPlayer.started_player:
                self.lrcPlayer.media_lyric.setText(self.lrcPlayer.media_font.get_formatted_text("April Music Player"))
                return

            self.lrcPlayer.media_lyric.setText(
                self.lrcPlayer.media_font.get_formatted_text(self.lrcPlayer.current_lyric_text))

        else:
            print("in disabling")
            self.ej.edit_value("show_lyrics", False)
            self.lrcPlayer.show_lyrics = False
            self.show_lyrics_action.setChecked(False)
            if self.lrcPlayer.media_sync_connected:
                self.music_player.player.positionChanged.disconnect(self.lrcPlayer.update_media_lyric)
                self.lrcPlayer.media_sync_connected = False
            self.lrcPlayer.media_lyric.setText(self.lrcPlayer.media_font.get_formatted_text("Lyrics Syncing Disabled"))
            self.lrcPlayer.current_index = 0

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
        self.playlist_widget = PlaylistDialog(self, self.songTableWidget.load_table_data)
        self.playlist_widget.exec()

    def createMenuBar(self):
        # this is the menubar that will hold all together
        menubar = self.menuBar()

        reload_directories_action = QAction("Reload Music Files [Ctrl + Alt + R]", self)
        reload_directories_action.triggered.connect(self.toggle_reload_directories)

        # Actions that will become buttons for each menu
        add_directories_action = QAction("Manage Music Directories", self)
        add_directories_action.triggered.connect(self.toggle_add_directories)

        # Get the standard "close" icon from the system
        close_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogCloseButton)

        # Create the Exit action
        close_action = QAction(close_icon, "Exit [Ctrl + Q]", self)
        close_action.triggered.connect(self.exit_app)

        show_shortcuts_action = QAction("Show Shortcuts", self)
        show_shortcuts_action.triggered.connect(self.show_shortcuts)

        preparation_tips = QAction("Preparation of files", self)
        preparation_tips.triggered.connect(self.show_preparation)

        fromMe = QAction("From Developer", self)
        fromMe.triggered.connect(self.show_fromMe)

        add_lrc_background = QAction("Change Lrc Background Image with Custom Local Image", self)
        add_lrc_background.triggered.connect(self.ask_for_background_image)

        set_default_background = QAction(self.default_wallpaper_icon, "Set Default Background Image by April", self)
        set_default_background.triggered.connect(self.set_default_background_image)

        self.show_lyrics_action = QAction("Show Lyrics [Ctrl + L]", self)
        self.show_lyrics_action.setCheckable(True)
        self.show_lyrics_action.setChecked(self.lrcPlayer.show_lyrics)
        self.show_lyrics_action.triggered.connect(self.toggle_on_off_lyrics)

        # Add Font Settings to options menu
        self.font_settings_action = QAction(self.settings_icon, "Font Configurations", self)
        self.font_settings_action.triggered.connect(self.show_font_settings)

        self.font_settings_window = FontSettingsWindow(self)

        # Play song at startup action
        self.play_song_at_startup = QAction("Play Song At Program Startup [Ctrl + I]", self)
        self.play_song_at_startup.setCheckable(True)
        self.play_song_at_startup.setChecked(self.ej.get_value("play_song_at_startup"))
        self.play_song_at_startup.triggered.connect(self.trigger_play_song_at_startup)

        # Start zotify gui
        self.start_zotify_gui_action = QAction("Music Downloader", self)
        self.start_zotify_gui_action.triggered.connect(self.start_zotify_gui)

        self.start_playlist_widget_action = QAction("Saved Playlists", self)
        self.start_playlist_widget_action.triggered.connect(self.toggle_playlist_widget)

        # These are main menus in the menu bar
        settings_menu = menubar.addMenu("Configuration")
        music_files_menu = QMenu("⚙️ Music Files Configurations", self)
        lyrics_display_menu = QMenu("⚙️ Lyrics Display Configurations", self)

        settings_menu.addMenu(music_files_menu)
        settings_menu.addMenu(lyrics_display_menu)

        menubar.addAction(self.start_zotify_gui_action)
        menubar.addAction(self.start_playlist_widget_action)

        help_menu = menubar.addMenu("Help")

        # Add a sub-menu for text color selection with radio buttons
        lyrics_color_menu = QMenu("Choose Lyrics Color", self)
        lyrics_color_menu.setIcon(self.colors_icon)
        self.create_lyrics_color_actions(lyrics_color_menu)

        # Add a sub-menu for sync threshold selection with radio buttons
        sync_threshold_menu = QMenu("Choose Syncing Interval", self)
        self.sync_threshold_menu_actions(sync_threshold_menu)

        # Set the previously selected threshold
        self.threshold_actions[self.ej.get_value("sync_threshold")].setChecked(True)

        """Linking actions and menus"""
        # settings menu
        settings_menu.addAction(self.play_song_at_startup)
        settings_menu.addAction(self.show_lyrics_action)
        settings_menu.addAction(close_action)

        # music file menu
        music_files_menu.addAction(add_directories_action)
        music_files_menu.addAction(reload_directories_action)

        # help menu
        help_menu.addAction(fromMe)
        help_menu.addAction(preparation_tips)
        help_menu.addAction(show_shortcuts_action)

        # lyrics display menu
        lyrics_display_menu.addAction(self.font_settings_action)
        lyrics_display_menu.addAction(add_lrc_background)
        lyrics_display_menu.addAction(set_default_background)
        lyrics_display_menu.addMenu(lyrics_color_menu)
        lyrics_display_menu.addMenu(sync_threshold_menu)

    def sync_threshold_menu_actions(self, sync_threshold_menu):
        # Add a QLabel at the top of the menu with your message
        label = QLabel(
            "This is basically the refresh rate. Shorter interval provides \nsmoother syncing but uses more CPU.", self)
        label_action = QWidgetAction(self)
        label_action.setDefaultWidget(label)

        # Create an action group to enforce a single selection (radio button behavior)
        threshold_group = QActionGroup(self)
        threshold_group.setExclusive(True)

        # Define threshold options in seconds
        thresholds = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
        self.threshold_actions = {}
        for THRESHOLD in thresholds:
            action = QAction(f"{THRESHOLD} seconds", self)
            action.setCheckable(True)
            action.setActionGroup(threshold_group)
            action.triggered.connect(self.set_sync_threshold)  # Connect to method
            sync_threshold_menu.addAction(action)
            self.threshold_actions[THRESHOLD] = action

        sync_threshold_menu.addAction(label_action)

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
        if not hasattr(self, 'zotify_gui') or self.zotify_gui is None:
            self.zotify_gui = MusicDownloaderWidget(self)
        self.zotify_gui.show()
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
        self.lrcPlayer.update_interval = selected_threshold

    def show_fromMe(self):
        text = FROMME
        QMessageBox.information(self, "Thank you for using April", text)

    def show_preparation(self):
        text = PREPARATION
        QMessageBox.information(self, "Preparation of files", text)

    def show_shortcuts(self):
        # Create a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Shortcuts")
        dialog.resize(600, 600)

        # Create a layout for the entire dialog
        main_layout = QVBoxLayout(dialog)

        # Create a search bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Search shortcuts...")
        main_layout.addWidget(search_bar)

        # Create a scrollable area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        main_layout.addWidget(scroll_area)

        # Create a widget to hold the shortcuts text
        self.content_widget = QTextEdit()
        self.content_widget.setHtml(SHORTCUTS)
        self.content_widget.setReadOnly(True)

        # Set text formatting options
        self.content_widget.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.content_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        # Add the widget to the scroll area
        scroll_area.setWidget(self.content_widget)

        # Store original HTML for search functionality
        self.original_html = self.content_widget.toHtml()

        # Connect the search bar's textChanged signal
        search_bar.textChanged.connect(self.filter_shortcuts)

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
            self.content_widget.setHtml(self.original_html)
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

        self.content_widget.setHtml(highlighted_html)

    def ask_for_background_image(self):
        # Set default directory based on the operating system
        if self.running_platform == "Windows":
            default_directory = os.path.expanduser("~\\Pictures")
        elif self.running_platform == "Darwin":  # macOS
            default_directory = os.path.expanduser("~/Pictures")
        else:  # Linux and other Unix-like OS
            default_directory = os.path.expanduser("~/Pictures")

        # Open a file dialog with the default directory set
        file_path, _ = QFileDialog.getOpenFileName(self, "Select an Image file for lrc display background image", default_directory)

        if file_path:
            self.ej.edit_value("background_image", file_path)
            self.lrcPlayer.resizeBackgroundImage(file_path)
            # Show the selected file path in a QMessageBox
            QMessageBox.information(self, "Load Background Image", f"You selected: {file_path}")
        else:
            QMessageBox.warning(self, "No File Selected", "You did not select any file.")

    def show_context_menu(self, pos):
        # Get the item at the clicked position
        item = self.songTableWidget.itemAt(pos)

        if item and "Album Title:" not in item.text():
            # Create the context menu
            context_menu = QMenu(self)

            # Smart download: single or multiple
            download_lyrics_action = context_menu.addAction("ᯓ Download Lyrics with lrcdl")
            download_lyrics_action.triggered.connect(self.lyrics_downloader.start_download_from_selection)

            # Add an action to copy the file path
            copy_action = context_menu.addAction("➡️ Copy Song Path (Ctrl+C)")

            # Connect the action to a method
            copy_action.triggered.connect(lambda: self.copy_item_path(item))

            file_tagger_action = context_menu.addAction("ⓘ Edit Song's Metadata")
            file_tagger_action.triggered.connect(self.activate_file_tagger)

            # Show the context menu at the cursor position
            context_menu.exec(QCursor.pos())

    def copy_current_row_path(self):
        current_item = self.songTableWidget.currentItem()
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
        self.file_path = self.songTableWidget.item(row, 7).text()  # Retrieve the file path from the hidden column

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
        currentRow = self.songTableWidget.currentRow()
        music_file = self.songTableWidget.item(currentRow, 7).text()
        tagger = TagDialog(self, music_file, self.songTableWidget, self.albumTreeWidget, self.albumTreeWidget.cursor,
                           self.albumTreeWidget.conn)
        tagger.exec()

    def createWidgetsAndLayouts(self):
        """ The main layout of the music player UI with accurate splitter ratios """
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Create the song collection widget
        self.albumTreeWidget.loadSongsToCollection(self.directories)

        # Create the playlist widget
        playlist_widget = QWidget()
        playlist_layout = QVBoxLayout(playlist_widget)
        playlist_layout.addWidget(self.songTableWidget)

        # Create the media widget
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        self.mediaLayout = media_layout  # Keep reference to mediaLayout for later use

        # Create a horizontal splitter for adjustable layouts
        splitter = ColumnSplitter()
        splitter.setOrientation(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)  # Make the splitter handle thinner

        # Add the widgets to the splitter
        splitter.addWidget(self.albumTreeWidget)
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
        self.setupSongListWidget(playlist_layout)
        self.setupMediaPlayerWidget(media_layout)

    def setupSongListWidget(self, playlist_layout):
        # volume control to add
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Filter Songs From the Playlist...")
        self.search_bar.setToolTip("[Ctrl + Shift + F] for shortcut")
        self.search_bar.setFocus()  # Place the cursor in the search bar

        # Connect search bar returnPressed signal to the search method
        self.search_bar.returnPressed.connect(self.filterSongs)

        self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "assets", "media-icons", "loop-default.ico")))
        self.loop_playlist_button.clicked.connect(lambda: self.click_on_playback_button("loop"))

        self.repeat_button.setIcon(QIcon(os.path.join(self.script_path, "assets", "media-icons", "repeat-default.ico")))
        self.repeat_button.clicked.connect(lambda: self.click_on_playback_button("repeat"))

        self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "assets", "media-icons", "shuffle-default.ico")))
        self.shuffle_button.clicked.connect(lambda: self.click_on_playback_button("shuffle"))

        self.playback_management_layout = QHBoxLayout()
        self.playback_management_layout.addWidget(self.loop_playlist_button)
        self.playback_management_layout.addWidget(self.repeat_button)
        self.playback_management_layout.addWidget(self.shuffle_button)

        self.search_bar_layout = QHBoxLayout()
        self.search_bar_layout.addLayout(self.playback_management_layout)
        self.search_bar_layout.addWidget(self.search_bar)

        playlist_layout.addLayout(self.search_bar_layout)
        if self.ej.get_value("music_directories") is None:
            self.addnewdirectory.add_directory()

        self.music_player.setup_playback_buttons()

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

    def setupMediaPlayerWidget(self, right_layout=QVBoxLayout):
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
            self.seekBack()

        elif event.key() == Qt.Key.Key_Right:
            print("right key pressed")
            self.seekForward()

        elif event.key() == Qt.Key.Key_Space:
            print("Space key pressed")
            self.play_pause()

    def slider_mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Calculate the position relative to the slider length
            slider_length = self.slider.width() if self.slider.orientation() == Qt.Orientation.Horizontal else self.slider.height()
            click_pos = event.position().x() if self.slider.orientation() == Qt.Orientation.Horizontal else event.position().y()

            # Map click position to slider range
            ratio = click_pos / slider_length
            new_value = self.slider.minimum() + ratio * (self.slider.maximum() - self.slider.minimum())
            self.slider.setValue(int(new_value))
            self.music_player.player.setPosition(int(new_value))
            self.last_updated_position = float(new_value)

        # Call the original mousePressEvent from the base class to retain dragging functionality
        QSlider.mousePressEvent(self.slider, event)

    def update_slider(self, position):
        time_difference = abs(self.music_player.player.position() - self.last_updated_position)
        if self.update_interval_millisecond > time_difference:
            return
        else:
            self.update_progress_label(self.music_player.player.position())
            self.slider.setValue(position)
            self.last_updated_position = self.music_player.player.position()

    def update_slider_range(self, duration):
        print("update duration range called")
        self.slider.setRange(0, duration)

    def activate_lrc_display(self):
        # Check if the LRC file is available
        if self.lrcPlayer.file:
            # Check if lyrics are enabled for display
            if self.lrcPlayer.show_lyrics:
                self.hide()  # Hide current UI
                self.lrcPlayer.startUI(self, self.lrc_file)  # Start the lyrics display
            else:
                # Show a warning if the lyrics display is disabled
                QMessageBox.warning(
                    self,
                    "Lyrics Display Disabled",
                    "The lyrics display is currently turned off.\n"
                    "You can enable/disable it by pressing Ctrl + I."
                )
        else:
            if not self.lrcPlayer.show_lyrics:
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
                        "No Lyrics Found",
                        "There is no lyrics file associated with this song."
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
        self.setup_slider()

        self.lrcPlayer.media_lyric.doubleClicked.connect(self.activate_lrc_display)

        right_layout.addWidget(self.lrcPlayer.media_lyric)
        self.lrcPlayer.media_lyric.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        right_layout.addLayout(self.slider_layout)

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

        self.prev_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "seek-backward.ico")))
        self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "play.ico")))
        self.forward_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "seek-forward.ico")))
        self.prev_song_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "previous-song.ico")))
        self.next_song_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "next-song.ico")))

        self.prev_button.clicked.connect(self.seekBack)
        self.play_pause_button.clicked.connect(self.play_pause)
        self.forward_button.clicked.connect(self.seekForward)
        self.prev_song_button.clicked.connect(self.play_previous_song)
        self.next_song_button.clicked.connect(self.play_next_song)

        controls_layout.addWidget(self.prev_song_button)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_pause_button)
        controls_layout.addWidget(self.forward_button)
        controls_layout.addWidget(self.next_song_button)

        right_layout.addLayout(controls_layout)
        self.play_last_played_song()

    def setup_slider(self):
        self.slider_layout = QHBoxLayout()

        self.duration_label = QLabel()

        # Create a QSlider
        self.slider_layout.addWidget(self.slider)
        self.slider_layout.addWidget(self.duration_label)
        self.slider.keyPressEvent = self.slider_key_event
        self.slider.setRange(0, self.music_player.get_duration() or 100)
        self.slider.setValue(0)

        # Connect the slider to the player's position
        self.music_player.player.positionChanged.connect(self.update_slider)
        self.music_player.player.durationChanged.connect(self.update_slider_range)
        self.slider.sliderMoved.connect(self.update_player_from_slider)

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
        for row in range(self.songTableWidget.rowCount()):
            self.songTableWidget.setRowHidden(row, False)

    def filterSongs(self):
        self.hidden_rows = True
        self.songTableWidget.clearSelection()  # Clear previous selections (highlighting)
        if self.search_bar.hasFocus():
            search_text = self.search_bar.text().lower()

            if search_text == "":  # If the search text is empty, reset the table view
                self.restore_table()

            elif search_text == "random":  # If the search text is "random", play a random song
                self.play_random_song()

            elif search_text == "load background":
                self.songTableWidget.setup_backgroundimage_logo()

            elif search_text == "detach":
                self.detachMediaWidget()

            elif search_text == "float":
                self.floatMediaWidget()

            elif search_text == "attach":
                self.attachMediaWidget()

            elif search_text == "crash":
                raise ValueError("This is a ValueError for testing purposes.")

            else:
                found_at_least_one = False  # Flag to track if at least one match is found
                for row in range(self.songTableWidget.rowCount()):
                    match = False
                    item = self.songTableWidget.item(row, 0)  # Check the first column of each row

                    # Hide album title rows (rows containing 'Album Title:')
                    if item and "Album Title:" in item.text():
                        self.songTableWidget.setRowHidden(row, True)
                        continue  # Skip further processing for album title rows

                    # Now filter regular song rows
                    for column in range(2):  # Check first two columns for a match
                        item = self.songTableWidget.item(row, column)
                        if item and search_text in item.text().lower():
                            match = True
                            found_at_least_one = True  # Set flag to True if at least one match is found
                            break

                    # Highlight matched rows and hide unmatched rows if at least one match is found
                    if found_at_least_one:
                        self.songTableWidget.setRowHidden(row, not match)
                        # if match:
                        #     self.songTableWidget.selectRow(row)  # Highlight the row if it matches
                        #     self.songTableWidget.scroll_to_current_row()
                    else:
                        self.songTableWidget.setRowHidden(row, True)  # Hide the other rows

            # Clear the search bar and reset the placeholder text
            self.search_bar.clear()
            self.search_bar.setPlaceholderText("Filter Songs From the Playlist...")

    def cleanDetails(self):
        # clear the remaining from previous play
        self.lrcPlayer.file = None
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
        for row in range(self.songTableWidget.rowCount()):
            item = self.songTableWidget.item(row, 7)
            if item:
                current_file_path = self.songTableWidget.item(row, 7).text()

                # Check if the current file path matches the target file path
                if current_file_path == target_file_path:
                    print(f"File found in row: {row}")
                    # Perform any action you want with the found row, such as selecting it
                    self.songTableWidget.selectRow(row)
                    return row
        else:
            print("File path not found.")

    def song_initializing_stuff(self):
        self.update_information()
        self.get_lrc_file()
        self.music_player.update_music_file(self.music_file)
        self.music_player.default_pause_state()
        self.lrcPlayer.reset_labels()
        self.update_slider_range(self.music_player.get_duration())

    def play_previous_song(self):
        if self.music_player.playback_states["shuffle"]:
            self.current_playing_random_song_index -= 1
            if self.current_playing_random_song_index < 1:
                self.current_playing_random_song_index = len(self.songTableWidget.random_song_list) - 1
            self.play_random_song(user_clicking=True)
            self.songTableWidget.setFocus()
        else:
            previous_song = self.songTableWidget.get_previous_song_object()
            self.handleRowDoubleClick(previous_song)
            self.songTableWidget.setFocus()

    def play_next_song(self, fromStart=None):
        self.songTableWidget.clearSelection()
        if fromStart:
            next_song = self.songTableWidget.get_next_song_object(fromstart=True)
            self.handleRowDoubleClick(next_song)
            return

        if self.music_player.playback_states['shuffle']:
            self.current_playing_random_song_index += 1
            if self.current_playing_random_song_index > len(self.songTableWidget.random_song_list) - 1:
                self.current_playing_random_song_index = 0
            self.play_random_song(user_clicking=True)
            self.songTableWidget.setFocus()
        else:
            next_song = self.songTableWidget.get_next_song_object(fromstart=False)
            self.handleRowDoubleClick(next_song)
            self.songTableWidget.setFocus()

    def play_the_song_at_the_top(self):
        print("inside play the song at the top method")
        if self.songTableWidget.files_on_playlist:
            self.songTableWidget.clearSelection()
            print("Files on playlist")
            print(self.songTableWidget.files_on_playlist)
            self.music_file = self.songTableWidget.files_on_playlist[0]
            self.songTableWidget.song_playing_row = self.find_row(self.music_file)
            self.song_initializing_stuff()
            self.play_song()

    def play_random_song(self, user_clicking=False, from_shortcut=False):
        if not self.songTableWidget.files_on_playlist:
            return

        self.songTableWidget.clearSelection()

        print(self.current_playing_random_song_index, "current index")

        if not user_clicking:  # without user clicking next/previous
            self.current_playing_random_song_index += 1

            if self.current_playing_random_song_index > len(self.songTableWidget.random_song_list) - 1:
                self.lrcPlayer.media_lyric.setText(
                    self.lrcPlayer.media_font.get_formatted_text(self.music_player.eop_text))
                self.ej.edit_value("last_played_song", value={})
                return

        if from_shortcut:
            self.music_file = choice(self.songTableWidget.files_on_playlist)
        else:
            self.music_file = self.songTableWidget.random_song_list[self.current_playing_random_song_index]

        random_song_row = self.find_row(self.music_file)
        self.songTableWidget.song_playing_row = random_song_row

        # Here is to start doing the normal stuff of preparation and playing song.
        self.song_initializing_stuff()
        self.play_song()


    """Original Method"""
    # def handleRowDoubleClick(self, item):
    #     row = None
    #     try:
    #         row = item.row()
    #     except AttributeError:
    #         return

    #     if item and item.text():
    #         if "Album Title: " in item.text():
    #             return
    #         else:
    #             self.item = item
    #             print(item.text())
    #             self.songTableWidget.song_playing_row = row
    #             self.lrcPlayer.started_player = True
    #             if self.get_music_file_from_click(item):
    #                 self.song_initializing_stuff()
    #                 self.play_song()
    #                 ## if the user has picked an item while shuffle is on, the shuffle index will be updated to the current music file
    #                 if self.ej.get_value("playback_states")["shuffle"]:
    #                     self.current_playing_random_song_index = int(self.songTableWidget.random_song_list.index(self.music_file))
    #             else:
    #                 return
    #     else:
    #         return

    #     if self.hidden_rows:
    #         self.songTableWidget.clearSelection()
    #         self.restore_table()
    #         self.songTableWidget.setFocus()

    #         self.songTableWidget.scroll_to_current_row_simulate()
    #         self.simulate_keypress(self.songTableWidget, Qt.Key.Key_G)  # only imitation of key press work.
    #         # Direct calling the method doesn't work. IDk why.
    #         self.hidden_rows = False

    # """Experimental Method"""
    def handleRowDoubleClick(self, item=None):
        # Check if the item exists and is valid
        if item is None:
            return

        row = item.row()  # Get the row of the clicked item

        the_text = item.text()

        if the_text:
            if "Album Title: " in the_text:
                album_title = the_text.replace("Album Title: ", "")
                pass
            else:
                self.item = item
                self.songTableWidget.song_playing_row = row
                self.lrcPlayer.started_player = True

                # Check if a valid music file was clicked
                if self.get_music_file_from_click(item):
                    self.song_initializing_stuff()  # Initialize player
                    self.play_song()  # Play the song

                    # Update shuffle state if shuffle is enabled
                    if self.ej.get_value("playback_states")["shuffle"]:
                        print(self.songTableWidget.random_song_list)
                        self.current_playing_random_song_index = int(self.songTableWidget.random_song_list.index(self.music_file))
                else:
                    self.lrcPlayer.disconnect_syncing()
                    return

        elif the_text == "":
            # Handle case where the clicked item is empty
            print("Empty cell clicked!")
            return

        # Handling hidden rows and restoration logic
        if self.hidden_rows:
            self.restore_table()

            # self.songTableWidget.clearSelection()
            self.songTableWidget.setFocus()

            # Reset hidden rows flag
            self.hidden_rows = False
            self.simulate_keypress(self.songTableWidget, Qt.Key.Key_G)  # Simulate keypres

    def stop_song(self):
        if self.music_player.started_playing:
            self.music_player.player.stop()
            self.lrcPlayer.started_player = False
            self.lrcPlayer.disconnect_syncing()
            self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "play.ico")))
            self.lrcPlayer.media_lyric.setText(self.lrcPlayer.media_font.get_formatted_text("April Music Player"))
            self.duration_label.setText("")
            self.music_player.started_playing = False
            self.clear_song_details_and_image()

    def play_song(self):
        self.last_updated_position = 0.0
        # current for checking lrc on/off state and then play song
        self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "pause.ico")))
        if self.lrcPlayer.show_lyrics:
            self.lrcPlayer.activate_sync_lyric_connection(self.lrc_file)
        else:
            if self.lrcPlayer.media_sync_connected:
                self.music_player.player.positionChanged.disconnect(self.lrcPlayer.update_media_lyric)
                self.lrcPlayer.media_sync_connected = False

        self.music_player.started_playing = True
        self.music_player.play()
        self.lrcPlayer.clean_labels_text()

        if self.saved_position:
            self.music_player.player.setPosition(int(self.saved_position))
        else:
            self.music_player.player.setPosition(int(0))

    def seekBack(self):
        self.music_player.seek_backward()

    def seekForward(self):
        self.music_player.seek_forward()

    def play_pause(self):
        # for checking eop then calling button changing method for play/pause
        current_text = html_to_plain_text(self.lrcPlayer.media_lyric.text())
        if current_text == self.music_player.eop_text:
            if self.music_player.playback_states["shuffle"]:
                self.songTableWidget.random_song_list = self.get_random_song_list()
                self.current_playing_random_song_index = 0
                self.play_random_song(user_clicking=True)
            else:
                self.play_next_song(True)
        else:
            self.music_player.play_pause_music()

    def update_player_from_slider(self, position):
        print("update player from slider method called")
        # Set the media player position when the slider is moved
        self.music_player.player.setPosition(position)
        print(self.music_player.player.position)


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
            self.lrcPlayer.file = None
            self.lrcPlayer.music_file = self.music_file
            print(self.lrcPlayer.file)

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

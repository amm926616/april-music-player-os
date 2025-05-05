from PyQt6.QtWidgets import QDialog, QLineEdit, QVBoxLayout, QLabel, QPushButton, QGroupBox, QHBoxLayout, QFormLayout
from PyQt6.QtGui import QKeyEvent, QIcon
from PyQt6.QtCore import Qt
from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TCON, TDRC, TRCK, COMM
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
from mutagen.wave import WAVE


def save_tag_to_file(file_path, metadata):
    if file_path.lower().endswith('.mp3'):
        try:
            audio = ID3(file_path)  # the crash is due to mp3 file not having metadata.
        except ID3NoHeaderError:
            # Create an empty ID3 tag if none exists
            audio = ID3()

        # Update metadata using ID3 frames
        audio['TIT2'] = TIT2(encoding=3, text=metadata.get('title', ''))
        audio['TPE1'] = TPE1(encoding=3, text=metadata.get('artist', ''))
        audio['TALB'] = TALB(encoding=3, text=metadata.get('album', ''))
        audio['TCON'] = TCON(encoding=3, text=metadata.get('genre', ''))
        audio['TDRC'] = TDRC(encoding=3, text=metadata.get('year', ''))
        audio['TRCK'] = TRCK(encoding=3, text=metadata.get('track_number', ''))
        audio['COMM'] = COMM(encoding=3, lang='eng', desc='', text=metadata.get('comment', ''))

        # Save changes
        audio.save(file_path)

    elif file_path.lower().endswith('.flac'):
        audio = FLAC(file_path)
        # Update metadata using FLAC fields
        audio['title'] = metadata.get('title', '')
        audio['artist'] = metadata.get('artist', '')
        audio['album'] = metadata.get('album', '')
        audio['genre'] = metadata.get('genre', '')
        audio['date'] = metadata.get('year', '')
        audio['comment'] = metadata.get('comment', '')
        audio['tracknumber'] = metadata.get('track_number', '')
        audio.save()

    elif file_path.lower().endswith('.ogg'):
        audio = OggVorbis(file_path)
        # Update metadata using OggVorbis fields
        audio['title'] = metadata.get('title', '')
        audio['artist'] = metadata.get('artist', '')
        audio['album'] = metadata.get('album', '')
        audio['genre'] = metadata.get('genre', '')
        audio['date'] = metadata.get('year', '')
        audio['comment'] = metadata.get('comment', '')
        audio['tracknumber'] = metadata.get('track_number', '')
        audio.save()

    elif file_path.lower().endswith('.m4a'):
        audio = MP4(file_path)
        # Update metadata using MP4 tags
        audio.tags['\xa9nam'] = [metadata.get('title', '')]       # Title
        audio.tags['\xa9ART'] = [metadata.get('artist', '')]      # Artist
        audio.tags['\xa9alb'] = [metadata.get('album', '')]       # Album
        audio.tags['\xa9gen'] = [metadata.get('genre', '')]       # Genre
        audio.tags['\xa9day'] = [metadata.get('year', '')]        # Year
        audio.tags['\xa9cmt'] = [metadata.get('comment', '')]     # Comment
        # Track number handling
        track_number_str = metadata.get('track_number', '0')
        try:
            track_number = int(track_number_str)
        except ValueError:
            track_number = 0  # Default to 0 if invalid track number

        audio.tags['trkn'] = [(track_number, 0)]  # Track number in MP4 format

        # Save changes
        audio.save()

    elif file_path.lower().endswith('.wav'):
        audio = WAVE(file_path)
        # WAV files generally use ID3v2 tags for metadata
        audio['TIT2'] = TIT2(encoding=3, text=metadata.get('title', ''))
        audio['TPE1'] = TPE1(encoding=3, text=metadata.get('artist', ''))
        audio['TALB'] = TALB(encoding=3, text=metadata.get('album', ''))
        audio['TCON'] = TCON(encoding=3, text=metadata.get('genre', ''))
        audio['TDRC'] = TDRC(encoding=3, text=metadata.get('year', ''))
        audio['TRCK'] = TRCK(encoding=3, text=metadata.get('track_number', ''))

        # Add comment metadata (COMM frame)
        audio['COMM'] = COMM(encoding=3, lang='eng', desc='', text=metadata.get('comment', ''))

        # Save changes
        audio.save()

    else:
        print("Unsupported file type.")
        return


class TagDialog(QDialog):
    def __init__(self, parent=None, file_path=None, songTableWidget=None, albumTreeWidget=None, db_cursor=None,
                 conn=None):
        super().__init__(parent)
        self.comment_edit = None
        self.parent = parent
        self.track_number_edit = None
        self.year_edit = None
        self.genre_edit = None
        self.album_edit = None
        self.artist_edit = None
        self.title_edit = None
        self.songTableWidget = songTableWidget
        self.albumTreeWidget = albumTreeWidget  # Reference to your QTreeWidget
        self.cursor = db_cursor  # Database cursor for updating the metadata
        self.conn = conn
        self.setWindowTitle("Edit Metadata")
        self.file_path = file_path
        self.metadata = {}

        self.initUI()

    def initUI(self):
        # Main layout
        layout = QVBoxLayout()

        # Group box for metadata input fields
        metadata_group = QGroupBox("Song's Metadata")
        metadata_layout = QFormLayout()

        # Create input fields for metadata with placeholder text
        self.title_edit = QLineEdit(self)
        self.title_edit.setPlaceholderText("Enter song title")
        self.artist_edit = QLineEdit(self)
        self.artist_edit.setPlaceholderText("Enter artist name")
        self.album_edit = QLineEdit(self)
        self.album_edit.setPlaceholderText("Enter album name")
        self.genre_edit = QLineEdit(self)
        self.genre_edit.setPlaceholderText("Enter genre")
        self.year_edit = QLineEdit(self)
        self.year_edit.setPlaceholderText("Enter year (e.g. 2024)")
        self.comment_edit = QLineEdit(self)
        self.comment_edit.setPlaceholderText("Add comment")
        self.track_number_edit = QLineEdit(self)
        self.track_number_edit.setPlaceholderText("Enter track number")

        # Add fields to form layout
        metadata_layout.addRow(QLabel("Title:"), self.title_edit)
        metadata_layout.addRow(QLabel("Artist:"), self.artist_edit)
        metadata_layout.addRow(QLabel("Album:"), self.album_edit)
        metadata_layout.addRow(QLabel("Genre:"), self.genre_edit)
        metadata_layout.addRow(QLabel("Year:"), self.year_edit)
        metadata_layout.addRow(QLabel("Comment"), self.comment_edit)
        metadata_layout.addRow(QLabel("Track Number:"), self.track_number_edit)

        # Add form layout to group box
        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

        # Add spacing between form and buttons
        layout.addSpacing(15)

        # Buttons layout (aligned horizontally)
        buttons_layout = QHBoxLayout()

        ok_button = QPushButton("OK", self)
        ok_button.setIcon(QIcon("ok_icon.png"))  # Optional: Set icon if you have one
        ok_button.clicked.connect(self.on_accept)

        cancel_button = QPushButton("Cancel", self)
        cancel_button.setIcon(QIcon("cancel_icon.png"))  # Optional: Set icon if you have one
        cancel_button.clicked.connect(self.close)

        # Add buttons to horizontal layout
        buttons_layout.addStretch(1)
        buttons_layout.addWidget(ok_button)
        buttons_layout.addWidget(cancel_button)

        # Add buttons layout to the main layout
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Pre-fill the dialog with existing metadata
        if self.file_path:
            self.populate_meta_data()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

        elif event.key() == Qt.Key.Key_S and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.on_accept()

    def closeEvent(self, event):
        print("Cleaning up UI components")
        self.deleteLater()
        super(TagDialog, self).closeEvent(event)  # Call the base class closeEvent            

    def populate_meta_data(self):
        # Determine the file type
        metadata = self.parent.get_metadata(self.file_path)
        print(metadata)
        self.title_edit.setText(metadata['title'])
        self.artist_edit.setText(metadata['artist'])
        self.album_edit.setText(metadata['album'])
        self.genre_edit.setText(metadata['genre'])
        self.year_edit.setText(str(metadata['year']))
        self.track_number_edit.setText(str(metadata['track_number']))
        self.comment_edit.setText(metadata['comment'])

    def get_user_added_metadata(self):
        return {
            'title': self.title_edit.text(),
            'artist': self.artist_edit.text(),
            'album': self.album_edit.text(),
            'genre': self.genre_edit.text(),
            'year': self.year_edit.text(),
            'comment': self.comment_edit.text(),
            'track_number': self.track_number_edit.text()
        }

    def on_accept(self):
        # Tag the file with the new metadata
        user_added_metadata = self.get_user_added_metadata()
        save_tag_to_file(self.file_path, user_added_metadata)

        metadata = self.parent.get_metadata(self.file_path)
        print("metadata from on_accept")
        print(metadata)

        # # update on database
        # self.update_song_on_database(self.file_path, metadata=metadata)

        # Update the current row in the song table
        self.albumTreeWidget.updateSongMetadata(self.file_path, metadata)

        self.parent.updateSongDetails(self.file_path)

        # Accept the dialog
        self.accept()

    # def update_song_on_database(self, file_path, metadata):
    #     # Otherwise, extract the metadata and store it in the database
    #     self.cursor.execute('''
    #         UPDATE songs
    #         SET title = ?, artist = ?, album = ?, year = ?, genre = ?, track_number = ?
    #         WHERE file_path = ?
    #     ''', (metadata['title'],
    #           metadata['artist'],
    #           metadata['album'],
    #           metadata['year'],
    #           metadata['genre'],
    #           metadata['track_number'],
    #           file_path
    #           ))
    #
    #     self.conn.commit()

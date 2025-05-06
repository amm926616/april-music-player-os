import json
from PyQt6.QtWidgets import QTreeWidgetItem, QWidget, QLineEdit, QTreeWidget, QVBoxLayout, QTableWidgetItem
from PyQt6.QtGui import QFont, QKeyEvent, QDrag, QCursor
from PyQt6.QtCore import Qt, QMimeData
from collections import defaultdict
import sqlite3
import os
from fuzzywuzzy import fuzz
from components.loadingbar import LoadingBar


def extract_track_number(track_number):
    track_number = str(track_number)
    """
    Extracts the track number from a string, handling cases like "1/6" or "02/12".
    Returns the integer part before the slash, or the whole number if there's no slash.
    """
    if '/' in track_number:
        return int(track_number.split('/')[0])
    elif track_number.isdigit():
        return int(track_number)
    return float('inf')  # For non-numeric track numbers, place them at the end


class AlbumTreeWidget(QWidget):
    ARTIST_ROLE = Qt.ItemDataRole.UserRole + 1
    ALBUM_ROLE = Qt.ItemDataRole.UserRole + 2
    SONG_ROLE = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None, songTableWidget=None):
        super().__init__(parent)
        self.parent = parent
        self.tree_widget = None
        self.songTableWidget = songTableWidget
        self.matched_item = None
        self.config_path = self.parent.config_path
        self.conn = None
        self.cursor = None
        self.search_bar = QLineEdit()
        self.initUI()
        self.initialize_database()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.search_bar.hasFocus():
                if self.matched_item:
                    self.on_item_double_clicked(self.matched_item)
                else:
                    return
                self.search_bar.clear()
                self.search_bar.setPlaceholderText("Search by song title...")

            elif self.tree_widget.hasFocus():  # Check if the tree widget has focus
                selected_items = self.tree_widget.selectedItems()
                if selected_items:  # Make sure an item is selected
                    self.on_item_double_clicked(selected_items[0])  # Call the method for the selected item

        elif event.key() == Qt.Key.Key_Up:
            current_item = self.tree_widget.currentItem()

            # Find the first visible item
            first_visible_item = None
            for i in range(self.tree_widget.topLevelItemCount()):
                item = self.tree_widget.topLevelItem(i)
                if not item.isHidden():  # Check if the item is visible
                    first_visible_item = item
                    break

            if current_item == first_visible_item:
                self.search_bar.setFocus()  # Set focus on the QTextEdit widget
            else:
                # Allow normal behavior for moving between items
                self.tree_widget.setFocus()

        elif event.key() == Qt.Key.Key_Down:
            self.tree_widget.setFocus()

            # Find the first visible item
            first_visible_item = None
            for i in range(self.tree_widget.topLevelItemCount()):
                item = self.tree_widget.topLevelItem(i)
                if not item.isHidden():  # Check if the item is visible
                    first_visible_item = item
                    break

            if first_visible_item:
                self.tree_widget.setCurrentItem(first_visible_item)

        else:
            super().keyPressEvent(event)

    def tree_item_mouse_double_click_event(self, event):
        # Override the mouse double click event
        item = self.tree_widget.itemAt(event.pos())
        if item:
            self.on_item_double_clicked(item)
        # Ignore the event to prevent expanding
        event.accept()

    def filter_items(self):
        search_text = self.search_bar.text().lower()
        matched_songs = []  # List to store matched and visible songs
        matched_albums = []  # List to store matched and visible albums
        matched_artists = []  # List to store matched and visible artists

        def matches_search(text):
            # Simplify the matching function by checking directly for fuzzy match if needed
            return search_text in text.lower() or (search_text and fuzz.partial_ratio(search_text, text.lower()) > 80)

        for i in range(self.tree_widget.topLevelItemCount()):
            artist_item = self.tree_widget.topLevelItem(i)
            artist_visible = False  # To track if artist should be visible due to albums/songs

            # Check if artist matches the search
            if matches_search(artist_item.text(0)):
                matched_artists.append(artist_item)
                artist_visible = True

            for j in range(artist_item.childCount()):
                album_item = artist_item.child(j)
                album_visible = False  # To track if album should be visible due to songs

                # Check if album matches the search
                if matches_search(album_item.text(0)):
                    matched_albums.append(album_item)
                    album_visible = True  # Album should remain visible regardless of songs

                for k in range(album_item.childCount()):
                    song_item = album_item.child(k)
                    song_visible = matches_search(song_item.text(0))
                    song_item.setHidden(not song_visible)

                    # If a song is visible, album and artist should be visible too
                    if song_visible:
                        matched_songs.append(song_item)
                        album_visible = True  # Keep album visible if any song matches
                        artist_visible = True  # Keep artist visible if any song matches

                # Set album visibility (keep it visible if it matched, or any song matched)
                album_item.setHidden(not album_visible)

            # Set artist visibility (keep it visible if it matched, or any album or song matched)
            artist_item.setHidden(not artist_visible)

        # Assign the first matched item in priority: song > album > artist
        if matched_songs:
            self.matched_item = matched_songs[0]
        elif matched_albums:
            self.matched_item = matched_albums[0]
        elif matched_artists:
            self.matched_item = matched_artists[0]
        else:
            self.matched_item = None

    def initUI(self):
        self.search_bar.setPlaceholderText("Search Songs by name...")
        self.search_bar.setToolTip("Filer/Search songs by name [Ctrl + F]. \nPress [Enter] to place the matched song in the playlist.")

        self.tree_widget = QTreeWidget()
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.startDrag = self.startDragMethod
        self.tree_widget.mouseDoubleClickEvent = self.tree_item_mouse_double_click_event
        self.tree_widget.setHeaderHidden(True)  # Hide the header

        layout = QVBoxLayout(self)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.tree_widget)

        self.search_bar.textChanged.connect(self.filter_items)
        self.tree_widget.itemPressed.connect(self.on_item_right_clicked)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

    def startDragMethod(self, supported_actions):
        print("Inside drag start method")
        selected_item = self.tree_widget.currentItem()
        if not selected_item:
            print("No item selected")
            return

        print(f"Selected item: {selected_item.text(0)}")
        item_role = selected_item.data(0, Qt.ItemDataRole.UserRole)
        print(f"Item role: {item_role}")
        file_path = None
        if item_role == self.SONG_ROLE:
            file_path = selected_item.data(0, Qt.ItemDataRole.UserRole + 4)
            print(f"File path: {file_path}")

        # Serialize the data
        passing_data = [selected_item.text(0), item_role, file_path]
        serialized_data = json.dumps(passing_data)
        print(f"Serialized data: {serialized_data}")

        # Start drag
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setData("application/x-item-data", serialized_data.encode("utf-8"))
        drag.setMimeData(mime_data)

        # # Set custom drag cursor using QCursor
        # drag.setDragCursor(QCursor(Qt.CursorShape.OpenHandCursor), Qt.DropAction.CopyAction)

        # drag.setDragCursor(self, QCursor(Qt.CursorShape.OpenHandCursor))

        self.parent.app.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))  # Example: wait cursor

        # Execute the drag operation
        drag.exec(supported_actions)

        # Reset cursor after the drag has finished
        self.parent.app.restoreOverrideCursor()

    def on_item_right_clicked(self, item=None):
        if self.parent.app.mouseButtons() == Qt.MouseButton.RightButton:
            print(item)
            if item:
                if item.isExpanded():
                    self.tree_widget.collapseItem(item)  # Collapse if already expanded
                else:
                    self.tree_widget.expandItem(item)  # Expand if collapsed

    def on_item_double_clicked(self, item=None, data=None, role=None, file_path=None):
        """
        text is for the information to get data from the database, which is the name of artist, album, song.
        role is to check the clicked data's role to extract from the database.
        file_path if the clicked item is a single song.
        """
        
        self.songTableWidget.clearSelection()

        if item:
            data = item.text(0)
            role = item.data(0, Qt.ItemDataRole.UserRole)
            if role == self.SONG_ROLE:
                file_path = item.data(0, Qt.ItemDataRole.UserRole + 4)  # Retrieve file path
            else:
                file_path = None

        if role == self.ARTIST_ROLE:
            self.add_songs_by_artist(data)
        elif role == self.ALBUM_ROLE:
            self.add_songs_by_album(data)
        elif role == self.SONG_ROLE:
            self.add_song_by_file_path(file_path)  # Use file path to add song
        else:
            print(f"Unknown item double-clicked: {item.text(0)}")

        if self.parent.ej.get_value("playback_states")["shuffle"]:
            self.parent.songTableWidget.prepare_for_random()

        self.songTableWidget.horizontalScrollBar().setValue(0)

    def initialize_database(self):
        if self.conn:
            self.conn.close()  # Close the previous connection if it exists

        self.conn = sqlite3.connect(os.path.join(self.config_path, "databases", "songs.db"))
        self.cursor = self.conn.cursor()

        # Create the table for storing song metadata if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                title TEXT,
                artist TEXT,
                album TEXT,
                year TEXT,
                genre TEXT,
                track_number TEXT,
                duration INTEGER,
                file_path TEXT PRIMARY KEY,
                file_type TEXT
            )
        ''')

        self.conn.commit()

    def loadSongsToCollection(self, directories=None, loadAgain=False):
        if loadAgain:
            self.tree_widget.clear()
            self.parent.media_files.clear()
            self.parent.cleanDetails()

            if not directories:
                directories = self.parent.ej.get_value("music_directories")

        self.parent.media_files.clear()  # clean the remaining files first

        media_extensions = {'.mp3', '.ogg', '.wav', '.flac', '.aac', '.m4a'}

        for directory, value in directories.items():
            if value:
                # Recursively find all media files
                for root, _, files in os.walk(directory):
                    for file in files:
                        if os.path.splitext(file)[1].lower() in media_extensions:
                            self.parent.media_files.append(os.path.join(root, file))

        songs_by_artist = defaultdict(list)

        loadingBar = LoadingBar(self, len(self.parent.media_files), directories)
        loadingBar.show()

        # Query the database for all stored songs
        self.cursor.execute('SELECT file_path FROM songs')
        all_db_songs = self.cursor.fetchall()

        # Remove songs from the database if the file does not exist on the device
        for db_song in all_db_songs:
            file_path = db_song[0]
            if not os.path.exists(file_path):
                self.cursor.execute('DELETE FROM songs WHERE file_path=?', (file_path,))
                self.conn.commit()

        # Check if the database already has the songs stored
        for index, item_path in enumerate(self.parent.media_files):
            loadingBar.update_loadingbar(index + 1)
            self.cursor.execute('SELECT * FROM songs WHERE file_path=?', (item_path,))
            result = self.cursor.fetchone()

            def format_duration(seconds):
                minutes = seconds // 60
                seconds = seconds % 60
                return f"{int(minutes):02}:{int(seconds):02}"

            if result:
                # If the song is already in the database, use the stored metadata
                metadata = {
                    'title': result[0],
                    'artist': result[1],
                    'album': result[2],
                    'year': result[3],
                    'genre': result[4],
                    'track_number': result[5],
                    'duration': result[6],
                    'file_type': result[8]
                }
            else:
                # Otherwise, extract the metadata and store it in the database
                self.parent.music_file = item_path
                metadata = self.parent.get_metadata(item_path)

                self.cursor.execute('''
                    INSERT INTO songs (title, artist, album, year, genre, track_number, duration, file_path, file_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metadata['title'],
                    metadata['artist'],
                    metadata['album'],
                    str(metadata['year']),
                    metadata['genre'],
                    metadata['track_number'],
                    format_duration(metadata['duration']),
                    item_path,
                    metadata['file_type']
                ))
                self.conn.commit()

            artist = metadata['artist'] if metadata['artist'] else 'Unknown Artist'
            album = metadata['album'] if metadata['album'] else 'Unknown Album'
            track_number = metadata['track_number']
            songs_by_artist[artist].append((album, track_number, item_path, metadata))

        self.loadSongsToAlbumTree(songs_by_artist)
        loadingBar.close()

    def loadSongsToAlbumTree(self, songs_by_artist):
        self.tree_widget.clear()  # Clear existing items

        for artist in sorted(songs_by_artist.keys(), key=lambda x: x.lower()):
            artist_item = QTreeWidgetItem([artist])
            artist_item.setData(0, Qt.ItemDataRole.UserRole, self.ARTIST_ROLE)
            artist_item.setFlags(artist_item.flags() | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.tree_widget.addTopLevelItem(artist_item)

            songs_by_album = defaultdict(list)
            for album, track_number, item_path, metadata in songs_by_artist[artist]:
                songs_by_album[album].append((track_number, item_path, metadata))

            for album in sorted(songs_by_album.keys()):
                album_item = QTreeWidgetItem([album])
                album_item.setData(0, Qt.ItemDataRole.UserRole, self.ALBUM_ROLE)
                album_item.setFlags(album_item.flags() | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsSelectable)
                artist_item.addChild(album_item)

                sorted_songs = sorted(songs_by_album[album], key=lambda x: extract_track_number(x[0]))
                for track_number, item_path, metadata in sorted_songs:
                    title = metadata['title']
                    track_item = QTreeWidgetItem([f"{track_number}. {title}"])
                    track_item.setData(0, Qt.ItemDataRole.UserRole, self.SONG_ROLE)
                    track_item.setData(0, Qt.ItemDataRole.UserRole + 4, item_path)  # Store file path
                    track_item.setFlags(track_item.flags() | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsSelectable)
                    album_item.addChild(track_item)

    def add_song_by_file_path(self, file_path):
        print(file_path)

        if not file_path in self.songTableWidget.files_on_playlist:
            # Fetch song details from the database
            self.cursor.execute('SELECT * FROM songs WHERE file_path=?', (file_path,))
            song = self.cursor.fetchone()
            if song:
                file_path = song[7]  # Assuming file_path is at index 7

                # Check if the file_path is already in the playlist
                if not file_path in self.songTableWidget.files_on_playlist:
                    self.add_album_title_row(song[2])
                    self.add_song_row(song)  # Use add_song_row to add the song to the QTableWidget

        one_single_row = [self.find_row_by_exact_match(file_path)]
        self.songTableWidget.scroll_to_and_highlight_multiple_rows(one_single_row)
        self.parent.simulate_keypress(self.songTableWidget, Qt.Key.Key_Return)  # play the current hilighted song

    def add_song_row(self, song):
        # Insert song data into the QTableWidget
        row_position = self.songTableWidget.rowCount()
        self.songTableWidget.insertRow(row_position)

        # Assuming columns are: title, artist, album, year, genre, track_number, duration, file_path, file_type
        for i, data in enumerate(song):
            item = QTableWidgetItem(str(data))
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.songTableWidget.setItem(row_position, i, item)
                    
        file_path = song[7]  # Assuming file_path is at index 7
        if not file_path in self.songTableWidget.files_on_playlist:
            self.songTableWidget.files_on_playlist.append(file_path)

    def add_album_title_row(self, album):
        album_text = f"Album Title: [{album}]"

        # Check if the album title already exists in the table
        for row in range(self.songTableWidget.rowCount()):
            item = self.songTableWidget.item(row, 0)
            if item and item.text() == album_text:
                return row  # Return the existing row position if album title is found

        # Insert a new row to display the album title
        row_position = self.songTableWidget.rowCount()
        self.songTableWidget.insertRow(row_position)

        # Set the album title text and font style
        album_name_item = QTableWidgetItem(album_text)
        font = QFont("Komika Axis", 10)
        album_name_item.setFont(font)

        # Make the item non-selectable and only enabled
        album_name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.NoItemFlags & ~Qt.ItemFlag.ItemIsSelectable)

        # Span the item across all columns for better visual emphasis
        self.songTableWidget.setSpan(row_position, 0, 1, self.songTableWidget.columnCount())
        self.songTableWidget.setItem(row_position, 0, album_name_item)

        return row_position  # Return the new row position if a new row was inserted

    def add_songs_by_album(self, album):
        if not self.cursor:
            return

        self.cursor.execute('SELECT * FROM songs WHERE album=?', (album,))
        songs = self.cursor.fetchall()

        sorted_songs_data = sorted(songs, key=lambda x: extract_track_number(x[5]))  # Sort by track_number
        sorted_songs = [song[7] for song in sorted_songs_data]

        # Convert lists to sets for efficient operations
        sorted_songs_set = set(sorted_songs)
        files_on_playlist_set = set(self.songTableWidget.files_on_playlist)

        # Find the intersection of the two sets
        common_songs = sorted_songs_set.intersection(files_on_playlist_set)
        the_remaining_songs = sorted_songs_set - common_songs

        if common_songs:
            # Find rows corresponding to the common songs
            common_song_rows = [self.find_row_by_exact_match(song) for song in common_songs]
            # Highlight and scroll to the rows
            self.songTableWidget.scroll_to_and_highlight_multiple_rows(common_song_rows)
            
            for song in the_remaining_songs:
                self.add_song_by_file_path(song)

        else:
            self.add_album_title_row(album)
            for song in sorted_songs_data:
                self.add_song_row(song)
                
    def add_songs_by_artist(self, artist):
        self.songTableWidget.clearSelection()
        
        if not self.cursor:
            return

        self.cursor.execute('SELECT * FROM songs WHERE artist=?', (artist,))
        songs = self.cursor.fetchall()

        sorted_albums = defaultdict(list)
        for song in songs:
            sorted_albums[song[2]].append(song)  # song[2] is the album

        files_on_playlist_set = set(self.songTableWidget.files_on_playlist)

        for album, album_songs in sorted(sorted_albums.items()):
            sorted_songs_data = sorted(album_songs, key=lambda x: extract_track_number(x[5]))  # Sort by track_number

            sorted_songs = [song[7] for song in sorted_songs_data]  # Use sorted_songs_data

            if set(sorted_songs).issubset(files_on_playlist_set):
                existing_song_rows = [self.find_row_by_exact_match(song) for song in sorted_songs]
                self.songTableWidget.scroll_to_and_highlight_multiple_rows(existing_song_rows)

            else:
                self.add_album_title_row(album)
                for song in sorted_songs_data:
                    self.add_song_row(song)

    def find_row_by_exact_match(self, search_text: str):  # just to search in col 7 exact file path
        """
        search_text should is the string of the file path, this method return the exact row found on the songTableWidget
        """
        # Use findItems to search for the exact match in the entire table
        matching_items = self.songTableWidget.findItems(search_text, Qt.MatchFlag.MatchExactly)

        # Filter the matching items by checking if they are in the desired column
        for item in matching_items:
            if item.column() == 7:
                return item.row()  # Return the row index if a match is found in the specified column

        return -1  # Return -1 if no match is found

    def updateSongMetadata(self, file_path, new_metadata):
        self.update_metadata_to_database(file_path, new_metadata)
        self.updateMetadataInTableWidget(new_metadata)
        self.updateSongInTree(file_path, new_metadata)

    def update_metadata_to_database(self, file_path, new_metadata):
        self.cursor.execute('''
            UPDATE songs
            SET title=?, artist=?, album=?, year=?, genre=?, track_number=?
            WHERE file_path=?
        ''', (
            new_metadata['title'],
            new_metadata['artist'],
            new_metadata['album'],
            str(new_metadata['year']),
            new_metadata['genre'],
            new_metadata['track_number'],
            file_path
        ))
        self.conn.commit()

    def updateMetadataInTableWidget(self, new_metadata):
        # Update each column in the current row of the song table widget
        row = self.songTableWidget.currentRow()

        self.songTableWidget.item(row, 0).setText(new_metadata['title'])
        self.songTableWidget.item(row, 1).setText(new_metadata['artist'])
        self.songTableWidget.item(row, 2).setText(new_metadata['album'])
        self.songTableWidget.item(row, 3).setText(str(new_metadata['year']))
        self.songTableWidget.item(row, 4).setText(new_metadata['genre'])
        self.songTableWidget.item(row, 5).setText(str(new_metadata['track_number']))

    def updateSongInTree(self, file_path, new_metadata):
        # Traverse through the top-level (artist) items in the tree widget
        for i in range(self.tree_widget.topLevelItemCount()):
            artist_item = self.tree_widget.topLevelItem(i)

            # For each artist, traverse through their albums
            for j in range(artist_item.childCount()):
                album_item = artist_item.child(j)

                # For each album, traverse through the songs
                for k in range(album_item.childCount()):
                    track_item = album_item.child(k)

                    # Check if this song's file path matches the one we updated
                    if track_item.data(0, Qt.ItemDataRole.UserRole + 4) == file_path:
                        # Update the tree item with new metadata
                        track_number = new_metadata['track_number']
                        title = new_metadata['title']
                        track_item.setText(0, f"{track_number}. {title}")

                        # Update the album information if needed (e.g., update album title or number of tracks)
                        self.updateAlbumItem(album_item, new_metadata["album"])

                        # Update the artist information if needed (e.g., aggregate album info under the artist)
                        self.updateArtistItem(artist_item, new_metadata["artist"])

                        # Force the UI to update
                        self.tree_widget.repaint()
                        return  # Exit after updating the item

    def updateAlbumItem(self, album_item, album_name):
        # Update the album title with the new album name
        # track_count = album_item.childCount()  # Number of songs on this album
        # album_item.setText(0, f"{album_name} ({track_count} tracks)")

        album_item.setText(0, album_name)

        # Update the album's data to store the new album name
        album_item.setData(0, self.ALBUM_ROLE, album_name)

    def updateArtistItem(self, artist_item, artist_name):
        # Update the artist title with the new artist name
        # album_count = artist_item.childCount()  # Number of albums under this artist
        # artist_item.setText(0, f"{artist_name} ({album_count} albums)")

        artist_item.setText(0, artist_name)

        # Update the artist's data to store the new artist name
        artist_item.setData(0, self.ARTIST_ROLE, artist_name)

from PyQt6.QtGui import QIcon
import os
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from music_player.musicplayerworker import MusicPlayerWorker
from _utils.easy_json import EasyJson


class MusicPlayer(QObject):  # Inherit from QObject
    # Define the signal as a class attribute
    start_play_signal = pyqtSignal()

    def __init__(self, parent, play_pause_button, loop_playlist_button, repeat_button, shuffle_button):
        super().__init__()  # Initialize QObject
        self.parent = parent
        self.ej = EasyJson()
        self.file_name = None
        self.eop_text = "End Of Playlist"
        self.player = MusicPlayerWorker(self.handle_media_status_changed)  # Create a worker instance

        self.thread = QThread()  # Create a QThread

        # Move the worker to the thread
        self.player.moveToThread(self.thread)

        # Connect the start_play_signal to the player's play method
        self.start_play_signal.connect(self.player.play)

        self.thread.start()

        self.started_playing = False
        self.paused_position = 0.0
        self.play_pause_button = play_pause_button
        self.loop_playlist_button = loop_playlist_button
        self.repeat_button = repeat_button
        self.shuffle_button = shuffle_button

        self.buttons = {
            "repeat": self.repeat_button,
            "shuffle": self.shuffle_button,
            "loop": self.loop_playlist_button
        }

        self.playback_states = self.ej.get_value("playback_states")
        print(self.playback_states)
        print(type(self.playback_states))

        self.script_path = self.ej.ej_path

    def cleanup(self):
        self.player.deleteLater()  # Ensure worker is deleted
        self.thread.quit()         # Stop the thread
        self.thread.wait()         # Wait for it to finish
        self.thread.deleteLater()  # Finally, delete the thread


    def reset_buttons_states(self):
        for key, button in self.buttons.items():
            button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", f"{key}-default.ico")))
            self.playback_states[key] = False
            self.ej.edit_value("buttons_all_default", True)

    def handle_button_press(self, pressed_button_name):
        if not self.playback_states[pressed_button_name]:
            for name in self.buttons.keys():
                if name == pressed_button_name:
                    self.playback_states[name] = True
                    self.buttons[name].setIcon(QIcon(os.path.join(self.script_path, "media-icons", f"{name}-on.ico")))
                    self.ej.edit_value(name, True)
                else:
                    self.playback_states[name] = False
                    self.buttons[name].setIcon(QIcon(os.path.join(self.script_path, "media-icons", f"{name}-off.ico")))
                    self.ej.edit_value(name, False)

            self.ej.edit_value("buttons_all_default", False)
        else:
            self.reset_buttons_states()

        print("The buttons states: ")
        for i in self.playback_states:
            print(i, self.playback_states[i])

    def play(self):
        self.started_playing = True
        self.update_music_file(self.file_name)
        # self.thread.start()  # Start the thread to play the song in the background
        self.player.play()

    def setup_playback_buttons(self):
        if self.ej.get_value("buttons_all_default"): # if all are default, no need to change icons
            return

        for name, state in self.playback_states.items():
            if state:
                self.buttons[name].setIcon(QIcon(os.path.join(self.script_path, "media-icons", f"{name}-on.ico")))
                self.playback_states[name] = True
            else:
                self.buttons[name].setIcon(QIcon(os.path.join(self.script_path, "media-icons", f"{name}-off.ico")))
                self.playback_states[name] = False

        if self.ej.get_value("playback_states")["shuffle"]:
            self.parent.songTableWidget.prepare_for_random()

    def toggle_loop_playlist(self):
        self.handle_button_press("loop")

    def toggle_repeat(self):
        self.handle_button_press("repeat")

    def toggle_shuffle(self):
        self.handle_button_press("shuffle")
        if self.playback_states['shuffle']:
            self.parent.songTableWidget.prepare_for_random()

    def disable_loop_playlist(self, no_setup=True):
        if self.playback_states["repeat"] or self.playback_states["shuffle"]:
            self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons",
                                                                 "loop-playlist-off.ico")))
            self.loop_playlist_button.setDisabled(True)
            self.previous_loop_state = self.playback_states["loop"]
            self.playback_states["loop"] = False
        else:
            if no_setup:
                self.loop_playlist_button.setDisabled(False)
                self.playback_states["loop"] = self.previous_loop_state
                if self.playback_states["loop"]:
                    self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons",
                                                                         "on-loop-playlist.ico")))
                else:
                    self.loop_playlist_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons",
                                                                         "loop-playlist.ico")))

    def disable_shuffle(self, no_setup=True):
        if self.playback_states["repeat"]:
            self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "shuffle-off.ico")))
            self.shuffle_button.setDisabled(True)
            self.previous_shuffle_state = self.playback_states["shuffle"]
            self.playback_states["shuffle"] = False
        else:
            if no_setup:
                self.shuffle_button.setDisabled(False)
                self.playback_states["shuffle"] = self.previous_shuffle_state
                if self.playback_states["shuffle"]:
                    self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "on-shuffle.ico")))
                else:
                    self.shuffle_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "shuffle.ico")))

    def default_pause_state(self):
        self.in_pause_state = False
        self.paused_position = 0.0

    def update_music_file(self, file):
        self.file_name = file
        self.player.setSource(self.file_name)

    def play_pause_music(self):
        if self.started_playing:  # pause state activating
            if not self.in_pause_state:
                # Record the current position before pausing
                self.paused_position = self.player.position()  # Assuming get_position() returns
                # the current position in seconds or milliseconds

                self.player.pause()
                self.in_pause_state = True
                self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "play.ico")))
            else:
                # Set the position to the recorded value before resuming
                self.player.setPosition(self.paused_position)  # Assuming set_position() sets the playback position

                # Continue playing
                self.player.play()
                self.in_pause_state = False
                self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "pause.ico")))

    def pause(self):
        self.paused_position = self.player.position()  # Assuming get_position()
        # returns the current position in seconds or milliseconds
        self.in_pause_state = True
        self.play_pause_button.setIcon(QIcon(os.path.join(self.script_path, "media-icons", "play.ico")))
        self.player.pause()

    def get_current_time(self):
        position = self.player.position() / 1000.0
        return position

    def seek_forward(self, saved_position=None):
        if self.player.isPlaying and not saved_position:
            self.player.setPosition(self.player.position() + 1000)
        else:
            self.player.setPosition(saved_position)

    def seek_backward(self):
        if self.player.isPlaying:
            self.player.setPosition(self.player.position() - 1000)

    def get_duration(self):
        return self.player.duration()

    def get_position(self):
        return self.player.position()

    def handle_media_status_changed(self, status):
        print("inside handle media status change")
        if status == self.player.MediaStatus.EndOfMedia:
            if self.playback_states["repeat"]:
                # Restart playback
                self.player.setPosition(0)
                self.player.play()
            else:
                if self.playback_states["shuffle"]:
                    self.parent.play_random_song()
                else:
                    self.parent.play_next_song()

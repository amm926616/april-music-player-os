from PyQt6.QtCore import QObject, pyqtSignal, QThread, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput


def handle_buffer_status(percent_filled):
    print(f"Buffer status: {percent_filled}%")


class MusicPlayerWorker(QObject):
    # Define signals if needed (for future callbacks or status updates)
    started = pyqtSignal()

    def __init__(self, handle_media_status_changed):
        super().__init__()

        # Create the media player and audio output
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()

        # Move them to the worker's thread
        self.player.moveToThread(QThread.currentThread())
        self.audio_output.moveToThread(QThread.currentThread())

        self.player.setAudioOutput(self.audio_output)

        # Connect the buffer status signal to a custom method
        self.player.bufferProgressChanged.connect(handle_buffer_status)

        # Connect the mediaStatusChanged signal to a slot
        self.player.mediaStatusChanged.connect(handle_media_status_changed)
        self.mediaStatusChanged = self.player.mediaStatusChanged

        self.positionChanged = self.player.positionChanged
        self.durationChanged = self.player.durationChanged

        self.MediaStatus = QMediaPlayer.MediaStatus

    def play(self):
        self.started.emit()  # Emit a signal when the player starts, if needed
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def position(self):
        return self.player.position()

    def isPlaying(self):
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def setSource(self, file):
        self.player.setSource(QUrl.fromLocalFile(file))

    def setPosition(self, position=int()):
        self.player.setPosition(position)

    def duration(self):
        return self.player.duration()

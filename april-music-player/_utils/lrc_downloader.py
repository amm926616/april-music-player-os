from PyQt6.QtCore import QObject, QThread, pyqtSignal, QCoreApplication
from PyQt6.QtWidgets import QProgressDialog, QMessageBox
from lrcdl import Track, Options
from lrcdl.exceptions import LyricsAlreadyExists, LyricsNotAvailable
import os

class LyricsDownloadWorker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)

    def __init__(self, track_path):
        super().__init__()
        self.track_path = track_path

    def run(self):
        try:
            track = Track(self.track_path)
            for i in range(5):
                QThread.msleep(200)
                self.progress.emit((i + 1) * 20)
            track.download_lyrics(Options())
            self.success.emit(f"Lyrics downloaded for: {self.track_path}")
        except LyricsAlreadyExists:
            self.error.emit("Lyrics already exist for this track.")
        except LyricsNotAvailable:
            self.error.emit("No lyrics found for this track.")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")
        finally:
            self.finished.emit()


class LyricsDownloader(QObject):
    def __init__(self, parent, song_table_widget, app, get_path_callback):
        super().__init__()
        self.parent = parent
        self.song_table_widget = song_table_widget
        self.app = app
        self.get_music_file = get_path_callback
        self.active_threads = []

    def start_download(self, clicked_item):
        selected_items = self.song_table_widget.selectedItems()
        selected_rows = {item.row() for item in selected_items}
        if len(selected_rows) > 1:
            self._batch_download(selected_rows)
        else:
            file_path = self.get_music_file(clicked_item)
            self._start_single_download(file_path)

    def _batch_download(self, rows):
        self.batch_files = []
        for row in rows:
            file_item = self.song_table_widget.item(row, 0)
            if file_item:
                self.batch_files.append(self.get_music_file(file_item))

        self.batch_progress = QProgressDialog("Downloading lyrics...", "Cancel", 0, len(self.batch_files), self.parent)
        self.batch_progress.setWindowTitle("Batch Download")
        self.batch_progress.setWindowModality(self.parent.windowModality())
        self.batch_progress.canceled.connect(self.cancel_batch)
        self.batch_progress.show()
        self._process_next_batch_item()

    def _process_next_batch_item(self):
        if not self.batch_files:
            self.batch_progress.close()
            QMessageBox.information(self.parent, "Done", "Batch download complete!")
            return
        file_path = self.batch_files.pop(0)
        self.batch_progress.setLabelText(f"Downloading: {os.path.basename(file_path)}")
        self._start_single_download(file_path, batch_mode=True)

    def _start_single_download(self, file_path, batch_mode=False):
        if not batch_mode:
            self.download_progress = QProgressDialog("Downloading lyrics...", None, 0, 100, self.parent)
            self.download_progress.setCancelButton(None)
            self.download_progress.setWindowTitle("Downloading")
            self.download_progress.setWindowModality(self.parent.windowModality())
            self.download_progress.show()

        thread = QThread()
        worker = LyricsDownloadWorker(file_path)
        worker.moveToThread(thread)
        self.active_threads.append((thread, worker))

        def cleanup():
            thread.quit()
            thread.wait()
            thread.deleteLater()
            worker.deleteLater()
            self.active_threads.remove((thread, worker))

        thread.started.connect(worker.run)
        worker.finished.connect(cleanup)

        if not batch_mode:
            worker.progress.connect(self.download_progress.setValue)
            worker.success.connect(lambda msg: QMessageBox.information(self.parent, "Success", msg))
            worker.error.connect(lambda msg: QMessageBox.warning(self.parent, "Error", msg))
            worker.finished.connect(self.download_progress.close)
        else:
            worker.success.connect(self._handle_batch_progress)
            worker.error.connect(self._handle_batch_progress)

        thread.start()

    def _handle_batch_progress(self, msg):
        self.batch_progress.setValue(self.batch_progress.value() + 1)
        QCoreApplication.processEvents()
        self._process_next_batch_item()

    def cancel_batch(self):
        self.batch_files = []
        self.batch_progress.close()

    def start_download_from_selection(self):
        selected_items = self.song_table_widget.selectedItems()
        if not selected_items:
            return
        self.start_download(selected_items[0])  # Pass one of the selected items for fallback


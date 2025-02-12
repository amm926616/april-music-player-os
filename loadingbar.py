from PyQt6.QtWidgets import QProgressDialog, QApplication


class LoadingBar(QProgressDialog):
    def __init__(self, parent, n, directories):
        super().__init__(parent)
        self.setRange(0, n)

        # Extract only the directory paths and format them as a bulleted list
        directory_paths = "\n".join(f"• {path}" for path in directories.keys())

        # Set the label text with a user-friendly message and formatted directory paths
        self.setLabelText(
            f"Processing Music Files from the following directories:\n\n{directory_paths}")

        # self.setCancelButton(None)  # Remove the cancel button if not needed
        self.setWindowTitle("Initializing Database")
        self.setModal(True)
        self.setMinimumDuration(0)  # Ensure the dialog appears immediately

    def update_loadingbar(self, value):
        self.setValue(value)
        QApplication.processEvents()  # Process events to update the UI

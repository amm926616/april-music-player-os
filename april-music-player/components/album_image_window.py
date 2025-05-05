from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
import os

class AlbumImageWindow(QDialog):
    def __init__(self, parent=None, image=None, icon=None, imageName=None, screenheight=None):
        super().__init__()
        self.parent = parent
        # Resize the image while maintaining aspect ratio
        self.screenheight = screenheight

        # Default value for size
        size = 640

        if self.screenheight > 1200:
            size = 1100
        elif 1080 <= self.screenheight < 1200:
            size = 900
        elif 700 <= self.screenheight < 800:
            size = 650

        new_width = size
        new_height = size

        # if image.width() > new_height: # just disable it for now. I have to show the image in screen resolution
        #     new_width = image.width()
        #     new_height = image.width()

        self.image = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)

        self.image_name = imageName

        title = self.image_name.split('/')[-1]

        # Set up the dialog window
        self.setWindowTitle(f"{title} - ({new_width}x{new_height})px")
        if icon:
            self.setWindowIcon(QIcon(icon))

        # Create a label to display the image
        image_label = QLabel(self)
        save_button = QPushButton("Save Image")
        save_button.setIcon(QIcon(os.path.join(self.parent.script_path, "media-icons", "png", "download.png")))

        if self.image:
            image_label.setPixmap(self.image)

        # Optional: Align the image to the center
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create and set the layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(image_label)
        layout.addWidget(save_button)
        self.setLayout(layout)

        # Optional: Set the size of the window to fit the image
        self.adjustSize()

        save_button.clicked.connect(self.save_image)

    def save_image(self):
        default_image_folder = self.parent.ej.get_value("default_image_folder")

        # Define the file name and the full path
        file_name = self.image_name.split('/')[-1]

        # Check if the OS is Windows
        if os.name == 'nt':  # 'nt' stands for Windows
            file_name = self.image_name.split("\\")[-1]  # တော်တော်သောက်လုပ်ရှပ်တဲ့ window

        for ext in ['.mp3', '.ogg', '.asc']:
            if file_name.endswith(ext):
                file_name = file_name.removesuffix(ext)

        save_path = os.path.join(default_image_folder, file_name) + ".png"
        print(save_path)

        # Save the pixmap to the specified path in PNG format
        success = self.image.save(save_path, format='PNG')

        # Create a QMessageBox to notify the user
        msg_box = QMessageBox(self)
        if success:
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText(f"Image saved successfully at {save_path}")
            msg_box.setWindowTitle("Success")
        else:
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText("Failed to save the image.")
            msg_box.setWindowTitle("Error")

        msg_box.exec()

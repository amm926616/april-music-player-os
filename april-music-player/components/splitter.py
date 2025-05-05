from functools import reduce

from PyQt6.QtWidgets import QSplitter, QSplitterHandle

class ColumnSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.default_stretch_factors = [3, 13, 5]  # Default scaling factors

    def mouseDoubleClickEvent(self, event):
        splitter = self.parent()  # Get the QSplitter
        handle_index = splitter.indexOf(self)  # Get the index of this handle

        sizes = splitter.sizes()  # Get current widget sizes
        total_size = sum(sizes)  # Total available size

        if handle_index == 1:  # First handle (between widget 0 & 1)
            print("Handle 0 double-clicked!")
            if sizes[0] > 0:  # Collapse left widget
                splitter.setSizes([0, sizes[1] + sizes[0], sizes[2]])
            else:  # Expand using default proportions
                new_sizes = [
                    int(self.default_stretch_factors[0] / sum(self.default_stretch_factors) * total_size),
                    int(self.default_stretch_factors[1] / sum(self.default_stretch_factors) * total_size),
                    int(self.default_stretch_factors[2] / sum(self.default_stretch_factors) * total_size),
                ]
                splitter.setSizes(new_sizes)

        elif handle_index == 2:  # Second handle (between widget 1 & 2)
            print("Handle 1 double-clicked!")
            if sizes[2] > 0:  # Collapse right widget
                splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])
            else:  # Expand using default proportions
                new_sizes = [
                    int(self.default_stretch_factors[0] / sum(self.default_stretch_factors) * total_size),
                    int(self.default_stretch_factors[1] / sum(self.default_stretch_factors) * total_size),
                    int(self.default_stretch_factors[2] / sum(self.default_stretch_factors) * total_size),
                ]
                splitter.setSizes(new_sizes)

        super().mouseDoubleClickEvent(event)


class ColumnSplitter(QSplitter):
    def __init__(self, theme_color="red"):
        super().__init__()
        self.setStyleSheet(f"""
            QSplitter::handle {{
                background: gray;
                border: none;
            }}
            QSplitter::handle:hover {{
                background: {theme_color};
            }}
        """)

    def createHandle(self):
        return ColumnSplitterHandle(self.orientation(), self)

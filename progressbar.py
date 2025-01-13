"""
This is the progressbar module, used to display the progression of the
current filename generation in the TrueName GUI.
"""

from PyQt6.QtWidgets import (
    QDialog,
    QProgressBar,
    QVBoxLayout,
    QTextEdit,
    QHBoxLayout,
    QPushButton
)
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import pyqtSlot

import sys


class ProgressBarWindow(QDialog):
    """
    A simple progress bar window to represent the progress of the current
    filename generation. It include a toggled "details" text area where
    in-depth information on the file handling is displayed.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Filename generation in progress...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)  # Example range

        self.details_text_edit = QTextEdit()
        self.details_text_edit.setReadOnly(True)  # Set to read-only mode
        self.details_text_edit.show()
        self.visible_details = True

        layout = QVBoxLayout()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.details_text_edit)
        layout.addStretch()
        layout.setStretchFactor(self.details_text_edit, 1)
        self.setLayout(layout)


        buttons_layout = QHBoxLayout()

        self.details_button = QPushButton(self)
        self.details_button.setText("Details")
        self.details_button.clicked.connect(self.show_details_widget)
        buttons_layout.addWidget(self.details_button)

        # Adding a stretch between the two buttons
        buttons_layout.addStretch()

        self.ok_button = QPushButton(self)
        self.ok_button.setText("OK")
        self.ok_button.clicked.connect(self.close_progress_window)
        buttons_layout.addWidget(self.ok_button)

        layout.addLayout(buttons_layout)


        # Redirect STDOUT to the QTextEdit widget
        sys.stdout = EmittingStream(text_written=self._append_text)

    def _append_text(self, text):
        """
        Adds the given text into the textedit widget and sets up the cursor
        at the end.
        """
        # self.details_text_edit.clear()
        cursor = self.details_text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.details_text_edit.ensureCursorVisible()

    @pyqtSlot(int)
    def set_progress(self, value):
        """
        Updates the progress level of the progress bar widget to the
        given value.
        """
        self.show()
        self.raise_()  # Bring the window to the front
        self.progress_bar.setValue(value)

    @pyqtSlot()
    def show_details_widget(self):
        """
        When the details button is clicked, shows or hides details under the
        progress bar and updates the corresponding boolean to reflect the
        change.
        """
        if self.visible_details:
            self.details_text_edit.hide()
            self.visible_details = False
        else:
            self.details_text_edit.show()
            self.visible_details = True

    @pyqtSlot()
    def close_progress_window(self):
        """
        Closes the progress window if the progress bar is full when the user
        clicks the OK button.
        """
        if self.progress_bar.value() == 100:
            self.close()


# TODO Not sure I like this, could need overhaul ?
class EmittingStream:
    def __init__(self, text_written):
        self.text_written = text_written

    def write(self, text):
        self.text_written(text)

    def flush(self):
        pass # Not flushing for now

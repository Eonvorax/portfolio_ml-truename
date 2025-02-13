"""
This is the main_window module, used for displaying the TrueName GUI.
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QHBoxLayout,
    QAbstractItemView,
    QLabel,
    QListWidgetItem,
    QStyledItemDelegate,
    QMessageBox
)
from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QColor, QIcon
import sys
# from namegen import generate_new_file_paths
from progressbar import ProgressBarWindow
from time import time
import file
from os.path import normpath, exists, basename, split, abspath, join
from os import getcwd
from typing import List
from clean_filename import secure_filename, dynamic_rename
from ctypes import windll
from os import startfile


PATH_TO_ICON = 'truename_icon.ico'

# Differentiate the app from other Python apps
# to ensure that the correct icon is used in the taskbar :
APP_ID = 'Portfolio.TrueName.GUI.1'
windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)

# TODO update variables and docs, clean up inconsistencies, rename "namegen"

class TrueNameMainWindow(QMainWindow):
    """
    Represents the TrueName dialog window.

    Inherits from QMainWindow and provides functionality for opening a file dialog, generating new names,
    and displaying original paths and filenames as well as new filenames.
    """
    # TODO rewrite docs
    def __init__(self):
        """
        Initializes the TrueName dialog window.

        Sets the window title, size, and layout. Creates buttons for opening the file dialog and generating new names.
        Sets up the layout for the buttons and adds them to the general layout. Creates list widgets for displaying
        original paths and filenames, as well as new filenames. Adds the list widgets to the general layout.
        """
        super().__init__()
        self.setWindowTitle("TrueName")
        self.setWindowIcon(QIcon(get_resource_path(PATH_TO_ICON)))
        fit_to_screen(self, 0.9)

        # General layout for the main widget
        self.general_layout = QVBoxLayout()
        central_widget = QWidget(self)
        central_widget.setLayout(self.general_layout)
        self.setCentralWidget(central_widget)

        # Horizontal layout containing buttons for source list widget interaction
        left_buttons_layout = QHBoxLayout()

        # Horizontal layout containing buttons for new paths list widget interaction
        right_buttons_layout = QHBoxLayout()

        # Horizontal layout for list widgets
        list_widgets_layout = QHBoxLayout()

        # Layouts for each side of the app: source paths, and new file paths
        source_paths_layout = QVBoxLayout()
        new_paths_layout = QVBoxLayout()

        # Button to add files to the widget
        add_button = QPushButton(self)
        add_button.setText("Add files")
        add_button.clicked.connect(self.open_dialog)
        left_buttons_layout.addWidget(add_button)

        # Button to remove files from the widget
        remove_button = QPushButton(self)
        remove_button.setText("Remove files")
        remove_button.clicked.connect(self.remove_files)
        left_buttons_layout.addWidget(remove_button)

        # Button to generate names for the selected source files
        gen_button = QPushButton(self)
        gen_button.setText("Generate names")
        gen_button.clicked.connect(self.generate_filenames)
        left_buttons_layout.addWidget(gen_button)

        left_buttons_layout.addStretch(1)

        # "Select all" button to select all items in source_files_list
        select_all_source_button = QPushButton(self)
        select_all_source_button.setText("Select all source files")
        left_buttons_layout.addWidget(select_all_source_button)
        left_buttons_layout.setSpacing(3)

        # Another "Select all" button, for items in new_file_paths_list
        select_all_new_files_button = QPushButton(self)
        select_all_new_files_button.setText("Select all new filenames")
        right_buttons_layout.addWidget(select_all_new_files_button)

        right_buttons_layout.addStretch(1)

        # Button to rename the files with the selected filenames
        rename_button = QPushButton(self)
        rename_button.setObjectName("rename_button")
        rename_button.setText("Rename files")
        rename_button.clicked.connect(self.rename_files)
        right_buttons_layout.addWidget(rename_button)

        # Button to revert the recent rename operation
        revert_button = QPushButton(self)
        revert_button.setObjectName("revert_button")
        revert_button.setText("Revert rename")
        revert_button.clicked.connect(self.revert_rename)
        right_buttons_layout.addWidget(revert_button)

        right_buttons_layout.setSpacing(3)

        # Add the horizontal button layout to the source list layout
        source_paths_layout.addLayout(left_buttons_layout)

        # Create a QLabel for the title of the source file paths list widget
        self.source_files_label = QLabel('Original files')
        self.source_files_label.setObjectName("source_files_label")
        self.source_files_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        source_paths_layout.addWidget(self.source_files_label)
        # Removing spacing between Label and list widget
        source_paths_layout.setSpacing(0)

        # List widget listing original paths and filenames
        self.source_files_list = QListWidget(self)
        self.source_files_list.setObjectName("source_files_list")
        self.source_files_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.source_files_list.itemDoubleClicked.connect(self.open_file)
        source_list_scrollbar = self.source_files_list.verticalScrollBar()
        source_paths_layout.addWidget(self.source_files_list)

        # Select all source files when the button is clicked
        select_all_source_button.clicked.connect(lambda: self.select_all_items(self.source_files_list))

        # Add the horizontal button layout to the new paths list layout
        new_paths_layout.addLayout(right_buttons_layout)

        # Create a QLabel for the title of the new file paths list widget
        self.new_file_paths_label = QLabel('New filenames')
        self.new_file_paths_label.setObjectName("new_file_paths_label")
        self.new_file_paths_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        new_paths_layout.addWidget(self.new_file_paths_label)
        # Removing spacing between Label and list widget
        new_paths_layout.setSpacing(0)
        select_all_new_files_button.clicked.connect(lambda: self.select_all_items(self.new_file_paths_list))

        # Adding a second list widget for the new names
        self.new_file_paths_list = QListWidget(self)
        self.new_file_paths_list.setObjectName("new_file_paths_list")
        self.new_file_paths_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.new_file_paths_list.itemDoubleClicked.connect(self.make_item_editable)
        self.new_file_paths_list.itemChanged.connect(self.on_item_changed)
        new_list_scrollbar = self.new_file_paths_list.verticalScrollBar()
        new_paths_layout.addWidget(self.new_file_paths_list)

        # Adding both list widgets to the lists layout, then adding it to the general layout
        list_widgets_layout.addLayout(source_paths_layout)
        list_widgets_layout.setStretchFactor(source_paths_layout, 6)
        list_widgets_layout.addLayout(new_paths_layout)
        list_widgets_layout.setStretchFactor(new_paths_layout, 6)

        self.general_layout.addLayout(list_widgets_layout)

        # Connecting the scrollbars of the two list widgets to sync them
        source_list_scrollbar.valueChanged.connect(new_list_scrollbar.setValue)
        new_list_scrollbar.valueChanged.connect(source_list_scrollbar.setValue)

        # Progress bar window
        self.progress_window = ProgressBarWindow()
        fit_to_screen(self.progress_window, 0.7)

        # Load the CSS file
        with open(get_resource_path("styles.qss"), "r") as f:
            self.setStyleSheet(f.read())

        # File list
        self.files_instance_list: List[file.File] = []


    @pyqtSlot()
    def open_dialog(self):
        """
        Opens the file dialog and adds selected files (file paths) to the
        source_files_list widget.
        """
        added_file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add File",
            str(getcwd()),
            "Documents (*.pdf *.jpg *.jpeg *.png *.webp);; All Files (*)"
        )
        # TODO only allow file extensions supported by the app

        # List of file paths listed in the widget before adding more
        present_file_paths = []
        for i in range(self.source_files_list.count()):
            item = self.source_files_list.item(i)
            present_file_paths.append(item.text())

        # Adding file paths to the list widget
        for added_file_path in added_file_paths:
            # Only if they're not already in the list (no doubles)
            if normpath(added_file_path) not in present_file_paths:
                item = QListWidgetItem(self.source_files_list)
                item.setText(normpath(added_file_path))
                self.source_files_list.addItem(item)
                current_file = file.File(added_file_path)
                self.files_instance_list.append(current_file)


    @pyqtSlot()
    def generate_filenames(self):
        """
        Generates new names for the selected files and displays them in the new_file_paths_list.
        """
        # TODO extended for bugfixing and security, might be better as a loop
        # I'd like to rework/refactor this method anyway
        file_paths = [item.text() for item in self.source_files_list.selectedItems() if exists(item.text())]
        file_count = len(file_paths)

        # If no file path was added, don't do anything
        if file_count == 0:
            return

        start_time = time()
        print(file_paths)
        file_number = 0
        progress = 0
        self.progress_window.show()
        print(f"Working on {file_count} files...")

        # NOTE Could trade worse memory usage for better performance here ?
        for current_file in self.files_instance_list:
            if current_file.original_path in file_paths:
                # Update progress bar before process a File
                self.progress_window.set_progress(int(progress))
                QApplication.processEvents()
                file_number += 1
                progress = file_number / file_count * 100
                current_file.process_file(file_number)

        # Updating after the loop in any case (esp. for file_count = 0)
        self.progress_window.set_progress(int(progress))
        QApplication.processEvents()

        end_time = time()
        print(f"Elapsed time : {end_time - start_time:.03f} seconds.")
        self.display_new_file_paths()


    @pyqtSlot()
    def rename_files(self):
        """
        Renames the files whose (new) names are selected in the right-side widget
        """
        # TODO rework into one loop using item, not item.text() ?
        file_paths = [normpath(item.text()) for item in self.new_file_paths_list.selectedItems()]

        # NOTE need to be careful the slash/antislash Windows quirks
        for current_file in self.files_instance_list:
            if current_file.new_path in file_paths:
                old_path = normpath(current_file.original_path)
                new_path = normpath(current_file.new_path)
                if exists(old_path):
                    dynamic_rename(old_path, new_path)

        # Color all the renamed items (for UX reasons)
        for item in self.new_file_paths_list.selectedItems():
            if item.text() != "":
                self.new_file_paths_list.blockSignals(True)
                item.setBackground(QColor("lightgreen"))
                self.new_file_paths_list.blockSignals(False)


    def display_new_file_paths(self):
        """
        Displays the generated file paths in the second list widget by
        creates the corresponding items in the list widget. Item flags
        are set up to allow editing only if the path wasn't empty.
        """
        self.new_file_paths_list.clear()
        # All the new file paths, including for files not selected by the user
        file_paths = [file_item.new_path for file_item in self.files_instance_list]
        for path in file_paths:
            # The displayed path will be an empty string if the source path was not selected
            item = QListWidgetItem(path)
            # NOTE This condition makes it so empty paths (unselected) are not editable
            if path != "":
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.new_file_paths_list.addItem(item)

        delegate = FileNameDelegate()
        self.new_file_paths_list.setItemDelegate(delegate)


    def make_item_editable(self, item):
        """
        Starts the editing for the given item by the user, if the item is
        editable.
        """
        # Checking the flags so we don't try to edit a non-editable item
        if item.flags() & Qt.ItemFlag.ItemIsEditable:
            self.new_file_paths_list.editItem(item)

    def on_item_changed(self, item: QListWidgetItem):
        """
        Triggers when the item changes, be it from a setText, setBackground,
        or any other change to the item data. Checks the validity of each
        path in the new_file_paths_list widget, and updates the corresponding
        values for the File objects.
        If the path is invalid, the File Object is not updated and the
        invalid path is highlighted in red.
        If the path is valid or an empty string, the file object is updated
        and the path is highlighted in white (the default color).
        """
        # TODO this seems pointless now, could use the list widget directly
        new_paths_list = []
        for i in range(self.new_file_paths_list.count()):
            item = self.new_file_paths_list.item(i)
            new_paths_list.append(item.text())

        i_new_paths = 0
        for f_obj in self.files_instance_list:
            path = new_paths_list[i_new_paths]
            # NOTE briefly blocking signals to prevent infinite recursion
            self.new_file_paths_list.blockSignals(True)
            if path != "":
                dir_path, filename = split(normpath(path))
                # NOTE could also do filename = secure_filename() instead
                # but I prefer leaving it to the user in this case.
                if exists(dir_path) and filename == secure_filename(filename):
                    f_obj.new_path = path
                    self.new_file_paths_list.item(i_new_paths).setBackground(QColor("white"))
                else:
                    self.new_file_paths_list.item(i_new_paths).setText(f_obj.new_path)
                    self.new_file_paths_list.item(i_new_paths).setBackground(QColor("red"))
            else:
                self.new_file_paths_list.item(i_new_paths).setBackground(QColor("white"))
            self.new_file_paths_list.blockSignals(False)
            i_new_paths += 1

    @pyqtSlot()
    def revert_rename(self):
        """
        Reverts a previous rename by renaming current current file paths
        using the corresponding original_path value.
        Similar to rename_files but in reverse, using a different color code.
        """
        file_paths = [normpath(item.text()) for item in self.new_file_paths_list.selectedItems()]

        for current_file in self.files_instance_list:
            if current_file.new_path in file_paths:
                old_path = normpath(current_file.original_path)
                new_path = normpath(current_file.new_path)
                if exists(new_path):
                    # Inverse rename using old path value for this file
                    dynamic_rename(new_path, old_path)

        # Color all the reverted filenames (orange this time, again for UX reasons)
        for item in self.new_file_paths_list.selectedItems():
            if item.text() != "":
                self.new_file_paths_list.blockSignals(True)
                item.setBackground(QColor("orange"))
                self.new_file_paths_list.blockSignals(False)

    @pyqtSlot()
    def select_all_items(self, list_widget: QListWidget):
        """
        Selects all the ListWidgetItem objects in the given ListWidget object,
        or unselects them if they are all already selected.
        """

        if all(list_widget.item(i).isSelected() for i in range(list_widget.count())):
            list_widget.clearSelection()
        else:
            list_widget.selectAll()

    @pyqtSlot()
    def remove_files(self):
        """
        Removes all selected files from the list widget and files_instance_list.
        The current selection is cleared.
        """

        items_to_remove = []

        for item in self.source_files_list.selectedItems():
            path = item.text()
            for index, current_file in enumerate(self.files_instance_list):
                if current_file.original_path == path:
                    items_to_remove.append(index)
                    self.source_files_list.takeItem(self.source_files_list.row(item))

        # Remove items from self.files_instance_list in reverse order to avoid index shifting
        for index in sorted(items_to_remove, reverse=True):
            del self.files_instance_list[index]

        # Clear selected items in self.source_files_list
        self.source_files_list.clearSelection()

        # Clear the "new filenames" widget so the files are not misaligned
        self.new_file_paths_list.clear()
    
    @pyqtSlot(QListWidgetItem)
    def open_file(self, item):
        """
        Opens the file represented by the given QListWidgetItem.
        The file is opened with the default application for its file type.
        If the file cannot be opened, an error message box is displayed.
        """
        file_path = item.text()
        try:
            if sys.platform == 'win32':
                startfile(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file: {file_path}\n\n{str(e)}")


class FileNameDelegate(QStyledItemDelegate):
    """
    Proxy class to customize the styling of an element.
    """
    def displayText(self, value, locale):
        """
        Reformats the displayed path to only show the filename part.
        The actual data is not affected.
        """
        # TODO test edge cases with inconvenient characters
        # Display only the filename or a truncated path
        filename = basename(value)
        return f"{filename}"


def get_resource_path(relative_path):
    """
    Get correct absolute path to resource, works for dev version (script) and
    for distribution version with PyInstaller.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # No _MEIPASS, assuming dev version & using the basic absolute path
        base_path = abspath(".")

    return join(base_path, relative_path)


def fit_to_screen(widget: QWidget, ratio: float):
    """
    Fits the widget to the screen, using the given float ratio.
    The widget will occupy (ratio * 10)% of the primary screen.
    Use a ratio between 0 and 1, ideally closer to 1.
    """
    # Getting the available screen resolution of the monitor
    screen = QApplication.primaryScreen().availableGeometry()

    # Calculating the desired size
    desired_width = int(screen.width() * ratio)
    desired_height = int(screen.height() * ratio)

    # Calculating the margins to center the widget
    margin_left = int((screen.width() - desired_width) / 2)
    margin_top = int((screen.height() - desired_height) / 2)

    # Resize and move the widget
    widget.setGeometry(margin_left, margin_top, desired_width, desired_height)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_gui = TrueNameMainWindow()
    main_gui.show()
    sys.exit(app.exec())

#!/usr/bin/env python3

from sys import argv, exit
from time import sleep, time
import file
from progressbar import ProgressBarWindow
from main_window import fit_to_screen
from PyQt6.QtWidgets import (
    QApplication
)


def context_generate_name(argv, progress_window: ProgressBarWindow):
    """
    Generates names from the given filename, ran from the
    Windows context menu.
    """
    # TODO add path checking to file paths

    files_instance_list = [file.File(path) for path in argv]
    file_count = len(files_instance_list)

    # If no file path was added, don't do anything
    if file_count == 0:
        return

    start_time = time()
    print(argv)
    file_number = 0
    progress = 0
    progress_window.show()
    print(f"Working on {file_count} files...")

    # NOTE Could trade worse memory usage for better performance here ?
    for current_file in files_instance_list:
        # Update progress bar before process a File
        progress_window.set_progress(int(progress))
        QApplication.processEvents()
        file_number += 1
        progress = file_number / file_count * 100
        current_file.process_file(file_number)

    # Updating after the loop in any case (esp. for file_count = 0)
    progress_window.set_progress(int(progress))
    QApplication.processEvents()

    end_time = time()
    print(f"Elapsed time : {end_time - start_time:.03f} seconds.")


def main():
    """
    Main for context_namegen: handles command-line arguments, creates a
    progress bar window, fits it to the primary screen and then generates
    names.
    """

    # TODO Add renaming, handle potential registry & context lauch issues
    if len(argv) < 2:
        print("Usage: python context_namegen.py filename [...]")
        exit(1)
    app = QApplication(argv)
    progress_window = ProgressBarWindow()

    fit_to_screen(progress_window, 0.5)

    context_generate_name(argv[1:], progress_window)
    exit(app.exec())


if __name__ == "__main__":
    main()

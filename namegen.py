#!/usr/bin/env python3
"""
This is the namegen module. It contains methods used to iterate over
the files, generate filenames, and rename them
(NOTE "manipulate files" ?)
"""
from time import time
import file


def generate_new_filenames(file_paths, progress_callback=None):
    """
    Iterates over a given list of file paths, instantiates a File class
    object for each file, extracts its content, identifies its language
    then generates a new filename based on it content.

    Returns:
        A list of new filenames
    """
    # TODO Might need to return a list of File objects instead for convenience
    start_time = time()

    file_count = len(file_paths)
    print(f"Working on {file_count} files...")
    new_filenames = []
    for file_number, file_path in enumerate(file_paths, start=1):
        # Calculate current progress
        progress = file_number / file_count * 100
        print(f"\nWorking on file {file_number}")
        current_file = file.File(file_path)
        current_file.extract_content()
        current_file.identify_language()
        print(f"Detected language: {current_file.language}")
        current_file.generate_name()
        print(f"Generated new name: [{current_file.new_name}]")
        new_filenames.append(current_file.new_name)

        # Update progress
        if progress_callback:
            progress_callback(progress)

    end_time = time()
    print(f"Elapsed time : {end_time - start_time:.03f} seconds.")

    return new_filenames

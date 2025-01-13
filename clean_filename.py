#!/usr/bin/env python3
"""
This is the clean_filename module, used to modify filenames so they don't
cause issues with future file manipulation.
"""

from unicodedata import normalize, category
from re import sub
from os import rename
from os.path import splitext, join


def clean_unicode(filename: str):
    """
    Normalizes the given filename string then secures it by replacing
    problematic unicode characters with an underscore.
    """
    filename_normd = normalize('NFKD', filename)

    # TODO could replace bad chars by nothing and not "_"
    cleaned_filename = ''
    for c in filename_normd:
        if category(c) == 'Cc' or category(c) == 'So':
            cleaned_filename += '_'
        else:
            cleaned_filename += c

    return cleaned_filename

def clean_forbidden_chars(filename: str):
    """
    Cleans up the given filename string so it doesn't contain characters
    forbidden by Windows. Rejected characters are replaced with an
    underscore.
    """
    forbidden_chars = r'[<>:"/\\|?*]'

    cleaned_filename = sub(forbidden_chars, '_', filename)

    return cleaned_filename

def secure_filename(filename: str):
    """
    Secures a filename by replacing various forbidden characters, to avoid
    issues with future file manipulation.
    """
    unicode_cleaned_filename = clean_unicode(filename)
    return clean_forbidden_chars(unicode_cleaned_filename)

def dynamic_rename(src_path: str, dest_path: str):
    """
    A modified os.rename that can create a dynamic file name if the new_path
    file already exists.
    """
    try:
        rename(src_path, dest_path)
    except FileExistsError:
        successful = False
        count = 1
        while not successful:
            file_root, file_ext = splitext(dest_path)
            file_root += f"_({count})"
            dynamic_path = file_root + file_ext
            try:
                rename(src_path, dynamic_path)
                successful = True
            except FileExistsError:
                pass
            count += 1

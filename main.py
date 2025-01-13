#!/usr/bin/env python3

"""
This is the test module for the File class
"""
from sys import argv
from time import time
from os import rename
from os.path import abspath
import file

start_time = time()

file_path = abspath(argv[1])
my_file = file.File(file_path)
print(f"Working on file: '{my_file.original_name}.{my_file.file_type}'")
print(f"File path : {my_file.original_path}")
my_file.extract_content()
print("Extracted file content.")
my_file.identify_language()
print(f"Detected language: {my_file.language}")
my_file.generate_name()
print(f"Generated new name: [{my_file.new_name}]")
my_file.build_new_path()
print(f"Built new path: {my_file.new_path}")

rename(my_file.original_path, my_file.new_path)

end_time = time()
print(f"Elapsed time : {end_time - start_time:.03f} seconds.")

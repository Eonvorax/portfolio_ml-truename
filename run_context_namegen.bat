@echo off

REM Activate the virtual environment
call "C:\Users\Bishop\Desktop\Holberton\Repos\portfolio-true_name\venv\Scripts\activate.bat"

REM Call the Python script with all file paths as arguments
python "C:\Users\Bishop\Desktop\Holberton\Repos\portfolio-true_name\context_namegen.py" %1

REM Deactivate the virtual environment (optional)
call "C:\Users\Bishop\Desktop\Holberton\Repos\portfolio-true_name\venv\Scripts\deactivate.bat"

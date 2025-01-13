#!/usr/bin/env python3
from context_menu import menus

# Working regedit command:
# On PC : "C:\Users\Bishop\Desktop\Holberton\Repos\portfolio-true_name\run_context_namegen.bat" "%L"
# On laptop "C:\Users\PC\Desktop\Holberton\portfolio-true_name\run_context_namegen.bat" "%L"

# NOTE This needs to be tested with multiple files again since it appears the log.txt doesn't contain everything
fc = menus.FastCommand('TrueName quick namegen', type='FILES', command='launch_namegen.bat', command_vars=['FILENAME'])
fc.compile()

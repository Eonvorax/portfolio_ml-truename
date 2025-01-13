# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_window.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('venv/Lib/site-packages/en_core_web_sm', 'en_core_web_sm'),
        ('venv/Lib/site-packages/fr_core_news_sm', 'fr_core_news_sm'),
        ('venv/Lib/site-packages/en_core_web_sm-3.7.1.dist-info', 'en_core_web_sm-3.7.1.dist-info'),
        ('venv/Lib/site-packages/fr_core_news_sm-3.7.0.dist-info', 'fr_core_news_sm-3.7.0.dist-info'),
        ('styles.qss', '.'),
        ('truename_icon.ico', '.')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TrueName',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    windowed=True,
    icon="truename_icon.ico"
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TrueName',
)

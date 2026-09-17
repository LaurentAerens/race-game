# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Base directory is the repository root
base_dir = os.path.abspath(os.path.join(SPECPATH, '..'))

a = Analysis(
    [os.path.join(base_dir, 'main.py')],
    pathex=[base_dir],
    binaries=[],
    datas=[
        (os.path.join(base_dir, 'tracks'), 'tracks'),
        (os.path.join(base_dir, 'data'), 'data'),
    ],
    hiddenimports=[
        'sqlite3',
        'pygame',
        'pygame_gui',
        'scipy',
        'shapely',
        'numpy',
        'requests',
        'networkx',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'tensorflow',
        'tensorboard',
        'matplotlib',
        'sympy',
        'IPython',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MotorsportTycoon',
    icon=os.path.join(base_dir, 'data', 'app_icon.ico'),
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='MotorsportTycoon',
)

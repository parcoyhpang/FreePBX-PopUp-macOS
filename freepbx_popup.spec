# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for FreePBX Popup Client.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Get the path to the resources directory
resources_dir = os.path.join(os.getcwd(), 'resources')

# Collect all data files
datas = [
    (os.path.join(resources_dir, 'icon.png'), 'resources'),
    (os.path.join(resources_dir, 'menu_bar_icon.png'), 'resources'),
]

# Add any additional data files
if os.path.exists(os.path.join(resources_dir, 'icon.icns')):
    datas.append((os.path.join(resources_dir, 'icon.icns'), 'resources'))

# Add main window launcher
main_window_launcher = os.path.join(os.getcwd(), 'asterisk_popup', 'ui', 'wx', 'main_window_launcher.py')
if os.path.exists(main_window_launcher):
    datas.append((main_window_launcher, '.'))

# Add standalone main window launcher
standalone_launcher = os.path.join(os.getcwd(), 'main_window_launcher.py')
if os.path.exists(standalone_launcher):
    datas.append((standalone_launcher, '.'))

# We don't need to include the config directory as it will be created at runtime

# Collect all hidden imports
hidden_imports = [
    'rumps',
    'wx',
    'PIL',
    'requests',
    'sqlalchemy',
    'objc',
    'Foundation',
    'AppKit',
    'py_sip_xnu',
    'applescript',
    'markdown2',
]

# Add all submodules from the asterisk_popup package
hidden_imports.extend(collect_submodules('asterisk_popup'))

a = Analysis(
    ['run_asterisk_popup.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FreePBX Popup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
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
    name='FreePBX Popup',
)

# Create a macOS application bundle
app = BUNDLE(
    coll,
    name='FreePBX Popup.app',
    icon=os.path.join(resources_dir, 'icon.icns'),
    bundle_identifier='com.parcopang.freepbxpopup',
    info_plist={
        'LSUIElement': True,  # Run as agent (no dock icon)
        'CFBundleName': 'FreePBX Popup',
        'CFBundleDisplayName': 'FreePBX Popup',
        'CFBundleIdentifier': 'com.parcopang.freepbxpopup',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': '© 2024 Parco Y.H. Pang',
        'NSHighResolutionCapable': True,
    },
)

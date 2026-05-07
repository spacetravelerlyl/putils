# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Collect all plugin modules dynamically
import os
import sys
import glob

# Use appropriate path separator for the platform
path_sep = os.sep

plugin_pattern = os.path.join('putils', 'plugins', '*.py')
plugin_files = glob.glob(plugin_pattern)
plugin_modules = []
for pf in plugin_files:
    module_name = os.path.splitext(os.path.basename(pf))[0]
    if module_name != '__init__':
        plugin_modules.append(f'putils.plugins.{module_name}')

print(f"Discovered plugins: {plugin_modules}")

a = Analysis(
    ['putils' + path_sep + 'app.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include all Python source files from putils package
        ('putils' + path_sep + '*.py', 'putils'),
        # Include plugins directory with all plugin files
        ('putils' + path_sep + 'plugins' + path_sep + '*.py', 'putils' + path_sep + 'plugins'),
    ],
    hiddenimports=[
        # Core putils modules - MUST be first
        'putils',
        'putils.app',
        'putils.database',
        'putils.i18n',
        'putils.paths',
        'putils.plugin_api',
        'putils.plugin_loader',
        'putils.tk_utils',
        # Plugin modules (dynamically discovered)
    ] + plugin_modules + [
        # Critical standard library modules - ensure these are loaded early
        'encodings',
        'encodings.utf_8',
        'encodings.latin_1',
        'codecs',
        '_collections_abc',
        'os',
        'sys',
        'io',
        'abc',
        # Other standard library modules
        'zoneinfo',
        'json',
        'subprocess',
        'threading',
        'concurrent.futures',
        'pathlib',
        'importlib',
        'pkgutil',
        'shutil',
        'datetime',
        'collections',
        'functools',
        'time',
        'typing',
        'dataclasses',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'sqlite3',
        'hashlib',
        'textwrap',
        'contextlib',
        'enum',
        'copy',
        'weakref',
        'types',
        'operator',
        're',
        'string',
        'errno',
        'stat',
        'genericpath',
        'ntpath',
        'posixpath',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test and development modules
        'test',
        'unittest',
        'doctest',
        'pdb',
        'pydoc',
        'distutils',
        'setuptools',
        'pip',
        # Exclude unnecessary modules to reduce size
        'email',
        'html',
        'http',
        'xml',
        'urllib',
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
    name='putils',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='putils.ico',  # Uncomment and add icon file if available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='putils',
)

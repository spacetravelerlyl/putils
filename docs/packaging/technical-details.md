# PUtils Portable Packaging Guide

## Overview

This guide explains how to package PUtils as a portable Windows application that can run on any Windows machine without requiring Python or dependency installation.

## Prerequisites

Before building, ensure you have:
- Python 3.8 or later installed
- pip (Python package manager)
- All dependencies listed in `requirements.txt`

## Build Methods

There are two build methods available:

### Method 1: Directory-based Package (Recommended for Development)

Creates a folder with the executable and all dependencies separately.

**Advantages:**
- Faster startup time
- Easier to debug
- Smaller initial extraction

**Build Command:**
```batch
build_portable.bat
```

**Output:** `dist\putils\` folder containing:
- `putils.exe` - Main executable
- All required DLL files and libraries
- Plugin files
- README.txt with usage instructions

### Method 2: Single-File Executable (Recommended for Distribution)

Creates a single `.exe` file that contains everything.

**Advantages:**
- Easier to distribute (single file)
- Cleaner appearance
- No folder structure to manage

**Disadvantages:**
- Slower first launch (extracts to temp directory)
- Larger file size
- Harder to debug

**Build Command:**
```batch
build_single_file.bat
```

**Output:** `dist\putils.exe` - Single standalone executable

## Usage After Building

### For Directory-based Package:
1. Copy the entire `dist\putils` folder to target machine
2. Run `putils.exe`
3. Application data will be stored in `%APPDATA%\PUtils` by default

### For Single-File Executable:
1. Copy `dist\putils.exe` to target machine
2. Run `putils.exe`
3. First launch may take a few seconds to extract temporary files
4. Application data will be stored in `%APPDATA%\PUtils` by default

## Important Notes

### Data Storage
- Configuration, logs, and cache are stored in `%APPDATA%\PUtils` by default
- Users can change the data directory in Settings
- This ensures data persists across application updates

### Plugin Dependencies
- Video saturation plugin requires **ffmpeg** to be installed on the target machine
- ffmpeg must be in the system PATH
- Other plugins may have their own external dependencies

### Customizing the Build

#### Adding an Icon
Edit the spec file or build script to include an icon:
```python
icon='path/to/icon.ico'
```

#### Console Mode (for debugging)
Change `console=False` to `console=True` in the spec file to show console output.

#### Reducing File Size
- Remove unused plugins from `putils/plugins/`
- Exclude unnecessary modules in the spec file
- Enable UPX compression (already enabled by default)

## Troubleshooting

### Build Fails with Import Errors
Ensure all dependencies are installed:
```batch
pip install -r requirements.txt
```

### Application Doesn't Start
1. Try running with console mode enabled to see errors
2. Check if all required files are included in the build
3. Verify plugin imports are listed in `hiddenimports`

### Plugins Not Loading
1. Ensure plugins directory is included in the build
2. Check that plugin module names are in `hiddenimports`
3. Verify `plugin_loader.py` can find the plugins

### Large Executable Size
- Use `--exclude-module` for unnecessary modules
- Remove unused plugins
- Consider using Method 1 (directory-based) instead

## Advanced Configuration

### Environment Variables
- `PUTILS_DATA_DIR`: Override the data directory location
- Set this before launching the executable to use custom data location

### Including Additional Files
Add to the `datas` list in `putils.spec`:
```python
datas=[
    ('source/path', 'destination/path'),
]
```

### Multiple Python Versions
The built executable includes its own Python runtime, so it will work regardless of what Python version (if any) is installed on the target machine.

## Distribution Checklist

Before distributing:
- [ ] Test the executable on a clean Windows machine
- [ ] Verify all plugins work correctly
- [ ] Check that settings are saved properly
- [ ] Ensure data directory configuration works
- [ ] Test with and without ffmpeg installed
- [ ] Verify internationalization works
- [ ] Check file size is acceptable
- [ ] Include README or usage instructions

## Example Distribution Package

For directory-based distribution, create a ZIP file:
```
putils-v0.1.0-windows.zip
├── putils/
│   ├── putils.exe
│   ├── *.dll files
│   ├── plugins/
│   └── README.txt
└── INSTALLATION.txt
```

For single-file distribution:
```
putils-v0.1.0-windows.exe
```

#!/bin/bash
# Build script for creating single-file portable Linux executable

set -e  # Exit on error

echo "========================================"
echo "Building putils Single-File Executable for Linux"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed or not in PATH"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Step 1: Install dependencies
echo "[1/3] Installing dependencies..."
pip3 install -r requirements.txt || pip install -r requirements.txt
echo ""

# Step 2: Clean previous builds
echo "[2/3] Cleaning previous build..."
rm -rf dist build
echo "Done."
echo ""

# Step 3: Build single-file executable
echo "[3/3] Building single-file executable..."
pyinstaller --clean \
    --name=putils \
    --windowed \
    --onefile \
    --add-data "putils/i18n.py:putils" \
    --add-data "putils/plugins:putils/plugins" \
    --hidden-import=putils.plugins \
    --hidden-import=putils.plugins.video_saturation \
    --hidden-import=zoneinfo \
    --hidden-import=tkinter \
    --hidden-import=sqlite3 \
    --collect-all=tkinter \
    putils/app.py

if [ ! -f "dist/putils" ]; then
    echo "ERROR: Build failed"
    exit 1
fi

# Create distribution package
mkdir -p dist/package
cp dist/putils dist/package/

cat > dist/package/README.txt << 'EOF'
PUtils - Portable Utility Application (Linux)
==============================================

This is a single-file executable.
Make it executable and run:

  chmod +x putils
  ./putils

System Requirements:
- Linux (Ubuntu 18.04+, Fedora 28+, or equivalent)
- No Python installation required
- X11 or Wayland display server

Optional: Install ffmpeg for video processing features
  Ubuntu/Debian: sudo apt install ffmpeg
  Fedora: sudo dnf install ffmpeg
  Arch: sudo pacman -S ffmpeg

Your settings and data are stored in:
~/.local/share/putils

Note: First launch may take a few seconds to extract temporary files.

For more information, see README_PORTABLE.md
EOF

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "Single-file executable location: dist/package/putils"
echo ""
echo "This is a standalone executable that can be copied to any Linux machine."
echo "Remember to make it executable: chmod +x dist/package/putils"
echo "Note: First launch may take a few seconds to extract temporary files."
echo ""

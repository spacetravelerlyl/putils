#!/bin/bash
# Build script for creating portable Linux executable of putils

set -e  # Exit on error

echo "========================================"
echo "Building putils Portable Executable for Linux"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed or not in PATH"
    echo "Please install Python 3.8+ (e.g., sudo apt install python3)"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Step 1: Install dependencies
echo "[1/4] Installing dependencies..."
pip3 install -r requirements.txt || pip install -r requirements.txt
echo ""

# Step 2: Clean previous builds
echo "[2/4] Cleaning previous build..."
rm -rf dist build *.spec.backup
echo "Done."
echo ""

# Step 3: Build with PyInstaller
echo "[3/4] Building executable with PyInstaller..."
pyinstaller --clean putils.spec
echo ""

# Step 4: Create distribution package
echo "[4/4] Creating portable package..."
BUILD_DIR="dist/putils"

if [ ! -d "$BUILD_DIR" ]; then
    echo "ERROR: Build directory not found"
    exit 1
fi

# Create README for distribution
cat > "$BUILD_DIR/README.txt" << 'EOF'
PUtils - Portable Utility Application (Linux)
==============================================

To use this application:
1. Copy the entire 'putils' folder to your desired location
2. Make the executable runnable: chmod +x putils
3. Run ./putils

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

For more information, see README_PORTABLE.md
EOF

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "Portable executable location: dist/putils/"
echo ""
echo "You can now copy the entire 'dist/putils' folder to any Linux machine."
echo "Remember to make it executable: chmod +x dist/putils/putils"
echo ""

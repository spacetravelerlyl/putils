#!/bin/bash
# Interactive build script for Linux with validation and packaging

set -e

echo "========================================"
echo "PUtils Portable Build System for Linux"
echo "========================================"
echo ""

# Step 0: Validate prerequisites
echo "[Step 0/5] Validating prerequisites..."
chmod +x check_prerequisites_linux.sh
./check_prerequisites_linux.sh
if [ $? -ne 0 ]; then
    echo ""
    echo "Prerequisites check failed. Please fix the issues above."
    exit 1
fi
echo ""

# Ask user for build type
echo "Select build type:"
echo "  1. Directory-based package (faster startup, recommended for testing)"
echo "  2. Single-file executable (easier distribution)"
echo ""
read -p "Enter choice (1 or 2): " BUILD_TYPE

if [ "$BUILD_TYPE" = "1" ]; then
    BUILD_MODE="dir"
elif [ "$BUILD_TYPE" = "2" ]; then
    BUILD_MODE="single"
else
    echo "Invalid choice. Defaulting to directory-based build."
    BUILD_MODE="dir"
fi

echo ""

if [ "$BUILD_MODE" = "single" ]; then
    echo "========================================"
    echo "Building Single-File Executable"
    echo "========================================"
    echo ""
    
    # Install dependencies
    echo "[Step 1/4] Installing dependencies..."
    pip3 install -r requirements.txt || pip install -r requirements.txt
    echo ""
    
    # Clean builds
    echo "[Step 2/4] Cleaning previous builds..."
    rm -rf dist build
    echo "Done."
    echo ""
    
    # Build
    echo "[Step 3/4] Building single-file executable..."
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
    echo ""
    
    # Create distribution package
    echo "[Step 4/4] Creating distribution package..."
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
    echo "Build completed successfully!"
    echo "Location: dist/package/putils"
    echo ""
    
else
    echo "========================================"
    echo "Building Directory-based Package"
    echo "========================================"
    echo ""
    
    # Install dependencies
    echo "[Step 1/4] Installing dependencies..."
    pip3 install -r requirements.txt || pip install -r requirements.txt
    echo ""
    
    # Clean builds
    echo "[Step 2/4] Cleaning previous builds..."
    rm -rf dist build *.spec.backup
    echo "Done."
    echo ""
    
    # Build
    echo "[Step 3/4] Building with PyInstaller..."
    pyinstaller --clean putils.spec
    echo ""
    
    # Create distribution package
    echo "[Step 4/4] Creating distribution package..."
    BUILD_DIR="dist/putils"
    
    if [ ! -d "$BUILD_DIR" ]; then
        echo "ERROR: Build directory not found"
        exit 1
    fi
    
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
    echo "Build completed successfully!"
    echo "Location: dist/putils/"
    echo ""
fi

echo "========================================"
echo "Next steps:"
echo "1. Test the executable: cd dist/putils && chmod +x putils && ./putils"
echo "2. Verify all features work correctly"
echo "3. Package for distribution (tar.gz, AppImage, etc.)"
echo "========================================"
echo ""

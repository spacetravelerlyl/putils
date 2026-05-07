#!/bin/bash
# Pre-build validation script for Linux

echo "========================================"
echo "PUtils Linux Build Prerequisites Check"
echo "========================================"
echo ""

ERRORS=0

# Check Python3
echo "[1/5] Checking Python3 installation..."
if command -v python3 &> /dev/null; then
    echo "OK: $(python3 --version)"
else
    echo "ERROR: Python3 is not installed"
    echo "Install with: sudo apt install python3 (Ubuntu/Debian)"
    echo "           or: sudo dnf install python3 (Fedora)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check pip
echo "[2/5] Checking pip..."
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    echo "OK: pip found"
else
    echo "ERROR: pip is not available"
    echo "Install with: sudo apt install python3-pip (Ubuntu/Debian)"
    echo "           or: sudo dnf install python3-pip (Fedora)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check tkinter
echo "[3/5] Checking tkinter..."
if python3 -c "import tkinter" 2>/dev/null; then
    echo "OK: tkinter found"
else
    echo "ERROR: tkinter is not available"
    echo "Install with: sudo apt install python3-tk (Ubuntu/Debian)"
    echo "           or: sudo dnf install python3-tkinter (Fedora)"
    echo "           or: sudo pacman -S tk (Arch)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check sqlite3
echo "[4/5] Checking sqlite3..."
if python3 -c "import sqlite3" 2>/dev/null; then
    echo "OK: sqlite3 found"
else
    echo "ERROR: sqlite3 is not available"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check source files
echo "[5/5] Checking source files..."
if [ ! -d "putils/plugins" ]; then
    echo "ERROR: plugins directory not found"
    ERRORS=$((ERRORS + 1))
else
    echo "OK: plugins directory found"
fi

if [ ! -f "putils/i18n.py" ]; then
    echo "ERROR: i18n.py not found"
    ERRORS=$((ERRORS + 1))
else
    echo "OK: i18n.py found"
fi
echo ""

# Check display server (for GUI apps)
echo "Checking display server..."
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "WARNING: No display server detected"
    echo "GUI applications require X11 or Wayland"
else
    echo "OK: Display server detected"
fi
echo ""

# Summary
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    echo "All checks passed! Ready to build."
    echo ""
    echo "You can now run:"
    echo "  ./build_linux.sh              (directory-based package)"
    echo "  ./build_linux_single.sh       (single-file executable)"
else
    echo "Found $ERRORS error(s). Please fix them before building."
fi
echo "========================================"
echo ""

exit $ERRORS

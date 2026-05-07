@echo off
REM Alternative build script for single-file portable executable

echo ========================================
echo Building putils Single-File Executable
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/3] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [2/3] Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo.

echo [3/3] Building single-file executable...
pyinstaller --clean ^
    --name=putils ^
    --windowed ^
    --onefile ^
    --icon=NONE ^
    --add-data "putils/i18n.py;putils" ^
    --add-data "putils/plugins;putils/plugins" ^
    --hidden-import=putils.plugins ^
    --hidden-import=putils.plugins.video_saturation ^
    --hidden-import=zoneinfo ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=sqlite3 ^
    --collect-all=tkinter ^
    putils/app.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Single-file executable location: dist\putils.exe
echo.
echo This is a standalone executable that can be copied to any Windows machine.
echo Note: First launch may take a few seconds to extract temporary files.
echo.
pause

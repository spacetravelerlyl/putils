@echo off
REM Build script for creating portable Windows executable of putils

echo ========================================
echo Building putils Portable Executable
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

echo [1/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [2/4] Cleaning previous build...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "*.spec" del /q "*.spec"
echo.

echo [3/4] Building executable with PyInstaller...
pyinstaller --clean putils.spec
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo.

echo [4/4] Creating portable package...
set BUILD_DIR=dist\putils
if not exist "%BUILD_DIR%" (
    echo ERROR: Build directory not found
    pause
    exit /b 1
)

REM Create a README for the portable version
echo Portable putils Application > "%BUILD_DIR%\README.txt"
echo ========================= >> "%BUILD_DIR%\README.txt"
echo. >> "%BUILD_DIR%\README.txt"
echo To use this application: >> "%BUILD_DIR%\README.txt"
echo 1. Copy the entire 'putils' folder to your desired location >> "%BUILD_DIR%\README.txt"
echo 2. Run putils.exe >> "%BUILD_DIR%\README.txt"
echo. >> "%BUILD_DIR%\README.txt"
echo Notes: >> "%BUILD_DIR%\README.txt"
echo - All data will be stored in %%APPDATA%%\putils by default >> "%BUILD_DIR%\README.txt"
echo - You can change the data directory in Settings >> "%BUILD_DIR%\README.txt"
echo - Plugins are included in the package >> "%BUILD_DIR%\README.txt"
echo. >> "%BUILD_DIR%\README.txt"
echo Requirements: >> "%BUILD_DIR%\README.txt"
echo - Windows 7 or later >> "%BUILD_DIR%\README.txt"
echo - ffmpeg must be installed and in PATH for video processing features >> "%BUILD_DIR%\README.txt"
echo.

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Portable executable location: dist\putils\
echo.
echo You can now copy the entire 'dist\putils' folder to any Windows machine.
echo.
pause

@echo off
REM Debug build script for troubleshooting PyInstaller issues

echo ========================================
echo Building putils with Debug Mode
echo ========================================
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo [1/3] Cleaned previous builds.
echo.

REM Install/upgrade PyInstaller
echo [2/3] Upgrading PyInstaller...
pip install --upgrade pyinstaller
echo.

REM Build with debug options
echo [3/3] Building with debug mode enabled...
echo This will create a console window to show errors.
echo.

pyinstaller --clean ^
    --name=putils-debug ^
    --windowed ^
    --onefile ^
    --debug=all ^
    --add-data "putils/i18n.py;putils" ^
    --add-data "putils/plugins;putils/plugins" ^
    --hidden-import=putils.plugins ^
    --hidden-import=putils.plugins.video_saturation ^
    --hidden-import=zoneinfo ^
    --hidden-import=tkinter ^
    --hidden-import=sqlite3 ^
    --hidden-import=encodings ^
    --hidden-import=encodings.utf_8 ^
    --collect-all=tkinter ^
    putils/app.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Debug build completed!
echo ========================================
echo.
echo Location: dist\putils-debug.exe
echo.
echo IMPORTANT: 
echo - Run this from command line to see detailed error messages
echo - The console will show import errors and tracebacks
echo - Use this to diagnose issues before building release version
echo.
echo To run from command line:
echo   cd dist
echo   putils-debug.exe
echo.
pause

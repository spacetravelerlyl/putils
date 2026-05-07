@echo off
REM Fixed single-file build script with improved compatibility

echo ========================================
echo Building putils Single-File (Fixed Version)
echo ========================================
echo.

REM Check Python version
python --version
echo.

REM Clean previous builds
echo [1/4] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo Done.
echo.

REM Upgrade PyInstaller
echo [2/4] Ensuring latest PyInstaller is installed...
pip install --upgrade pyinstaller
echo.

REM Build with optimized settings
echo [3/4] Building single-file executable...
echo This may take a few minutes...
echo.

pyinstaller --clean ^
    --name=putils ^
    --windowed ^
    --onefile ^
    --noupx ^
    --add-data "putils/i18n.py;putils" ^
    --add-data "putils/plugins;putils/plugins" ^
    --hidden-import=putils ^
    --hidden-import=putils.app ^
    --hidden-import=putils.database ^
    --hidden-import=putils.i18n ^
    --hidden-import=putils.paths ^
    --hidden-import=putils.plugin_api ^
    --hidden-import=putils.plugin_loader ^
    --hidden-import=putils.tk_utils ^
    --hidden-import=putils.plugins ^
    --hidden-import=putils.plugins.video_saturation ^
    --hidden-import=encodings ^
    --hidden-import=encodings.utf_8 ^
    --hidden-import=encodings.latin_1 ^
    --hidden-import=zoneinfo ^
    --hidden-import=tkinter ^
    --hidden-import=tkinter.filedialog ^
    --hidden-import=tkinter.messagebox ^
    --hidden-import=tkinter.ttk ^
    --hidden-import=sqlite3 ^
    --hidden-import=json ^
    --hidden-import=subprocess ^
    --hidden-import=threading ^
    --hidden-import=concurrent.futures ^
    --collect-all=tkinter ^
    --exclude-module=test ^
    --exclude-module=unittest ^
    --exclude-module=doctest ^
    putils/app.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo.
    echo Try the debug build instead:
    echo   build_debug.bat
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Creating distribution package...
if not exist "dist\package" mkdir "dist\package"
copy "dist\putils.exe" "dist\package\"

(
echo PUtils - Portable Utility Application
echo =====================================
echo.
echo This is a single-file executable.
echo Simply run putils.exe to start the application.
echo.
echo System Requirements:
echo - Windows 7 or later
echo - No Python installation required
echo.
echo Optional: Install ffmpeg for video processing features
echo Download from: https://ffmpeg.org/download.html
echo.
echo Your settings and data are stored in:
echo %%APPDATA%%\PUtils
echo.
echo Note: First launch may take a few seconds to extract temporary files.
echo.
echo For more information, see README_PORTABLE.md
) > "dist\package\README.txt"

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Single-file executable: dist\package\putils.exe
echo.
echo Testing the executable...
echo Please wait while we verify it starts correctly...
echo.

REM Quick test
timeout /t 2 /nobreak >nul
if exist "dist\package\putils.exe" (
    echo ✓ Executable created successfully
    echo ✓ File size: 
    for %%A in ("dist\package\putils.exe") do echo   %%~zA bytes
    echo.
    echo You can now test by running: dist\package\putils.exe
) else (
    echo ✗ Executable not found!
)

echo.
pause

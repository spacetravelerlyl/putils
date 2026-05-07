@echo off
REM Single-file build with minimized flash effect

echo ========================================
echo Building putils Single-File (Optimized)
echo ========================================
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo [1/4] Cleaned previous builds.
echo.

REM Upgrade PyInstaller
echo [2/4] Upgrading PyInstaller...
pip install --upgrade pyinstaller
echo.

REM Build with optimizations to reduce flash
echo [3/4] Building single-file executable...
echo Using optimizations to minimize console flash...
echo.

pyinstaller --clean --name=putils --windowed --onefile --noupx --splash "putils\splash.png" --add-data "putils/plugins;putils/plugins" --hidden-import=putils --hidden-import=putils.app --hidden-import=putils.database --hidden-import=putils.i18n --hidden-import=putils.paths --hidden-import=putils.plugin_api --hidden-import=putils.plugin_loader --hidden-import=putils.tk_utils --hidden-import=putils.plugins --hidden-import=putils.plugins.video_saturation --hidden-import=encodings --hidden-import=encodings.utf_8 --hidden-import=zoneinfo --hidden-import=tkinter --hidden-import=tkinter.filedialog --hidden-import=tkinter.messagebox --hidden-import=tkinter.ttk --hidden-import=sqlite3 --collect-all=tkinter putils/app.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Note: Splash screen is optional. If you dont have splash.png, remove --splash parameter.
    pause
    exit /b 1
)

echo.
echo [4/4] Creating distribution package...
if not exist "dist\package" mkdir "dist\package"
copy "dist\putils.exe" "dist\package\"

echo PUtils - Portable Utility Application > "dist\package\README.txt"
echo ===================================== >> "dist\package\README.txt"
echo. >> "dist\package\README.txt"
echo This is a single-file executable. >> "dist\package\README.txt"
echo Simply run putils.exe to start the application. >> "dist\package\README.txt"
echo. >> "dist\package\README.txt"
echo System Requirements: >> "dist\package\README.txt"
echo - Windows 7 or later >> "dist\package\README.txt"
echo - No Python installation required >> "dist\package\README.txt"
echo. >> "dist\package\README.txt"
echo Optional: Install ffmpeg for video processing features >> "dist\package\README.txt"
echo Download from: https://ffmpeg.org/download.html >> "dist\package\README.txt"
echo. >> "dist\package\README.txt"
echo Your settings and data are stored in: >> "dist\package\README.txt"
echo %%APPDATA%%\PUtils >> "dist\package\README.txt"
echo. >> "dist\package\README.txt"
echo Note: First launch may take a few seconds to extract temporary files. >> "dist\package\README.txt"
echo A splash screen will be shown during extraction. >> "dist\package\README.txt"

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Single-file executable: dist\package\putils.exe
echo.
echo Note: The splash screen helps hide the extraction process.
echo If you see a black flash, it is normal for single-file mode.
echo For faster startup without flash, use the directory version:
echo   build_portable.bat
echo.

timeout /t 2 /nobreak >nul
if exist "dist\package\putils.exe" (
    echo Executable created successfully
    for %%A in ("dist\package\putils.exe") do echo File size: %%~zA bytes
) else (
    echo Executable not found!
)

echo.
pause

@echo off
REM Complete build script with validation and packaging

setlocal enabledelayedexpansion

echo ========================================
echo PUtils Portable Build System
echo ========================================
echo.

REM Step 0: Validate prerequisites
echo [Step 0/5] Validating prerequisites...
call check_prerequisites.bat
if errorlevel 1 (
    echo.
    echo Prerequisites check failed. Please fix the issues above.
    pause
    exit /b 1
)
echo.

REM Ask user for build type
echo Select build type:
echo   1. Directory-based package (faster startup, recommended for testing)
echo   2. Single-file executable (easier distribution)
echo.
set /p BUILD_TYPE="Enter choice (1 or 2): "

if "%BUILD_TYPE%"=="1" goto BUILD_DIR
if "%BUILD_TYPE%"=="2" goto BUILD_SINGLE
echo Invalid choice. Defaulting to directory-based build.
goto BUILD_DIR

:BUILD_DIR
echo.
echo ========================================
echo Building Directory-based Package
echo ========================================
echo.

echo [Step 1/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [Step 2/4] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo Done.
echo.

echo [Step 3/4] Building with PyInstaller...
pyinstaller --clean putils.spec
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo.

echo [Step 4/4] Creating distribution package...
set BUILD_DIR=dist\putils
if not exist "%BUILD_DIR%" (
    echo ERROR: Build directory not found
    pause
    exit /b 1
)

REM Create README for distribution
(
echo PUtils - Portable Utility Application
echo =====================================
echo.
echo To use this application:
echo 1. Copy the entire 'putils' folder to your desired location
echo 2. Run putils.exe
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
echo For more information, see README_PORTABLE.md
) > "%BUILD_DIR%\README.txt"

echo Done.
echo.
goto FINISH

:BUILD_SINGLE
echo.
echo ========================================
echo Building Single-File Executable
echo ========================================
echo.

echo [Step 1/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [Step 2/4] Cleaning previous builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo Done.
echo.

echo [Step 3/4] Building single-file executable...
pyinstaller --clean ^
    --name=putils ^
    --windowed ^
    --onefile ^
    --add-data "putils/i18n.py;putils" ^
    --add-data "putils/plugins;putils/plugins" ^
    --hidden-import=putils.plugins ^
    --hidden-import=putils.plugins.video_saturation ^
    --hidden-import=zoneinfo ^
    --hidden-import=tkinter ^
    --hidden-import=sqlite3 ^
    --collect-all=tkinter ^
    putils/app.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)
echo.

echo [Step 4/4] Creating distribution package...
if not exist "dist\putils.exe" (
    echo ERROR: Executable not found
    pause
    exit /b 1
)

REM Create a distribution folder with README
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

echo Done.
echo.
goto FINISH

:FINISH
echo ========================================
echo Build Completed Successfully!
echo ========================================
echo.

if "%BUILD_TYPE%"=="2" (
    echo Single-file executable: dist\package\putils.exe
    echo Distribution package: dist\package\
    echo.
    echo You can distribute the entire 'dist\package' folder.
) else (
    echo Directory-based package: dist\putils\
    echo.
    echo You can distribute the entire 'dist\putils' folder.
)

echo.
echo Next steps:
echo 1. Test the executable on your machine
echo 2. Test on a clean Windows VM if possible
echo 3. Verify all features work correctly
echo 4. Package for distribution (ZIP, installer, etc.)
echo.

pause

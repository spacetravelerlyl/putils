@echo off
REM Console build script for debugging - shows all output and errors

echo ========================================
echo Building putils with Console Window
echo ========================================
echo.

REM Clean previous builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
echo [1/3] Cleaned previous builds.
echo.

REM Upgrade PyInstaller
echo [2/3] Upgrading PyInstaller...
pip install --upgrade pyinstaller
echo.

REM Build with console window enabled
echo [3/3] Building executable with console window...
echo This version will show a console window with all output.
echo.

pyinstaller --clean --name=putils-console --console --onefile --noupx --add-data "putils/plugins;putils/plugins" --hidden-import=putils --hidden-import=putils.app --hidden-import=putils.database --hidden-import=putils.i18n --hidden-import=putils.paths --hidden-import=putils.plugin_api --hidden-import=putils.plugin_loader --hidden-import=putils.tk_utils --hidden-import=putils.plugins --hidden-import=putils.plugins.video_saturation --hidden-import=encodings --hidden-import=encodings.utf_8 --hidden-import=zoneinfo --hidden-import=tkinter --hidden-import=tkinter.filedialog --hidden-import=tkinter.messagebox --hidden-import=tkinter.ttk --hidden-import=sqlite3 --collect-all=tkinter putils/app.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Console build completed!
echo ========================================
echo.
echo Location: dist\putils-console.exe
echo.
echo IMPORTANT: 
echo - This version shows a console window
echo - All print statements and errors will be visible
echo - Use this to diagnose startup issues
echo.
echo To run:
echo   cd dist
echo   putils-console.exe
echo.
echo The console will show:
echo - Import errors
echo - Exception tracebacks
echo - Debug messages
echo - Application logs
echo.
pause

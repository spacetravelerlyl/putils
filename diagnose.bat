@echo off
REM Diagnostic script to test the packaged application

echo ========================================
echo PUtils Diagnostic Test
echo ========================================
echo.

if not exist "dist\package\putils.exe" (
    echo ERROR: putils.exe not found in dist\package
    echo Please run build_single_file_fixed.bat first
    pause
    exit /b 1
)

echo [1/4] Testing file existence...
echo Executable: dist\package\putils.exe
for %%A in ("dist\package\putils.exe") do echo Size: %%~zA bytes
echo.

echo [2/4] Checking dependencies...
python -c "import tkinter; print('tkinter: OK')" 2>nul
if errorlevel 1 echo tkinter: MISSING
python -c "import sqlite3; print('sqlite3: OK')" 2>nul
if errorlevel 1 echo sqlite3: MISSING
echo.

echo [3/4] Running with console output...
echo This will show any errors that occur during startup.
echo Press Ctrl+C to stop if it hangs.
echo.
echo Starting application...
timeout /t 2 /nobreak >nul

REM Run and capture output
dist\package\putils.exe > diagnostic_output.txt 2>&1

if errorlevel 1 (
    echo.
    echo ERROR: Application exited with error code %errorlevel%
    echo.
    echo Console output saved to: diagnostic_output.txt
    echo Contents:
    type diagnostic_output.txt
) else (
    echo.
    echo Application started successfully (or is running).
    echo Check if a window appeared.
    echo.
    echo If no window appeared, check diagnostic_output.txt for clues.
    if exist diagnostic_output.txt (
        echo Contents of diagnostic_output.txt:
        type diagnostic_output.txt
    )
)

echo.
echo [4/4] Diagnostic complete.
echo.
echo Next steps:
echo 1. Check if a window appeared
echo 2. Review diagnostic_output.txt for errors
echo 3. Try building with console mode: build_console.bat
echo 4. Run the console version to see real-time errors
echo.
pause

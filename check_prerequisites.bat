@echo off
REM Pre-build validation script

echo ========================================
echo PUtils Build Prerequisites Check
echo ========================================
echo.

set ERRORS=0

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    set /a ERRORS+=1
) else (
    python --version
    echo OK: Python found
)
echo.

REM Check pip
echo [2/5] Checking pip...
pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    set /a ERRORS+=1
) else (
    echo OK: pip found
)
echo.

REM Check PyInstaller
echo [3/5] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo WARNING: PyInstaller not installed (will be installed during build)
) else (
    echo OK: PyInstaller found
)
echo.

REM Check tkinter
echo [4/5] Checking tkinter...
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ERROR: tkinter is not available
    echo Note: On Windows, tkinter should come with Python
    set /a ERRORS+=1
) else (
    echo OK: tkinter found
)
echo.

REM Check sqlite3
echo [5/5] Checking sqlite3...
python -c "import sqlite3" >nul 2>&1
if errorlevel 1 (
    echo ERROR: sqlite3 is not available
    set /a ERRORS+=1
) else (
    echo OK: sqlite3 found
)
echo.

REM Check plugin files
echo Checking plugin files...
if not exist "putils\plugins" (
    echo ERROR: plugins directory not found
    set /a ERRORS+=1
) else (
    echo OK: plugins directory found
)

if not exist "putils\i18n.py" (
    echo ERROR: i18n.py not found
    set /a ERRORS+=1
) else (
    echo OK: i18n.py found
)
echo.

REM Summary
echo ========================================
if %ERRORS% EQU 0 (
    echo All checks passed! Ready to build.
    echo.
    echo You can now run:
    echo   build_portable.bat        (directory-based package)
    echo   build_single_file.bat     (single-file executable)
) else (
    echo Found %ERRORS% error(s). Please fix them before building.
)
echo ========================================
echo.

pause
exit /b %ERRORS%

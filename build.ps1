# PowerShell Build Script for PUtils
# Usage: .\build.ps1 [-BuildType "dir"|"single"]

param(
    [ValidateSet("dir", "single")]
    [string]$BuildType = "dir"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PUtils Portable Build System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "[1/5] Checking Python..." -NoNewline
    try {
        $pythonVersion = python --version 2>&1
        Write-Host " OK" -ForegroundColor Green
        Write-Host "       $pythonVersion"
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        throw "Python is not installed or not in PATH"
    }

    Write-Host "[2/5] Checking pip..." -NoNewline
    try {
        pip --version | Out-Null
        Write-Host " OK" -ForegroundColor Green
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        throw "pip is not available"
    }

    Write-Host "[3/5] Checking tkinter..." -NoNewline
    try {
        python -c "import tkinter" 2>&1 | Out-Null
        Write-Host " OK" -ForegroundColor Green
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        throw "tkinter is not available"
    }

    Write-Host "[4/5] Checking sqlite3..." -NoNewline
    try {
        python -c "import sqlite3" 2>&1 | Out-Null
        Write-Host " OK" -ForegroundColor Green
    } catch {
        Write-Host " FAILED" -ForegroundColor Red
        throw "sqlite3 is not available"
    }

    Write-Host "[5/5] Checking source files..." -NoNewline
    if (-not (Test-Path "putils\plugins")) {
        Write-Host " FAILED" -ForegroundColor Red
        throw "plugins directory not found"
    }
    if (-not (Test-Path "putils\i18n.py")) {
        Write-Host " FAILED" -ForegroundColor Red
        throw "i18n.py not found"
    }
    Write-Host " OK" -ForegroundColor Green
    Write-Host ""
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install dependencies"
    }
    Write-Host ""
}

# Function to clean builds
function Clean-Builds {
    Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    Get-ChildItem -Filter "*.spec.backup" | Remove-Item -Force
    Write-Host "Done." -ForegroundColor Green
    Write-Host ""
}

# Function to build directory package
function Build-DirectoryPackage {
    Write-Host "Building directory-based package..." -ForegroundColor Cyan
    
    Clean-Builds
    
    Write-Host "Running PyInstaller..." -ForegroundColor Yellow
    pyinstaller --clean putils.spec
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }
    
    $buildDir = "dist\putils"
    if (-not (Test-Path $buildDir)) {
        throw "Build directory not found"
    }
    
    # Create README
    $readmeContent = @"
PUtils - Portable Utility Application
=====================================

To use this application:
1. Copy the entire 'putils' folder to your desired location
2. Run putils.exe

System Requirements:
- Windows 7 or later
- No Python installation required

Optional: Install ffmpeg for video processing features
Download from: https://ffmpeg.org/download.html

Your settings and data are stored in:
%APPDATA%\PUtils

For more information, see README_PORTABLE.md
"@
    $readmeContent | Out-File -FilePath "$buildDir\README.txt" -Encoding UTF8
    
    Write-Host ""
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Location: dist\putils\" -ForegroundColor Cyan
    Write-Host ""
}

# Function to build single-file executable
function Build-SingleFile {
    Write-Host "Building single-file executable..." -ForegroundColor Cyan
    
    Clean-Builds
    
    Write-Host "Running PyInstaller..." -ForegroundColor Yellow
    $pyinstallerArgs = @(
        "--clean",
        "--name=putils",
        "--windowed",
        "--onefile",
        "--add-data", "putils/i18n.py;putils",
        "--add-data", "putils/plugins;putils/plugins",
        "--hidden-import=putils.plugins",
        "--hidden-import=putils.plugins.video_saturation",
        "--hidden-import=zoneinfo",
        "--hidden-import=tkinter",
        "--hidden-import=sqlite3",
        "--collect-all=tkinter",
        "putils/app.py"
    )
    
    & pyinstaller $pyinstallerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }
    
    if (-not (Test-Path "dist\putils.exe")) {
        throw "Executable not found"
    }
    
    # Create distribution package
    New-Item -ItemType Directory -Force -Path "dist\package" | Out-Null
    Copy-Item "dist\putils.exe" "dist\package\"
    
    $readmeContent = @"
PUtils - Portable Utility Application
=====================================

This is a single-file executable.
Simply run putils.exe to start the application.

System Requirements:
- Windows 7 or later
- No Python installation required

Optional: Install ffmpeg for video processing features
Download from: https://ffmpeg.org/download.html

Your settings and data are stored in:
%APPDATA%\PUtils

Note: First launch may take a few seconds to extract temporary files.

For more information, see README_PORTABLE.md
"@
    $readmeContent | Out-File -FilePath "dist\package\README.txt" -Encoding UTF8
    
    Write-Host ""
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Location: dist\package\putils.exe" -ForegroundColor Cyan
    Write-Host ""
}

# Main execution
try {
    Test-Prerequisites
    Install-Dependencies
    
    if ($BuildType -eq "single") {
        Build-SingleFile
    } else {
        Build-DirectoryPackage
    }
    
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Test the executable" -ForegroundColor White
    Write-Host "2. Verify all features work correctly" -ForegroundColor White
    Write-Host "3. Package for distribution (ZIP, etc.)" -ForegroundColor White
    Write-Host "========================================" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    exit 1
}

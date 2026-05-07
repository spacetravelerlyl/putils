# PUtils - Portable Utility Application

## Quick Start for End Users

### Running the Application

**If you received a folder:**
1. Copy the entire `putils` folder to your desired location (e.g., `C:\Programs\putils`)
2. Double-click `putils.exe` to launch

**If you received a single .exe file:**
1. Copy `putils.exe` to your desired location
2. Double-click to launch
3. First launch may take a few seconds

### System Requirements

- Windows 7 or later (64-bit recommended)
- No Python installation required
- **Optional:** ffmpeg for video processing features

### Data Storage

Your settings, logs, and cache are automatically saved to:
```
C:\Users\[YourUsername]\AppData\Roaming\PUtils
```

This means:
- Your settings persist between application launches
- You can update the application without losing data
- Multiple users on the same machine have separate settings

### Changing Data Location

If you want to store data in a different location:
1. Open Settings tab in the application
2. Change the "Data Directory" path
3. Click "Save Settings"
4. Optionally click "Migrate" to move existing data

### Video Processing Features

To use video saturation adjustment:
1. Install ffmpeg from https://ffmpeg.org/download.html
2. Add ffmpeg to your system PATH, or place it in the same folder as putils.exe
3. Restart putils

### Troubleshooting

**Application won't start:**
- Ensure you're using Windows 7 or later
- Try running as Administrator
- Check Windows Event Viewer for error details

**Video features not working:**
- Verify ffmpeg is installed: Open Command Prompt and type `ffmpeg -version`
- Ensure ffmpeg is in your system PATH

**Settings not saving:**
- Check that you have write permissions to the AppData folder
- Try running as Administrator once to create initial files

## For Developers

See [Packaging Documentation](../packaging/cross-platform-packaging.md) for build instructions.

Related documentation:
- [Cross-Platform Packaging Guide](../packaging/cross-platform-packaging.md)
- [Windows Packaging Guide](../packaging/windows-packaging.md)
- [Quick Start](../packaging/quick-start.md)

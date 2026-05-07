# PUtils - Portable Utility Application (Linux)

## Quick Start for Linux Users

### Running the Application

**If you received a folder:**
```bash
# Navigate to the application directory
cd putils

# Make the executable runnable
chmod +x putils

# Run the application
./putils
```

**If you received a single file:**
```bash
# Make it executable
chmod +x putils

# Run the application
./putils
```

### System Requirements

- **Distribution**: Ubuntu 18.04+, Fedora 28+, or equivalent
- **Display Server**: X11 or Wayland
- **No Python installation required**
- **Architecture**: x86_64 (64-bit)

### Installing Required Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3-tk ffmpeg
```

#### Fedora
```bash
sudo dnf install python3-tkinter ffmpeg
```

#### Arch Linux
```bash
sudo pacman -S tk ffmpeg
```

### Data Storage

Your settings, logs, and cache are automatically saved to:
```
~/.local/share/putils/
├── config.sqlite3    # Configuration database
├── logs.sqlite3      # Log database
└── cache.sqlite3     # Cache database
```

This follows the XDG Base Directory Specification.

### Changing Data Location

Set the `PUTILS_DATA_DIR` environment variable before launching:

```bash
export PUTILS_DATA_DIR=/path/to/custom/data/dir
./putils
```

Or permanently in your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
echo 'export PUTILS_DATA_DIR=/path/to/custom/data/dir' >> ~/.bashrc
source ~/.bashrc
```

### Video Processing Features

To use video saturation adjustment, install ffmpeg:

```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg

# Verify installation
ffmpeg -version
```

### Troubleshooting

**Application won't start:**
- Ensure you have execute permissions: `chmod +x putils`
- Check if display server is running: `echo $DISPLAY` or `echo $WAYLAND_DISPLAY`
- Verify tkinter is installed: `python3 -c "import tkinter"`

**Chinese characters display as squares:**
Install Chinese fonts:
```bash
# Ubuntu/Debian
sudo apt install fonts-wqy-zenith fonts-wqy-microhei

# Fedora
sudo dnf install wqy-zenhei-fonts wqy-microhei-fonts
```

**Settings not saving:**
- Check write permissions to `~/.local/share/putils`
- Ensure the directory exists: `mkdir -p ~/.local/share/putils`

**Video features not working:**
- Verify ffmpeg is installed: `ffmpeg -version`
- Check if ffmpeg is in PATH: `which ffmpeg`

### Distribution-Specific Notes

#### Ubuntu/Debian
- Works out of the box with standard installation
- May need to install `python3-tk` separately

#### Fedora
- Ensure RPM Fusion repository is enabled for ffmpeg
- Use `dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm`

#### Arch Linux
- All dependencies available in official repositories
- Consider using AUR helpers for additional codecs

#### openSUSE
```bash
sudo zypper install python3-tk ffmpeg
```

### Creating Desktop Entry (Optional)

Create `~/.local/share/applications/putils.desktop`:

```ini
[Desktop Entry]
Name=PUtils
Comment=Portable Utility Application
Exec=/path/to/putils/putils
Icon=/path/to/putils/icon.png
Terminal=false
Type=Application
Categories=Utility;
```

Then make it executable:
```bash
chmod +x ~/.local/share/applications/putils.desktop
```

### Building from Source

If you want to build from source:

```bash
# Install dependencies
sudo apt install python3 python3-pip python3-tk pyinstaller

# Clone repository
git clone <repository-url>
cd putils

# Install Python dependencies
pip3 install -r requirements.txt

# Build
./build_linux_interactive.sh
```

### Uninstalling

Simply delete the application folder and data:

```bash
# Remove application
rm -rf /path/to/putils

# Remove user data (optional)
rm -rf ~/.local/share/putils
```

## For Developers

See [Cross-Platform Packaging Guide](../packaging/cross-platform-packaging.md) for detailed build instructions.

Related documentation:
- [Linux Build Scripts](../../build_linux_interactive.sh)
- [Packaging Quick Start](../packaging/quick-start.md)
- [Technical Details](../packaging/technical-details.md)

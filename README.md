# PUtils

PUtils is a cross-platform desktop utility host with plugin-based extensions.

## 🌟 Features

- **Cross-Platform**: Works on Windows and Linux
- **Plugin System**: Extensible architecture
- **Portable**: No Python installation required (when packaged)
- **Internationalization**: Multi-language support
- **Logging**: Built-in log management

## 📦 Current Plugins

- **Video Saturation Adjustment**: Batch-adjust video saturation using `ffmpeg`

## 🚀 Quick Start

### For End Users (Packaged Version)

#### Windows
1. Download `putils-vX.X.X-windows.zip`
2. Extract to desired location
3. Run `putils.exe`

#### Linux
```bash
# Download and extract
tar -xzf putils-vX.X.X-linux.tar.gz
cd putils

# Make executable and run
chmod +x putils
./putils
```

### For Developers (From Source)

```bash
# Clone repository
git clone <repository-url>
cd putils

# Install dependencies
pip install -r requirements.txt

# Run application
python -m putils.app
```

## 📚 Documentation

All documentation is organized in the [`docs/`](docs/) directory:

### User Guides
- **[Windows User Guide](docs/user-guides/windows-user-guide.md)** - Complete Windows usage guide
- **[Linux User Guide](docs/user-guides/linux-user-guide.md)** - Complete Linux usage guide
- **[General User Guide](docs/user-guide.md)** - Feature overview and basic usage

### Packaging Guides
- **[Quick Start](docs/packaging/quick-start.md)** - Get started with packaging in 5 minutes
- **[Cross-Platform Packaging](docs/packaging/cross-platform-packaging.md)** - ⭐ Complete Windows + Linux packaging tutorial
- **[Windows Packaging](docs/packaging/windows-packaging.md)** - Windows-specific packaging guide
- **[Quick Reference](docs/packaging/quick-reference.md)** - Commands and troubleshooting cheat sheet
- **[Technical Details](docs/packaging/technical-details.md)** - PyInstaller configuration details

### Development
- **[Developer Guide](docs/development.md)** - Plugin development and architecture
- **[Documentation Index](docs/README.md)** - Complete documentation navigation

## 🔧 Building Portable Executables

### Windows
```batch
# Interactive build (recommended)
build.bat

# Or quick builds
build_portable.bat          # Directory-based
build_single_file.bat       # Single executable
```

### Linux
```bash
# Interactive build (recommended)
chmod +x build_linux_interactive.sh
./build_linux_interactive.sh

# Or quick builds
chmod +x build_linux.sh
./build_linux.sh            # Directory-based

chmod +x build_linux_single.sh
./build_linux_single.sh     # Single executable
```

See [Cross-Platform Packaging Guide](docs/packaging/cross-platform-packaging.md) for detailed instructions.

## 💻 System Requirements

### Windows
- Windows 7 SP1 or later
- x86_64 (64-bit) recommended

### Linux
- Ubuntu 18.04+ / Fedora 28+ or equivalent
- X11 or Wayland display server
- x86_64 (64-bit)

### Optional Dependencies
- **ffmpeg**: Required for video processing features
  - Windows: Download from https://ffmpeg.org/download.html
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Fedora: `sudo dnf install ffmpeg`
  - Arch: `sudo pacman -S ffmpeg`

## 📁 Project Structure

```
putils/
├── putils/                 # Main application package
│   ├── app.py             # Main application
│   ├── plugins/           # Plugin directory
│   │   └── video_saturation.py
│   ├── database.py        # Database management
│   ├── i18n.py           # Internationalization
│   ├── paths.py          # Path utilities
│   └── ...
├── docs/                   # Documentation
│   ├── packaging/         # Packaging guides
│   ├── user-guides/       # User manuals
│   ├── development.md     # Developer guide
│   └── README.md          # Documentation index
├── build.bat              # Windows build scripts
├── build_linux.sh         # Linux build scripts
├── putils.spec            # PyInstaller configuration
└── README.md              # This file
```

## 🤝 Contributing

Contributions are welcome! Please read the [Developer Guide](docs/development.md) first.

## 📄 License

[Add your license information here]

## 🙏 Acknowledgments

- **PyInstaller**: For creating portable executables
- **tkinter**: For the GUI framework
- **ffmpeg**: For video processing capabilities
- All contributors and plugin developers

---

**Download Latest Release**: [GitHub Releases](link-to-releases)  
**Report Issues**: [GitHub Issues](link-to-issues)  
**Browse Documentation**: [docs/README.md](docs/README.md)

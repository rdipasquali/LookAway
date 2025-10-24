# LookAway Linux Installer

This directory contains the complete Linux build system for LookAway, providing cross-platform installer creation capabilities.

## Files Overview

### Core Linux Build Scripts
- **`installer_wizard_linux.py`** - Complete GUI installer for Linux systems
- **`build_linux_app.py`** - Builds the main LookAway executable for Linux
- **`create_linux_installer.py`** - Creates installer with embedded files
- **`build_linux_complete.py`** - Complete Linux build process
- **`build_cross_platform.py`** - Unified build script for Windows and Linux

### Test and Utility Scripts
- **`test_linux_build.py`** - Tests Linux build system on Windows (validation)

## Linux System Requirements

### Build Requirements
- Python 3.7+ with pip
- PyInstaller (`pip install pyinstaller`)
- tkinter (`python3-tk` package)
- Standard Linux development tools

### Runtime Requirements (for end users)
- Linux with X11 or Wayland display server
- tkinter support (`python3-tk`)
- Desktop notification support (`libnotify-bin`)
- System tray support (varies by desktop environment)

## Supported Linux Distributions

### Tested Compatibility
The installer is designed to work on:
- **Ubuntu 18.04+** / **Debian 9+**
- **Fedora 30+** / **CentOS 8+** 
- **Arch Linux** (current)
- **openSUSE Leap 15+**
- **Linux Mint 19+**

### Desktop Environment Support
- **GNOME** (3.28+) - with extensions for system tray
- **KDE Plasma** (5.12+) - full system tray support
- **XFCE** (4.14+) - native system tray
- **MATE** (1.20+) - native system tray
- **Cinnamon** (4.0+) - native system tray
- **Other window managers** - basic functionality

## Building on Linux

### Quick Build (Recommended)
```bash
# Build everything
python build_linux_complete.py

# Or use cross-platform script
python build_cross_platform.py
```

### Step-by-Step Build
```bash
# 1. Build main application
python build_linux_app.py

# 2. Create installer with embedded files  
python create_linux_installer.py

# 3. Build installer executable
python -m PyInstaller --onefile --name=lookaway-installer-linux linux_installer_with_files.py
```

### Install Dependencies (Ubuntu/Debian)
```bash
# Required packages
sudo apt-get update
sudo apt-get install python3 python3-pip python3-tk libnotify-bin

# Optional (for system tray on GNOME)
sudo apt-get install gnome-shell-extensions

# Install Python dependencies
pip3 install -r requirements.txt
```

### Install Dependencies (Fedora)
```bash
# Required packages  
sudo dnf install python3 python3-pip tkinter libnotify

# Install Python dependencies
pip3 install -r requirements.txt
```

### Install Dependencies (Arch Linux)
```bash
# Required packages
sudo pacman -S python python-pip tk libnotify

# Install Python dependencies  
pip install -r requirements.txt
```

## Linux Installer Features

### Installation Process
1. **Welcome & License** - Shows license agreement
2. **Directory Selection** - Choose install location (default: `~/.local/share/LookAway`)
3. **Notification Setup** - Configure desktop/email/Telegram notifications
4. **Email Configuration** - SMTP setup with provider presets
5. **Telegram Configuration** - Bot token and chat ID setup
6. **System Integration** - Desktop entry and autostart configuration
7. **File Installation** - Extract and install all files
8. **Completion** - Launch options and uninstaller creation

### Desktop Integration
- **Application Menu Entry** - Creates `~/.local/share/applications/lookaway.desktop`
- **Autostart Entry** - Creates `~/.config/autostart/lookaway.desktop`
- **Icon Installation** - Installs application icon
- **Uninstaller** - Creates `uninstall.sh` script

### Configuration Management
- **Settings Storage** - `~/.config/LookAway/settings.json`
- **Log Files** - `~/.local/share/LookAway/logs/`
- **Follows XDG Standards** - Respects Linux filesystem hierarchy

## Distribution

### Final Output Files
After successful build:
- **`dist/lookaway`** - Standalone application (~17MB)
- **`dist/lookaway-installer-linux`** - Complete installer (~29MB)

### Distribution Instructions
1. Test the installer on target Linux distributions
2. Provide installation instructions for dependencies
3. Consider packaging for distribution-specific package managers

### Package Manager Integration (Future)
The installer could be adapted for:
- **DEB packages** (Ubuntu/Debian)
- **RPM packages** (Fedora/RHEL)
- **AUR packages** (Arch Linux)
- **Snap packages** (Universal)
- **Flatpak** (Universal)
- **AppImage** (Portable)

## Troubleshooting

### Common Build Issues

**PyInstaller not found:**
```bash
pip install pyinstaller
```

**tkinter import error:**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# Fedora  
sudo dnf install tkinter

# Arch
sudo pacman -S tk
```

**Missing desktop notifications:**
```bash
# Ubuntu/Debian
sudo apt-get install libnotify-bin

# Test notifications
notify-send "Test" "Desktop notifications working"
```

### Common Runtime Issues

**No system tray icon:**
- Install desktop environment extensions
- Use console mode: `./lookaway --no-tray`

**Permission denied:**
```bash
chmod +x lookaway
chmod +x lookaway-installer-linux
```

**Missing dependencies:**
- Run installer dependency check
- Install system packages as shown above

## Development Notes

### Cross-Platform Compatibility
The Linux build system is designed to work alongside the Windows build system:
- Shared configuration format
- Similar UI/UX design
- Compatible file formats
- Unified build scripts

### Testing on Windows
While the main build must happen on Linux, basic testing can be done on Windows:
```bash
python test_linux_build.py
```

This validates:
- Script syntax and imports
- Basic class functionality  
- File structure completeness
- Cross-platform compatibility

### Future Enhancements
- **Wayland native support** - Currently uses X11 compatibility
- **Package manager integration** - Native .deb/.rpm creation
- **Multiple architectures** - ARM64, RISC-V support
- **Containerized builds** - Docker-based cross-compilation
- **CI/CD integration** - Automated Linux builds

## Support

### Linux-Specific Issues
- Check desktop environment compatibility
- Verify system tray support
- Test notification system
- Review file permissions

### Getting Help
1. Check system requirements above
2. Run dependency installation commands
3. Test with `./lookaway --help` 
4. Check logs in `~/.local/share/LookAway/logs/`

For more information, see the main README.md file.
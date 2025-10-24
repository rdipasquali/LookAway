# LookAway Standalone Installer

This directory contains all the components needed to create a standalone Windows installer for LookAway that works on any Windows PC without requiring Python or any development dependencies.

## Files Overview

### Core Installer Components
- **`installer_wizard.py`** - Main GUI installation wizard with all screens (license, path selection, configuration, email/telegram setup, etc.)
- **`create_installer.py`** - Embeds the main application and all dependencies into the installer
- **`build_app.py`** - Builds the main LookAway.exe application
- **`build_complete.py`** - Complete build script that creates both app and installer

### Supporting Files
- **`installer.manifest`** - Windows manifest for admin privileges
- **`requirements.txt`** - Dependencies needed to build the installer
- **`README.md`** - This documentation file

## Features

### Installation Wizard
- ✅ Welcome screen with application information
- ✅ License agreement with scrollable text
- ✅ Installation path selection with browse dialog
- ✅ Initial configuration (reminder intervals, sleep hours, notifications)
- ✅ Installation options (shortcuts, startup, launch after install)
- ✅ Progress tracking during installation
- ✅ Completion screen with launch option

### System Integration
- ✅ Desktop shortcut creation (with fallback methods)
- ✅ Start Menu entry
- ✅ Windows startup registry entry (optional)
- ✅ Windows Programs & Features registration
- ✅ Uninstaller creation

### Standalone Features
- ✅ No Python runtime required on target system
- ✅ All dependencies bundled in single executable
- ✅ Application files embedded and extracted during installation
- ✅ Works on clean Windows systems

## Building the Installer

### Prerequisites

On your development system, you need:
```bash
pip install PyInstaller
pip install pywin32  # Optional, for enhanced shortcut creation
```

### Quick Build

1. **Build everything (recommended):**
   ```bash
   cd installer
   python build_complete.py
   ```

2. **Or build components separately:**
   ```bash
   cd installer
   python build_app.py          # Build LookAway.exe
   python create_installer.py   # Create installer with embedded files
   # Then build with PyInstaller
   ```

3. **Find your installer:**
   - The final installer will be in `../dist/LookAway-Installer.exe`
   - A complete installation package will be in `../dist/LookAway-Installation-Package/`

### Build Process Details

The build script performs these steps:

1. **Builds Main Application**
   - Uses PyInstaller to create `LookAway.exe` with all Python dependencies
   - Bundles all source files, configuration, and assets

2. **Embeds Resources**
   - Compresses and base64-encodes all application files
   - Embeds them directly into the installer source code

3. **Creates Standalone Installer**
   - Uses PyInstaller to create `LookAway-Installer.exe`
   - Results in a single executable that needs no external dependencies

4. **Creates Installation Package**
   - Includes installer, documentation, and instructions
   - Ready for distribution

## Testing

### Local Testing
```bash
cd installer
python test_installer.py
```

### Full Installation Testing
1. Build the installer as described above
2. Copy `LookAway-Installer.exe` to a clean Windows system (virtual machine recommended)
3. Run the installer and verify:
   - All installation steps work
   - Application launches correctly
   - Shortcuts are created
   - Uninstaller works

## Distribution

The generated `LookAway-Installer.exe` is completely self-contained:
- ✅ No Python runtime required
- ✅ No additional DLLs needed  
- ✅ No registry dependencies
- ✅ Works on Windows 10 and later
- ✅ Digital signing ready (add certificates as needed)

## Troubleshooting

### Common Build Issues

**PyInstaller not found:**
```bash
pip install PyInstaller
```

**Missing modules during build:**
- Check `hiddenimports` in the PyInstaller spec files
- Add missing modules to the imports list

**Installer too large:**
- The installer includes the full Python runtime and all dependencies
- Expected size: 30-50 MB (this is normal for standalone installers)

**Shortcuts not working:**
- The installer has fallback methods for shortcut creation
- If `.lnk` files fail, it creates `.bat` and `.ps1` alternatives

### Runtime Issues

**Installer won't start on target system:**
- Ensure target system is Windows 10 or later
- Check if antivirus is blocking the unsigned executable
- Try running as administrator

**Installation fails:**
- Check if user has write permissions to selected directory
- Verify enough disk space (requires ~50 MB)
- Check if any files are locked by running processes

## Customization

### Changing Application Files
Edit `resource_embedder.py` to modify which files are embedded:
```python
# Add custom files
embedder.embed_file('path/to/custom/file.txt', 'destination/file.txt')

# Exclude patterns
exclude_patterns = ['*.log', 'temp/*', 'cache/*']
```

### Modifying Installation Steps
Edit `installer_wizard.py` to customize:
- License text (see `get_license_text()`)
- Default installation path
- Configuration options
- Installation steps

### Custom Branding
- Replace icon: Add `icon='path/to/icon.ico'` in PyInstaller specs
- Modify window titles and text in `installer_wizard.py`
- Add custom images to the `assets/` directory

## Architecture

```
LookAway Project/
├── main.py                    # Main application
├── src/                       # Application source
├── config/                    # Configuration files
├── installer/                 # Installer components
│   ├── installer_wizard.py    # GUI wizard
│   ├── resource_embedder.py   # File embedding
│   ├── build_standalone_installer.py  # Build script
│   └── assets/               # Installer assets
└── dist/                     # Built files
    ├── LookAway.exe          # Main application (built)
    ├── LookAway-Installer.exe  # Standalone installer
    └── LookAway-Installation-Package/  # Distribution package
```

## Security Considerations

- The installer is unsigned by default
- Windows SmartScreen may warn users about unsigned executables
- For production distribution, consider code signing with a valid certificate
- The installer requires administrator privileges for system-wide installation

## License

The installer framework is part of the LookAway project and follows the same MIT license terms.
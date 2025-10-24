# LookAway - Eye Break Reminder

A cross-platform Python application that sends periodic reminders to take breaks from screen time to protect your eye health.\
Disclaimer: this is a personal test for "vibe coding". Apart from the starting idea, language, features and this row all is written by GitHub Copilot in Agent mode with Claude Sonnet 4.

## Features

- 🔔 **Multiple Notification Methods**: Desktop notifications, email, and Telegram
- ⏰ **Customizable Intervals**: Set reminder frequency (default: 20 minutes)
- 😴 **Sleep Hours Awareness**: Automatically pause during configured sleep hours
- 🎯 **Smart Break Types**: Quick eye breaks (20 seconds) and longer breaks (5 minutes)
- ⏸️ **Snooze & Pause**: Temporary postpone reminders or pause indefinitely
- 🔕 **Do Not Disturb**: Quick toggle for presentations or focused work
- 🖥️ **System Tray Integration**: Runs quietly in the background
- 🚀 **Auto-start Support**: Configure to start with Windows/Linux boot
- ⚙️ **Interactive Setup**: Easy configuration wizard for first-time setup

## Installation

### Prerequisites

- Python 3.7 or higher
- Internet connection (for email/Telegram notifications)

### Quick Install

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/yourusername/LookAway.git
   cd LookAway
   ```

2. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the setup wizard:**
   ```bash
   python main.py setup
   ```

4. **Start the application:**
   ```bash
   python main.py start
   ```

### Alternative Installation with Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv lookaway-env

# Activate virtual environment
# On Windows:
lookaway-env\Scripts\activate
# On Linux/Mac:
source lookaway-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run setup
python main.py setup
```

## Configuration

### First Run Setup

The application will automatically launch a setup wizard on first run that will guide you through:

1. **Reminder Interval**: How often to receive reminders (1-480 minutes)
2. **Notification Methods**: Choose from desktop, email, and/or Telegram
3. **Sleep Hours**: Set quiet hours to avoid nighttime reminders
4. **Advanced Settings**: Long break intervals, custom messages, etc.

### Notification Setup

#### Desktop Notifications
- **Windows**: Uses native Windows toast notifications
- **Linux**: Uses libnotify (install with `sudo apt-get install libnotify-bin`)
- **Enabled by default** - no additional configuration needed

#### Email Notifications
You'll need to provide:
- SMTP server (e.g., `smtp.gmail.com`)
- Port (usually `587` for TLS)
- Your email address
- App password (recommended) or regular password
- Recipient email address

**Gmail Users**: Use an [App Password](https://myaccount.google.com/apppasswords) instead of your regular password.

#### Telegram Notifications
1. Create a bot by messaging [@BotFather](https://t.me/botfather) on Telegram
2. Get your bot token from BotFather
3. Start a chat with your bot
4. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

### Configuration File

Settings are stored in `config/settings.json`. You can edit this file directly or use the setup wizard:

```bash
python main.py setup --force
```

## Usage

### Command Line Interface

```bash
# Start the application (default: with system tray)
python main.py start

# Start in console mode (no system tray)
python main.py start --no-tray

# Run setup wizard
python main.py setup

# Force reconfiguration
python main.py setup --force

# Show current status
python main.py status
```

### System Tray (Default Mode)

When running with system tray, right-click the tray icon for options:
- **Status**: View current application status
- **Snooze 5 min**: Postpone next reminder
- **Pause/Resume**: Toggle reminder pause
- **Do Not Disturb**: Toggle DND mode
- **Test Notifications**: Send test messages
- **Reload Config**: Reload configuration file
- **Exit**: Stop the application

### Console Mode

In console mode, you can use these commands:
- `status` - Show current status
- `pause` - Pause reminders
- `resume` - Resume reminders
- `snooze` - Snooze next reminder (specify minutes)
- `dnd` - Toggle Do Not Disturb
- `test` - Test all notification methods
- `quit` - Exit application

## Auto-Start Setup

### Windows

Run the provided script to add LookAway to Windows startup:

```bash
scripts\install_windows_startup.bat
```

To remove from startup:
```bash
scripts\uninstall_windows_startup.bat
```

### Linux

Run the provided script to add LookAway to system startup:

```bash
chmod +x scripts/install_linux_startup.sh
./scripts/install_linux_startup.sh
```

The script will automatically choose the best method for your system:
- **systemd** (recommended): Creates a user service
- **Desktop autostart**: Creates a `.desktop` file in autostart directory
- **Init script**: Creates a system service (requires sudo)

## Break Recommendations

LookAway follows the **20-20-20 rule** and other eye health best practices:

### Quick Breaks (Default: Every 20 minutes)
- Look at something 20+ feet away for 20 seconds
- Blink several times to moisten eyes
- Look around the room or out a window

### Long Breaks (Default: Every 3rd reminder)
- Step away from the computer for 5 minutes
- Walk around or stretch
- Get some fresh air if possible
- Hydrate

### Custom Messages

You can add custom reminder messages during setup or by editing the configuration file. Messages are randomly selected for each reminder.

## Troubleshooting

### Common Issues

1. **Desktop notifications not working on Linux:**
   ```bash
   sudo apt-get install libnotify-bin
   ```

2. **Email notifications failing:**
   - Check SMTP settings
   - Use app passwords for Gmail/Outlook
   - Verify firewall/antivirus isn't blocking connections

3. **Telegram notifications not working:**
   - Verify bot token is correct
   - Ensure you've started a conversation with your bot
   - Check chat ID format (should be numeric)

4. **System tray not appearing:**
   - Try running in console mode: `python main.py start --no-tray`
   - Install system tray dependencies

### Logging

Application logs are stored in the `logs/` directory:
- `lookaway.log` - Main application log
- Check for error messages and troubleshooting information

### Reset Configuration

To reset all settings:

1. Stop the application
2. Delete the `config/settings.json` file
3. Restart the application (setup wizard will run)

## Creating Windows Installer

### Building the Installer Executable

LookAway includes a comprehensive build system to create a professional Windows installer that embeds all necessary files and provides a user-friendly setup experience.

#### Prerequisites for Building

1. **Python Environment**: Ensure you have the virtual environment set up:
   ```bash
   # Activate virtual environment
   .venv\Scripts\activate
   
   # Install all dependencies
   pip install -r requirements.txt
   ```

2. **PyInstaller**: The build system uses PyInstaller (automatically installed):
   ```bash
   pip install pyinstaller
   ```

#### Build Methods

##### Method 1: Complete Build (Recommended)

Build both the main application and installer in one step:

```bash
cd installer
python build_complete.py
```

This creates:
- `dist\LookAway.exe` - Standalone application (17+ MB)
- `dist\LookAway-Installer.exe` - Complete installer with setup wizard (29+ MB)

##### Method 2: Step-by-Step Build

1. **Build the main application:**
   ```bash
   cd installer
   python build_app.py
   ```

2. **Create installer with embedded files:**
   ```bash
   python create_installer.py
   ```

3. **Build installer executable:**
   ```bash
   python -m PyInstaller --onefile --windowed --name=LookAway-Installer installer_wizard.py
   ```

#### Installer Features

The created installer (`LookAway-Installer.exe`) includes:

- **Embedded Files**: Contains the complete LookAway.exe and all configuration files
- **Installation Wizard**: Step-by-step GUI setup process
- **Email Configuration**: Interactive email settings with validation
- **Telegram Setup**: Complete Telegram bot configuration walkthrough
- **Auto-start Setup**: Optional Windows startup integration
- **License Display**: Shows the actual LICENSE file content
- **Installation Path Selection**: Choose custom installation directory
- **Uninstaller Creation**: Automatic uninstaller generation

#### Build Configuration

The build system includes several configuration files in the `installer/` directory:

```
installer/
├── build_app.py              # Builds main LookAway.exe
├── build_complete.py         # Complete build process
├── create_installer.py       # Creates installer with embedded files
├── installer_wizard.py       # GUI installation wizard
├── requirements.txt          # Installer-specific dependencies
└── README.md                # Build system documentation
```

#### Advanced Build Options

##### Custom PyInstaller Options

The build system uses optimized PyInstaller settings:

```bash
# Main application build
python -m PyInstaller \
    --onefile \
    --windowed \
    --name=LookAway \
    --hidden-import=plyer \
    --hidden-import=pystray \
    --hidden-import=telegram \
    --collect-all=plyer \
    --collect-all=telegram \
    --add-data=src;src \
    --add-data=config;config \
    main.py
```

##### Installer Customization

Edit `installer_wizard.py` to customize:
- Installation steps and pages
- Email/Telegram configuration UI
- Installation directory defaults
- Auto-start behavior
- License text display

#### Distribution

The final installer is completely self-contained and can be distributed without dependencies:

1. **Share `LookAway-Installer.exe`** - Users run this to install LookAway
2. **Alternative: Share `LookAway.exe`** - Direct executable (requires manual configuration)

#### Troubleshooting Build Issues

**Common Build Problems:**

1. **Unicode Character Errors:**
   ```
   UnicodeEncodeError: 'charmap' codec can't encode character
   ```
   - Fixed in build scripts by removing Unicode symbols
   - Use ASCII-compatible characters only

2. **Missing Dependencies:**
   ```
   ModuleNotFoundError: No module named 'plyer'
   ```
   - Ensure virtual environment is activated
   - Run: `pip install -r requirements.txt`

3. **PyInstaller Import Errors:**
   - Build scripts include comprehensive `--hidden-import` flags
   - All required modules are explicitly included

**Build Verification:**

Test the built executable:
```bash
cd dist
.\LookAway.exe --help           # Test main application
.\LookAway-Installer.exe       # Test installer GUI
```

#### Size Optimization

Current build sizes:
- **LookAway.exe**: ~17.4 MB (includes all Python dependencies)
- **LookAway-Installer.exe**: ~29.6 MB (includes LookAway.exe + installer GUI)

The installer uses gzip compression for embedded files to minimize size.

## Development

### Project Structure

```
LookAway/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── src/
│   ├── config_manager.py   # Configuration management
│   ├── notifications.py    # Notification handlers
│   ├── scheduler.py        # Main reminder scheduler
│   └── setup.py           # Setup wizard
├── scripts/
│   ├── install_windows_startup.bat
│   ├── uninstall_windows_startup.bat
│   └── install_linux_startup.sh
├── config/                 # Configuration files (created on first run)
├── logs/                   # Application logs (created on first run)
└── README.md
```

### Adding New Features

The application is designed to be extensible:

1. **New notification methods**: Add handlers in `src/notifications.py`
2. **Custom break types**: Modify break configuration in `config_manager.py`
3. **Additional scheduling options**: Extend the scheduler in `src/scheduler.py`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on both Windows and Linux if possible
5. Submit a pull request

## Requirements

### Python Packages

- `schedule==1.2.0` - Task scheduling
- `plyer==2.1.0` - Cross-platform desktop notifications
- `python-telegram-bot==20.7` - Telegram Bot API
- `python-dotenv==1.0.0` - Environment variable management
- `pystray==0.19.4` - System tray integration
- `Pillow==10.0.1` - Image processing for tray icons

### System Requirements

#### Windows
- Windows 10 or later (for toast notifications)
- No additional system packages required

#### Linux
- `libnotify-bin` for desktop notifications
- Display server (X11 or Wayland)
- System tray support (GNOME, KDE, XFCE, etc.)

## License

MIT License - see LICENSE file for details.

## Health Disclaimer

This application is designed to help remind you to take breaks for eye health. It is not a substitute for professional medical advice. If you experience persistent eye strain, vision problems, or other health issues, please consult with a qualified healthcare provider.

## Acknowledgments

- Inspired by the 20-20-20 rule for digital eye strain prevention
- Built with Python and cross-platform libraries for maximum compatibility
- Thanks to the open-source community for the excellent libraries used in this project

---

**Take care of your eyes! 👀**

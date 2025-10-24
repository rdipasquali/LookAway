#!/bin/bash
# LookAway Linux Startup Script
# This script installs LookAway to run automatically at Linux startup

set -e

LOOKAWAY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="lookaway"
PYTHON_PATH=$(which python3 || which python)

echo "Installing LookAway to Linux startup..."

# Check if we have Python
if [ -z "$PYTHON_PATH" ]; then
    echo "Error: Python not found. Please install Python 3."
    exit 1
fi

# Create systemd service file
create_systemd_service() {
    SERVICE_FILE="$HOME/.config/systemd/user/$SERVICE_NAME.service"
    
    # Create directory if it doesn't exist
    mkdir -p "$HOME/.config/systemd/user"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=LookAway Eye Break Reminder
After=graphical-session.target

[Service]
Type=simple
ExecStart=$PYTHON_PATH $LOOKAWAY_DIR/main.py start --no-tray
WorkingDirectory=$LOOKAWAY_DIR
Restart=always
RestartSec=10
Environment=DISPLAY=:0
Environment=PYTHONPATH=$LOOKAWAY_DIR/src

[Install]
WantedBy=default.target
EOF

    echo "Created systemd service: $SERVICE_FILE"
    
    # Reload systemd and enable service
    systemctl --user daemon-reload
    systemctl --user enable "$SERVICE_NAME.service"
    
    echo "Service enabled. Starting service..."
    systemctl --user start "$SERVICE_NAME.service"
    
    if systemctl --user is-active --quiet "$SERVICE_NAME.service"; then
        echo "✓ LookAway service is now running!"
    else
        echo "⚠ Service may not have started properly. Check with: systemctl --user status $SERVICE_NAME"
    fi
}

# Create desktop autostart entry
create_desktop_autostart() {
    AUTOSTART_DIR="$HOME/.config/autostart"
    DESKTOP_FILE="$AUTOSTART_DIR/lookaway.desktop"
    
    mkdir -p "$AUTOSTART_DIR"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=LookAway
Comment=Eye Break Reminder
Exec=$PYTHON_PATH $LOOKAWAY_DIR/main.py start
Path=$LOOKAWAY_DIR
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
StartupNotify=false
Terminal=false
EOF

    echo "Created desktop autostart entry: $DESKTOP_FILE"
}

# Create init script (for systems without systemd)
create_init_script() {
    INIT_SCRIPT="/etc/init.d/$SERVICE_NAME"
    
    echo "Creating init script requires sudo privileges..."
    
    sudo tee "$INIT_SCRIPT" > /dev/null << EOF
#!/bin/bash
### BEGIN INIT INFO
# Provides:          lookaway
# Required-Start:    \$local_fs \$network
# Required-Stop:     \$local_fs \$network
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Description:       LookAway Eye Break Reminder
### END INIT INFO

DAEMON_USER="$USER"
DAEMON_NAME="lookaway"
DAEMON_PATH="$LOOKAWAY_DIR/main.py"
DAEMON_OPTS="start --no-tray"
PYTHON_PATH="$PYTHON_PATH"

PIDFILE="/var/run/\${DAEMON_NAME}.pid"

case "\$1" in
    start)
        echo "Starting \$DAEMON_NAME..."
        start-stop-daemon --start --quiet --pidfile \$PIDFILE --make-pidfile \\
            --background --chuid \$DAEMON_USER --exec \$PYTHON_PATH -- \$DAEMON_PATH \$DAEMON_OPTS
        ;;
    stop)
        echo "Stopping \$DAEMON_NAME..."
        start-stop-daemon --stop --quiet --pidfile \$PIDFILE
        rm -f \$PIDFILE
        ;;
    restart)
        \$0 stop
        sleep 2
        \$0 start
        ;;
    status)
        if [ -f \$PIDFILE ]; then
            echo "\$DAEMON_NAME is running (PID: \$(cat \$PIDFILE))"
        else
            echo "\$DAEMON_NAME is not running"
        fi
        ;;
    *)
        echo "Usage: \$0 {start|stop|restart|status}"
        exit 1
        ;;
esac

exit 0
EOF

    sudo chmod +x "$INIT_SCRIPT"
    echo "Created init script: $INIT_SCRIPT"
    
    # Enable service
    if command -v update-rc.d >/dev/null 2>&1; then
        sudo update-rc.d "$SERVICE_NAME" defaults
    elif command -v chkconfig >/dev/null 2>&1; then
        sudo chkconfig --add "$SERVICE_NAME"
        sudo chkconfig "$SERVICE_NAME" on
    fi
}

# Detect the best method for the system
if systemctl --user status >/dev/null 2>&1; then
    echo "Using systemd (user service)..."
    create_systemd_service
elif [ -d "$HOME/.config/autostart" ] || [ -d "/etc/xdg/autostart" ]; then
    echo "Using desktop autostart..."
    create_desktop_autostart
    echo "✓ LookAway will start with your desktop session"
    echo "  You may need to log out and back in for changes to take effect"
else
    echo "Using init script (requires sudo)..."
    create_init_script
    echo "✓ LookAway installed as system service"
fi

echo
echo "Installation complete!"
echo
echo "To manage the service:"
if systemctl --user status >/dev/null 2>&1; then
    echo "  Start:   systemctl --user start $SERVICE_NAME"
    echo "  Stop:    systemctl --user stop $SERVICE_NAME"
    echo "  Status:  systemctl --user status $SERVICE_NAME"
    echo "  Disable: systemctl --user disable $SERVICE_NAME"
else
    echo "  The application will start automatically with your session"
    echo "  To remove: delete ~/.config/autostart/lookaway.desktop"
fi
echo
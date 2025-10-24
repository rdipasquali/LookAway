#!/usr/bin/env python3
"""
Linux Installer Wizard for LookAway Eye Break Reminder

Cross-platform GUI installer that works on Linux systems with tkinter support.
Provides step-by-step installation with configuration options.
"""

import os
import sys
import gzip
import base64
import json
import subprocess
import shutil
import stat
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import tempfile

class LinuxLookAwayInstaller:
    """Linux installer GUI for LookAway application."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LookAway - Linux Installer")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Configure style
        self.setup_styles()
        
        # Installation state
        self.install_dir = None
        self.config_data = {}
        self.current_step = 0
        self.steps = []
        
        # Initialize installation steps
        self.setup_installation_steps()
        
        # Create main UI
        self.setup_ui()
        
        # Show first step
        self.show_step(0)
    
    def setup_styles(self):
        """Configure UI styles for Linux."""
        style = ttk.Style()
        
        # Try to use a native theme if available
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'alt' in available_themes:
            style.theme_use('alt')
        
        # Configure button styles
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Install.TButton', padding=(20, 10))
    
    def setup_installation_steps(self):
        """Define installation steps."""
        self.steps = [
            {
                'title': 'Welcome to LookAway Installer',
                'function': self.create_welcome_page
            },
            {
                'title': 'License Agreement',
                'function': self.create_license_page
            },
            {
                'title': 'Choose Installation Directory',
                'function': self.create_directory_page
            },
            {
                'title': 'Configure Notifications',
                'function': self.create_notification_page
            },
            {
                'title': 'Email Configuration',
                'function': self.create_email_config_page
            },
            {
                'title': 'Telegram Configuration',
                'function': self.create_telegram_config_page
            },
            {
                'title': 'System Integration',
                'function': self.create_integration_page
            },
            {
                'title': 'Installing Files',
                'function': self.create_install_page
            },
            {
                'title': 'Installation Complete',
                'function': self.create_complete_page
            }
        ]
    
    def setup_ui(self):
        """Create the main UI layout."""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=1)
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame, 
            text="LookAway Installer", 
            style='Title.TLabel'
        )
        self.title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Content area
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Navigation buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        
        self.back_button = ttk.Button(
            self.button_frame, 
            text="← Back", 
            command=self.previous_step
        )
        self.back_button.pack(side=tk.LEFT)
        
        self.next_button = ttk.Button(
            self.button_frame, 
            text="Next →", 
            command=self.next_step,
            style='Install.TButton'
        )
        self.next_button.pack(side=tk.RIGHT)
        
        self.cancel_button = ttk.Button(
            self.button_frame, 
            text="Cancel", 
            command=self.cancel_installation
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=(0, 10))
    
    def show_step(self, step_index):
        """Display a specific installation step."""
        if 0 <= step_index < len(self.steps):
            self.current_step = step_index
            
            # Clear content area
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # Update title
            step = self.steps[step_index]
            self.title_label.config(text=step['title'])
            
            # Create step content
            step['function']()
            
            # Update navigation buttons
            self.back_button.config(state='normal' if step_index > 0 else 'disabled')
            
            if step_index == len(self.steps) - 1:
                self.next_button.config(text="Finish", command=self.finish_installation)
            else:
                self.next_button.config(text="Next →", command=self.next_step)
    
    def create_welcome_page(self):
        """Create welcome page."""
        welcome_text = """Welcome to the LookAway Eye Break Reminder installer for Linux!

LookAway helps protect your eye health by sending periodic reminders to take breaks from screen time, following the 20-20-20 rule and other eye health best practices.

Features:
• Desktop notifications using your system's notification daemon
• Email reminders via SMTP
• Telegram notifications via bot integration
• Customizable break intervals and messages
• System tray integration (on supported desktops)
• Automatic startup configuration
• Sleep hours awareness

This installer will guide you through the setup process and help configure the application for your system.

Click 'Next' to continue with the installation."""
        
        text_widget = scrolledtext.ScrolledText(
            self.content_frame,
            wrap=tk.WORD,
            height=15,
            font=('Arial', 11)
        )
        text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_widget.insert('1.0', welcome_text)
        text_widget.config(state='disabled')
    
    def create_license_page(self):
        """Create license agreement page."""
        license_frame = ttk.Frame(self.content_frame)
        license_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        license_frame.columnconfigure(0, weight=1)
        license_frame.rowconfigure(1, weight=1)
        
        ttk.Label(
            license_frame,
            text="License Agreement",
            style='Heading.TLabel'
        ).grid(row=0, column=0, pady=(0, 10))
        
        # License text
        license_text = self.get_license_text()
        
        text_widget = scrolledtext.ScrolledText(
            license_frame,
            wrap=tk.WORD,
            height=20,
            font=('Courier', 10)
        )
        text_widget.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_widget.insert('1.0', license_text)
        text_widget.config(state='disabled')
        
        # Agreement checkbox
        self.license_agreed = tk.BooleanVar()
        agreement_frame = ttk.Frame(license_frame)
        agreement_frame.grid(row=2, column=0, pady=(10, 0))
        
        ttk.Checkbutton(
            agreement_frame,
            text="I accept the terms of the license agreement",
            variable=self.license_agreed,
            command=self.update_next_button
        ).pack(anchor='w')
    
    def create_directory_page(self):
        """Create installation directory selection page."""
        dir_frame = ttk.Frame(self.content_frame)
        dir_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Label(
            dir_frame,
            text="Choose Installation Directory",
            style='Heading.TLabel'
        ).grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        ttk.Label(dir_frame, text="Install to:").grid(row=1, column=0, sticky='w', pady=5)
        
        self.install_dir_var = tk.StringVar()
        default_dir = os.path.expanduser("~/.local/share/LookAway")
        self.install_dir_var.set(default_dir)
        
        dir_entry = ttk.Entry(dir_frame, textvariable=self.install_dir_var, width=50)
        dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5))
        
        ttk.Button(
            dir_frame,
            text="Browse",
            command=self.browse_install_dir
        ).grid(row=1, column=2, padx=(5, 0))
        
        # Info text
        info_text = """The application will be installed to the selected directory.
        
Default location: ~/.local/share/LookAway
This follows Linux filesystem hierarchy standards and doesn't require administrator privileges.

You can also choose:
• /opt/LookAway (requires sudo)
• ~/Applications/LookAway (user applications folder)
• Any custom directory of your choice

The installer will create the directory if it doesn't exist."""
        
        info_label = ttk.Label(dir_frame, text=info_text, justify='left')
        info_label.grid(row=2, column=0, columnspan=3, pady=(20, 0), sticky='w')
    
    def create_notification_page(self):
        """Create notification configuration page."""
        notif_frame = ttk.Frame(self.content_frame)
        notif_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(
            notif_frame,
            text="Configure Notification Methods",
            style='Heading.TLabel'
        ).grid(row=0, column=0, pady=(0, 20))
        
        # Desktop notifications
        self.desktop_enabled = tk.BooleanVar(value=True)
        desktop_frame = ttk.LabelFrame(notif_frame, text="Desktop Notifications", padding="10")
        desktop_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(
            desktop_frame,
            text="Enable desktop notifications",
            variable=self.desktop_enabled
        ).pack(anchor='w')
        
        ttk.Label(
            desktop_frame,
            text="Uses your desktop's notification system (notify-send, dunst, etc.)",
            font=('Arial', 9)
        ).pack(anchor='w', pady=(5, 0))
        
        # Email notifications
        self.email_enabled = tk.BooleanVar()
        email_frame = ttk.LabelFrame(notif_frame, text="Email Notifications", padding="10")
        email_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(
            desktop_frame,
            text="Enable email notifications",
            variable=self.email_enabled,
            command=self.update_step_visibility
        ).pack(anchor='w')
        
        ttk.Label(
            email_frame,
            text="Send reminder emails via SMTP (Gmail, Outlook, etc.)",
            font=('Arial', 9)
        ).pack(anchor='w', pady=(5, 0))
        
        # Telegram notifications
        self.telegram_enabled = tk.BooleanVar()
        telegram_frame = ttk.LabelFrame(notif_frame, text="Telegram Notifications", padding="10")
        telegram_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(
            telegram_frame,
            text="Enable Telegram notifications",
            variable=self.telegram_enabled,
            command=self.update_step_visibility
        ).pack(anchor='w')
        
        ttk.Label(
            telegram_frame,
            text="Send notifications via Telegram bot",
            font=('Arial', 9)
        ).pack(anchor='w', pady=(5, 0))
        
        # Basic settings
        settings_frame = ttk.LabelFrame(notif_frame, text="Basic Settings", padding="10")
        settings_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(20, 5))
        
        ttk.Label(settings_frame, text="Reminder interval (minutes):").pack(anchor='w')
        self.interval_var = tk.StringVar(value="20")
        interval_entry = ttk.Entry(settings_frame, textvariable=self.interval_var, width=10)
        interval_entry.pack(anchor='w', pady=(2, 10))
        
        ttk.Label(settings_frame, text="Sleep hours:").pack(anchor='w')
        sleep_frame = ttk.Frame(settings_frame)
        sleep_frame.pack(anchor='w', pady=(2, 0))
        
        ttk.Label(sleep_frame, text="From:").pack(side='left')
        self.sleep_start_var = tk.StringVar(value="23:00")
        ttk.Entry(sleep_frame, textvariable=self.sleep_start_var, width=8).pack(side='left', padx=(5, 10))
        
        ttk.Label(sleep_frame, text="To:").pack(side='left')
        self.sleep_end_var = tk.StringVar(value="07:00")
        ttk.Entry(sleep_frame, textvariable=self.sleep_end_var, width=8).pack(side='left', padx=(5, 0))
    
    def create_email_config_page(self):
        """Create email configuration page."""
        if not self.email_enabled.get():
            self.next_step()
            return
            
        # Create scrollable frame for email config
        canvas = tk.Canvas(self.content_frame)
        scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Email configuration form
        ttk.Label(
            scrollable_frame,
            text="Email Configuration",
            style='Heading.TLabel'
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # SMTP Server
        ttk.Label(scrollable_frame, text="SMTP Server:").grid(row=1, column=0, sticky='w', pady=5)
        self.smtp_server_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.smtp_server_var, width=40).grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # SMTP Port
        ttk.Label(scrollable_frame, text="SMTP Port:").grid(row=2, column=0, sticky='w', pady=5)
        self.smtp_port_var = tk.StringVar(value="587")
        ttk.Entry(scrollable_frame, textvariable=self.smtp_port_var, width=20).grid(row=2, column=1, sticky='w', padx=(10, 0))
        
        # Email Address
        ttk.Label(scrollable_frame, text="Your Email:").grid(row=3, column=0, sticky='w', pady=5)
        self.email_address_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.email_address_var, width=40).grid(row=3, column=1, sticky='w', padx=(10, 0))
        
        # Password
        ttk.Label(scrollable_frame, text="Password:").grid(row=4, column=0, sticky='w', pady=5)
        self.email_password_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.email_password_var, width=40, show="*").grid(row=4, column=1, sticky='w', padx=(10, 0))
        
        # Recipient
        ttk.Label(scrollable_frame, text="Send To:").grid(row=5, column=0, sticky='w', pady=5)
        self.email_recipient_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.email_recipient_var, width=40).grid(row=5, column=1, sticky='w', padx=(10, 0))
        
        # Common providers info
        info_frame = ttk.LabelFrame(scrollable_frame, text="Common SMTP Settings", padding="10")
        info_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0), sticky=(tk.W, tk.E))
        
        provider_info = """Gmail: smtp.gmail.com:587 (use App Password)
Outlook/Hotmail: smtp-mail.outlook.com:587
Yahoo: smtp.mail.yahoo.com:587
ProtonMail: 127.0.0.1:1025 (requires ProtonMail Bridge)

For Gmail: Enable 2FA and create an App Password at:
https://myaccount.google.com/apppasswords"""
        
        ttk.Label(info_frame, text=provider_info, justify='left', font=('Courier', 9)).pack(anchor='w')
        
        # Test button
        ttk.Button(
            scrollable_frame,
            text="Test Email Configuration",
            command=self.test_email_config
        ).grid(row=7, column=0, columnspan=2, pady=(20, 0))
    
    def create_telegram_config_page(self):
        """Create Telegram configuration page."""
        if not self.telegram_enabled.get():
            self.next_step()
            return
            
        telegram_frame = ttk.Frame(self.content_frame)
        telegram_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        telegram_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            telegram_frame,
            text="Telegram Configuration",
            style='Heading.TLabel'
        ).grid(row=0, column=0, pady=(0, 20))
        
        # Instructions
        instructions = """To set up Telegram notifications:

1. Create a bot:
   • Open Telegram and search for @BotFather
   • Send /newbot and follow the instructions
   • Copy the bot token (looks like: 123456789:ABCdefGhIjKlMnOpQrStUvWxYz)

2. Get your Chat ID:
   • Search for @userinfobot and start a conversation
   • It will send you your Chat ID (a number like: 123456789)
   • OR send a message to your bot, then visit:
     https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates

3. Enter the information below:"""
        
        inst_label = ttk.Label(telegram_frame, text=instructions, justify='left')
        inst_label.grid(row=1, column=0, pady=(0, 20), sticky='w')
        
        # Configuration form
        config_frame = ttk.Frame(telegram_frame)
        config_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(config_frame, text="Bot Token:").grid(row=0, column=0, sticky='w', pady=5)
        self.telegram_token_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.telegram_token_var, width=50).grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        ttk.Label(config_frame, text="Chat ID:").grid(row=1, column=0, sticky='w', pady=5)
        self.telegram_chat_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.telegram_chat_var, width=30).grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # Test button
        ttk.Button(
            telegram_frame,
            text="Test Telegram Configuration",
            command=self.test_telegram_config
        ).grid(row=3, column=0, pady=(20, 0))
    
    def create_integration_page(self):
        """Create system integration options page."""
        integration_frame = ttk.Frame(self.content_frame)
        integration_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(
            integration_frame,
            text="System Integration",
            style='Heading.TLabel'
        ).grid(row=0, column=0, pady=(0, 20))
        
        # Auto-start options
        autostart_frame = ttk.LabelFrame(integration_frame, text="Startup Options", padding="10")
        autostart_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.autostart_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            autostart_frame,
            text="Start LookAway automatically on login",
            variable=self.autostart_enabled
        ).pack(anchor='w')
        
        autostart_info = """This will create a desktop entry in ~/.config/autostart/
Works with most Linux desktop environments (GNOME, KDE, XFCE, etc.)"""
        
        ttk.Label(autostart_frame, text=autostart_info, font=('Arial', 9)).pack(anchor='w', pady=(5, 0))
        
        # Desktop integration
        desktop_frame = ttk.LabelFrame(integration_frame, text="Desktop Integration", padding="10")
        desktop_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.desktop_entry_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            desktop_frame,
            text="Create application menu entry",
            variable=self.desktop_entry_enabled
        ).pack(anchor='w')
        
        desktop_info = """Creates a desktop entry in ~/.local/share/applications/
Allows launching LookAway from the application menu"""
        
        ttk.Label(desktop_frame, text=desktop_info, font=('Arial', 9)).pack(anchor='w', pady=(5, 0))
        
        # System tray info
        tray_frame = ttk.LabelFrame(integration_frame, text="System Tray", padding="10")
        tray_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        tray_info = """LookAway will attempt to use your desktop's system tray.
        
Supported on:
• GNOME (with TopIcons or AppIndicator extensions)
• KDE Plasma
• XFCE
• MATE
• Cinnamon
• Other desktop environments with system tray support

If system tray is not available, LookAway can run in console mode."""
        
        ttk.Label(tray_frame, text=tray_info, justify='left', font=('Arial', 9)).pack(anchor='w')
    
    def create_install_page(self):
        """Create installation progress page."""
        install_frame = ttk.Frame(self.content_frame)
        install_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        install_frame.columnconfigure(0, weight=1)
        install_frame.rowconfigure(2, weight=1)
        
        ttk.Label(
            install_frame,
            text="Installing LookAway",
            style='Heading.TLabel'
        ).grid(row=0, column=0, pady=(0, 20))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            install_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status text
        self.status_text = scrolledtext.ScrolledText(
            install_frame,
            height=15,
            state='disabled',
            font=('Courier', 10)
        )
        self.status_text.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Disable navigation during install
        self.back_button.config(state='disabled')
        self.next_button.config(state='disabled')
        
        # Start installation
        self.root.after(100, self.perform_installation)
    
    def create_complete_page(self):
        """Create installation complete page."""
        complete_frame = ttk.Frame(self.content_frame)
        complete_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        complete_frame.columnconfigure(0, weight=1)
        
        ttk.Label(
            complete_frame,
            text="Installation Complete!",
            style='Title.TLabel'
        ).grid(row=0, column=0, pady=(0, 20))
        
        success_text = f"""LookAway has been successfully installed!

Installation directory: {self.install_dir}

What's next:
• LookAway will start automatically on next login (if enabled)
• You can launch it from the application menu
• Or run it from terminal: {self.install_dir}/lookaway

Configuration:
• Settings are stored in ~/.config/LookAway/
• You can modify configuration anytime by running the setup wizard

To start LookAway now, click the 'Launch Now' button below.

Thank you for using LookAway! Take care of your eyes! 👀"""
        
        text_widget = scrolledtext.ScrolledText(
            complete_frame,
            wrap=tk.WORD,
            height=15,
            font=('Arial', 11),
            state='disabled'
        )
        text_widget.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_widget.config(state='normal')
        text_widget.insert('1.0', success_text)
        text_widget.config(state='disabled')
        
        # Launch button
        button_frame = ttk.Frame(complete_frame)
        button_frame.grid(row=2, column=0, pady=(20, 0))
        
        ttk.Button(
            button_frame,
            text="Launch LookAway Now",
            command=self.launch_application,
            style='Install.TButton'
        ).pack(side='left', padx=(0, 10))
        
        ttk.Button(
            button_frame,
            text="Open Installation Directory",
            command=self.open_install_dir
        ).pack(side='left')
        
        # Update finish button
        self.next_button.config(text="Finish", command=self.finish_installation)
    
    # Navigation methods
    def next_step(self):
        """Move to next installation step."""
        if self.validate_current_step():
            self.show_step(self.current_step + 1)
    
    def previous_step(self):
        """Move to previous installation step."""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)
    
    def validate_current_step(self):
        """Validate current step before proceeding."""
        if self.current_step == 1:  # License page
            if not hasattr(self, 'license_agreed') or not self.license_agreed.get():
                messagebox.showerror("License Agreement", "You must accept the license agreement to continue.")
                return False
        
        elif self.current_step == 2:  # Directory page
            install_dir = self.install_dir_var.get().strip()
            if not install_dir:
                messagebox.showerror("Installation Directory", "Please select an installation directory.")
                return False
            
            # Check if directory is writable
            parent_dir = Path(install_dir).parent
            if not parent_dir.exists():
                try:
                    parent_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    messagebox.showerror("Directory Error", f"Cannot create directory: {e}")
                    return False
            
            if not os.access(parent_dir, os.W_OK):
                messagebox.showerror("Permission Error", "No write permission for selected directory.")
                return False
            
            self.install_dir = install_dir
        
        elif self.current_step == 4:  # Email config
            if self.email_enabled.get():
                if not all([
                    self.smtp_server_var.get().strip(),
                    self.smtp_port_var.get().strip(),
                    self.email_address_var.get().strip(),
                    self.email_password_var.get().strip()
                ]):
                    messagebox.showerror("Email Configuration", "Please fill in all email settings.")
                    return False
                
                try:
                    int(self.smtp_port_var.get().strip())
                except ValueError:
                    messagebox.showerror("Email Configuration", "SMTP port must be a number.")
                    return False
        
        elif self.current_step == 5:  # Telegram config
            if self.telegram_enabled.get():
                if not all([
                    self.telegram_token_var.get().strip(),
                    self.telegram_chat_var.get().strip()
                ]):
                    messagebox.showerror("Telegram Configuration", "Please fill in Telegram bot token and chat ID.")
                    return False
        
        return True
    
    def update_next_button(self):
        """Update next button state based on current page."""
        if self.current_step == 1:  # License page
            if hasattr(self, 'license_agreed'):
                self.next_button.config(state='normal' if self.license_agreed.get() else 'disabled')
    
    def update_step_visibility(self):
        """Update which steps should be shown based on configuration."""
        pass  # Steps are always shown, but will be skipped if not needed
    
    # Utility methods
    def browse_install_dir(self):
        """Open directory browser for installation path."""
        directory = filedialog.askdirectory(
            title="Choose Installation Directory",
            initialdir=self.install_dir_var.get()
        )
        if directory:
            self.install_dir_var.set(directory)
    
    def test_email_config(self):
        """Test email configuration."""
        try:
            import smtplib
            import email.mime.text
            
            server = smtplib.SMTP(
                self.smtp_server_var.get().strip(),
                int(self.smtp_port_var.get().strip())
            )
            server.starttls()
            server.login(
                self.email_address_var.get().strip(),
                self.email_password_var.get().strip()
            )
            
            # Send test message
            msg = email.mime.text.MIMEText("LookAway email configuration test successful!")
            msg['Subject'] = "LookAway Test Email"
            msg['From'] = self.email_address_var.get().strip()
            msg['To'] = self.email_recipient_var.get().strip() or self.email_address_var.get().strip()
            
            server.send_message(msg)
            server.quit()
            
            messagebox.showinfo("Email Test", "Test email sent successfully!")
            
        except Exception as e:
            messagebox.showerror("Email Test Failed", f"Email test failed:\n{str(e)}")
    
    def test_telegram_config(self):
        """Test Telegram configuration."""
        try:
            # Basic validation
            token = self.telegram_token_var.get().strip()
            chat_id = self.telegram_chat_var.get().strip()
            
            if not token or not chat_id:
                messagebox.showerror("Telegram Test", "Please enter both bot token and chat ID.")
                return
            
            # Try to send test message (requires internet connection)
            import urllib.request
            import urllib.parse
            import json
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': '🔔 LookAway Telegram configuration test successful!'
            }
            
            data_encoded = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(url, data_encoded)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('ok'):
                    messagebox.showinfo("Telegram Test", "Test message sent successfully!")
                else:
                    messagebox.showerror("Telegram Test", f"Telegram API error: {result.get('description', 'Unknown error')}")
        
        except Exception as e:
            messagebox.showerror("Telegram Test Failed", f"Telegram test failed:\n{str(e)}")
    
    def get_license_text(self):
        """Get license text from embedded data or default."""
        # This will be replaced by create_installer.py with actual license
        return """MIT License

Copyright (c) 2025 LookAway

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""

    def get_embedded_app_data(self):
        """Get embedded application data. This will be replaced by build script."""
        # This method will be replaced by the installer creation script
        # with actual embedded file data
        return {
            'lookaway': 'embedded_app_data_placeholder',
            'config/settings.json': '{}',
            'README.md': 'LookAway Eye Break Reminder',
            'LICENSE': self.get_license_text()
        }
    
    def log_status(self, message):
        """Log status message to the status text widget."""
        if hasattr(self, 'status_text'):
            self.status_text.config(state='normal')
            self.status_text.insert(tk.END, f"{message}\n")
            self.status_text.config(state='disabled')
            self.status_text.see(tk.END)
            self.root.update()
    
    def perform_installation(self):
        """Perform the actual installation."""
        try:
            self.log_status("Starting installation...")
            self.progress_var.set(10)
            
            # Create installation directory
            install_path = Path(self.install_dir)
            self.log_status(f"Creating installation directory: {install_path}")
            install_path.mkdir(parents=True, exist_ok=True)
            self.progress_var.set(20)
            
            # Extract and install files
            self.log_status("Extracting application files...")
            embedded_data = self.get_embedded_app_data()
            
            for filename, data in embedded_data.items():
                file_path = install_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                self.log_status(f"Installing: {filename}")
                
                if filename == 'lookaway':
                    # Main executable - decode and decompress
                    try:
                        compressed_data = base64.b64decode(data.encode('ascii'))
                        exe_data = gzip.decompress(compressed_data)
                        
                        with open(file_path, 'wb') as f:
                            f.write(exe_data)
                        
                        # Make executable
                        file_path.chmod(file_path.stat().st_mode | stat.S_IEXEC)
                        
                    except Exception as e:
                        self.log_status(f"Error installing {filename}: {e}")
                        raise
                else:
                    # Text files
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(data)
            
            self.progress_var.set(60)
            
            # Create configuration
            self.log_status("Creating configuration...")
            self.create_configuration()
            self.progress_var.set(70)
            
            # Create desktop integration
            if self.desktop_entry_enabled.get():
                self.log_status("Creating desktop entry...")
                self.create_desktop_entry()
            self.progress_var.set(80)
            
            # Create autostart entry
            if self.autostart_enabled.get():
                self.log_status("Setting up autostart...")
                self.create_autostart_entry()
            self.progress_var.set(90)
            
            # Create uninstaller
            self.log_status("Creating uninstaller...")
            self.create_uninstaller()
            
            self.progress_var.set(100)
            self.log_status("Installation completed successfully!")
            
            # Enable next button
            self.next_button.config(state='normal')
            
        except Exception as e:
            self.log_status(f"Installation failed: {e}")
            messagebox.showerror("Installation Error", f"Installation failed:\n{str(e)}")
            self.back_button.config(state='normal')
    
    def create_configuration(self):
        """Create application configuration."""
        config = {
            "reminder_interval_minutes": int(self.interval_var.get() or "20"),
            "notifications": {
                "desktop": self.desktop_enabled.get(),
                "email": self.email_enabled.get(),
                "telegram": self.telegram_enabled.get()
            },
            "sleep_hours": {
                "start": self.sleep_start_var.get() or "23:00",
                "end": self.sleep_end_var.get() or "07:00"
            },
            "messages": [
                "Time for a break! Look away from your screen for 20 seconds.",
                "Take a moment to rest your eyes. Look at something 20 feet away.",
                "Eye break time! Blink several times and look into the distance.",
                "Give your eyes a rest. Focus on something far away for a moment.",
                "Break time! Close your eyes for a few seconds or look outside."
            ],
            "break_types": {
                "quick_break": {
                    "duration_seconds": 20,
                    "description": "Quick eye rest - look away for 20 seconds"
                },
                "long_break": {
                    "duration_seconds": 300,
                    "description": "Long break - step away from computer for 5 minutes"
                }
            },
            "long_break_interval": 3,
            "snooze_minutes": 5,
            "do_not_disturb": False,
            "first_run": False
        }
        
        # Email settings
        if self.email_enabled.get():
            config["email_settings"] = {
                "smtp_server": self.smtp_server_var.get().strip(),
                "smtp_port": int(self.smtp_port_var.get().strip()),
                "email": self.email_address_var.get().strip(),
                "password": self.email_password_var.get().strip(),
                "recipient": self.email_recipient_var.get().strip() or self.email_address_var.get().strip()
            }
        else:
            config["email_settings"] = {
                "smtp_server": "",
                "smtp_port": 587,
                "email": "",
                "password": "",
                "recipient": ""
            }
        
        # Telegram settings
        if self.telegram_enabled.get():
            config["telegram_settings"] = {
                "bot_token": self.telegram_token_var.get().strip(),
                "chat_id": self.telegram_chat_var.get().strip()
            }
        else:
            config["telegram_settings"] = {
                "bot_token": "",
                "chat_id": ""
            }
        
        # Save configuration
        config_dir = Path.home() / ".config" / "LookAway"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_file = config_dir / "settings.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
    
    def create_desktop_entry(self):
        """Create desktop entry for application menu."""
        desktop_entry = f"""[Desktop Entry]
Name=LookAway
Comment=Eye Break Reminder
Exec={self.install_dir}/lookaway
Icon={self.install_dir}/icon.png
Terminal=false
Type=Application
Categories=Utility;Health;
StartupWMClass=lookaway
"""
        
        # Create desktop entry directory
        desktop_dir = Path.home() / ".local" / "share" / "applications"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        
        # Write desktop entry
        desktop_file = desktop_dir / "lookaway.desktop"
        with open(desktop_file, 'w', encoding='utf-8') as f:
            f.write(desktop_entry)
        
        # Make executable
        desktop_file.chmod(0o755)
    
    def create_autostart_entry(self):
        """Create autostart entry."""
        autostart_entry = f"""[Desktop Entry]
Name=LookAway
Comment=Eye Break Reminder
Exec={self.install_dir}/lookaway
Icon={self.install_dir}/icon.png
Terminal=false
Type=Application
X-GNOME-Autostart-enabled=true
Hidden=false
NoDisplay=false
"""
        
        # Create autostart directory
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        
        # Write autostart entry
        autostart_file = autostart_dir / "lookaway.desktop"
        with open(autostart_file, 'w', encoding='utf-8') as f:
            f.write(autostart_entry)
        
        # Make executable
        autostart_file.chmod(0o755)
    
    def create_uninstaller(self):
        """Create uninstaller script."""
        uninstaller_script = f"""#!/bin/bash
# LookAway Uninstaller

echo "Uninstalling LookAway..."

# Stop any running instances
pkill -f lookaway

# Remove installation directory
rm -rf "{self.install_dir}"

# Remove desktop entry
rm -f ~/.local/share/applications/lookaway.desktop

# Remove autostart entry
rm -f ~/.config/autostart/lookaway.desktop

# Ask about configuration
read -p "Remove configuration files? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.config/LookAway
    echo "Configuration files removed."
else
    echo "Configuration files kept."
fi

echo "LookAway has been uninstalled."
"""
        
        uninstaller_path = Path(self.install_dir) / "uninstall.sh"
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        # Make executable
        uninstaller_path.chmod(0o755)
    
    def launch_application(self):
        """Launch the installed application."""
        try:
            app_path = Path(self.install_dir) / "lookaway"
            subprocess.Popen([str(app_path)], cwd=self.install_dir)
            messagebox.showinfo("Launch", "LookAway has been launched!")
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch application:\n{str(e)}")
    
    def open_install_dir(self):
        """Open installation directory in file manager."""
        try:
            subprocess.run(["xdg-open", self.install_dir])
        except Exception:
            # Fallback for systems without xdg-open
            try:
                subprocess.run(["nautilus", self.install_dir])
            except Exception:
                try:
                    subprocess.run(["dolphin", self.install_dir])
                except Exception:
                    messagebox.showinfo("Directory", f"Installation directory:\n{self.install_dir}")
    
    def cancel_installation(self):
        """Cancel installation and exit."""
        if messagebox.askyesno("Cancel Installation", "Are you sure you want to cancel the installation?"):
            self.root.quit()
    
    def finish_installation(self):
        """Finish installation and exit."""
        self.root.quit()
    
    def run(self):
        """Run the installer."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass


def main():
    """Main entry point."""
    # Check if running on Linux
    if not sys.platform.startswith('linux'):
        print("This installer is designed for Linux systems.")
        print("Current platform:", sys.platform)
        input("Press Enter to continue anyway...")
    
    # Check for tkinter
    try:
        import tkinter as tk
    except ImportError:
        print("ERROR: tkinter is not available.")
        print("Please install tkinter:")
        print("  Ubuntu/Debian: sudo apt-get install python3-tk")
        print("  Fedora/CentOS: sudo dnf install tkinter")
        print("  Arch Linux: sudo pacman -S tk")
        sys.exit(1)
    
    # Run installer
    installer = LinuxLookAwayInstaller()
    installer.run()


if __name__ == "__main__":
    main()
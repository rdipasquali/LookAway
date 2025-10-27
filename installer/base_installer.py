#!/usr/bin/env python3
"""
Unified Installer Base Class for LookAway Eye Break Reminder

This module contains the common GUI logic for both Windows and Linux installers.
Platform-specific functionality is handled by subclasses.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import threading
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod


class BaseInstallerWizard(ABC):
    """Base installer wizard with unified GUI logic."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LookAway - Eye Break Reminder Installer")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        # Center the window
        self.center_window()
        
        # Installation configuration
        self.config = {
            'install_dir': self.get_default_install_dir(),
            'desktop_shortcut': True,
            'start_menu': True,  # Windows only, ignored on Linux
            'autostart': True,
            'desktop_notifications': True,
            'email_enabled': False,
            'telegram_enabled': False,
            'email_config': {},
            'telegram_config': {}
        }
        
        # Current page tracking
        self.current_page = 0
        self.pages = []
        
        # Create GUI
        self.setup_ui()
        self.create_pages()
        self.show_page(0)
    
    def center_window(self):
        """Center the window on the screen."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def get_license_text(self):
        """Get the license text from the actual LICENSE file"""
        # Try multiple paths to find the LICENSE file
        license_paths = [
            # For development - LICENSE is in parent directory
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "LICENSE"),
            # For PyInstaller - if LICENSE is bundled
            self.get_resource_path("LICENSE"),
            # Current directory fallback
            "LICENSE"
        ]
        
        for license_path in license_paths:
            try:
                if os.path.exists(license_path):
                    with open(license_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        return content
            except Exception as e:
                continue
        
        # Fallback to the actual LICENSE content (matching the real file)
        return """MIT License

Copyright (c) 2025 rdipasquali

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
AUTHORS OR COPYR

HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
    
    def setup_ui(self):
        """Setup the main UI structure."""
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.title_label = ttk.Label(header_frame, text="", font=('Arial', 16, 'bold'))
        self.title_label.pack()
        
        # Main content area
        self.main_frame = ttk.Frame(self.main_container)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(self.main_container)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        self.cancel_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.next_button = ttk.Button(button_frame, text="Next →", command=self.next_page)
        self.next_button.pack(side=tk.RIGHT)
        
        self.back_button = ttk.Button(button_frame, text="← Back", command=self.previous_page)
        self.back_button.pack(side=tk.RIGHT, padx=(0, 10))
    
    def create_pages(self):
        """Create all installer pages."""
        self.pages = [
            {"title": "Welcome to LookAway Installer", "func": self.create_welcome_page},
            {"title": "License Agreement", "func": self.create_license_page},
            {"title": "Installation Directory", "func": self.create_directory_page},
            {"title": "Notification Settings", "func": self.create_notification_page},
            {"title": "Installation Options", "func": self.create_options_page},
            {"title": "Installing LookAway", "func": self.create_install_page},
            {"title": "Installation Complete", "func": self.create_finish_page}
        ]
    
    def show_page(self, page_index):
        """Show a specific page."""
        if 0 <= page_index < len(self.pages):
            self.current_page = page_index
            
            # Clear main frame
            for widget in self.main_frame.winfo_children():
                widget.destroy()
            
            # Update title
            page = self.pages[page_index]
            self.title_label.config(text=page["title"])
            
            # Create page content
            page["func"]()
            
            # Update buttons
            self.update_buttons()
    
    def update_buttons(self):
        """Update button states based on current page."""
        # Back button
        if self.current_page == 0:
            self.back_button.config(state='disabled')
        else:
            self.back_button.config(state='normal')
        
        # Next/Install/Finish button
        if self.current_page == len(self.pages) - 2:  # Install page
            self.next_button.config(text="Install", command=self.start_installation)
        elif self.current_page == len(self.pages) - 1:  # Finish page
            self.next_button.config(text="Finish", command=self.finish)
        else:
            self.next_button.config(text="Next →", command=self.next_page)
        
        # Cancel button visibility
        if self.current_page == len(self.pages) - 1:  # Finish page
            self.cancel_button.config(state='disabled')
    
    def next_page(self):
        """Go to next page."""
        if self.validate_current_page():
            self.show_page(self.current_page + 1)
    
    def previous_page(self):
        """Go to previous page."""
        self.show_page(self.current_page - 1)
    
    def validate_current_page(self):
        """Validate current page before proceeding."""
        if self.current_page == 1:  # License page
            if not hasattr(self, 'license_accepted') or not self.license_accepted.get():
                messagebox.showerror("License Agreement", "You must accept the license agreement to continue.")
                return False
        elif self.current_page == 2:  # Directory page
            if not self.config['install_dir']:
                messagebox.showerror("Installation Directory", "Please select an installation directory.")
                return False
        elif self.current_page == 3:  # Notification page
            # Validate email configuration if enabled
            if hasattr(self, 'email_var') and self.email_var.get():
                if not self.validate_email_config():
                    return False
            
            # Validate telegram configuration if enabled
            if hasattr(self, 'telegram_var') and self.telegram_var.get():
                if not self.validate_telegram_config():
                    return False
        return True
    
    def validate_email_config(self):
        """Validate email configuration."""
        if not hasattr(self, 'smtp_server_var') or not self.smtp_server_var.get().strip():
            messagebox.showerror("Email Configuration", "SMTP Server is required.")
            return False
        if not hasattr(self, 'smtp_port_var') or not self.smtp_port_var.get().strip():
            messagebox.showerror("Email Configuration", "SMTP Port is required.")
            return False
        if not hasattr(self, 'email_address_var') or not self.email_address_var.get().strip():
            messagebox.showerror("Email Configuration", "Email address is required.")
            return False
        if not hasattr(self, 'email_password_var') or not self.email_password_var.get().strip():
            messagebox.showerror("Email Configuration", "Password is required.")
            return False
        if not hasattr(self, 'email_recipient_var') or not self.email_recipient_var.get().strip():
            messagebox.showerror("Email Configuration", "Recipient email is required.")
            return False
        
        # Save email configuration
        self.config['email_config'] = {
            'smtp_server': self.smtp_server_var.get().strip(),
            'smtp_port': int(self.smtp_port_var.get()),
            'email': self.email_address_var.get().strip(),
            'password': self.email_password_var.get(),
            'recipient': self.email_recipient_var.get().strip()
        }
        return True
    
    def validate_telegram_config(self):
        """Validate telegram configuration."""
        if not hasattr(self, 'telegram_token_var') or not self.telegram_token_var.get().strip():
            messagebox.showerror("Telegram Configuration", "Bot token is required.")
            return False
        if not hasattr(self, 'telegram_chat_id_var') or not self.telegram_chat_id_var.get().strip():
            messagebox.showerror("Telegram Configuration", "Chat ID is required.")
            return False
        
        # Save telegram configuration
        self.config['telegram_config'] = {
            'bot_token': self.telegram_token_var.get().strip(),
            'chat_id': self.telegram_chat_id_var.get().strip()
        }
        return True
    
    # Page creation methods
    def create_welcome_page(self):
        """Create welcome page."""
        welcome_frame = ttk.Frame(self.main_frame)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        # Welcome text
        welcome_text = """Welcome to the LookAway Eye Break Reminder installer!

LookAway helps protect your eyes by reminding you to take regular breaks from your computer screen. It follows the 20-20-20 rule: every 20 minutes, look at something 20 feet away for 20 seconds.

Features:
• Customizable break reminders
• System tray integration
• Email and Telegram notifications
• Sleep time detection
• Multiple notification methods

This installer will guide you through the setup process.

Click 'Next' to continue."""
        
        text_label = ttk.Label(welcome_frame, text=welcome_text, justify='left')
        text_label.pack(pady=20)
    
    def create_license_page(self):
        """Create license agreement page."""
        license_frame = ttk.Frame(self.main_frame)
        license_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(license_frame, text="Please read and accept the license agreement:").pack(anchor=tk.W, pady=(0, 10))
        
        # License text area
        license_text = scrolledtext.ScrolledText(license_frame, wrap=tk.WORD, height=15, width=70)
        license_text.pack(fill=tk.BOTH, expand=True)
        license_text.insert(tk.END, self.get_license_text())
        license_text.config(state='disabled')
        
        # Accept checkbox
        self.license_accepted = tk.BooleanVar()
        accept_check = ttk.Checkbutton(license_frame, text="I accept the license agreement", 
                                      variable=self.license_accepted)
        accept_check.pack(anchor=tk.W, pady=(10, 0))
    
    def create_directory_page(self):
        """Create installation directory selection page."""
        dir_frame = ttk.Frame(self.main_frame)
        dir_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(dir_frame, text="Choose installation directory:").pack(anchor=tk.W, pady=(0, 10))
        
        # Directory selection
        dir_select_frame = ttk.Frame(dir_frame)
        dir_select_frame.pack(fill=tk.X, pady=10)
        
        self.install_dir_var = tk.StringVar(value=self.config['install_dir'])
        dir_entry = ttk.Entry(dir_select_frame, textvariable=self.install_dir_var, width=50)
        dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_button = ttk.Button(dir_select_frame, text="Browse...", command=self.browse_directory)
        browse_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Info text
        info_text = f"""The application will be installed to the selected directory.
Space required: ~50 MB
Default location: {self.get_default_install_dir()}

The installer will create the directory if it doesn't exist."""
        
        ttk.Label(dir_frame, text=info_text, justify='left').pack(anchor=tk.W, pady=(20, 0))
    
    def create_notification_page(self):
        """Create notification configuration page."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Basic notifications tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Notifications")
        
        ttk.Label(basic_frame, text="Choose how you want to receive reminders:").pack(anchor=tk.W, pady=(0, 10))
        
        # Desktop notifications (always enabled)
        desktop_frame = ttk.Frame(basic_frame)
        desktop_frame.pack(fill=tk.X, pady=5)
        self.desktop_var = tk.BooleanVar(value=True)
        desktop_check = ttk.Checkbutton(desktop_frame, text="Desktop notifications", 
                                       variable=self.desktop_var, state="disabled")
        desktop_check.pack(side=tk.LEFT)
        ttk.Label(desktop_frame, text="(Recommended)", font=('Arial', 9, 'italic')).pack(side=tk.LEFT, padx=(5, 0))
        
        # Email notifications
        self.email_var = tk.BooleanVar(value=self.config['email_enabled'])
        email_check = ttk.Checkbutton(basic_frame, text="Email notifications", 
                                     variable=self.email_var, command=self.on_email_toggle)
        email_check.pack(anchor=tk.W, pady=5)
        
        # Telegram notifications
        self.telegram_var = tk.BooleanVar(value=self.config['telegram_enabled'])
        telegram_check = ttk.Checkbutton(basic_frame, text="Telegram notifications", 
                                        variable=self.telegram_var, command=self.on_telegram_toggle)
        telegram_check.pack(anchor=tk.W, pady=5)
        
        # Email configuration tab
        self.email_frame = ttk.Frame(notebook)
        notebook.add(self.email_frame, text="Email Setup", state="disabled")
        
        self.create_email_config_tab()
        
        # Telegram configuration tab
        self.telegram_frame = ttk.Frame(notebook)
        notebook.add(self.telegram_frame, text="Telegram Setup", state="disabled")
        
        self.create_telegram_config_tab()
        
        # Store notebook reference
        self.notebook = notebook
    
    def on_email_toggle(self):
        """Handle email notification toggle."""
        if self.email_var.get():
            self.notebook.tab(1, state="normal")
        else:
            self.notebook.tab(1, state="disabled")
    
    def on_telegram_toggle(self):
        """Handle telegram notification toggle."""
        if self.telegram_var.get():
            self.notebook.tab(2, state="normal")
        else:
            self.notebook.tab(2, state="disabled")
    
    def create_email_config_tab(self):
        """Create email configuration tab."""
        # Main container with scrolling
        canvas = tk.Canvas(self.email_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.email_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Form content
        form_frame = ttk.Frame(scrollable_frame)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # SMTP Server
        ttk.Label(form_frame, text="SMTP Server:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.smtp_server_var = tk.StringVar(value="smtp.gmail.com")
        ttk.Entry(form_frame, textvariable=self.smtp_server_var, width=25).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # SMTP Port
        ttk.Label(form_frame, text="SMTP Port:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.smtp_port_var = tk.StringVar(value="587")
        ttk.Entry(form_frame, textvariable=self.smtp_port_var, width=8).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Email address
        ttk.Label(form_frame, text="Your Email:").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.email_address_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_address_var, width=25).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Password
        ttk.Label(form_frame, text="Password/App Password:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.email_password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_password_var, width=25, show="*").grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Recipient
        ttk.Label(form_frame, text="Recipient Email:").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.email_recipient_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.email_recipient_var, width=25).grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Help text
        help_frame = ttk.LabelFrame(scrollable_frame, text="💡 Gmail Setup Tip", padding="10")
        help_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        help_text = ttk.Label(help_frame, 
                             text="Use an App Password for Gmail (not your regular password).\nGenerate one in Google Account → Security → 2-Step Verification → App passwords",
                             font=('Arial', 8), justify=tk.LEFT)
        help_text.pack()
    
    def create_telegram_config_tab(self):
        """Create telegram configuration tab."""
        # Bot settings
        bot_frame = ttk.LabelFrame(self.telegram_frame, text="Bot Configuration", padding="15")
        bot_frame.pack(fill=tk.X, pady=(20, 10))
        
        # Bot token
        ttk.Label(bot_frame, text="Bot Token:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.telegram_token_var = tk.StringVar()
        ttk.Entry(bot_frame, textvariable=self.telegram_token_var, width=40).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Chat ID
        ttk.Label(bot_frame, text="Chat ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.telegram_chat_id_var = tk.StringVar()
        ttk.Entry(bot_frame, textvariable=self.telegram_chat_id_var, width=20).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Help text
        help_frame = ttk.LabelFrame(self.telegram_frame, text="📋 Setup Instructions", padding="10")
        help_frame.pack(fill=tk.X, pady=(10, 0))
        
        help_text = """1. Create a bot: Message @BotFather on Telegram with /newbot
2. Get your bot token from @BotFather
3. Get your chat ID: Message @userinfobot with /start
4. Enter both values above"""
        
        ttk.Label(help_frame, text=help_text, justify=tk.LEFT, font=('Arial', 9)).pack(anchor=tk.W)
    
    def create_options_page(self):
        """Create installation options page."""
        options_frame = ttk.Frame(self.main_frame)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        # Shortcuts frame
        shortcuts_frame = ttk.LabelFrame(options_frame, text="Shortcuts", padding="15")
        shortcuts_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.desktop_shortcut_var = tk.BooleanVar(value=self.config['desktop_shortcut'])
        desktop_check = ttk.Checkbutton(shortcuts_frame, text="Create desktop shortcut", 
                                       variable=self.desktop_shortcut_var)
        desktop_check.pack(anchor=tk.W)
        
        # Platform-specific shortcuts
        self.create_platform_specific_shortcuts(shortcuts_frame)
        
        # Startup frame
        startup_frame = ttk.LabelFrame(options_frame, text="Startup Options", padding="15")
        startup_frame.pack(fill=tk.X)
        
        self.autostart_var = tk.BooleanVar(value=self.config['autostart'])
        autostart_check = ttk.Checkbutton(startup_frame, text="Start LookAway automatically when I log in", 
                                         variable=self.autostart_var)
        autostart_check.pack(anchor=tk.W)
    
    def create_install_page(self):
        """Create installation progress page."""
        install_frame = ttk.Frame(self.main_frame)
        install_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(install_frame, text="Ready to install LookAway!", font=('Arial', 12, 'bold')).pack(pady=(0, 20))
        
        # Installation summary
        summary_text = f"""Installation Summary:

Installation Directory: {self.config['install_dir']}
Desktop Shortcut: {'Yes' if self.config['desktop_shortcut'] else 'No'}
Autostart: {'Yes' if self.config['autostart'] else 'No'}
Desktop Notifications: {'Yes' if self.config['desktop_notifications'] else 'No'}
Email Notifications: {'Yes' if self.config['email_enabled'] else 'No'}
Telegram Notifications: {'Yes' if self.config['telegram_enabled'] else 'No'}

Click 'Install' to begin the installation process."""
        
        ttk.Label(install_frame, text=summary_text, justify='left').pack(anchor=tk.W)
        
        # Progress bar (hidden initially)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(install_frame, variable=self.progress_var, mode='indeterminate')
        
        # Status label (hidden initially)
        self.status_label = ttk.Label(install_frame, text="")
    
    def create_finish_page(self):
        """Create installation complete page."""
        finish_frame = ttk.Frame(self.main_frame)
        finish_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(finish_frame, text="Installation Complete!", font=('Arial', 16, 'bold')).pack(pady=(0, 20))
        
        success_text = """LookAway has been successfully installed!

The application is now ready to help protect your eyes with regular break reminders.

You can:
• Launch LookAway now to start using it
• Configure additional settings in the application
• Access LookAway from your desktop shortcut or start menu

Thank you for choosing LookAway! Take care of your eyes! 👀"""
        
        ttk.Label(finish_frame, text=success_text, justify='left').pack(anchor=tk.W, pady=(0, 20))
        
        # Launch option
        self.launch_var = tk.BooleanVar(value=True)
        launch_check = ttk.Checkbutton(finish_frame, text="Launch LookAway now", 
                                      variable=self.launch_var)
        launch_check.pack(anchor=tk.W)
    
    # Event handlers
    def browse_directory(self):
        """Browse for installation directory."""
        directory = filedialog.askdirectory(initialdir=self.config['install_dir'])
        if directory:
            self.config['install_dir'] = directory
            self.install_dir_var.set(directory)
    
    def start_installation(self):
        """Start the installation process."""
        # Update config from UI
        self.config['install_dir'] = self.install_dir_var.get()
        self.config['desktop_shortcut'] = self.desktop_shortcut_var.get()
        self.config['autostart'] = self.autostart_var.get()
        self.config['desktop_notifications'] = self.desktop_var.get()
        self.config['email_enabled'] = self.email_var.get()
        self.config['telegram_enabled'] = self.telegram_var.get()
        
        # Show progress elements
        self.progress_bar.pack(fill=tk.X, pady=(20, 10))
        self.status_label.pack(anchor=tk.W)
        self.progress_bar.start()
        
        # Disable navigation
        self.next_button.config(state='disabled')
        self.back_button.config(state='disabled')
        
        # Start installation in separate thread
        install_thread = threading.Thread(target=self.perform_installation)
        install_thread.daemon = True
        install_thread.start()
    
    def perform_installation(self):
        """Perform the actual installation (to be implemented by subclasses)."""
        try:
            # This method should be overridden by platform-specific subclasses
            self.install_application()
            
            # Installation complete
            self.root.after(0, self.installation_complete)
        except Exception as e:
            self.root.after(0, lambda: self.installation_failed(str(e)))
    
    def installation_complete(self):
        """Called when installation is complete."""
        self.progress_bar.stop()
        self.show_page(len(self.pages) - 1)  # Show finish page
    
    def installation_failed(self, error_message):
        """Called when installation fails."""
        self.progress_bar.stop()
        messagebox.showerror("Installation Failed", f"Installation failed: {error_message}")
        self.next_button.config(state='normal', text="Retry", command=self.start_installation)
        self.back_button.config(state='normal')
    
    def cancel(self):
        """Cancel installation."""
        if messagebox.askquestion("Cancel Installation", "Are you sure you want to cancel the installation?") == 'yes':
            self.root.quit()
    
    def finish(self):
        """Finish installation and exit."""
        if hasattr(self, 'launch_var') and self.launch_var.get():
            self.launch_application()
        self.root.quit()
    
    # Abstract methods to be implemented by subclasses
    @abstractmethod
    def get_default_install_dir(self):
        """Get the default installation directory for this platform."""
        pass
    
    @abstractmethod
    def create_platform_specific_shortcuts(self, parent_frame):
        """Create platform-specific shortcut options."""
        pass
    
    @abstractmethod
    def install_application(self):
        """Perform the platform-specific installation."""
        pass
    
    @abstractmethod
    def launch_application(self):
        """Launch the application after installation."""
        pass
    
    def run(self):
        """Run the installer."""
        self.root.mainloop()
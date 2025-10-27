#!/usr/bin/env python3
"""
Linux Installation Wizard for LookAway Eye Break Reminder
Based on the Windows installer structure - same functionality, Linux implementation.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import shutil
import tempfile
import json
import threading
import stat
from pathlib import Path
import base64
import gzip


class LinuxInstallerWizard:
    def __init__(self):
        print("DEBUG: LinuxInstallerWizard.__init__() started")
        
        self.root = tk.Tk()
        self.root.title("LookAway Installation Wizard")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"600x500+{x}+{y}")
        
        # Installation configuration - SAME as Windows but with Linux defaults
        self.config = {
            'install_path': str(Path.home() / ".local" / "share" / "LookAway"),
            'create_desktop_shortcut': True,
            'create_start_menu': True,  # Will be application menu on Linux
            'auto_start': False,
            'launch_after_install': True,
            'reminder_interval': 20,
            'notification_method': 'desktop',
            'email_enabled': False,
            'telegram_enabled': False,
            'sleep_start': '22:00',
            'sleep_end': '07:00'
        }
        
        # Current step
        self.current_step = 0
        # Base steps - additional steps will be added dynamically (SAME as Windows)
        self.base_steps = [
            self.create_welcome_page,
            self.create_license_page,
            self.create_installation_path_page,
            self.create_configuration_page,
            self.create_options_page,
        ]
        self.final_steps = [
            self.create_installation_page,
            self.create_completion_page
        ]
        # Initial steps (will be rebuilt when configuration changes)
        self.steps = self.base_steps + self.final_steps
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create navigation frame
        self.nav_frame = ttk.Frame(self.root)
        self.nav_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=20, pady=10)
        
        self.back_btn = ttk.Button(self.nav_frame, text="< Back", command=self.go_back, state="disabled")
        self.back_btn.pack(side=tk.LEFT)
        
        self.next_btn = ttk.Button(self.nav_frame, text="Next >", command=self.go_next)
        self.next_btn.pack(side=tk.RIGHT)
        
        self.cancel_btn = ttk.Button(self.nav_frame, text="Cancel", command=self.cancel_installation)
        self.cancel_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Progress bar
        self.progress_frame = ttk.Frame(self.root)
        self.progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=20, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Show first page
        self.update_progress()
        self.show_current_step()
    
    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def get_license_text(self):
        """Get the license text"""
        # Try to read from actual LICENSE file
        license_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "LICENSE"),
            self.get_resource_path("LICENSE"),
            "LICENSE"
        ]
        
        for license_path in license_paths:
            try:
                if os.path.exists(license_path):
                    with open(license_path, 'r', encoding='utf-8') as f:
                        return f.read()
            except Exception:
                continue
        
        # Fallback license text
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
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""
    
    def show_current_step(self):
        """Display the current installation step"""
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Call the current step function
        if 0 <= self.current_step < len(self.steps):
            self.steps[self.current_step]()
        
        # Update navigation buttons
        self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons"""
        # Back button
        self.back_btn.config(state="normal" if self.current_step > 0 else "disabled")
        
        # Next/Install/Finish button
        if self.current_step == len(self.steps) - 2:  # Installation page
            self.next_btn.config(text="Install", command=self.start_installation)
        elif self.current_step == len(self.steps) - 1:  # Completion page
            self.next_btn.config(text="Finish", command=self.finish_installation)
        else:
            self.next_btn.config(text="Next >", command=self.go_next)
    
    def update_progress(self):
        """Update progress bar"""
        if len(self.steps) > 0:
            progress = (self.current_step / len(self.steps)) * 100
            self.progress_var.set(progress)
    
    def go_next(self):
        """Move to the next installation step"""
        if self.validate_current_step():
            # Rebuild steps if we're leaving the configuration page
            if self.current_step == 3:  # Configuration page (0-indexed)
                self.rebuild_steps()
            
            self.current_step += 1
            self.update_progress()
            self.show_current_step()
    
    def go_back(self):
        """Move to the previous installation step"""
        if self.current_step > 0:
            self.current_step -= 1
            self.update_progress()
            self.show_current_step()
    
    def cancel_installation(self):
        """Cancel the installation"""
        if messagebox.askyesno("Cancel Installation", "Are you sure you want to cancel the installation?"):
            self.root.quit()
    
    def rebuild_steps(self):
        """Rebuild step sequence based on configuration - SAME as Windows"""
        # Start with base steps
        new_steps = self.base_steps.copy()
        
        # Add configuration steps based on user selections
        if hasattr(self, 'email_var') and self.email_var.get():
            new_steps.append(self.create_email_config_page)
        
        if hasattr(self, 'telegram_var') and self.telegram_var.get():
            new_steps.append(self.create_telegram_config_page)
        
        # Add final steps
        new_steps.extend(self.final_steps)
        
        # Update steps if changed
        if new_steps != self.steps:
            old_step_count = len(self.steps)
            self.steps = new_steps
            print(f"DEBUG: Steps rebuilt - was {old_step_count}, now {len(self.steps)}")
    
    def validate_current_step(self):
        """Validate current step before proceeding"""
        if self.current_step == 2:  # Installation path
            if not os.path.exists(os.path.dirname(self.config['install_path'])):
                messagebox.showerror("Invalid Path", "The selected installation directory is not valid.")
                return False
        elif self.steps[self.current_step] == self.create_configuration_page:
            # Configuration page validation and saving - SAME as Windows
            self.config['reminder_interval'] = self.interval_var.get()
            self.config['sleep_start'] = self.sleep_start_var.get()
            self.config['sleep_end'] = self.sleep_end_var.get()
            self.config['email_enabled'] = self.email_var.get()
            self.config['telegram_enabled'] = self.telegram_var.get()
            print(f"DEBUG: Config updated - email: {self.config['email_enabled']}, telegram: {self.config['telegram_enabled']}")
            return True
        elif self.steps[self.current_step] == self.create_email_config_page:
            # Email configuration validation and saving
            if self.validate_email_config():
                # Save email configuration
                self.config['email_settings'] = {
                    'smtp_server': self.smtp_server_var.get(),
                    'smtp_port': int(self.smtp_port_var.get()),
                    'email': self.email_address_var.get(),
                    'password': self.email_password_var.get(),
                    'recipient': self.email_recipient_var.get()
                }
                return True
            return False
        elif self.steps[self.current_step] == self.create_telegram_config_page:
            # Telegram configuration validation and saving
            if self.validate_telegram_config():
                # Save telegram configuration
                self.config['telegram_settings'] = {
                    'bot_token': self.telegram_token_var.get(),
                    'chat_id': self.telegram_chat_id_var.get()
                }
                return True
            return False
        return True
    
    # Page creation methods - SAME structure as Windows
    def create_welcome_page(self):
        """Welcome page"""
        print("DEBUG: Creating welcome page")
        welcome_frame = ttk.Frame(self.main_frame)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(welcome_frame, text="Welcome to LookAway Setup", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        description_text = """LookAway helps protect your eyes by reminding you to take regular breaks from your computer screen.

Features:
• Customizable reminder intervals
• Multiple notification methods (desktop, email, Telegram)
• Sleep time detection
• System tray integration
• Cross-platform support

This wizard will guide you through the installation process.

Click 'Next' to continue."""
        
        desc_label = ttk.Label(welcome_frame, text=description_text, justify='left')
        desc_label.pack(pady=20)
    
    def create_license_page(self):
        """License agreement page"""
        print("DEBUG: Creating license page")
        license_frame = ttk.Frame(self.main_frame)
        license_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(license_frame, text="License Agreement", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        ttk.Label(license_frame, text="Please read and accept the license agreement:").pack(anchor=tk.W)
        
        # License text area
        text_frame = ttk.Frame(license_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        license_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, width=60, height=15)
        license_text.pack(fill=tk.BOTH, expand=True)
        license_text.insert(tk.END, self.get_license_text())
        license_text.config(state='disabled')
        
        # Accept checkbox
        self.license_accepted = tk.BooleanVar()
        accept_frame = ttk.Frame(license_frame)
        accept_frame.pack(fill=tk.X, pady=(10, 0))
        
        accept_check = ttk.Checkbutton(accept_frame, text="I accept the license agreement", 
                                      variable=self.license_accepted)
        accept_check.pack(anchor=tk.W)
    
    def create_installation_path_page(self):
        """Installation path selection page"""
        print("DEBUG: Creating installation path page")
        path_frame = ttk.Frame(self.main_frame)
        path_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(path_frame, text="Choose Installation Location", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        ttk.Label(path_frame, text="Select the folder where LookAway will be installed:").pack(anchor=tk.W, pady=(0, 10))
        
        # Path selection frame
        path_select_frame = ttk.Frame(path_frame)
        path_select_frame.pack(fill=tk.X, pady=10)
        
        self.path_var = tk.StringVar(value=self.config['install_path'])
        path_entry = ttk.Entry(path_select_frame, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(path_select_frame, text="Browse...", command=self.browse_install_path)
        browse_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Info frame
        info_frame = ttk.Frame(path_frame)
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        info_text = f"""Space required: approximately 50 MB
Default location: {Path.home() / ".local" / "share" / "LookAway"}

The installer will create the directory if it doesn't exist."""
        
        ttk.Label(info_frame, text=info_text, justify='left').pack(anchor=tk.W)
    
    def browse_install_path(self):
        """Browse for installation directory"""
        path = filedialog.askdirectory(initialdir=os.path.dirname(self.config['install_path']))
        if path:
            self.config['install_path'] = os.path.join(path, 'LookAway')
            self.path_var.set(self.config['install_path'])
    
    # Step 4: Configuration - SAME as Windows
    def create_configuration_page(self):
        """Configuration page with tabs - EXACTLY like Windows"""
        print("DEBUG: Creating configuration page")
        config_frame = ttk.Frame(self.main_frame)
        config_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(config_frame, text="Initial Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(config_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Basic settings tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Settings")
        
        # Reminder interval
        interval_frame = ttk.LabelFrame(basic_frame, text="Reminder Frequency", padding="10")
        interval_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(interval_frame, text="Remind me every:").pack(anchor=tk.W)
        
        interval_entry_frame = ttk.Frame(interval_frame)
        interval_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.interval_var = tk.IntVar(value=self.config['reminder_interval'])
        interval_spin = ttk.Spinbox(interval_entry_frame, from_=1, to=480, 
                                   textvariable=self.interval_var, width=10)
        interval_spin.pack(side=tk.LEFT)
        ttk.Label(interval_entry_frame, text="minutes").pack(side=tk.LEFT, padx=(5, 0))
        
        # Sleep hours
        sleep_frame = ttk.LabelFrame(basic_frame, text="Sleep Hours (No Reminders)", padding="10")
        sleep_frame.pack(fill=tk.X, pady=(0, 10))
        
        sleep_entry_frame = ttk.Frame(sleep_frame)
        sleep_entry_frame.pack(fill=tk.X)
        
        ttk.Label(sleep_entry_frame, text="From:").pack(side=tk.LEFT)
        self.sleep_start_var = tk.StringVar(value=self.config['sleep_start'])
        start_entry = ttk.Entry(sleep_entry_frame, textvariable=self.sleep_start_var, width=8)
        start_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(sleep_entry_frame, text="To:").pack(side=tk.LEFT)
        self.sleep_end_var = tk.StringVar(value=self.config['sleep_end'])
        end_entry = ttk.Entry(sleep_entry_frame, textvariable=self.sleep_end_var, width=8)
        end_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(sleep_frame, text="Format: HH:MM (24-hour)").pack(anchor=tk.W, pady=(5, 0))
        
        # Notifications tab
        notif_frame = ttk.Frame(notebook)
        notebook.add(notif_frame, text="Notifications")
        
        ttk.Label(notif_frame, text="Choose how you want to receive reminders:").pack(anchor=tk.W, pady=(0, 10))
        
        # Desktop notifications (always enabled)
        desktop_frame = ttk.Frame(notif_frame)
        desktop_frame.pack(fill=tk.X, pady=5)
        self.desktop_var = tk.BooleanVar(value=True)
        desktop_check = ttk.Checkbutton(desktop_frame, text="Desktop notifications", 
                                       variable=self.desktop_var, state="disabled")
        desktop_check.pack(side=tk.LEFT)
        ttk.Label(desktop_frame, text="(Recommended)", font=('Arial', 9, 'italic')).pack(side=tk.LEFT, padx=(5, 0))
        
        # Email notifications
        self.email_var = tk.BooleanVar(value=self.config['email_enabled'])
        email_check = ttk.Checkbutton(notif_frame, text="Email notifications", 
                                     variable=self.email_var)
        email_check.pack(anchor=tk.W, pady=5)
        
        # Telegram notifications
        self.telegram_var = tk.BooleanVar(value=self.config['telegram_enabled'])
        telegram_check = ttk.Checkbutton(notif_frame, text="Telegram notifications", 
                                        variable=self.telegram_var)
        telegram_check.pack(anchor=tk.W, pady=5)
        
        ttk.Label(notif_frame, text="Note: Additional configuration steps will be added if you select email or Telegram.", 
                 font=('Arial', 9, 'italic')).pack(anchor=tk.W, pady=(15, 0))
    
    def create_options_page(self):
        """Installation options page"""
        print("DEBUG: Creating options page")
        options_frame = ttk.Frame(self.main_frame)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(options_frame, text="Installation Options", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Shortcuts frame
        shortcuts_frame = ttk.LabelFrame(options_frame, text="Shortcuts", padding="15")
        shortcuts_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.desktop_shortcut_var = tk.BooleanVar(value=self.config['create_desktop_shortcut'])
        desktop_check = ttk.Checkbutton(shortcuts_frame, text="Create desktop shortcut", 
                                       variable=self.desktop_shortcut_var)
        desktop_check.pack(anchor=tk.W, pady=2)
        
        self.start_menu_var = tk.BooleanVar(value=self.config['create_start_menu'])
        start_menu_check = ttk.Checkbutton(shortcuts_frame, text="Add to application menu", 
                                          variable=self.start_menu_var)
        start_menu_check.pack(anchor=tk.W, pady=2)
        
        # Startup frame
        startup_frame = ttk.LabelFrame(options_frame, text="Startup Options", padding="15")
        startup_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.auto_start_var = tk.BooleanVar(value=self.config['auto_start'])
        auto_start_check = ttk.Checkbutton(startup_frame, 
                                          text="Start LookAway when I log in",
                                          variable=self.auto_start_var)
        auto_start_check.pack(anchor=tk.W, pady=2)
        
        self.launch_after_var = tk.BooleanVar(value=self.config['launch_after_install'])
        launch_check = ttk.Checkbutton(startup_frame, 
                                      text="Launch LookAway after installation",
                                      variable=self.launch_after_var)
        launch_check.pack(anchor=tk.W, pady=2)
    
    # Email Configuration Page (shown if email notifications enabled) - SAME as Windows
    def create_email_config_page(self):
        print("DEBUG: Creating email configuration page")
        
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        title_label = ttk.Label(self.main_frame, text="Email Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Create scrollable frame if needed
        main_container = ttk.Frame(self.main_frame)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Use canvas for scrolling if content is too tall
        canvas = tk.Canvas(main_container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Compact form layout
        form_frame = ttk.Frame(scrollable_frame)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # SMTP Server (row 0)
        ttk.Label(form_frame, text="SMTP Server:").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.smtp_server_var = tk.StringVar(value="smtp.gmail.com")
        smtp_entry = ttk.Entry(form_frame, textvariable=self.smtp_server_var, width=25)
        smtp_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # SMTP Port (row 1)
        ttk.Label(form_frame, text="SMTP Port:").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.smtp_port_var = tk.StringVar(value="587")
        port_entry = ttk.Entry(form_frame, textvariable=self.smtp_port_var, width=8)
        port_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Separator
        separator = ttk.Separator(form_frame, orient='horizontal')
        separator.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=8)
        
        # Email address (row 3)
        ttk.Label(form_frame, text="Your Email:").grid(row=3, column=0, sticky=tk.W, pady=3)
        self.email_address_var = tk.StringVar()
        email_entry = ttk.Entry(form_frame, textvariable=self.email_address_var, width=25)
        email_entry.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Password (row 4)
        ttk.Label(form_frame, text="Password/App Password:").grid(row=4, column=0, sticky=tk.W, pady=3)
        self.email_password_var = tk.StringVar()
        password_entry = ttk.Entry(form_frame, textvariable=self.email_password_var, width=25, show="*")
        password_entry.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Recipient (row 5)
        ttk.Label(form_frame, text="Recipient Email:").grid(row=5, column=0, sticky=tk.W, pady=3)
        self.email_recipient_var = tk.StringVar()
        recipient_entry = ttk.Entry(form_frame, textvariable=self.email_recipient_var, width=25)
        recipient_entry.grid(row=5, column=1, sticky=tk.W, padx=(10, 0), pady=3)
        
        # Help text in a compact frame
        help_frame = ttk.LabelFrame(scrollable_frame, text="💡 Gmail Setup Tip", padding="10")
        help_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        
        help_text = ttk.Label(help_frame, 
                             text="Use an App Password for Gmail (not your regular password).\nGenerate one in Google Account → Security → 2-Step Verification → App passwords",
                             font=('Arial', 8), justify=tk.LEFT)
        help_text.pack()
        
        # Configure column weights for proper resizing
        form_frame.columnconfigure(1, weight=1)
    
    # Telegram Configuration Page (shown if telegram notifications enabled) - SAME as Windows
    def create_telegram_config_page(self):
        print("DEBUG: Creating telegram configuration page")
        
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        title_label = ttk.Label(self.main_frame, text="Telegram Configuration", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        telegram_frame = ttk.Frame(self.main_frame)
        telegram_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(telegram_frame, text="Configure your Telegram bot for notifications:", 
                 font=('Arial', 10)).pack(pady=(0, 15))
        
        # Bot settings
        bot_frame = ttk.LabelFrame(telegram_frame, text="Bot Configuration", padding="15")
        bot_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Bot token
        ttk.Label(bot_frame, text="Bot Token:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.telegram_token_var = tk.StringVar()
        token_entry = ttk.Entry(bot_frame, textvariable=self.telegram_token_var, width=40)
        token_entry.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Chat ID
        ttk.Label(bot_frame, text="Chat ID:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.telegram_chat_id_var = tk.StringVar()
        chat_entry = ttk.Entry(bot_frame, textvariable=self.telegram_chat_id_var, width=20)
        chat_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Help text
        help_frame = ttk.LabelFrame(telegram_frame, text="📋 Setup Instructions", padding="10")
        help_frame.pack(fill=tk.X, pady=(10, 0))
        
        help_text = """1. Create a bot: Message @BotFather on Telegram with /newbot
2. Get your bot token from @BotFather  
3. Get your chat ID: Message @userinfobot with /start
4. Enter both values above"""
        
        ttk.Label(help_frame, text=help_text, justify=tk.LEFT, font=('Arial', 9)).pack(anchor=tk.W)
    
    def validate_email_config(self):
        """Validate email configuration"""
        if not self.smtp_server_var.get().strip():
            messagebox.showerror("Email Setup", "Please enter the SMTP server.")
            return False
        if not self.smtp_port_var.get().strip():
            messagebox.showerror("Email Setup", "Please enter the SMTP port.")
            return False
        try:
            int(self.smtp_port_var.get())
        except ValueError:
            messagebox.showerror("Email Setup", "SMTP port must be a number.")
            return False
        if not self.email_address_var.get().strip():
            messagebox.showerror("Email Setup", "Please enter your email address.")
            return False
        if not self.email_password_var.get().strip():
            messagebox.showerror("Email Setup", "Please enter your password.")
            return False
        if not self.email_recipient_var.get().strip():
            messagebox.showerror("Email Setup", "Please enter the recipient email.")
            return False
        return True
    
    def validate_telegram_config(self):
        """Validate telegram configuration"""
        if not self.telegram_token_var.get().strip():
            messagebox.showerror("Telegram Setup", "Please enter the bot token.")
            return False
        if not self.telegram_chat_id_var.get().strip():
            messagebox.showerror("Telegram Setup", "Please enter the chat ID.")
            return False
        return True
    
    def create_installation_page(self):
        """Installation progress page"""
        print("DEBUG: Creating installation page")
        install_frame = ttk.Frame(self.main_frame)
        install_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(install_frame, text="Installing LookAway", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Installation summary
        summary = f"""Ready to install LookAway with the following settings:

Installation Path: {self.config['install_path']}
Desktop Shortcut: {'Yes' if self.config['create_desktop_shortcut'] else 'No'}
Application Menu: {'Yes' if self.config['create_start_menu'] else 'No'}
Auto Start: {'Yes' if self.config['auto_start'] else 'No'}
Reminder Interval: {self.config['reminder_interval']} minutes
Sleep Hours: {self.config['sleep_start']} - {self.config['sleep_end']}
Email Notifications: {'Yes' if self.config['email_enabled'] else 'No'}
Telegram Notifications: {'Yes' if self.config['telegram_enabled'] else 'No'}

Click 'Install' to begin the installation."""
        
        summary_label = ttk.Label(install_frame, text=summary, justify='left')
        summary_label.pack(pady=10)
        
        # Progress area (will be shown during installation)
        self.install_progress_frame = ttk.Frame(install_frame)
        
        self.install_status_label = ttk.Label(self.install_progress_frame, text="")
        
        self.install_progress_var = tk.DoubleVar()
        self.install_progress_bar = ttk.Progressbar(self.install_progress_frame, 
                                                   variable=self.install_progress_var,
                                                   mode='indeterminate')
    
    def start_installation(self):
        """Start the installation process"""
        print("DEBUG: Starting installation")
        
        # Update remaining configuration from UI (main config already updated in validation)
        self.config['install_path'] = self.path_var.get()
        self.config['create_desktop_shortcut'] = self.desktop_shortcut_var.get()
        self.config['create_start_menu'] = self.start_menu_var.get()
        self.config['auto_start'] = self.auto_start_var.get()
        self.config['launch_after_install'] = self.launch_after_var.get()
        
        # Show progress elements
        self.install_progress_frame.pack(fill=tk.X, pady=(20, 10))
        self.install_status_label.pack()
        self.install_progress_bar.pack(fill=tk.X, pady=(10, 0))
        self.install_progress_bar.start()
        
        # Disable navigation
        self.next_btn.config(state='disabled')
        self.back_btn.config(state='disabled')
        self.cancel_btn.config(state='disabled')
        
        # Start installation in separate thread
        install_thread = threading.Thread(target=self.perform_installation)
        install_thread.daemon = True
        install_thread.start()
    
    def perform_installation(self):
        """Perform the actual installation - Linux implementation"""
        try:
            install_dir = Path(self.config['install_path'])
            
            # Update status
            self.root.after(0, lambda: self.install_status_label.config(text="Creating installation directory..."))
            install_dir.mkdir(parents=True, exist_ok=True)
            
            # Get embedded application data
            app_data = self.get_embedded_app_data()
            
            # Extract main application
            self.root.after(0, lambda: self.install_status_label.config(text="Installing LookAway application..."))
            
            if 'lookaway' in app_data:
                if app_data['lookaway'] == 'embedded_app_data_placeholder':
                    self.root.after(0, lambda: messagebox.showwarning("Installation Warning", 
                                                 "This installer was not properly built with embedded application files.\n"
                                                 "Please use the create_linux_installer.py script to create a proper installer."))
                    return
                
                # Get the application binary (already decompressed by get_embedded_app_data)
                app_binary = app_data['lookaway']
                
                # Write the application
                app_path = install_dir / "lookaway"
                with open(app_path, 'wb') as f:
                    f.write(app_binary)
                
                # Make executable
                app_path.chmod(0o755)
            
            # Create configuration files
            self.root.after(0, lambda: self.install_status_label.config(text="Creating configuration..."))
            self.create_config_files(install_dir)
            
            # Create shortcuts
            if self.config['create_desktop_shortcut']:
                self.root.after(0, lambda: self.install_status_label.config(text="Creating desktop shortcut..."))
                self.create_desktop_shortcut(install_dir)
            
            if self.config['create_start_menu']:
                self.root.after(0, lambda: self.install_status_label.config(text="Adding to application menu..."))
                self.create_application_menu_entry(install_dir)
            
            # Setup autostart
            if self.config['auto_start']:
                self.root.after(0, lambda: self.install_status_label.config(text="Setting up autostart..."))
                self.create_autostart_entry(install_dir)
            
            # Create uninstaller
            self.root.after(0, lambda: self.install_status_label.config(text="Creating uninstaller..."))
            self.create_uninstaller(install_dir)
            
            self.root.after(0, lambda: self.install_status_label.config(text="Installation complete!"))
            
            # Installation complete
            self.root.after(0, self.installation_complete)
            
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda: self.installation_failed(error_message))
    
    def get_embedded_app_data(self):
        """Get embedded application data. Override this method in build scripts."""
        # This is a placeholder - the actual build script should replace this method
        return {
            'lookaway': 'embedded_app_data_placeholder',
            'config/settings.json': '{}',
            'LICENSE': self.get_license_text()
        }
    
    def create_config_files(self, install_dir):
        """Create application configuration files"""
        config_dir = install_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        # Create settings
        settings = {
            "reminder_interval_minutes": self.config['reminder_interval'],
            "break_duration": 20,
            "long_break_interval": 3,
            "long_break_duration": 300,
            "sleep_hours": {
                "start": self.config['sleep_start'],
                "end": self.config['sleep_end']
            },
            "notifications": {
                "desktop": True,
                "email": self.config['email_enabled'],
                "telegram": self.config['telegram_enabled']
            },
            "snooze_minutes": 5,
            "logging": {
                "level": "INFO",
                "max_log_files": 5,
                "max_file_size_mb": 10
            }
        }
        
        # Add email configuration if enabled
        if self.config['email_enabled'] and 'email_settings' in self.config:
            settings["email"] = self.config['email_settings']
        
        # Add telegram configuration if enabled
        if self.config['telegram_enabled'] and 'telegram_settings' in self.config:
            settings["telegram"] = self.config['telegram_settings']
        
        # Write settings file
        settings_file = config_dir / "settings.json"
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    
    def create_desktop_shortcut(self, install_dir):
        """Create desktop shortcut"""
        desktop_dir = Path.home() / "Desktop"
        if not desktop_dir.exists():
            return
        
        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=LookAway
Comment=Eye Break Reminder
Exec={install_dir}/lookaway
Icon={install_dir}/lookaway.png
Path={install_dir}
Terminal=false
StartupNotify=true
Categories=Utility;Health;
"""
        
        desktop_file = desktop_dir / "lookaway.desktop"
        with open(desktop_file, 'w', encoding='utf-8') as f:
            f.write(desktop_entry)
        
        # Make executable
        desktop_file.chmod(0o755)
    
    def create_application_menu_entry(self, install_dir):
        """Create application menu entry"""
        apps_dir = Path.home() / ".local" / "share" / "applications"
        apps_dir.mkdir(parents=True, exist_ok=True)
        
        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=LookAway
Comment=Eye Break Reminder
Exec={install_dir}/lookaway
Icon={install_dir}/lookaway.png
Path={install_dir}
Terminal=false
StartupNotify=true
Categories=Utility;Health;
"""
        
        desktop_file = apps_dir / "lookaway.desktop"
        with open(desktop_file, 'w', encoding='utf-8') as f:
            f.write(desktop_entry)
        
        # Make executable
        desktop_file.chmod(0o755)
    
    def create_autostart_entry(self, install_dir):
        """Create autostart entry"""
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        
        autostart_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=LookAway
Comment=Eye Break Reminder
Exec={install_dir}/lookaway
Icon={install_dir}/lookaway.png
Path={install_dir}
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
Hidden=false
NoDisplay=false
"""
        
        autostart_file = autostart_dir / "lookaway.desktop"
        with open(autostart_file, 'w', encoding='utf-8') as f:
            f.write(autostart_entry)
        
        # Make executable
        autostart_file.chmod(0o755)
    
    def create_uninstaller(self, install_dir):
        """Create uninstaller script"""
        uninstaller_script = f"""#!/bin/bash
# LookAway Uninstaller

echo "Uninstalling LookAway..."

# Stop any running instances
pkill -f lookaway

# Remove installation directory
rm -rf "{install_dir}"

# Remove desktop entry
rm -f ~/Desktop/lookaway.desktop

# Remove application menu entry
rm -f ~/.local/share/applications/lookaway.desktop

# Remove autostart entry
rm -f ~/.config/autostart/lookaway.desktop

echo "LookAway has been uninstalled."
"""
        
        uninstaller_path = install_dir / "uninstall.sh"
        with open(uninstaller_path, 'w', encoding='utf-8') as f:
            f.write(uninstaller_script)
        
        # Make executable
        uninstaller_path.chmod(0o755)
    
    def installation_complete(self):
        """Called when installation is complete"""
        self.install_progress_bar.stop()
        self.current_step += 1
        self.update_progress()
        self.show_current_step()
    
    def installation_failed(self, error_message):
        """Called when installation fails"""
        self.install_progress_bar.stop()
        messagebox.showerror("Installation Failed", f"Installation failed: {error_message}")
        self.next_btn.config(state='normal', text="Retry", command=self.start_installation)
        self.back_btn.config(state='normal')
        self.cancel_btn.config(state='normal')
    
    def create_completion_page(self):
        """Installation completion page"""
        print("DEBUG: Creating completion page")
        completion_frame = ttk.Frame(self.main_frame)
        completion_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(completion_frame, text="Installation Complete!", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        success_text = f"""LookAway has been successfully installed!

Installation location: {self.config['install_path']}

You can now:
• Launch LookAway to start protecting your eyes
• Configure additional settings in the application
• Access LookAway from your desktop or application menu

Thank you for choosing LookAway!"""
        
        success_label = ttk.Label(completion_frame, text=success_text, justify='left')
        success_label.pack(pady=20)
        
        # Launch option
        if hasattr(self, 'launch_after_var'):
            launch_frame = ttk.Frame(completion_frame)
            launch_frame.pack(pady=(20, 0))
            
            launch_check = ttk.Checkbutton(launch_frame, text="Launch LookAway now", 
                                          variable=self.launch_after_var)
            launch_check.pack()
    
    def finish_installation(self):
        """Finish installation and exit"""
        if hasattr(self, 'launch_after_var') and self.launch_after_var.get():
            self.launch_application()
        self.root.quit()
    
    def launch_application(self):
        """Launch the application after installation"""
        try:
            app_path = Path(self.config['install_path']) / "lookaway"
            subprocess.Popen([str(app_path)], cwd=self.config['install_path'])
        except Exception as e:
            messagebox.showwarning("Launch Failed", f"Could not launch LookAway: {e}")
    
    def run(self):
        """Run the installer"""
        self.root.mainloop()


def main():
    """Main entry point"""
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
    installer = LinuxInstallerWizard()
    installer.run()


if __name__ == "__main__":
    main()
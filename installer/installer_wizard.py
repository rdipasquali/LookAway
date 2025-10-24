#!/usr/bin/env python3
"""
LookAway Installation Wizard
A comprehensive GUI installer for the LookAway eye break reminder application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import shutil
import zipfile
import tempfile
import json
import threading
import winreg
from pathlib import Path
import base64
import zlib


class InstallerWizard:
    def __init__(self):
        print("DEBUG: InstallerWizard.__init__() started")
        
        self.root = tk.Tk()
        self.root.title("LookAway Installation Wizard")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"600x500+{x}+{y}")
        
        # Application icon (if available)
        try:
            self.root.iconbitmap(self.get_resource_path("assets/icon.ico"))
        except:
            pass
        
        # Installation configuration
        self.config = {
            'install_path': os.path.join(os.environ.get('PROGRAMFILES', 'C:\\Program Files'), 'LookAway'),
            'create_desktop_shortcut': True,
            'create_start_menu': True,
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
        # Base steps - additional steps will be added dynamically
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
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Show first step
        print("DEBUG: About to show first step")
        self.show_current_step()
        print("DEBUG: InstallerWizard.__init__() completed")
    
    def get_resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def clear_main_frame(self):
        """Clear all widgets from main frame"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    
    def show_current_step(self):
        """Display the current installation step"""
        print(f"DEBUG: Showing step {self.current_step + 1} of {len(self.steps)}")
        print(f"DEBUG: Step function: {self.steps[self.current_step].__name__}")
        
        self.clear_main_frame()
        self.steps[self.current_step]()
        self.update_navigation()
        self.update_progress()
    
    def update_navigation(self):
        """Update navigation button states"""
        self.back_btn.config(state="normal" if self.current_step > 0 else "disabled")
        
        if self.current_step == len(self.steps) - 1:
            self.next_btn.config(text="Finish", state="normal")
        elif self.current_step == len(self.steps) - 2:
            self.next_btn.config(text="Install", state="normal")
        else:
            self.next_btn.config(text="Next >", state="normal")
    
    def update_progress(self):
        """Update progress bar"""
        progress = (self.current_step / (len(self.steps) - 1)) * 100
        self.progress_var.set(progress)
    
    def go_next(self):
        """Go to next step"""
        print(f"DEBUG: go_next() called from step {self.current_step + 1}")
        
        # Rebuild steps after configuration page to include email/telegram pages
        if self.current_step == 3:  # After configuration page
            self.rebuild_steps()
        
        if self.current_step == len(self.steps) - 2:  # Install step
            print("DEBUG: Starting installation...")
            self.start_installation()
        elif self.current_step < len(self.steps) - 1:
            if self.validate_current_step():
                print(f"DEBUG: Moving to next step ({self.current_step + 2})")
                self.current_step += 1
                self.show_current_step()
        else:  # Finish
            print("DEBUG: Finishing installation...")
            self.finish_installation()
    
    def go_back(self):
        """Go to previous step"""
        print(f"DEBUG: go_back() called from step {self.current_step + 1}")
        
        if self.current_step > 0:
            self.current_step -= 1
            print(f"DEBUG: Moving back to step {self.current_step + 1}")
            self.show_current_step()
    
    def cancel_installation(self):
        """Cancel the installation"""
        if messagebox.askyesno("Cancel Installation", "Are you sure you want to cancel the installation?"):
            self.root.quit()
    
    def rebuild_steps(self):
        """Rebuild step sequence based on configuration"""
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
    
    # Step 1: Welcome Page
    def create_welcome_page(self):
        print("DEBUG: Creating welcome page")
        welcome_frame = ttk.Frame(self.main_frame)
        welcome_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(welcome_frame, text="Welcome to LookAway Setup", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_text = """This wizard will guide you through the installation of LookAway, 
an eye break reminder application that helps protect your vision during computer use.

LookAway follows the 20-20-20 rule: every 20 minutes, look at something 
20 feet away for at least 20 seconds.

Click Next to continue with the installation."""
        
        desc_label = ttk.Label(welcome_frame, text=desc_text, wraplength=500, justify=tk.LEFT)
        desc_label.pack(pady=20)
        
        # Version info
        version_label = ttk.Label(welcome_frame, text="Version 1.0.0", font=('Arial', 10, 'italic'))
        version_label.pack(pady=(40, 0))
    
    # Step 2: License Agreement
    def create_license_page(self):
        license_frame = ttk.Frame(self.main_frame)
        license_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(license_frame, text="License Agreement", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # License text
        license_text = self.get_license_text()
        
        text_widget = scrolledtext.ScrolledText(license_frame, height=15, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        text_widget.insert(tk.END, license_text)
        text_widget.config(state=tk.DISABLED)
        
        # Agreement checkbox
        self.license_var = tk.BooleanVar()
        license_check = ttk.Checkbutton(license_frame, 
                                       text="I accept the terms in the License Agreement",
                                       variable=self.license_var,
                                       command=self.update_next_button)
        license_check.pack(anchor=tk.W)
    
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
                        print(f"DEBUG: Successfully loaded LICENSE from {license_path}")
                        return content
            except Exception as e:
                print(f"DEBUG: Failed to read LICENSE from {license_path}: {e}")
                continue
        
        # Fallback to the actual LICENSE content (matching the real file)
        print("DEBUG: Using fallback LICENSE text")
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
    
    def update_next_button(self):
        """Enable/disable next button based on license acceptance"""
        if hasattr(self, 'license_var'):
            if self.license_var.get():
                self.next_btn.config(state="normal")
            else:
                self.next_btn.config(state="disabled")
    
    # Step 3: Installation Path
    def create_installation_path_page(self):
        path_frame = ttk.Frame(self.main_frame)
        path_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(path_frame, text="Choose Installation Location", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        desc_label = ttk.Label(path_frame, 
                              text="Choose the folder where you want to install LookAway.",
                              wraplength=500)
        desc_label.pack(pady=(0, 20))
        
        # Path selection frame
        path_select_frame = ttk.Frame(path_frame)
        path_select_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(path_select_frame, text="Destination folder:").pack(anchor=tk.W)
        
        path_entry_frame = ttk.Frame(path_select_frame)
        path_entry_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.path_var = tk.StringVar(value=self.config['install_path'])
        path_entry = ttk.Entry(path_entry_frame, textvariable=self.path_var, width=50)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(path_entry_frame, text="Browse...", 
                               command=self.browse_installation_path)
        browse_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Disk space info
        space_label = ttk.Label(path_frame, text="Space required: ~50 MB")
        space_label.pack(pady=(20, 0), anchor=tk.W)
    
    def browse_installation_path(self):
        """Browse for installation path"""
        path = filedialog.askdirectory(initialdir=os.path.dirname(self.config['install_path']))
        if path:
            self.config['install_path'] = os.path.join(path, 'LookAway')
            self.path_var.set(self.config['install_path'])
    
    # Step 4: Configuration
    def create_configuration_page(self):
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
        
        ttk.Label(notif_frame, text="Note: Email and Telegram can be configured later in the app.", 
                 font=('Arial', 9, 'italic')).pack(anchor=tk.W, pady=(10, 0))
    
    # Step 5: Options
    def create_options_page(self):
        options_frame = ttk.Frame(self.main_frame)
        options_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(options_frame, text="Installation Options", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Shortcuts frame
        shortcuts_frame = ttk.LabelFrame(options_frame, text="Shortcuts", padding="15")
        shortcuts_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.desktop_shortcut_var = tk.BooleanVar(value=self.config['create_desktop_shortcut'])
        desktop_check = ttk.Checkbutton(shortcuts_frame, 
                                       text="Create desktop shortcut",
                                       variable=self.desktop_shortcut_var)
        desktop_check.pack(anchor=tk.W, pady=2)
        
        self.start_menu_var = tk.BooleanVar(value=self.config['create_start_menu'])
        start_menu_check = ttk.Checkbutton(shortcuts_frame, 
                                          text="Add to Start Menu",
                                          variable=self.start_menu_var)
        start_menu_check.pack(anchor=tk.W, pady=2)
        
        # Startup frame
        startup_frame = ttk.LabelFrame(options_frame, text="Startup Options", padding="15")
        startup_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.auto_start_var = tk.BooleanVar(value=self.config['auto_start'])
        auto_start_check = ttk.Checkbutton(startup_frame, 
                                          text="Start LookAway when Windows starts",
                                          variable=self.auto_start_var)
        auto_start_check.pack(anchor=tk.W, pady=2)
        
        self.launch_after_var = tk.BooleanVar(value=self.config['launch_after_install'])
        launch_check = ttk.Checkbutton(startup_frame, 
                                      text="Launch LookAway after installation",
                                      variable=self.launch_after_var)
        launch_check.pack(anchor=tk.W, pady=2)
    
    # Email Configuration Page (shown if email notifications enabled)
    def create_email_config_page(self):
        print("DEBUG: Creating email configuration page")
        
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
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="Email Notification Setup", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
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
    
    # Telegram Configuration Page (shown if telegram notifications enabled)
    def create_telegram_config_page(self):
        print("DEBUG: Creating telegram configuration page")
        telegram_frame = ttk.Frame(self.main_frame)
        telegram_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(telegram_frame, text="Telegram Notification Setup", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
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
        help_frame = ttk.Frame(telegram_frame)
        help_frame.pack(fill=tk.X, pady=(10, 0))
        
        help_text = ttk.Label(help_frame, 
                             text="📋 How to set up Telegram notifications:\n" +
                                  "1. Create a bot: Send /newbot to @BotFather on Telegram\n" +
                                  "2. Get your Chat ID: Send /start to @userinfobot\n" +
                                  "3. Enter the bot token and your chat ID above",
                             font=('Arial', 9), foreground='blue', justify=tk.LEFT)
        help_text.pack(pady=5, anchor=tk.W)
    
    def validate_email_config(self):
        """Validate email configuration"""
        if not self.smtp_server_var.get().strip():
            messagebox.showerror("Error", "Please enter an SMTP server.")
            return False
        if not self.email_address_var.get().strip():
            messagebox.showerror("Error", "Please enter your email address.")
            return False
        if not self.email_password_var.get().strip():
            messagebox.showerror("Error", "Please enter your email password.")
            return False
        if not self.email_recipient_var.get().strip():
            messagebox.showerror("Error", "Please enter a recipient email address.")
            return False
        
        try:
            port = int(self.smtp_port_var.get())
            if port <= 0 or port > 65535:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid port number (1-65535).")
            return False
        
        return True
    
    def validate_telegram_config(self):
        """Validate telegram configuration"""
        if not self.telegram_token_var.get().strip():
            messagebox.showerror("Error", "Please enter a Telegram bot token.")
            return False
        if not self.telegram_chat_id_var.get().strip():
            messagebox.showerror("Error", "Please enter your Telegram chat ID.")
            return False
        return True
    
    # Step 6: Installation Progress
    def create_installation_page(self):
        install_frame = ttk.Frame(self.main_frame)
        install_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(install_frame, text="Installing LookAway", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Progress information
        self.install_status_var = tk.StringVar(value="Preparing installation...")
        status_label = ttk.Label(install_frame, textvariable=self.install_status_var)
        status_label.pack(pady=(0, 10))
        
        # Detailed progress bar
        self.install_progress_var = tk.DoubleVar()
        self.install_progress = ttk.Progressbar(install_frame, 
                                              variable=self.install_progress_var, 
                                              maximum=100, length=400)
        self.install_progress.pack(pady=(0, 20))
        
        # Installation log
        log_frame = ttk.LabelFrame(install_frame, text="Installation Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.install_log = scrolledtext.ScrolledText(log_frame, height=10, state=tk.DISABLED)
        self.install_log.pack(fill=tk.BOTH, expand=True)
    
    # Step 7: Completion
    def create_completion_page(self):
        completion_frame = ttk.Frame(self.main_frame)
        completion_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(completion_frame, text="Installation Complete!", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(20, 30))
        
        success_text = """LookAway has been successfully installed on your computer.

The application is ready to help you maintain healthy eye habits by 
reminding you to take regular breaks from screen time.

You can start the application now or access it later from:
• Desktop shortcut (if created)
• Start Menu
• Installation folder"""
        
        success_label = ttk.Label(completion_frame, text=success_text, 
                                 wraplength=500, justify=tk.CENTER)
        success_label.pack(pady=20)
        
        # Final options
        if hasattr(self, 'launch_after_var') and self.launch_after_var.get():
            launch_info = ttk.Label(completion_frame, 
                                   text="LookAway will start automatically when you click Finish.",
                                   font=('Arial', 10, 'italic'))
            launch_info.pack(pady=(20, 0))
    
    def log_installation_step(self, message):
        """Add message to installation log"""
        if hasattr(self, 'install_log'):
            self.install_log.config(state=tk.NORMAL)
            self.install_log.insert(tk.END, f"{message}\n")
            self.install_log.see(tk.END)
            self.install_log.config(state=tk.DISABLED)
            self.root.update()
    
    def update_installation_progress(self, progress, status):
        """Update installation progress"""
        if hasattr(self, 'install_progress_var'):
            self.install_progress_var.set(progress)
        if hasattr(self, 'install_status_var'):
            self.install_status_var.set(status)
        self.root.update()
    
    def start_installation(self):
        """Start the installation process"""
        # Collect final configuration
        self.config['install_path'] = self.path_var.get()
        self.config['reminder_interval'] = self.interval_var.get()
        self.config['sleep_start'] = self.sleep_start_var.get()
        self.config['sleep_end'] = self.sleep_end_var.get()
        self.config['email_enabled'] = self.email_var.get()
        self.config['telegram_enabled'] = self.telegram_var.get()
        self.config['create_desktop_shortcut'] = self.desktop_shortcut_var.get()
        self.config['create_start_menu'] = self.start_menu_var.get()
        self.config['auto_start'] = self.auto_start_var.get()
        self.config['launch_after_install'] = self.launch_after_var.get()
        
        # Disable navigation during installation
        self.next_btn.config(state="disabled")
        self.back_btn.config(state="disabled")
        self.cancel_btn.config(state="disabled")
        
        # Start installation in separate thread
        install_thread = threading.Thread(target=self.perform_installation)
        install_thread.daemon = True
        install_thread.start()
    
    def perform_installation(self):
        """Perform the actual installation"""
        try:
            # Installation steps
            steps = [
                ("Creating installation directory...", self.create_installation_directory, 10),
                ("Extracting application files...", self.extract_application_files, 30),
                ("Setting up configuration...", self.setup_configuration, 50),
                ("Creating shortcuts...", self.create_shortcuts, 70),
                ("Configuring startup options...", self.configure_startup, 85),
                ("Finalizing installation...", self.finalize_installation, 100)
            ]
            
            for status, func, progress in steps:
                self.update_installation_progress(progress, status)
                self.log_installation_step(status)
                func()
            
            self.log_installation_step("Installation completed successfully!")
            
            # Re-enable navigation
            self.root.after(0, self.enable_completion)
            
        except Exception as e:
            self.log_installation_step(f"Installation failed: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Installation Error", 
                                                           f"Installation failed: {str(e)}"))
            self.root.after(0, self.enable_completion)
    
    def enable_completion(self):
        """Enable completion navigation"""
        self.current_step += 1
        self.show_current_step()
        self.next_btn.config(state="normal")
    
    def create_installation_directory(self):
        """Create the installation directory"""
        os.makedirs(self.config['install_path'], exist_ok=True)
        self.log_installation_step(f"Created directory: {self.config['install_path']}")
    
    def extract_application_files(self):
        """Extract all application files to installation directory"""
        # This is where the embedded application files would be extracted
        # For now, we'll copy from the current directory structure
        
        app_files = self.get_embedded_app_data()
        
        for file_path, file_data in app_files.items():
            full_path = os.path.join(self.config['install_path'], file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            if isinstance(file_data, bytes):
                with open(full_path, 'wb') as f:
                    f.write(file_data)
            else:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_data)
            
            self.log_installation_step(f"Extracted: {file_path}")
    
    def get_embedded_app_data(self):
        """Get embedded application data"""
        # This function gets replaced with actual embedded files
        # For now, return a placeholder structure
        return {
            'LookAway.exe': b'# Placeholder for main executable',
            'config/settings.json': '{}',
            'LICENSE': self.get_license_text(),
            'README.txt': 'LookAway - Eye Break Reminder\n\nThank you for installing LookAway!'
        }
    
    def setup_configuration(self):
        """Set up initial configuration"""
        config_dir = os.path.join(self.config['install_path'], 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        # Create initial configuration
        initial_config = {
            'reminder_interval': self.config['reminder_interval'],
            'notification_methods': {
                'desktop': True,
                'email': self.config['email_enabled'],
                'telegram': self.config['telegram_enabled']
            },
            'sleep_hours': {
                'start': self.config['sleep_start'],
                'end': self.config['sleep_end']
            },
            'first_run': True,
            'version': '1.0.0'
        }
        
        # Add email configuration if enabled and configured
        if self.config['email_enabled'] and 'email_settings' in self.config:
            initial_config['email_settings'] = self.config['email_settings']
        
        # Add telegram configuration if enabled and configured
        if self.config['telegram_enabled'] and 'telegram_settings' in self.config:
            initial_config['telegram_settings'] = self.config['telegram_settings']
        
        config_file = os.path.join(config_dir, 'settings.json')
        with open(config_file, 'w') as f:
            json.dump(initial_config, f, indent=2)
        
        self.log_installation_step("Configuration file created")
    
    def create_shortcuts(self):
        """Create desktop and start menu shortcuts"""
        if self.config['create_desktop_shortcut']:
            self.create_desktop_shortcut()
        
        if self.config['create_start_menu']:
            self.create_start_menu_shortcut()
    
    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        try:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "LookAway.lnk")
            target_path = os.path.join(self.config['install_path'], "LookAway.exe")
            
            # Create shortcut using Windows Script Host
            self.create_windows_shortcut(shortcut_path, target_path, self.config['install_path'])
            self.log_installation_step("Desktop shortcut created")
        except Exception as e:
            self.log_installation_step(f"Failed to create desktop shortcut: {e}")
    
    def create_start_menu_shortcut(self):
        """Create Start Menu shortcut"""
        try:
            start_menu = os.path.join(os.environ['APPDATA'], 
                                     "Microsoft", "Windows", "Start Menu", "Programs")
            shortcut_dir = os.path.join(start_menu, "LookAway")
            os.makedirs(shortcut_dir, exist_ok=True)
            
            shortcut_path = os.path.join(shortcut_dir, "LookAway.lnk")
            target_path = os.path.join(self.config['install_path'], "LookAway.exe")
            
            self.create_windows_shortcut(shortcut_path, target_path, self.config['install_path'])
            self.log_installation_step("Start Menu shortcut created")
        except Exception as e:
            self.log_installation_step(f"Failed to create Start Menu shortcut: {e}")
    
    def create_windows_shortcut(self, shortcut_path, target_path, working_dir):
        """Create Windows shortcut using multiple methods"""
        try:
            # Method 1: Try using win32com if available
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = target_path
                shortcut.WorkingDirectory = working_dir
                shortcut.IconLocation = target_path
                shortcut.save()
                return
            except ImportError:
                pass
            
            # Method 2: Use VBS script (works without additional dependencies)
            vbs_script = f'''
Set WshShell = WScript.CreateObject("WScript.Shell")
Set Shortcut = WshShell.CreateShortcut("{shortcut_path}")
Shortcut.TargetPath = "{target_path}"
Shortcut.WorkingDirectory = "{working_dir}"
Shortcut.IconLocation = "{target_path}"
Shortcut.Save
'''
            
            vbs_path = shortcut_path.replace('.lnk', '_temp.vbs')
            with open(vbs_path, 'w') as f:
                f.write(vbs_script)
            
            # Execute VBS script
            result = subprocess.run(['cscript', '//NoLogo', vbs_path], 
                                  capture_output=True, text=True)
            os.remove(vbs_path)
            
            if result.returncode == 0:
                return
            
        except Exception:
            pass
        
        # Method 3: Fallback to batch file
        batch_path = shortcut_path.replace('.lnk', '.bat')
        with open(batch_path, 'w') as f:
            f.write(f'@echo off\ncd /d "{working_dir}"\nstart "" "{target_path}"\n')
        
        # Also create a PowerShell script version
        ps_path = shortcut_path.replace('.lnk', '.ps1')
        ps_content = f'''
Set-Location -Path "{working_dir}"
Start-Process -FilePath "{target_path}"
'''
        with open(ps_path, 'w') as f:
            f.write(ps_content)
    
    def configure_startup(self):
        """Configure Windows startup if requested"""
        if self.config['auto_start']:
            try:
                # Add to Windows startup registry
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                exe_path = os.path.join(self.config['install_path'], "LookAway.exe")
                winreg.SetValueEx(key, "LookAway", 0, winreg.REG_SZ, exe_path)
                winreg.CloseKey(key)
                self.log_installation_step("Added to Windows startup")
            except Exception as e:
                self.log_installation_step(f"Failed to add to startup: {e}")
    
    def finalize_installation(self):
        """Finalize the installation"""
        # Create uninstaller
        self.create_uninstaller()
        
        # Add to Windows Programs and Features
        self.register_with_windows()
        
        self.log_installation_step("Installation registered with Windows")
    
    def create_uninstaller(self):
        """Create uninstaller"""
        uninstaller_content = f'''
import os
import sys
import shutil
import winreg
from tkinter import messagebox

def uninstall():
    try:
        # Remove from startup
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 
                               0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "LookAway")
            winreg.CloseKey(key)
        except:
            pass
        
        # Remove shortcuts
        desktop = os.path.join(os.path.expanduser("~"), "Desktop", "LookAway.lnk")
        if os.path.exists(desktop):
            os.remove(desktop)
        
        # Remove installation directory
        install_dir = r"{self.config['install_path']}"
        if os.path.exists(install_dir):
            shutil.rmtree(install_dir)
        
        messagebox.showinfo("Uninstall Complete", "LookAway has been successfully removed.")
        
    except Exception as e:
        messagebox.showerror("Uninstall Error", f"Error during uninstallation: {{e}}")

if __name__ == "__main__":
    uninstall()
'''
        
        uninstaller_path = os.path.join(self.config['install_path'], 'uninstall.py')
        with open(uninstaller_path, 'w') as f:
            f.write(uninstaller_content)
    
    def register_with_windows(self):
        """Register application with Windows Programs and Features"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\LookAway"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "LookAway")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "LookAway Developer")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, self.config['install_path'])
            
            uninstall_path = os.path.join(self.config['install_path'], 'uninstall.py')
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'python "{uninstall_path}"')
            
            winreg.CloseKey(key)
        except Exception as e:
            self.log_installation_step(f"Failed to register with Windows: {e}")
    
    def finish_installation(self):
        """Finish installation and launch app if requested"""
        if self.config['launch_after_install']:
            try:
                exe_path = os.path.join(self.config['install_path'], 'LookAway.exe')
                if os.path.exists(exe_path):
                    subprocess.Popen([exe_path], cwd=self.config['install_path'])
            except Exception as e:
                messagebox.showerror("Launch Error", f"Could not launch LookAway: {e}")
        
        self.root.quit()
    
    def run(self):
        """Run the installer wizard"""
        self.root.mainloop()


def main():
    """Main entry point"""
    print("DEBUG: main() function started")
    try:
        print("DEBUG: Creating InstallerWizard instance...")
        installer = InstallerWizard()
        print("DEBUG: Running installer...")
        installer.run()
        print("DEBUG: Installer finished normally")
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Installer Error", f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("DEBUG: Script started")
    main()
#!/usr/bin/env python3
"""
LookAway - Eye Break Reminder Application

Main entry point for the LookAway application.
Handles application startup, system tray integration, and service management.
"""

import sys
import os
import logging
import signal
import argparse
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_manager import ConfigManager
from scheduler import EyeBreakScheduler, TrayController
from setup import SetupWizard


class LookAwayApp:
    """Main application controller."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.scheduler = None
        self.tray_controller = None
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def _setup_logging(self):
        """Setup application logging."""
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'lookaway.log')
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_setup(self, force=False):
        """Run the setup wizard."""
        if force or self.config_manager.is_first_run():
            wizard = SetupWizard()
            return wizard.run_setup()
        else:
            print("LookAway is already configured.")
            print("Use --force-setup to reconfigure.")
            return False
    
    def start_service(self, tray_mode=True):
        """Start the reminder service."""
        try:
            # Check if setup is needed
            if self.config_manager.is_first_run():
                print("First run detected. Starting setup wizard...")
                if not self.run_setup():
                    print("Setup required to run LookAway. Exiting.")
                    return False
            
            # Initialize scheduler
            self.scheduler = EyeBreakScheduler(self.config_manager)
            self.scheduler.start()
            
            self.logger.info("LookAway service started")
            
            if tray_mode:
                self._run_with_tray()
            else:
                self._run_console_mode()
            
            return True
            
        except KeyboardInterrupt:
            self.logger.info("Service stopped by user")
            return True
        except Exception as e:
            self.logger.error(f"Error starting service: {e}")
            return False
        finally:
            if self.scheduler:
                self.scheduler.stop()
    
    def _run_with_tray(self):
        """Run application with system tray integration."""
        self.tray_controller = TrayController(self.scheduler)
        
        if self.tray_controller.tray_available:
            tray_icon = self.tray_controller.create_tray_icon()
            if tray_icon:
                self.logger.info("System tray icon created. Application running in background.")
                print("LookAway is now running in the system tray.")
                print("Right-click the tray icon for options.")
                
                # Setup signal handlers for graceful shutdown
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
                
                # Run the tray icon (this blocks)
                tray_icon.run()
            else:
                self.logger.warning("Could not create tray icon, falling back to console mode")
                self._run_console_mode()
        else:
            self.logger.warning("System tray not available, running in console mode")
            self._run_console_mode()
    
    def _run_console_mode(self):
        """Run application in console mode."""
        print("LookAway running in console mode.")
        print("Commands:")
        print("  status  - Show current status")
        print("  pause   - Pause reminders")
        print("  resume  - Resume reminders")
        print("  snooze  - Snooze next reminder")
        print("  dnd     - Toggle Do Not Disturb")
        print("  test    - Test notifications")
        print("  quit    - Exit application")
        print()
        
        try:
            while True:
                command = input("LookAway> ").strip().lower()
                
                if command == 'status':
                    self._print_status()
                elif command == 'pause':
                    self.scheduler.pause()
                    print("Reminders paused.")
                elif command == 'resume':
                    self.scheduler.resume()
                    print("Reminders resumed.")
                elif command == 'snooze':
                    minutes = input("Snooze for how many minutes? (default: 5): ").strip()
                    try:
                        minutes = int(minutes) if minutes else 5
                        self.scheduler.snooze(minutes)
                        print(f"Next reminder snoozed for {minutes} minutes.")
                    except ValueError:
                        print("Invalid number.")
                elif command == 'dnd':
                    new_state = self.scheduler.toggle_do_not_disturb()
                    print(f"Do Not Disturb {'enabled' if new_state else 'disabled'}.")
                elif command == 'test':
                    results = self.scheduler.notification_manager.test_all_connections()
                    print(f"Notification test results: {results}")
                elif command in ['quit', 'exit', 'q']:
                    print("Exiting LookAway...")
                    break
                elif command == 'help':
                    print("Available commands: status, pause, resume, snooze, dnd, test, quit")
                elif command:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
                
        except (KeyboardInterrupt, EOFError):
            print("\nExiting LookAway...")
    
    def _print_status(self):
        """Print current application status."""
        status = self.scheduler.get_status()
        print("\nLookAway Status:")
        print(f"  Running: {status['is_running']}")
        print(f"  Paused: {status['is_paused']}")
        print(f"  Do Not Disturb: {status['do_not_disturb']}")
        print(f"  Sleep Time: {status['is_sleep_time']}")
        print(f"  Total Reminders: {status['reminder_count']}")
        print(f"  Reminder Interval: {status['interval_minutes']} minutes")
        print(f"  Enabled Notifications: {', '.join(status['enabled_notifications'])}")
        if status['last_reminder_time']:
            print(f"  Last Reminder: {status['last_reminder_time']}")
        if status['next_reminder_time']:
            print(f"  Next Reminder: {status['next_reminder_time']}")
        if status['snooze_until']:
            print(f"  Snoozed Until: {status['snooze_until']}")
        print()
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        if self.scheduler:
            self.scheduler.stop()
        if self.tray_controller and self.tray_controller.tray_icon:
            self.tray_controller.tray_icon.stop()
        sys.exit(0)
    
    def show_status(self):
        """Show application status and exit."""
        if not os.path.exists(self.config_manager.config_file):
            print("LookAway is not configured. Run setup first.")
            return
        
        # Create temporary scheduler to get status
        temp_scheduler = EyeBreakScheduler(self.config_manager)
        self._print_status_from_scheduler(temp_scheduler)
    
    def _print_status_from_scheduler(self, scheduler):
        """Print status from a scheduler instance."""
        config = scheduler.config
        
        print("\nLookAway Configuration:")
        print(f"  Reminder Interval: {config.get('reminder_interval_minutes', 20)} minutes")
        
        notifications = config.get('notifications', {})
        enabled_notifications = [k for k, v in notifications.items() if v]
        print(f"  Enabled Notifications: {', '.join(enabled_notifications) if enabled_notifications else 'None'}")
        
        sleep_hours = config.get('sleep_hours', {})
        print(f"  Sleep Hours: {sleep_hours.get('start', 'N/A')} - {sleep_hours.get('end', 'N/A')}")
        
        print(f"  Long Break Interval: Every {config.get('long_break_interval', 3)} reminders")
        print(f"  Snooze Duration: {config.get('snooze_minutes', 5)} minutes")
        
        # Check if service might be running
        print(f"\nService appears to be: {'Configured' if not config.get('first_run', True) else 'Not configured'}")
        print("Note: Use 'python main.py start' to run the service")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="LookAway - Eye Break Reminder")
    parser.add_argument('command', nargs='?', choices=['start', 'setup', 'status'], 
                       default='start', help='Command to run (default: start)')
    parser.add_argument('--no-tray', action='store_true', 
                       help='Run in console mode instead of system tray')
    parser.add_argument('--force-setup', action='store_true',
                       help='Force setup wizard to run')
    
    args = parser.parse_args()
    
    app = LookAwayApp()
    
    try:
        if args.command == 'setup' or args.force_setup:
            success = app.run_setup(force=args.force_setup)
            sys.exit(0 if success else 1)
        
        elif args.command == 'status':
            app.show_status()
            sys.exit(0)
        
        elif args.command == 'start':
            success = app.start_service(tray_mode=not args.no_tray)
            sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error: {e}")
        logging.error(f"Unhandled error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
LookAway - Eye Break Reminder Application

Main entry point for the LookAway application.
Handles application startup, system tray integration, and service management.
"""

import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

try:
    # Add src directory to path for imports FIRST
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

    # Initialize exception handling as early as possible
    from exception_handler import initialize_exception_handler, log_critical_error, cleanup_exception_handler, flush_exception_logs
    
    # Create a basic exception handler immediately
    _early_exception_handler = initialize_exception_handler(enabled=True)
    print("Early exception handling initialized")
    flush_exception_logs()
    
except Exception as e:
    log_critical_error(f"EARLY EXCEPTION TRACEBACK:\n{traceback.format_exc()}")
    print(f"Warning: Could not initialize early exception handling: {e}")

# Now import other modules
try:
    import logging
    import signal
    import argparse

    from config_manager import ConfigManager
    from scheduler import EyeBreakScheduler, TrayController
    from setup import SetupWizard

except Exception as e:
    log_critical_error(f"MODULE IMPORT EXCEPTION: {str(e)}")
    log_critical_error(f"MODULE IMPORT TRACEBACK:\n{traceback.format_exc()}")
    print(f"Critical Error: Failed to import required modules: {e}")
    sys.exit(1)


class LookAwayApp:
    """Main application controller."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.scheduler = None
        self.tray_controller = None
        self.exception_handler = None
        
        # Load config first
        try:
            self.config = self.config_manager.load_config()
        except Exception as e:
            print(f"Warning: Could not load config, using defaults: {e}")
            self.config = {}
        
        # Setup exception handling first
        self._setup_exception_handling()
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def _setup_exception_handling(self):
        """Setup centralized exception handling."""
        try:
            # Try to load config, but use defaults if it fails
            exception_logging_enabled = True
            log_directory = 'logs'
            
            try:
                config = self.config_manager.load_config()
                logging_config = config.get('logging', {})
                exception_logging_enabled = logging_config.get('exception_logging', True)
                log_directory = logging_config.get('log_directory', 'logs')
            except Exception as config_error:
                print(f"Warning: Could not load config for exception handling, using defaults: {config_error}")
            
            # Convert relative path to absolute
            if not os.path.isabs(log_directory):
                log_directory = os.path.join(os.path.dirname(__file__), log_directory)
            
            # Re-initialize exception handler with proper configuration
            # (The early handler might use defaults)
            self.exception_handler = initialize_exception_handler(
                enabled=exception_logging_enabled,
                log_dir=Path(log_directory)
            )
            
            if exception_logging_enabled:
                print(f"Exception logging configured - logs will be written to: {log_directory}")
            else:
                print("Exception logging disabled by configuration")
                
        except Exception as e:
            print(f"Warning: Failed to setup configured exception handling: {e}")
            # Continue with the early exception handler if it exists
    
    def _setup_logging(self):
        """Setup application logging."""
        # For .exe compatibility, use current working directory instead of __file__ location
        if getattr(sys, 'frozen', False):
            # Running as .exe - use current working directory
            log_dir = os.path.join(os.getcwd(), 'logs')
        else:
            # Running as Python script - use script directory
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            
        os.makedirs(log_dir, exist_ok=True)
        
        # Clean up old log files
        self._cleanup_old_logs(log_dir)
        
        log_file = os.path.join(log_dir, 'lookaway.log')
        
        # Clear any existing handlers to avoid conflicts
        logging.getLogger().handlers.clear()
        
        # Get logging level from config
        log_level_name = self.config.get('logging', {}).get('level', 'INFO')
        log_level = getattr(logging, log_level_name.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Control third-party library logging levels
        # Suppress httpx HTTP request logs (used by telegram library)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        # Also suppress telegram library's verbose logging
        logging.getLogger('telegram').setLevel(logging.WARNING)
        
        # Log the setup information for debugging
        logging.info(f"Logging configured - log file: {log_file}")
        logging.info(f"Working directory: {os.getcwd()}")
        logging.info(f"Script location: {os.path.dirname(__file__)}")
        logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    
    def _cleanup_old_logs(self, log_dir):
        """Clean up old log files based on configuration."""
        try:
            max_log_files = self.config.get('logging', {}).get('max_log_files', 5)
            max_file_size_mb = self.config.get('logging', {}).get('max_file_size_mb', 10)
            
            # Get all log files
            log_files = []
            for filename in os.listdir(log_dir):
                if filename.endswith(('.log', '.txt')):
                    filepath = os.path.join(log_dir, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        log_files.append({
                            'path': filepath,
                            'name': filename,
                            'mtime': stat.st_mtime,
                            'size': stat.st_size
                        })
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x['mtime'], reverse=True)
            
            # Remove files that are too large
            for log_file in log_files[:]:  # Copy list to modify during iteration
                size_mb = log_file['size'] / (1024 * 1024)
                if size_mb > max_file_size_mb:
                    try:
                        os.remove(log_file['path'])
                        print(f"Removed oversized log file: {log_file['name']} ({size_mb:.1f}MB)")
                        log_files.remove(log_file)
                    except OSError as e:
                        print(f"Failed to remove {log_file['name']}: {e}")
            
            # Keep only the newest N files
            if len(log_files) > max_log_files:
                for log_file in log_files[max_log_files:]:
                    try:
                        os.remove(log_file['path'])
                        print(f"Removed old log file: {log_file['name']}")
                    except OSError as e:
                        print(f"Failed to remove {log_file['name']}: {e}")
                        
        except Exception as e:
            print(f"Error during log cleanup: {e}")
            # Don't let log cleanup errors break the app

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
            log_critical_error(f"Failed to start LookAway service: {str(e)}", exc_info=True)
            return False
        finally:
            if self.scheduler:
                self.scheduler.stop()
            self._cleanup()
    
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
                try:
                    tray_icon.run()
                    # If we reach here, the tray icon exited normally
                    print("Tray icon exited")
                except Exception as tray_error:
                    # This IS a critical error - the tray crashed unexpectedly
                    log_critical_error(f"Tray icon crashed: {str(tray_error)}", exc_info=True)
                    print(f"Tray icon error: {tray_error}")
                    print("Falling back to console mode...")
                    self._run_console_mode()
            else:
                self.logger.warning("Could not create tray icon, falling back to console mode")
                self._run_console_mode()
        else:
            self.logger.warning("System tray not available, running in console mode")
            self._run_console_mode()
    
    def _run_console_mode(self):
        """Run application in console mode."""
        
        try:
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
            
            # Check if we have a proper console for input
            import sys
            if not sys.stdin.isatty():
                print("Running in simple mode (no interactive console)")
                print("LookAway will run until you close this window.")
                print("Press Ctrl+C to exit gracefully.")
                try:
                    import time
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nShutting down gracefully...")
                return
            
            while True:
                try:
                    command = input("LookAway> ").strip().lower()
                except EOFError:
                    print("\nEOF received, shutting down...")
                    break
                except Exception as input_error:
                    # If input fails, we can't continue in console mode
                    print("Console input failed, exiting...")
                    break
                
                if command == 'status':
                    self._print_status()
                elif command == 'pause':
                    self.scheduler.pause()
                    print("Reminders paused.")
                elif command == 'resume':
                    self.scheduler.resume()
                    print("Reminders resumed.")
                elif command == 'snooze':
                    try:
                        minutes = input("Snooze for how many minutes? (default: 5): ").strip()
                        minutes = int(minutes) if minutes else 5
                        self.scheduler.snooze(minutes)
                        print(f"Next reminder snoozed for {minutes} minutes.")
                    except (ValueError, EOFError) as snooze_error:
                        print("Using default 5 minutes.")
                        self.scheduler.snooze(5)
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
                elif command == '':
                    # Empty command, just continue
                    pass
                elif command:
                    print(f"Unknown command: {command}. Type 'help' for available commands.")
                
        except (KeyboardInterrupt, EOFError) as e:
            print("\nExiting LookAway...")
        except Exception as console_error:
            print(f"Console mode error: {console_error}")
        finally:
            print("Console mode cleanup complete")
    
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
        self._cleanup()
        sys.exit(0)
    
    def _cleanup(self):
        """Cleanup resources before exit."""
        try:
            cleanup_exception_handler()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
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
    
    app = None
    
    try:
        app = LookAwayApp()
        
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
        print(f"Critical Error: {e}")
        logging.error(f"Unhandled critical error: {e}", exc_info=True)
        
        # Try to log with exception handler if available
        try:
            logging.error(f"Unhandled critical error in main: {str(e)}", exc_info=True)
        except:
            pass  # Exception handler might not be initialized
        
        sys.exit(1)
    
    finally:
        # Ensure cleanup happens
        if app:
            app._cleanup()


if __name__ == "__main__":
    main()
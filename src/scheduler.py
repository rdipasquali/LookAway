import time
import random
import logging
import threading
from datetime import datetime, time as dt_time
from typing import Dict, Any, Optional
from config_manager import ConfigManager
from notifications import NotificationManager

# System tray imports
try:
    import pystray
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    pystray = None

# Import exception handler functions
try:
    from exception_handler import log_exception, log_critical_error, flush_exception_logs
except ImportError:
    # Fallback if exception handler is not available
    def log_exception(exc_info=None, context=""):
        pass
    def log_critical_error(message, exc_info=None):
        pass
    def flush_exception_logs():
        pass


class EyeBreakScheduler:
    """Main scheduler for eye break reminders."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.config = config_manager.load_config()
        self.notification_manager = NotificationManager(self.config)
        
        self.is_running = False
        self.is_paused = False
        self.scheduler_thread = None
        self.reminder_count = 0
        self.last_reminder_time = None
        self.snooze_until = None
        
        log_level_name = self.config.get('logging', {}).get('level', 'INFO')
        log_level = getattr(logging, log_level_name.upper(), logging.INFO)

        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """Start the reminder scheduler."""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        self.is_running = True
        # Set the last reminder time to now so the first reminder happens after the full interval
        self.last_reminder_time = datetime.now()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.logger.info("Eye break scheduler started")
    
    def stop(self):
        """Stop the reminder scheduler."""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.logger.info("Eye break scheduler stopped")
    
    def pause(self, duration_minutes: Optional[int] = None):
        """Pause reminders for a specified duration or indefinitely."""
        self.is_paused = True
        if duration_minutes:
            # Schedule resumption
            resume_time = datetime.now().timestamp() + (duration_minutes * 60)
            timer = threading.Timer(duration_minutes * 60, self.resume)
            timer.daemon = True
            timer.start()
            self.logger.info(f"Scheduler paused for {duration_minutes} minutes")
        else:
            self.logger.info("Scheduler paused indefinitely")
    
    def resume(self):
        """Resume reminders."""
        self.is_paused = False
        self.snooze_until = None
        self.logger.info("Scheduler resumed")
    
    def snooze(self, minutes: Optional[int] = None):
        """Snooze the next reminder for specified minutes."""
        if minutes is None:
            minutes = self.config.get('snooze_minutes', 5)
        
        self.snooze_until = datetime.now().timestamp() + (minutes * 60)
        self.logger.info(f"Next reminder snoozed for {minutes} minutes")
    
    def toggle_do_not_disturb(self) -> bool:
        """Toggle Do Not Disturb mode."""
        current_dnd = self.config.get('do_not_disturb', False)
        new_dnd = not current_dnd
        
        self.config_manager.update_setting('do_not_disturb', new_dnd)
        self.config = self.config_manager.load_config()
        
        self.logger.info(f"Do Not Disturb mode {'enabled' if new_dnd else 'disabled'}")
        return new_dnd
    
    def _run_scheduler(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                if self._should_send_reminder():
                    self._send_reminder()
                
                # Sleep for 1 minute before checking again
                time.sleep(60)
                
            except Exception as e:
                log_critical_error(f"Exception in scheduler loop: {str(e)}", exc_info=True)
                self.logger.error(f"Error in scheduler loop: {e}")
                log_exception(context="Scheduler main loop")
                time.sleep(60)  # Continue running even if there's an error
    
    def _should_send_reminder(self) -> bool:
        """Check if a reminder should be sent now."""
        # Check if paused or in do not disturb mode
        if self.is_paused or self.config.get('do_not_disturb', False):
            return False
        
        # Check if snoozed
        if self.snooze_until and datetime.now().timestamp() < self.snooze_until:
            return False
        
        # Check sleep hours
        if self._is_sleep_time():
            return False
        
        # Check if enough time has passed since last reminder
        now = datetime.now()
        interval_seconds = self.config.get('reminder_interval_minutes', 20) * 60
        
        # If last_reminder_time is None (shouldn't happen after start() but defensive coding)
        if self.last_reminder_time is None:
            self.last_reminder_time = now
            return False  # Don't send immediate reminder on first check
        
        time_since_last = (now - self.last_reminder_time).total_seconds()
        return time_since_last >= interval_seconds
    
    def _is_sleep_time(self) -> bool:
        """Check if current time is within sleep hours."""
        try:
            sleep_start, sleep_end = self.config_manager.get_sleep_hours()
            current_time = datetime.now().time()
            
            # Handle sleep period that crosses midnight
            if sleep_start > sleep_end:
                return current_time >= sleep_start or current_time <= sleep_end
            else:
                return sleep_start <= current_time <= sleep_end
                
        except Exception as e:
            self.logger.error(f"Error checking sleep time: {e}")
            log_exception(context="Checking sleep time")
            return False
    
    def _send_reminder(self):
        """Send a reminder notification."""
        try:
            self.reminder_count += 1
            
            # Determine if this should be a long break
            long_break_interval = self.config.get('long_break_interval', 3)
            is_long_break = (self.reminder_count % long_break_interval) == 0
            
            # Get appropriate message and title
            if is_long_break:
                title = "Time for a Long Break!"
                break_info = self.config.get('break_types', {}).get('long_break', {})
                duration = break_info.get('duration_seconds', 300)
                message = f"{break_info.get('description', 'Take a longer break')} ({duration // 60} minutes)"
            else:
                title = "Eye Break Reminder"
                break_info = self.config.get('break_types', {}).get('quick_break', {})
                duration = break_info.get('duration_seconds', 20)
                
                # Get random message from configured messages
                messages = self.config.get('messages', ["Time to rest your eyes!"])
                message = random.choice(messages)
            
            # Add reminder count to message
            message += f"\n\nReminder #{self.reminder_count}"
            
            # Send notification
            results = self.notification_manager.send_notification(title, message)
            
            # Log results
            successful_methods = [method for method, success in results.items() if success]
            if successful_methods:
                self.logger.info(f"Reminder #{self.reminder_count} sent via: {', '.join(successful_methods)}")
            else:
                self.logger.warning(f"Reminder #{self.reminder_count} failed to send via any method")
                log_critical_error(f"Reminder #{self.reminder_count} FAILED - no methods worked")
            
            # Update last reminder time
            self.last_reminder_time = datetime.now()
            
            # Clear snooze if it was set
            self.snooze_until = None
            
        except Exception as e:
            self.logger.error(f"Error sending reminder: {e}")
            log_exception(context=f"Sending reminder #{self.reminder_count}")
            log_critical_error(f"Exception during reminder #{self.reminder_count}: {str(e)}", exc_info=True)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        next_reminder_time = None
        if self.last_reminder_time:
            interval_seconds = self.config.get('reminder_interval_minutes', 20) * 60
            next_reminder_time = self.last_reminder_time.timestamp() + interval_seconds
        
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'do_not_disturb': self.config.get('do_not_disturb', False),
            'reminder_count': self.reminder_count,
            'last_reminder_time': self.last_reminder_time.isoformat() if self.last_reminder_time else None,
            'next_reminder_time': datetime.fromtimestamp(next_reminder_time).isoformat() if next_reminder_time else None,
            'snooze_until': datetime.fromtimestamp(self.snooze_until).isoformat() if self.snooze_until else None,
            'enabled_notifications': self.notification_manager.get_enabled_methods(),
            'is_sleep_time': self._is_sleep_time(),
            'interval_minutes': self.config.get('reminder_interval_minutes', 20)
        }
    
    def reload_config(self):
        """Reload configuration from file."""
        self.config = self.config_manager.load_config()
        self.notification_manager.reload_config(self.config)
        self.logger.info("Configuration reloaded")


class TrayController:
    """System tray controller for the application."""
    
    def __init__(self, scheduler: EyeBreakScheduler):
        self.scheduler = scheduler
        self.tray_icon = None
        
        try:
            import pystray
            from PIL import Image
            self.pystray = pystray
            self.PIL_Image = Image
            self.tray_available = True
        except ImportError:
            self.tray_available = False
            logging.warning("System tray not available (pystray/PIL not installed)")
    
    def create_tray_icon(self):
        """Create and configure the system tray icon."""
        if not TRAY_AVAILABLE:
            logging.warning("pystray not available, cannot create tray icon")
            return None
            
        try:
            # Create a simple icon using PIL
            from PIL import Image, ImageDraw
            
            # Create a 64x64 icon with a simple eye design
            image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw eye shape (circle with inner circle)
            draw.ellipse([8, 20, 56, 44], fill=(0, 100, 200, 255))  # Blue eye
            draw.ellipse([24, 26, 40, 38], fill=(255, 255, 255, 255))  # White center
            draw.ellipse([28, 28, 36, 36], fill=(0, 0, 0, 255))  # Black pupil
            
            # Create the menu items - simplified for better compatibility
            menu_items = [
                pystray.MenuItem("Snooze 5min", self._snooze_5_min),
                pystray.MenuItem("Pause/Resume", self._toggle_pause),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Do Not Disturb", self._toggle_dnd),
                pystray.MenuItem("Test Notifications", self._test_notifications),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Reload Config", self._reload_config),
                pystray.MenuItem("Exit", self._exit_application)
            ]
            
            # Create the tray icon with both left and right click support
            self.tray_icon = pystray.Icon(
                "lookaway",
                image,
                menu=pystray.Menu(*menu_items),
                title="LookAway - Eye Break Reminder"
            )
            
            # For Wayland compatibility, set default action on left click
            # Some desktop environments don't support right-click menus properly
            self.tray_icon.default_action = self._show_status_menu
            
            logging.info("Tray icon created successfully")
            print("DEBUG: Tray icon created with both left and right click support")
            return self.tray_icon
            
        except Exception as e:
            logging.error(f"Failed to create tray icon: {e}")
            print(f"DEBUG: Tray icon creation failed: {e}")
            return None
    
    def _show_about(self, icon, item):
        """Show about information."""
        pass  # Disabled menu item
    
    def _show_status(self, icon=None, item=None):
        """Show current status."""
        status = self.scheduler.get_status()
        status_text = f"""LookAway Status:

Running: {status['is_running']}
Paused: {status['is_paused']}
Do Not Disturb: {status['do_not_disturb']}
Total Reminders: {status['reminder_count']}
Interval: {status['interval_minutes']} minutes
Enabled Notifications: {', '.join(status['enabled_notifications'])}
Sleep Time: {status['is_sleep_time']}"""
        
        # Show GUI dialog
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # Create a temporary root window (hidden)
            temp_root = tk.Tk()
            temp_root.withdraw()
            
            # Show status dialog
            messagebox.showinfo("LookAway Status", status_text)
            
            # Clean up
            temp_root.destroy()
            
        except Exception as e:
            # Fallback to console output
            print(status_text)
            print(f"GUI dialog error: {e}")
        
        logging.info(f"Status requested via tray: {status}")

    def _snooze_5_min(self, icon, item):
        """Snooze for 5 minutes."""
        print("DEBUG: Snooze menu item clicked!")
        self.scheduler.snooze(5)
        logging.info("Snoozed for 5 minutes via tray")

    def _toggle_pause(self, icon, item):
        """Toggle pause state."""
        print("DEBUG: Pause/Resume menu item clicked!")
        if self.scheduler.is_paused:
            self.scheduler.resume()
            logging.info("Resumed via tray")
        else:
            self.scheduler.pause()
            logging.info("Paused via tray")

    def _toggle_dnd(self, icon, item):
        """Toggle Do Not Disturb mode."""
        print("DEBUG: Do Not Disturb menu item clicked!")
        new_state = self.scheduler.toggle_do_not_disturb()
        logging.info(f"Do Not Disturb {'enabled' if new_state else 'disabled'} via tray")

    def _test_notifications(self, icon, item):
        """Test all notification methods."""
        print("DEBUG: Test Notifications menu item clicked!")
        results = self.scheduler.notification_manager.test_all_connections()
        print(f"Notification test results: {results}")
        logging.info(f"Notification test via tray: {results}")

    def _reload_config(self, icon, item):
        """Reload configuration."""
        print("DEBUG: Reload Config menu item clicked!")
        self.scheduler.reload_config()
        logging.info("Config reloaded via tray")

    def _show_status_menu(self, icon, item=None):
        """Show status menu on left click for Wayland compatibility."""
        print("DEBUG: Left click on tray icon - showing status")
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            # Create a simple status window
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            status = "Paused" if self.scheduler.is_paused else "Running"
            dnd_status = "On" if hasattr(self.scheduler, 'do_not_disturb') and self.scheduler.do_not_disturb else "Off"
            
            message = f"""LookAway Status:
            
Status: {status}
Do Not Disturb: {dnd_status}
            
Right-click the tray icon for more options."""
            
            messagebox.showinfo("LookAway Status", message)
            root.destroy()
            
        except Exception as e:
            print(f"DEBUG: Failed to show status menu: {e}")
            logging.error(f"Failed to show status menu: {e}")

    def _exit_application(self, icon, item):
        """Exit the application."""
        print("DEBUG: Exit menu item clicked!")
        logging.info("Exit requested via tray")
        self.scheduler.stop()
        if self.tray_icon:
            self.tray_icon.stop()
# Quick test function
def test_scheduler():
    """Quick test of the scheduler functionality."""
    config_manager = ConfigManager()
    scheduler = EyeBreakScheduler(config_manager)
    
    print("Testing scheduler...")
    print(f"Status: {scheduler.get_status()}")
    
    # Test a manual reminder
    scheduler._send_reminder()
    
    print("Manual reminder sent (check your notifications)")
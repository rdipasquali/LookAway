import time
import random
import logging
import threading
from datetime import datetime, time as dt_time
from typing import Dict, Any, Optional
from config_manager import ConfigManager
from notifications import NotificationManager

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
        
        if self.last_reminder_time is None:
            return True
        
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
        """Create system tray icon."""
        if not self.tray_available:
            return None
        
        try:
            # Create a simple icon (you can replace this with an actual icon file)
            image = self.PIL_Image.new('RGB', (16, 16), color='blue')
            
            menu = self.pystray.Menu(
                self.pystray.MenuItem("LookAway", lambda: None, enabled=False),
                self.pystray.Menu.SEPARATOR,
                self.pystray.MenuItem("Status", self._show_status),
                self.pystray.MenuItem("Snooze 5 min", lambda: self.scheduler.snooze(5)),
                self.pystray.MenuItem("Pause/Resume", self._toggle_pause),
                self.pystray.MenuItem("Do Not Disturb", self._toggle_dnd),
                self.pystray.Menu.SEPARATOR,
                self.pystray.MenuItem("Test Notifications", self._test_notifications),
                self.pystray.MenuItem("Reload Config", self._reload_config),
                self.pystray.Menu.SEPARATOR,
                self.pystray.MenuItem("Exit", self._exit_application)
            )
            
            self.tray_icon = self.pystray.Icon(
                "LookAway",
                image,
                "LookAway - Eye Break Reminder",
                menu
            )
            
            return self.tray_icon
            
        except Exception as e:
            log_critical_error(f"Error creating tray icon: {str(e)}", exc_info=True)
            logging.error(f"Error creating tray icon: {e}")
            return None
    
    def _show_status(self):
        """Show current status."""
        status = self.scheduler.get_status()
        status_text = f"""
LookAway Status:
- Running: {status['is_running']}
- Paused: {status['is_paused']}
- Do Not Disturb: {status['do_not_disturb']}
- Total Reminders: {status['reminder_count']}
- Interval: {status['interval_minutes']} minutes
- Enabled Notifications: {', '.join(status['enabled_notifications'])}
- Sleep Time: {status['is_sleep_time']}
"""
        print(status_text)  # You could implement a proper dialog here
    
    def _toggle_pause(self):
        """Toggle pause state."""
        if self.scheduler.is_paused:
            self.scheduler.resume()
        else:
            self.scheduler.pause()
    
    def _toggle_dnd(self):
        """Toggle Do Not Disturb mode."""
        self.scheduler.toggle_do_not_disturb()
    
    def _test_notifications(self):
        """Test all notification methods."""
        results = self.scheduler.notification_manager.test_all_connections()
        print(f"Notification test results: {results}")
    
    def _reload_config(self):
        """Reload configuration."""
        self.scheduler.reload_config()
    
    def _exit_application(self):
        """Exit the application."""
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
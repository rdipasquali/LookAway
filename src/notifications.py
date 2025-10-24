import smtplib
import asyncio
import logging
from abc import ABC, abstractmethod
import email.mime.text
import email.mime.multipart
from typing import Dict, Any, Optional
from plyer import notification
import platform

try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

# Import exception handler functions
try:
    from exception_handler import log_exception, log_critical_error
except ImportError:
    # Fallback if exception handler is not available
    def log_exception(exc_info=None, context=""):
        pass
    def log_critical_error(message, exc_info=None):
        pass


class NotificationHandler(ABC):
    """Abstract base class for notification handlers."""
    
    @abstractmethod
    def send_notification(self, title: str, message: str) -> bool:
        """Send a notification. Returns True if successful."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the notification method is properly configured."""
        pass


class DesktopNotificationHandler(NotificationHandler):
    """Handles desktop notifications using plyer."""
    
    def __init__(self):
        self.app_name = "LookAway"
    
    def send_notification(self, title: str, message: str) -> bool:
        """Send a desktop notification."""
        try:
            # Different notification systems for different platforms
            if platform.system() == "Windows":
                notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    timeout=10,
                    toast=True
                )
            else:
                notification.notify(
                    title=title,
                    message=message,
                    app_name=self.app_name,
                    timeout=10
                )
            return True
        except Exception as e:
            log_critical_error(f"Desktop notification FAILED: {str(e)}", exc_info=True)
            logging.error(f"Desktop notification failed: {e}")
            log_exception(context="Desktop notification")
            return False
    
    def test_connection(self) -> bool:
        """Test desktop notifications."""
        return self.send_notification("LookAway Test", "Desktop notifications are working!")


class EmailNotificationHandler(NotificationHandler):
    """Handles email notifications via SMTP."""
    
    def __init__(self, config: Dict[str, Any]):
        self.smtp_server = config.get('smtp_server', '')
        self.smtp_port = config.get('smtp_port', 587)
        self.email = config.get('email', '')
        self.password = config.get('password', '')
        self.recipient = config.get('recipient', '')
    
    def send_notification(self, title: str, message: str) -> bool:
        """Send an email notification."""
        if not all([self.smtp_server, self.email, self.password, self.recipient]):
            logging.error("Email configuration incomplete")
            return False
        
        try:
            # Create message
            msg = email.mime.multipart.MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.recipient
            msg['Subject'] = f"LookAway Reminder: {title}"
            
            # Add body
            body = f"""
{title}

{message}

---
This is an automated reminder from LookAway.
Take care of your eyes! 👀
"""
            msg.attach(email.mime.text.MIMEText(body, 'plain'))
            
            # Connect to server and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            logging.error(f"Email notification failed: {e}")
            log_exception(context="Email notification")
            return False
    
    def test_connection(self) -> bool:
        """Test email configuration."""
        return self.send_notification("Test Notification", "Email notifications are working correctly!")


class TelegramNotificationHandler(NotificationHandler):
    """Handles Telegram notifications via bot."""
    
    def __init__(self, config: Dict[str, Any]):
        self.bot_token = config.get('bot_token', '')
        self.chat_id = config.get('chat_id', '')
        self.bot = None
        
        if TELEGRAM_AVAILABLE and self.bot_token:
            self.bot = Bot(token=self.bot_token)
    
    def send_notification(self, title: str, message: str) -> bool:
        """Send a Telegram notification."""
        try:
            if not TELEGRAM_AVAILABLE:
                logging.error("Telegram library not available")
                return False
                
            if not all([self.bot_token, self.chat_id]):
                logging.error("Telegram configuration incomplete")
                return False
            
            if not self.bot:
                logging.error("Telegram bot not initialized")
                return False
            
            try:
                full_message = f"🔔 *{title}*\n\n{message}\n\n_Take care of your eyes!_ 👀"
                
                # Improved asyncio handling for .exe environment
                
                # Use a more isolated approach for .exe compatibility
                import threading
                import queue
                
                result_queue = queue.Queue()
                exception_queue = queue.Queue()
                
                def telegram_thread():
                    """Run Telegram operation in separate thread with its own event loop."""
                    try:
                        # Create a completely fresh event loop for this thread
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        
                        try:
                            # Send the message in the new loop
                            new_loop.run_until_complete(
                                self.bot.send_message(
                                    chat_id=self.chat_id,
                                    text=full_message,
                                    parse_mode='Markdown'
                                )
                            )
                            result_queue.put(True)
                            
                        finally:
                            # Properly close the loop and all its resources
                            try:
                                # Cancel all running tasks
                                pending = asyncio.all_tasks(new_loop)
                                if pending:
                                    for task in pending:
                                        task.cancel()
                                    # Wait for cancellation to complete
                                    new_loop.run_until_complete(
                                        asyncio.gather(*pending, return_exceptions=True)
                                    )
                                
                                # Close the loop
                                new_loop.close()
                            except Exception as cleanup_error:
                                pass  # Ignore cleanup errors
                            
                    except Exception as thread_error:
                        exception_queue.put(thread_error)
                        result_queue.put(False)
                
                # Start the thread
                telegram_thread_obj = threading.Thread(target=telegram_thread, daemon=True)
                telegram_thread_obj.start()
                
                # Wait for completion with timeout
                telegram_thread_obj.join(timeout=30)  # 30 second timeout
                
                # Check results
                if telegram_thread_obj.is_alive():
                    logging.error("Telegram thread timed out")
                    return False
                
                if not exception_queue.empty():
                    thread_exception = exception_queue.get()
                    log_critical_error(f"Telegram thread exception: {str(thread_exception)}", exc_info=True)
                    raise thread_exception
                
                success = result_queue.get() if not result_queue.empty() else False
                return success
                        
            except TelegramError as telegram_error:
                log_critical_error(f"Telegram API error: {str(telegram_error)}", exc_info=True)
                logging.error(f"Telegram API error: {telegram_error}")
                return False
                
            except Exception as send_error:
                log_critical_error(f"Telegram send error: {str(send_error)}", exc_info=True)
                logging.error(f"Telegram notification failed: {send_error}")
                return False
                
        except Exception as outer_error:
            log_critical_error(f"Telegram notification outer exception: {str(outer_error)}", exc_info=True)
            logging.error(f"Telegram notification failed: {outer_error}")
            log_exception(context="Telegram notification outer")
            return False
    
    def test_connection(self) -> bool:
        """Test Telegram configuration."""
        if not TELEGRAM_AVAILABLE:
            return False
        return self.send_notification("Test Notification", "Telegram notifications are working correctly!")


class NotificationManager:
    """Manages multiple notification handlers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.handlers = {}
        self._initialize_handlers()
    
    def _initialize_handlers(self):
        """Initialize notification handlers based on configuration."""
        notifications_config = self.config.get('notifications', {})
        
        # Desktop notifications
        if notifications_config.get('desktop', False):
            self.handlers['desktop'] = DesktopNotificationHandler()
        
        # Email notifications
        if notifications_config.get('email', False):
            email_config = self.config.get('email_settings', {})
            self.handlers['email'] = EmailNotificationHandler(email_config)
        
        # Telegram notifications
        if notifications_config.get('telegram', False):
            telegram_config = self.config.get('telegram_settings', {})
            self.handlers['telegram'] = TelegramNotificationHandler(telegram_config)
    
    def send_notification(self, title: str, message: str) -> Dict[str, bool]:
        """Send notification via all enabled methods."""
        results = {}
        
        for name, handler in self.handlers.items():
            try:
                success = handler.send_notification(title, message)
                results[name] = success
                if success:
                    logging.info(f"Notification sent successfully via {name}")
                else:
                    logging.warning(f"Notification failed via {name}")
            except Exception as e:
                logging.error(f"Error sending notification via {name}: {e}")
                log_exception(context=f"Notification via {name}")
                results[name] = False
        
        return results
    
    def test_all_connections(self) -> Dict[str, bool]:
        """Test all configured notification methods."""
        results = {}
        
        for name, handler in self.handlers.items():
            try:
                results[name] = handler.test_connection()
            except Exception as e:
                logging.error(f"Error testing {name} connection: {e}")
                log_exception(context=f"Testing {name} connection")
                results[name] = False
        
        return results
    
    def get_enabled_methods(self) -> list[str]:
        """Get list of enabled notification methods."""
        return list(self.handlers.keys())
    
    def reload_config(self, config: Dict[str, Any]):
        """Reload configuration and reinitialize handlers."""
        self.config = config
        self.handlers.clear()
        self._initialize_handlers()
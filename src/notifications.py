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
            logging.error(f"Desktop notification failed: {e}")
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
        if not TELEGRAM_AVAILABLE:
            logging.error("Telegram library not available")
            return False
            
        if not all([self.bot_token, self.chat_id]):
            logging.error("Telegram configuration incomplete")
            return False
        
        try:
            full_message = f"🔔 *{title}*\n\n{message}\n\n_Take care of your eyes!_ 👀"
            
            # Use asyncio to run the async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.bot.send_message(
                        chat_id=self.chat_id,
                        text=full_message,
                        parse_mode='Markdown'
                    )
                )
                return True
            finally:
                loop.close()
                
        except Exception as e:
            logging.error(f"Telegram notification failed: {e}")
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
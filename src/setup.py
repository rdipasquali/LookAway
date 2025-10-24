import os
import sys
import getpass
import smtplib
import email.mime.text
from config_manager import ConfigManager


class SetupWizard:
    """Interactive setup wizard for first-time configuration."""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
    
    def run_setup(self):
        """Run the complete setup wizard."""
        print("=" * 60)
        print("🔔 Welcome to LookAway - Eye Break Reminder Setup 🔔")
        print("=" * 60)
        print()
        print("This wizard will help you configure your eye break reminders.")
        print("You can always modify these settings later.")
        print()
        
        try:
            # Basic reminder settings
            self._setup_basic_settings()
            
            # Notification methods
            self._setup_notifications()
            
            # Sleep hours
            self._setup_sleep_hours()
            
            # Advanced settings
            if self._ask_yes_no("Would you like to configure advanced settings?"):
                self._setup_advanced_settings()
            
            # Save configuration
            self.config_manager.save_config(self.config)
            self.config_manager.mark_setup_complete()
            
            print("\n" + "=" * 60)
            print("✅ Setup completed successfully!")
            print("=" * 60)
            print()
            print("Your LookAway application is now configured.")
            print("The reminder service will start automatically.")
            print()
            print("To modify settings later, run: python setup.py")
            print("To start/stop the service, use the system tray icon.")
            print()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user.")
            return False
        except Exception as e:
            print(f"\nError during setup: {e}")
            return False
    
    def _setup_basic_settings(self):
        """Setup basic reminder settings."""
        print("📅 BASIC REMINDER SETTINGS")
        print("-" * 30)
        
        # Reminder interval
        while True:
            try:
                interval = input(f"Reminder interval in minutes (default: 20): ").strip()
                if not interval:
                    interval = 20
                else:
                    interval = int(interval)
                
                if 1 <= interval <= 480:  # 1 minute to 8 hours
                    self.config['reminder_interval_minutes'] = interval
                    break
                else:
                    print("Please enter a value between 1 and 480 minutes.")
            except ValueError:
                print("Please enter a valid number.")
        
        print(f"✓ Reminder interval set to {interval} minutes")
        print()
    
    def _setup_notifications(self):
        """Setup notification methods."""
        print("🔔 NOTIFICATION METHODS")
        print("-" * 25)
        print("Choose how you want to receive reminders:")
        print()
        
        # Desktop notifications
        desktop = self._ask_yes_no("Enable desktop notifications?", default=True)
        self.config['notifications']['desktop'] = desktop
        
        # Email notifications
        email = self._ask_yes_no("Enable email notifications?")
        self.config['notifications']['email'] = email
        
        if email:
            self._setup_email_config()
        
        # Telegram notifications
        telegram = self._ask_yes_no("Enable Telegram notifications?")
        self.config['notifications']['telegram'] = telegram
        
        if telegram:
            self._setup_telegram_config()
        
        # Ensure at least one notification method is enabled
        if not any([desktop, email, telegram]):
            print("\n⚠️  Warning: No notification methods enabled!")
            print("Enabling desktop notifications as fallback...")
            self.config['notifications']['desktop'] = True
        
        print()
    
    def _setup_email_config(self):
        """Setup email notification configuration."""
        print("\n📧 EMAIL CONFIGURATION")
        print("-" * 22)
        
        # SMTP Server
        smtp_server = input("SMTP server (e.g., smtp.gmail.com): ").strip()
        self.config['email_settings']['smtp_server'] = smtp_server
        
        # SMTP Port
        while True:
            try:
                port = input("SMTP port (default: 587): ").strip()
                if not port:
                    port = 587
                else:
                    port = int(port)
                self.config['email_settings']['smtp_port'] = port
                break
            except ValueError:
                print("Please enter a valid port number.")
        
        # Email credentials
        email = input("Your email address: ").strip()
        self.config['email_settings']['email'] = email
        
        print("\n⚠️  For Gmail users:")
        print("   Use an 'App Password' instead of your regular password.")
        print("   Generate one at: https://myaccount.google.com/apppasswords")
        
        password = getpass.getpass("Email password (hidden input): ")
        self.config['email_settings']['password'] = password
        
        # Recipient
        recipient = input(f"Send reminders to (default: {email}): ").strip()
        if not recipient:
            recipient = email
        self.config['email_settings']['recipient'] = recipient
        
        # Test email
        if self._ask_yes_no("Test email configuration now?"):
            self._test_email_config()
        
        print("✓ Email configuration saved")
    
    def _setup_telegram_config(self):
        """Setup Telegram notification configuration."""
        print("\n💬 TELEGRAM CONFIGURATION")
        print("-" * 27)
        print("To use Telegram notifications, you need:")
        print("1. Create a bot by messaging @BotFather on Telegram")
        print("2. Get your bot token from BotFather")
        print("3. Start a chat with your bot and get your chat ID")
        print()
        print("For chat ID, you can:")
        print("- Message @userinfobot on Telegram")
        print("- Or send a message to your bot, then visit:")
        print("  https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates")
        print()
        
        bot_token = input("Bot token: ").strip()
        self.config['telegram_settings']['bot_token'] = bot_token
        
        chat_id = input("Your chat ID: ").strip()
        self.config['telegram_settings']['chat_id'] = chat_id
        
        # Test Telegram
        if self._ask_yes_no("Test Telegram configuration now?"):
            self._test_telegram_config()
        
        print("✓ Telegram configuration saved")
    
    def _setup_sleep_hours(self):
        """Setup sleep hours configuration."""
        print("😴 SLEEP HOURS")
        print("-" * 15)
        print("Set your sleep hours to avoid reminders during rest time.")
        print()
        
        while True:
            try:
                sleep_start = input("Sleep start time (HH:MM, e.g., 23:00): ").strip()
                if not sleep_start:
                    sleep_start = "23:00"
                
                # Validate format
                hours, minutes = map(int, sleep_start.split(':'))
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    self.config['sleep_hours']['start'] = sleep_start
                    break
                else:
                    print("Please enter a valid time in HH:MM format.")
            except ValueError:
                print("Please enter time in HH:MM format (e.g., 23:00).")
        
        while True:
            try:
                sleep_end = input("Sleep end time (HH:MM, e.g., 07:00): ").strip()
                if not sleep_end:
                    sleep_end = "07:00"
                
                # Validate format
                hours, minutes = map(int, sleep_end.split(':'))
                if 0 <= hours <= 23 and 0 <= minutes <= 59:
                    self.config['sleep_hours']['end'] = sleep_end
                    break
                else:
                    print("Please enter a valid time in HH:MM format.")
            except ValueError:
                print("Please enter time in HH:MM format (e.g., 07:00).")
        
        print(f"✓ Sleep hours set: {sleep_start} to {sleep_end}")
        print()
    
    def _setup_advanced_settings(self):
        """Setup advanced configuration options."""
        print("⚙️  ADVANCED SETTINGS")
        print("-" * 20)
        
        # Long break interval
        while True:
            try:
                interval = input("Long break every N reminders (default: 3): ").strip()
                if not interval:
                    interval = 3
                else:
                    interval = int(interval)
                
                if interval >= 1:
                    self.config['long_break_interval'] = interval
                    break
                else:
                    print("Please enter a positive number.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Snooze duration
        while True:
            try:
                snooze = input("Default snooze duration in minutes (default: 5): ").strip()
                if not snooze:
                    snooze = 5
                else:
                    snooze = int(snooze)
                
                if 1 <= snooze <= 60:
                    self.config['snooze_minutes'] = snooze
                    break
                else:
                    print("Please enter a value between 1 and 60 minutes.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Custom reminder messages
        if self._ask_yes_no("Would you like to add custom reminder messages?"):
            self._setup_custom_messages()
        
        print("✓ Advanced settings configured")
        print()
    
    def _setup_custom_messages(self):
        """Setup custom reminder messages."""
        print("\n📝 CUSTOM MESSAGES")
        print("-" * 18)
        print("Enter custom reminder messages (one per line).")
        print("Leave empty and press Enter when done.")
        print("Current messages will be replaced.")
        print()
        
        messages = []
        counter = 1
        
        while True:
            message = input(f"Message {counter}: ").strip()
            if not message:
                break
            messages.append(message)
            counter += 1
        
        if messages:
            self.config['messages'] = messages
            print(f"✓ Added {len(messages)} custom messages")
        else:
            print("No custom messages added, keeping defaults")
    
    def _test_email_config(self):
        """Test email configuration."""
        try:
            print("Testing email configuration...")
            
            smtp_server = self.config['email_settings']['smtp_server']
            smtp_port = self.config['email_settings']['smtp_port']
            email = self.config['email_settings']['email']
            password = self.config['email_settings']['password']
            recipient = self.config['email_settings']['recipient']
            
            # Create test message
            msg = email.mime.text.MIMEText("LookAway email configuration test successful!")
            msg['Subject'] = "LookAway Test Email"
            msg['From'] = email
            msg['To'] = recipient
            
            # Send test email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(email, password)
                server.send_message(msg)
            
            print("✅ Test email sent successfully!")
            
        except Exception as e:
            print(f"❌ Email test failed: {e}")
            print("Please check your configuration and try again.")
    
    def _test_telegram_config(self):
        """Test Telegram configuration."""
        try:
            print("Testing Telegram configuration...")
            
            # Import here to handle missing dependencies gracefully
            try:
                from telegram import Bot
                import asyncio
            except ImportError:
                print("❌ Telegram library not installed. Install with: pip install python-telegram-bot")
                return
            
            bot_token = self.config['telegram_settings']['bot_token']
            chat_id = self.config['telegram_settings']['chat_id']
            
            bot = Bot(token=bot_token)
            
            # Send test message
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    bot.send_message(
                        chat_id=chat_id,
                        text="🔔 LookAway Telegram configuration test successful!"
                    )
                )
                print("✅ Test message sent successfully!")
            finally:
                loop.close()
            
        except Exception as e:
            print(f"❌ Telegram test failed: {e}")
            print("Please check your bot token and chat ID.")
    
    def _ask_yes_no(self, question: str, default: bool = None) -> bool:
        """Ask a yes/no question with optional default."""
        if default is True:
            prompt = f"{question} [Y/n]: "
        elif default is False:
            prompt = f"{question} [y/N]: "
        else:
            prompt = f"{question} [y/n]: "
        
        while True:
            answer = input(prompt).strip().lower()
            
            if not answer and default is not None:
                return default
            elif answer in ['y', 'yes', '1', 'true']:
                return True
            elif answer in ['n', 'no', '0', 'false']:
                return False
            else:
                print("Please answer 'y' for yes or 'n' for no.")


def main():
    """Run setup wizard."""
    wizard = SetupWizard()
    
    # Check if this is first run or forced setup
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        print("Running forced setup (existing configuration will be updated)...")
    elif not wizard.config_manager.is_first_run():
        print("LookAway is already configured.")
        if not wizard._ask_yes_no("Do you want to run setup again?"):
            return
    
    success = wizard.run_setup()
    
    if success:
        print("Setup completed! You can now run the application.")
    else:
        print("Setup was not completed. You can run setup again anytime.")


if __name__ == "__main__":
    main()
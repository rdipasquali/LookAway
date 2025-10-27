import json
import os
import logging
from typing import Dict, Any, Optional
from datetime import time


class ConfigManager:
    """Manages application configuration settings."""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            # For .exe compatibility - prioritize installation directory over bundled config
            import sys
            
            if getattr(sys, 'frozen', False):
                # Running as .exe - use working directory (installation directory)
                config_dir = os.path.join(os.getcwd(), 'config')
            else:
                # Running as Python script - use script directory
                config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
        
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'settings.json')
        self.default_config = {
            'reminder_interval_minutes': 20,
            'notifications': {
                'desktop': True,
                'email': False,
                'telegram': False
            },
            'email_settings': {
                'smtp_server': '',
                'smtp_port': 587,
                'email': '',
                'password': '',
                'recipient': ''
            },
            'telegram_settings': {
                'bot_token': '',
                'chat_id': ''
            },
            'sleep_hours': {
                'start': '23:00',
                'end': '07:00'
            },
            'messages': [
                "Time for a break! Look away from your screen for 20 seconds.",
                "Take a moment to rest your eyes. Look at something 20 feet away.",
                "Eye break time! Blink several times and look into the distance.",
                "Give your eyes a rest. Focus on something far away for a moment.",
                "Break time! Close your eyes for a few seconds or look outside."
            ],
            'break_types': {
                'quick_break': {
                    'duration_seconds': 20,
                    'description': 'Quick eye rest - look away for 20 seconds'
                },
                'long_break': {
                    'duration_seconds': 300,
                    'description': 'Long break - step away from computer for 5 minutes'
                }
            },
            'long_break_interval': 3,  # Every 3rd reminder is a long break
            'snooze_minutes': 5,
            'do_not_disturb': False,
            'first_run': True,
            'logging': {
                'exception_logging': True,
                'log_directory': 'logs'
            }
        }
    
    def create_config_dir(self):
        """Create config directory if it doesn't exist."""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default if not exists."""
        import sys
        import logging
        
        # Log config loading information for debugging
        logging.debug(f"Loading config from: {self.config_file}")
        logging.debug(f"Config directory: {self.config_dir}")
        logging.debug(f"Config file exists: {os.path.exists(self.config_file)}")
        logging.debug(f"Frozen (exe): {getattr(sys, 'frozen', False)}")
        logging.debug(f"Working directory: {os.getcwd()}")
        
        self.create_config_dir()
        
        if not os.path.exists(self.config_file):
            logging.warning("Config file not found, using defaults")
            return self.default_config.copy()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logging.info("Config file loaded successfully")
            
            # Merge with default config to ensure all keys exist
            merged_config = self.default_config.copy()
            self._deep_merge(merged_config, config)
            return merged_config
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Error reading config file: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            self.create_config_dir()
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def _deep_merge(self, base_dict: Dict, update_dict: Dict):
        """Recursively merge update_dict into base_dict."""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_merge(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def is_first_run(self) -> bool:
        """Check if this is the first run of the application."""
        config = self.load_config()
        return config.get('first_run', True)
    
    def mark_setup_complete(self):
        """Mark the initial setup as complete."""
        config = self.load_config()
        config['first_run'] = False
        self.save_config(config)
    
    def get_sleep_hours(self) -> tuple[time, time]:
        """Get sleep hours as time objects."""
        config = self.load_config()
        sleep_settings = config.get('sleep_hours', {})
        
        start_str = sleep_settings.get('start', '23:00')
        end_str = sleep_settings.get('end', '07:00')
        
        start_time = time.fromisoformat(start_str)
        end_time = time.fromisoformat(end_str)
        
        return start_time, end_time
    
    def update_setting(self, key_path: str, value: Any) -> bool:
        """Update a specific setting using dot notation (e.g., 'notifications.email')."""
        config = self.load_config()
        
        keys = key_path.split('.')
        current = config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        
        return self.save_config(config)
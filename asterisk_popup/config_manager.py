"""
Configuration Manager for FreePBX Popup - Configuration management module.
Handles loading, saving, and accessing application configuration settings.
"""

import os
import json
import logging

logger = logging.getLogger('FreePBXPopup.ConfigManager')

class ConfigManager:
    """Configuration manager for FreePBX Popup"""

    def __init__(self):
        """Initialize configuration manager"""
        self.config = {
            'ami': {
                'host': 'localhost',
                'port': 5038,
                'username': 'admin',
                'secret': '',
                'auto_connect': True
            },
            'notifications': {
                'sound': 'default',
                'custom_sound_path': '',
                'show_missed_calls': True,
                'auto_dismiss': False,
                'auto_dismiss_timeout': 10
            },
            'extensions': {
                'monitor_all': True,
                'extensions_to_monitor': []
            },
            'general': {
                'start_at_login': True,
                'log_level': 'INFO'
            },
            'ui': {
                'theme': 'system',
                'show_in_dock': False
            }
        }

        self.config_dir = os.path.expanduser('~/Library/Application Support/FreePBXPopup')
        self.config_file = os.path.join(self.config_dir, 'config.json')

        self.load_config()

    def load_config(self):
        """Load configuration from file"""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)

            # Load config file if it exists
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)

                # Update config with loaded values
                self._update_dict(self.config, loaded_config)

                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                # Save default config
                self.save_config()
                logger.info("Configuration file not found, using defaults")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            # Create config directory if it doesn't exist
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)

            # Save config to file
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)

            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def _update_dict(self, target, source):
        """Update target dictionary with values from source dictionary"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value

    def get_ami_settings(self):
        """Get AMI settings"""
        return self.config.get('ami', {})

    def set_ami_settings(self, settings):
        """Set AMI settings"""
        self.config['ami'] = settings
        self.save_config()

    def get_extensions_to_monitor(self):
        """Get extensions to monitor"""
        extensions = self.config.get('extensions', {}).get('extensions_to_monitor', [])
        return extensions

    def set_extensions_to_monitor(self, extensions, monitor_all=None):
        """Set extensions to monitor"""
        if 'extensions' not in self.config:
            self.config['extensions'] = {}

        self.config['extensions']['extensions_to_monitor'] = extensions

        if monitor_all is not None:
            self.config['extensions']['monitor_all'] = monitor_all

        self.save_config()

    def get_notification_settings(self):
        """Get notification settings"""
        return self.config.get('notifications', {})

    def set_notification_settings(self, settings):
        """Set notification settings"""
        self.config['notifications'] = settings
        self.save_config()

    def get_general_settings(self):
        """Get general settings"""
        return self.config.get('general', {})

    def set_general_settings(self, settings):
        """Set general settings"""
        self.config['general'] = settings
        self.save_config()

    def get_ui_settings(self):
        """Get UI settings"""
        return self.config.get('ui', {})

    def set_ui_settings(self, settings):
        """Set UI settings"""
        self.config['ui'] = settings
        self.save_config()

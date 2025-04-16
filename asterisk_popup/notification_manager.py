"""
Notification Manager for FreePBX Popup - Call notification handling module.
Manages displaying notifications for incoming calls and tracking call status.
"""

import logging
import rumps
from datetime import datetime

logger = logging.getLogger('FreePBXPopup.NotificationManager')

class NotificationManager:
    """Notification manager for FreePBX Popup"""

    def __init__(self, config):
        """
        Initialize notification manager

        Args:
            config (ConfigManager): Configuration manager instance
        """
        self.config = config

        self.active_notifications = {}

        self._check_authorization()

    def _check_authorization(self):
        """Check if notifications are authorized"""
        try:
            logger.info("Notification authorization granted")
        except Exception as e:
            logger.warning(f"Notification authorization denied: {e}")

    def show_call_notification(self, call_info):
        """
        Show notification for incoming call

        Args:
            call_info (dict): Call information
                - caller_id_num (str): Caller ID number
                - caller_id_name (str): Caller ID name
                - extension (str): Extension
                - channel (str): Channel
                - timestamp (datetime): Timestamp
        """
        try:
            caller_id_num = call_info.get('caller_id_num', 'Unknown')
            caller_id_name = call_info.get('caller_id_name', 'Unknown')
            channel = call_info.get('channel', '')

            process = self._launch_notification_window(call_info)

            if channel and process:
                self.active_notifications[channel] = process

            logger.info(f"Showing notification for call from {caller_id_name} <{caller_id_num}>")
        except Exception as e:
            logger.error(f"Failed to show call notification: {e}")

    def handle_call_status(self, channel, status):
        """
        Handle call status updates

        Args:
            channel (str): Channel identifier
            status (str): New status ('answered', 'hangup', etc.)
        """
        try:
            logger.info(f"Call status update for channel {channel}: {status}")

            if channel in self.active_notifications:
                process = self.active_notifications[channel]

                try:
                    import tempfile
                    import json
                    import os

                    status_file = os.path.join(tempfile.gettempdir(), f"call_status_{channel.replace('/', '_')}.json")
                    with open(status_file, 'w') as f:
                        json.dump({'channel': channel, 'status': status}, f)

                    logger.info(f"Created status update file at {status_file}")
                except Exception as e:
                    logger.error(f"Failed to create status update file: {e}")

                if status == 'hangup':
                    if process and process.is_alive():
                        import threading
                        def check_and_terminate():
                            import time
                            time.sleep(5)
                            if process.is_alive():
                                logger.info(f"Terminating notification process for channel {channel}")
                                process.terminate()

                        threading.Thread(target=check_and_terminate, daemon=True).start()

                    del self.active_notifications[channel]
                    logger.info(f"Removed notification for channel {channel} due to {status}")
        except Exception as e:
            logger.error(f"Failed to handle call status update: {e}")

    def _launch_notification_window(self, call_info):
        """Launch notification window in a separate process"""
        try:
            import json
            import tempfile
            import subprocess
            import sys
            import os

            # Create temporary files for the call data and config
            call_info_copy = call_info.copy()
            config_copy = self.config.config.copy()

            if 'timestamp' in call_info_copy and isinstance(call_info_copy['timestamp'], datetime):
                call_info_copy['timestamp'] = call_info_copy['timestamp'].isoformat()

            # Create a temporary file for the call data
            call_data_file = tempfile.NamedTemporaryFile(mode='w', suffix='_call_data.json', delete=False)
            call_data_file.write(json.dumps(call_info_copy))
            call_data_file.close()

            # Create a temporary file for the config
            config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            config_file.write(json.dumps(config_copy))
            config_file.close()

            # Launch the notification window using the main script with the notification-launcher flag
            process = subprocess.Popen([
                sys.executable,
                '-m', 'asterisk_popup.main',  # Use the main module directly
                '--notification-launcher',  # Special flag to indicate this is a notification launcher
                config_file.name,
                call_data_file.name
            ])

            logger.info("Launched notification window in a separate process")
            return process
        except Exception as e:
            logger.error(f"Failed to launch notification window: {e}")
            self._show_simple_notification(call_info)

    def _run_notification_window(self, call_info, config_data):
        """Run notification window in a separate process"""
        try:
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            sys.path.insert(0, project_root)

            if 'timestamp' in call_info and isinstance(call_info['timestamp'], str):
                from datetime import datetime
                try:
                    call_info['timestamp'] = datetime.fromisoformat(call_info['timestamp'])
                except:
                    call_info['timestamp'] = datetime.now()

            import wx
            app = wx.App(False)

            from asterisk_popup.ui.wx.call_notification_window import CallNotificationWindow
            from asterisk_popup.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.config = config_data

            class SimpleCallHistoryManager:
                def __init__(self):
                    pass
                def add_call(self, _):
                    pass
                def get_calls(self, **_):
                    return []

            CallNotificationWindow(call_info, config_manager, SimpleCallHistoryManager())

            app.MainLoop()

        except Exception as e:
            import logging
            logger = logging.getLogger('FreePBXPopup.NotificationWindow')
            logger.error(f"Error running notification window: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def _show_simple_notification(self, call_info):
        """Show simple notification as fallback"""
        try:
            caller_id_num = call_info.get('caller_id_num', 'Unknown')
            caller_id_name = call_info.get('caller_id_name', 'Unknown')
            extension = call_info.get('extension', 'Unknown')

            title = f"Incoming Call to {extension}"
            message = f"From: {caller_id_name} <{caller_id_num}>"

            rumps.notification(
                title=title,
                subtitle="FreePBX Popup",
                message=message,
                sound=True
            )
        except Exception as e:
            logger.error(f"Failed to show simple notification: {e}")

    def show_test_notification(self):
        """Show a test notification"""
        try:
            call_info = {
                'caller_id_num': '5551234567',
                'caller_id_name': 'Test Caller',
                'extension': '100',
                'channel': 'SIP/test-1234',
                'timestamp': datetime.now(),
                'is_test': True
            }

            self.show_call_notification(call_info)

            logger.info("Showing test notification")
        except Exception as e:
            logger.error(f"Failed to show test notification: {e}")

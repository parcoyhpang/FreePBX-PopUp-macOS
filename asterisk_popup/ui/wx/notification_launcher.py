#!/usr/bin/env python3
"""
Launcher for call notification window - Notification process module.
Launches call notification windows in separate processes.
"""

import sys
import json
import logging
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.expanduser('~/Library/Logs/FreePBXPopup.log'))
    ]
)
logger = logging.getLogger('FreePBXPopup.NotificationLauncher')

def launch_notification():
    """Launch call notification window"""
    try:
        if len(sys.argv) < 2:
            logger.error("Not enough arguments")
            sys.exit(1)

        data_path = sys.argv[1]

        with open(data_path, 'r') as f:
            data = json.load(f)

        call_info = data.get('call_info', {})
        config_data = data.get('config', {})

        if 'timestamp' in call_info and isinstance(call_info['timestamp'], str):
            try:
                call_info['timestamp'] = datetime.fromisoformat(call_info['timestamp'])
            except:
                call_info['timestamp'] = datetime.now()

        import wx
        app = wx.App(False)

        import platform
        if platform.system() == 'Darwin':
            try:
                import objc
                from Foundation import NSBundle
                bundle = NSBundle.mainBundle()
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                info['LSUIElement'] = '1'
                logger.info("Hiding dock icon")
            except Exception as e:
                logger.error(f"Failed to hide dock icon: {e}")

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

        window = CallNotificationWindow(call_info, config_manager, SimpleCallHistoryManager())

        app.MainLoop()

    except Exception as e:
        logger.error(f"Error launching notification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    launch_notification()

"""
Launcher for wxPython windows - Process launcher module.
Provides functionality to launch UI windows in separate processes.
"""

import sys
import json
import logging
import wx
import importlib
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.expanduser('~/Library/Logs/FreePBXPopup.log'))
    ]
)
logger = logging.getLogger('FreePBXPopup.WxLauncher')

def launch_window():
    """Launch a wxPython window in a separate process"""
    try:
        if len(sys.argv) < 3:
            logger.error("Not enough arguments")
            sys.exit(1)

        window_type = sys.argv[1]
        config_path = sys.argv[2]

        with open(config_path, 'r') as f:
            config_data = json.load(f)

        app = wx.App(False)

        if window_type == 'preferences':
            from asterisk_popup.ui.wx.preferences_window import PreferencesWindow
            from asterisk_popup.config_manager import ConfigManager

            config_manager = ConfigManager()
            config_manager.config = config_data

            window = PreferencesWindow(config_manager, None, None)
            window.Show()

        else:
            logger.error(f"Unknown window type: {window_type}")
            sys.exit(1)

        app.MainLoop()

    except Exception as e:
        logger.error(f"Error launching window: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    launch_window()

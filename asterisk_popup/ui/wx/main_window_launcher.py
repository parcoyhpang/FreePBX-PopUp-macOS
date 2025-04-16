#!/usr/bin/env python3
"""
Standalone launcher for the main window - Main window process module.
Launches the main application window in a separate process with IPC capabilities.
"""

import sys
import os
import json
import logging
import wx
import threading
import tempfile
import time
import signal

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.expanduser('~/Library/Logs/FreePBXPopup.log'))
    ]
)
logger = logging.getLogger('FreePBXPopup.MainWindowLauncher')

# Hide dock icon on macOS
try:
    import platform
    if platform.system() == 'Darwin':
        try:
            import objc
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            info['LSUIElement'] = '1'  # Set to run as agent (no dock icon)
            logger.info("Hiding dock icon")
        except Exception as e:
            logger.error(f"Failed to hide dock icon: {e}")
except Exception as e:
    logger.error(f"Error setting up dock icon: {e}")

def run_main_window():
    """Run the main window"""
    try:
        # Check arguments
        if len(sys.argv) < 2:
            logger.error("Not enough arguments")
            sys.exit(1)

        # Get config file path
        config_path = sys.argv[1]

        # Check if config file exists
        if not os.path.exists(config_path):
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)

        # Load config
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        # Create wxPython app
        app = wx.App(False)

        # Import required modules
        from asterisk_popup.ui.wx.main_window import MainWindow
        from asterisk_popup.config_manager import ConfigManager

        # Create config manager
        config_manager = ConfigManager()
        config_manager.config = config_data

        # Create dummy AMI client and notification manager
        class DummyAMIClient:
            def __init__(self):
                self.status = {'connected': False, 'reconnect_attempts': 0}

            def get_status(self):
                # Return the current status
                return self.status

            def update_status(self, new_status):
                # Update the status
                self.status = new_status

        class DummyNotificationManager:
            def show_test_notification(self):
                wx.MessageBox(
                    "This is a test notification. In the actual application, this would show a native notification.",
                    "Test Notification",
                    wx.OK | wx.ICON_INFORMATION
                )

        ami_client = DummyAMIClient()
        notification_mgr = DummyNotificationManager()

        # Create main window
        window = MainWindow(config_manager, ami_client, notification_mgr)
        window.Show()

        # Set up IPC for communication with the main app
        setup_ipc(window, config_path)

        # Start main loop
        app.MainLoop()

    except Exception as e:
        logger.error(f"Error running main window: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def setup_ipc(window, config_path):
    """Set up IPC for communication with the main app"""
    try:
        # Create a file watcher thread to monitor the config file
        def watch_config_file():
            last_modified = os.path.getmtime(config_path)

            while True:
                try:
                    # Check if config file has been modified
                    current_modified = os.path.getmtime(config_path)

                    if current_modified > last_modified:
                        logger.info("Config file modified, reloading...")
                        last_modified = current_modified

                        # Load config
                        with open(config_path, 'r') as f:
                            config_data = json.load(f)

                        # Update config
                        wx.CallAfter(update_config, window, config_data)

                    # Check for command file
                    command_path = f"{config_path}.command"
                    if os.path.exists(command_path):
                        # Load command
                        with open(command_path, 'r') as f:
                            command_data = json.load(f)

                        # Process command
                        wx.CallAfter(process_command, window, command_data)

                        # Delete command file
                        os.remove(command_path)

                except Exception as e:
                    logger.error(f"Error in config watcher: {e}")

                # Sleep for a bit
                time.sleep(1)

        # Start watcher thread
        watcher_thread = threading.Thread(target=watch_config_file, daemon=True)
        watcher_thread.start()

    except Exception as e:
        logger.error(f"Error setting up IPC: {e}")

def update_config(window, config_data):
    """Update window config"""
    try:
        # Update config
        window.config.config = config_data

        # Refresh UI
        window.Refresh()

        logger.info("Config updated")
    except Exception as e:
        logger.error(f"Error updating config: {e}")

def process_command(window, command_data):
    """Process command from main app"""
    try:
        # Get command
        command = command_data.get('command')

        if command == 'show':
            # Show window
            window.Show()
            window.Raise()

            # Select tab if specified
            tab = command_data.get('tab')
            if tab == 'preferences':
                # Select preferences tab - Connection tab
                window.notebook.SetSelection(0)
            elif tab == 'about':
                # Select about tab
                window.notebook.SetSelection(3)

            logger.info(f"Showing window with tab: {tab if tab else 'default'}")

        elif command == 'hide':
            # Hide window
            window.Hide()

            logger.info("Hiding window")

        elif command == 'quit':
            # Quit application
            window.Close(True)

            logger.info("Quitting application")

        elif command == 'update_status':
            # Update connection status
            status = command_data.get('status', {})
            if hasattr(window, 'ami_client') and hasattr(window.ami_client, 'update_status'):
                window.ami_client.update_status(status)
                logger.debug(f"Updated connection status: {status}")

        else:
            logger.warning(f"Unknown command: {command}")

    except Exception as e:
        logger.error(f"Error processing command: {e}")

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))

    # Run main window
    run_main_window()

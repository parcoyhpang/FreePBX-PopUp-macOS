#!/usr/bin/env python3
"""
FreePBX Popup Client for macOS - Main application module.
Handles application initialization, component coordination, and lifecycle management.
"""

import os
import sys
import logging
import threading
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.expanduser('~/Library/Logs/FreePBXPopup.log'))
    ]
)
logger = logging.getLogger('FreePBXPopup')

from asterisk_popup.ami_client import AMIClient
from asterisk_popup.notification_manager import NotificationManager
from asterisk_popup.ui.menu_bar import MenuBarApp

def main():
    """Main entry point for the application"""
    logger.info("Starting FreePBX Popup Client")

    # Check if this is a special launcher process
    is_window_launcher = False
    is_notification_launcher = False

    for arg in sys.argv:
        if arg == '--window-launcher':
            is_window_launcher = True
            break
        elif arg == '--notification-launcher':
            is_notification_launcher = True
            break

    # If this is a special launcher, don't check for other instances
    if not is_window_launcher and not is_notification_launcher:
        # Check if another instance is already running
        if _check_already_running():
            logger.info("Another instance is already running. Exiting.")
            return

    # Check if this is a request to open the main window directly
    if is_window_launcher:
        try:
            # Find the config file argument
            config_file = None
            for arg in sys.argv:
                if arg.endswith('.json'):
                    config_file = arg
                    break

            if not config_file:
                logger.error("No config file specified for main window")
                return

            logger.info(f"Opening main window with config: {config_file}")

            # Import wx here to avoid loading it for the menu bar app
            import wx
            import json

            # Initialize wx app
            app = wx.App(False)

            # Import the main window
            from asterisk_popup.ui.wx.main_window import MainWindow

            # Load config
            with open(config_file, 'r') as f:
                config = json.load(f)

            # Create and show the main window
            window = MainWindow(config)
            window.Show()

            # Start the main loop
            app.MainLoop()
            return
        except Exception as e:
            logger.error(f"Error opening main window: {e}")
            return

    # Check if this is a request to open a notification window
    elif is_notification_launcher:
        try:
            # Find the config file argument
            config_file = None
            call_data_file = None

            for arg in sys.argv:
                if arg.endswith('.json') and 'call_data' in arg:
                    call_data_file = arg
                elif arg.endswith('.json'):
                    config_file = arg

            if not config_file or not call_data_file:
                logger.error(f"Missing required files for notification launcher: config={config_file}, call_data={call_data_file}")
                return

            logger.info(f"Opening notification window with config: {config_file} and call data: {call_data_file}")

            # Import wx here to avoid loading it for the menu bar app
            import wx
            import json

            # Initialize wx app
            app = wx.App(False)

            # Import the notification window
            from asterisk_popup.ui.wx.call_notification_window import CallNotificationWindow
            from asterisk_popup.config_manager import ConfigManager

            # Load config and call data
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            with open(call_data_file, 'r') as f:
                call_data = json.load(f)

            # Create config manager
            config_manager = ConfigManager()
            config_manager.config = config_data

            # Create a simple call history manager
            class SimpleCallHistoryManager:
                def __init__(self):
                    pass
                def add_call(self, _):
                    pass
                def get_calls(self, **_):
                    return []

            # Create and show the notification window
            window = CallNotificationWindow(call_data, config_manager, SimpleCallHistoryManager())
            window.Show()

            # Start the main loop
            app.MainLoop()
            return
        except Exception as e:
            logger.error(f"Error opening notification window: {e}")
            return

    # Create configuration manager
    from asterisk_popup.config_manager import ConfigManager
    config_manager = ConfigManager()

    # Create notification manager
    notification_mgr = NotificationManager(config_manager)

    # Create AMI client
    ami_client = AMIClient(
        config_manager,
        notification_callback=notification_mgr.show_call_notification,
        call_status_callback=notification_mgr.handle_call_status
    )

    ami_thread = threading.Thread(target=ami_client.start, daemon=True)
    ami_thread.start()

    try:
        app = MenuBarApp(config_manager, ami_client, notification_mgr)
        logger.info("Starting menu bar app")
        app.run()
        logger.info("Menu bar app ended")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in menu bar app: {e}")
    finally:
        try:
            ami_client.stop()
        except Exception as e:
            logger.error(f"Error stopping AMI client: {e}")
        logger.info("FreePBX Popup Client shutting down")

# Global variable to store the socket instance
_lock_socket = None

def _check_already_running():
    """Check if another instance of the application is already running"""
    global _lock_socket

    # Check if this is a child process (main window launcher)
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        # This is a child process, allow it to run
        return False

    # Check if we're running from a packaged app and being launched as a subprocess
    if getattr(sys, 'frozen', False) and os.environ.get('FREEPBX_POPUP_SUBPROCESS') == '1':
        # This is a subprocess of the main app, allow it to run
        return False

    try:
        import socket
        import tempfile
        import time

        # Create a unique socket name based on the application name
        socket_name = 'freepbxpopup-lock-{}'.format(int(time.time()))

        # Try to create and bind to the socket
        _lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

        # The abstract namespace is specific to Linux, so we need a different approach on macOS
        lock_file = os.path.join(tempfile.gettempdir(), 'freepbxpopup.lock')

        # Try to acquire the lock
        try:
            # Set the SO_REUSEADDR option to avoid "Address already in use" errors
            _lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Try to bind to a filesystem path instead of abstract namespace
            if os.path.exists(lock_file):
                # Check if the process is still running
                try:
                    # Try to connect to the socket to see if it's active
                    test_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
                    test_socket.settimeout(1)
                    test_socket.connect(lock_file)
                    test_socket.close()
                    # If we get here, the socket is active, another instance is running
                    return True
                except (socket.error, OSError):
                    # Socket exists but can't connect, remove the stale lock file
                    logger.info(f"Removing stale lock file: {lock_file}")
                    os.unlink(lock_file)

            # Bind to the lock file
            _lock_socket.bind(lock_file)
            logger.info(f"Created lock file: {lock_file}")

            # Keep the socket open to maintain the lock
            return False
        except (socket.error, OSError) as e:
            logger.error(f"Error binding to lock file: {e}")
            # Socket already exists and is active, another instance is running
            return True
    except Exception as e:
        logger.error(f"Error checking for running instance: {e}")
        # In case of error, assume no other instance is running
        return False

if __name__ == "__main__":
    main()

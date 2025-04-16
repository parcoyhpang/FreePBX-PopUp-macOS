#!/usr/bin/env python3
"""
Main window launcher for FreePBX Popup.
This script is used to launch the main window in a separate process.
"""

import sys
import os
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.expanduser('~/Library/Logs/FreePBXPopup_Window.log'))
    ]
)
logger = logging.getLogger('FreePBXPopup.MainWindowLauncher')

def main():
    """Main function"""
    logger.info("Starting main window launcher")

    # Set environment variable to indicate this is a subprocess
    os.environ['FREEPBX_POPUP_SUBPROCESS'] = '1'

    # Add --child argument to sys.argv to ensure we're recognized as a child process
    if '--child' not in sys.argv:
        sys.argv.append('--child')

    if len(sys.argv) < 2:
        logger.error("Usage: main_window_launcher.py <config_file>")
        sys.exit(1)

    # Find the config file argument
    config_file = None
    for arg in sys.argv:
        if arg.endswith('.json'):
            config_file = arg
            break

    if not config_file:
        logger.error("No config file specified")
        sys.exit(1)

    logger.info(f"Using config file: {config_file}")

    try:
        # Import wx
        import wx
        logger.info("Imported wx successfully")

        # Initialize wx app
        app = wx.App(False)
        logger.info("Created wx app")

        # Load config
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info("Loaded config file")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            sys.exit(1)

        # Import the main window
        try:
            logger.info("Attempting to import MainWindow")
            from asterisk_popup.ui.wx.main_window import MainWindow

            # Create and show the main window
            window = MainWindow(config)
            window.Show()
            logger.info("Showing main window")

            # Start the main loop
            app.MainLoop()
        except ImportError as e:
            logger.error(f"Error importing MainWindow: {e}")

            # Try to find the module path
            logger.info(f"Python path: {sys.path}")

            # Try to import the module directly
            try:
                import importlib.util

                # Try to find the module file
                module_path = None
                for path in sys.path:
                    potential_path = os.path.join(path, 'asterisk_popup', 'ui', 'wx', 'main_window.py')
                    if os.path.exists(potential_path):
                        module_path = potential_path
                        logger.info(f"Found module at: {potential_path}")
                        break

                if module_path:
                    logger.info(f"Loading module from: {module_path}")

                    # Load the module
                    spec = importlib.util.spec_from_file_location("main_window", module_path)
                    main_window = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(main_window)

                    # Create and show the main window
                    window = main_window.MainWindow(config)
                    window.Show()
                    logger.info("Showing main window (direct import)")

                    # Start the main loop
                    app.MainLoop()
                else:
                    logger.error("Could not find main_window.py")
                    sys.exit(1)
            except Exception as e:
                logger.error(f"Error loading module directly: {e}")
                sys.exit(1)
    except Exception as e:
        logger.error(f"Error in main window launcher: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

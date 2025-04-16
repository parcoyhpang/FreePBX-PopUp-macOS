"""
Menu Bar App for FreePBX Popup - System menu bar interface module.
Creates and manages the menu bar interface using rumps, providing access to application features.
"""

import os
import logging
import threading
import rumps
import json
import tempfile
import subprocess
import sys

logger = logging.getLogger('FreePBXPopup.MenuBarApp')

class MenuBarApp(rumps.App):
    """Menu bar application for FreePBX Popup"""

    def __init__(self, config, ami_client, notification_mgr):
        """
        Initialize menu bar application

        Args:
            config (ConfigManager): Configuration manager instance
            ami_client (AMIClient): AMI client instance
            notification_mgr (NotificationManager): Notification manager instance
        """
        super(MenuBarApp, self).__init__(
            "FreePBX Popup",
            icon=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'resources', 'menu_bar_icon.png'),
            quit_button=None
        )

        self.config = config
        self.ami_client = ami_client
        self.notification_mgr = notification_mgr

        self.status_update_timer = None
        self.preferences_window = None
        self.call_history_window = None

        self._setup_menu()

        self._start_status_update_timer()

        logger.info("MenuBarApp initialized")

    def _setup_menu(self):
        """Set up the menu bar menu"""
        self.status_item = rumps.MenuItem("Status: Disconnected")
        self.status_item.set_callback(None)
        self.menu.add(self.status_item)

        self.menu.add(None)

        # Test Notification menu item removed for production
        # self.menu.add(rumps.MenuItem("Test Notification", callback=self.on_test_notification))

        self.menu.add(rumps.MenuItem("Preferences...", callback=self.on_preferences))

        self.menu.add(None)

        self.menu.add(rumps.MenuItem("About", callback=self.on_about))

        self.menu.add(None)

        self.menu.add(rumps.MenuItem("Quit", callback=self.on_quit))

    def _start_status_update_timer(self):
        """Start timer to update status"""
        self._update_status()

    def _update_status(self):
        """Update status in menu"""
        try:
            if hasattr(self, 'ami_client') and self.ami_client:
                status = self.ami_client.get_status()

                if status.get('connected'):
                    status_text = "Status: Connected"
                else:
                    reconnect_attempts = status.get('reconnect_attempts', 0)
                    if reconnect_attempts > 0:
                        status_text = f"Status: Reconnecting ({reconnect_attempts})"
                    else:
                        status_text = "Status: Disconnected"
            else:
                status_text = "Status: Initializing"

            self.status_item.title = status_text

            if hasattr(self, 'main_window_process') and self.main_window_process and self.main_window_process.poll() is None:
                self._send_command_to_main_window({
                    'command': 'update_status',
                    'status': status
                })

        except Exception as e:
            logger.error(f"Failed to update status: {e}")

        self.status_update_timer = threading.Timer(5.0, self._update_status)
        self.status_update_timer.daemon = True
        self.status_update_timer.start()

    def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources")

        if self.status_update_timer:
            self.status_update_timer.cancel()

        self._cleanup_main_window()

        # Clean up lock file
        self._cleanup_lock_file()

    def _cleanup_lock_file(self):
        """Clean up the lock file"""
        try:
            import os
            import tempfile

            # Path to the lock file
            lock_file = os.path.join(tempfile.gettempdir(), 'freepbxpopup.lock')

            # Remove the lock file if it exists
            if os.path.exists(lock_file):
                logger.info(f"Removing lock file: {lock_file}")
                os.unlink(lock_file)
        except Exception as e:
            logger.error(f"Error cleaning up lock file: {e}")

    def _launch_window(self, window_type):
        """Launch a window in a separate process"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(self.config.config, temp_file)
                temp_file_path = temp_file.name

            launcher_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui', 'wx', 'launcher.py')

            subprocess.Popen([
                sys.executable,
                launcher_path,
                window_type,
                temp_file_path
            ])

            logger.info(f"Launched {window_type} window in a separate process")
        except Exception as e:
            logger.error(f"Failed to launch {window_type} window: {e}")
            raise

    # on_test_notification method removed for production

    def on_preferences(self, _):
        """Show main window with preferences tab"""
        try:
            self._show_main_window(tab='preferences')
        except Exception as e:
            logger.error(f"Error showing main window: {e}")
            rumps.alert(
                title="Error",
                message=f"Failed to show main window: {e}"
            )

    def _show_main_window(self, tab=None):
        """Show main window with specified tab"""
        try:
            if hasattr(self, 'main_window_process') and self.main_window_process and self.main_window_process.poll() is None:
                self._send_command_to_main_window({'command': 'show', 'tab': tab})
            else:
                self._launch_main_window(tab)

            logger.info(f"Showing main window with tab: {tab if tab else 'default'}")
        except Exception as e:
            logger.error(f"Failed to show main window: {e}")
            raise

    def _launch_main_window(self, tab=None):
        """Launch main window in a separate process"""
        try:
            import json
            import tempfile
            import subprocess
            import sys
            import os
            import atexit

            # Create a temporary config file for the main window
            config_data = self.config.config.copy()

            # Add AMI client configuration
            config_data['ami_settings'] = {
                'host': self.config.get_ami_settings().get('host', 'localhost'),
                'port': self.config.get_ami_settings().get('port', 5038),
                'username': self.config.get_ami_settings().get('username', ''),
                'secret': self.config.get_ami_settings().get('secret', ''),
                'connected': self.ami_client.is_connected() if hasattr(self, 'ami_client') and self.ami_client else False
            }

            # Write the config to a temporary file
            config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            config_file.write(json.dumps(config_data))
            config_file.close()

            self.main_window_config_path = config_file.name

            # Set environment variable to indicate this is a subprocess
            env = os.environ.copy()
            env['FREEPBX_POPUP_SUBPROCESS'] = '1'

            # Launch the main window as a separate process using the main script
            self.main_window_process = subprocess.Popen([
                sys.executable,
                '-m', 'asterisk_popup.main',  # Use the main module directly
                '--window-launcher',  # Special flag to indicate this is a window launcher
                self.main_window_config_path
            ], env=env)

            if tab:
                self._send_command_to_main_window({'command': 'show', 'tab': tab})

            atexit.register(self._cleanup_main_window)

            logger.info("Launched main window in a separate process")
        except Exception as e:
            logger.error(f"Failed to launch main window: {e}")
            raise

    def _send_command_to_main_window(self, command):
        """Send command to main window"""
        try:
            import json
            import os

            if not hasattr(self, 'main_window_config_path') or not self.main_window_config_path:
                logger.error("No config file path for main window")
                return

            # Create a command file next to the config file
            command_path = f"{self.main_window_config_path}.command"

            # Write the command to the file
            with open(command_path, 'w') as f:
                json.dump(command, f)

            logger.debug(f"Sent command to main window: {command}")
        except Exception as e:
            logger.error(f"Failed to send command to main window: {e}")

    def _cleanup_main_window(self):
        """Clean up main window resources"""
        try:
            import os

            # Send quit command to the main window
            self._send_command_to_main_window({'command': 'quit'})

            # Wait for the process to terminate
            if hasattr(self, 'main_window_process') and self.main_window_process:
                try:
                    self.main_window_process.wait(timeout=2)
                except:
                    # If the process doesn't terminate, kill it
                    try:
                        self.main_window_process.kill()
                    except:
                        pass

            # Clean up the config file
            if hasattr(self, 'main_window_config_path') and self.main_window_config_path and os.path.exists(self.main_window_config_path):
                try:
                    os.remove(self.main_window_config_path)
                except:
                    pass

            # Clean up the command file
            command_path = f"{self.main_window_config_path}.command" if hasattr(self, 'main_window_config_path') else None
            if command_path and os.path.exists(command_path):
                try:
                    os.remove(command_path)
                except:
                    pass

            logger.info("Cleaned up main window resources")
        except Exception as e:
            logger.error(f"Failed to clean up main window resources: {e}")

    def on_about(self, _):
        """Show about tab in main window"""
        try:
            self._show_main_window(tab='about')
        except Exception as e:
            logger.error(f"Error showing about tab: {e}")
            rumps.alert(
                title="Error",
                message=f"Failed to show about tab: {e}"
            )

    def on_quit(self, _):
        """Handle quit menu item"""
        try:
            logger.info("Quitting application")
            self.cleanup()

            # Check for and unload any LaunchAgents that might restart the app
            self._unload_launch_agents()

            # Quit the application
            rumps.quit_application()
        except Exception as e:
            logger.error(f"Error quitting application: {e}")
            import sys
            sys.exit(0)

    def _unload_launch_agents(self):
        """Unload any LaunchAgents that might restart the app"""
        try:
            import subprocess
            import os

            # Check for the LaunchAgent plist
            plist_path = os.path.expanduser('~/Library/LaunchAgents/com.freepbxpopup.plist')
            if os.path.exists(plist_path):
                logger.info(f"Found LaunchAgent at {plist_path}, temporarily unloading")
                try:
                    # Unload the LaunchAgent
                    subprocess.run(['launchctl', 'unload', plist_path], check=False)
                    logger.info("Successfully unloaded LaunchAgent")
                except Exception as e:
                    logger.error(f"Failed to unload LaunchAgent: {e}")

            # Also check for any other LaunchAgents that might be related
            try:
                result = subprocess.run(['launchctl', 'list'], capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    for line in result.stdout.splitlines():
                        if 'freepbxpopup' in line.lower():
                            parts = line.split()
                            if len(parts) > 0:
                                label = parts[-1]
                                logger.info(f"Found additional LaunchAgent: {label}, attempting to unload")
                                try:
                                    subprocess.run(['launchctl', 'remove', label], check=False)
                                    logger.info(f"Successfully removed LaunchAgent: {label}")
                                except Exception as e:
                                    logger.error(f"Failed to remove LaunchAgent {label}: {e}")
            except Exception as e:
                logger.error(f"Error checking for additional LaunchAgents: {e}")
        except Exception as e:
            logger.error(f"Error unloading LaunchAgents: {e}")

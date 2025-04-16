"""
Preferences Window for FreePBX Popup - Application settings configuration module.
Provides user interface for configuring all application settings and preferences.
"""

import os
import logging
import wx
import wx.lib.scrolledpanel as scrolled
import threading
import platform

logger = logging.getLogger('FreePBXPopup.PreferencesWindow')

class PreferencesWindow(wx.Frame):
    """Preferences window for FreePBX Popup"""

    def __init__(self, config, ami_client, notification_mgr):
        """
        Initialize preferences window

        Args:
            config (ConfigManager): Configuration manager instance
            ami_client (AMIClient): AMI client instance
            notification_mgr (NotificationManager): Notification manager instance
        """
        super(PreferencesWindow, self).__init__(
            None,
            title="Preferences",
            size=(500, 400),
            style=wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        )

        self.config = config
        self.ami_client = ami_client
        self.notification_mgr = notification_mgr

        # Create notebook for tabs
        self.notebook = wx.Notebook(self)

        # Create tabs
        self.connection_panel = ConnectionPanel(self.notebook, self.config, self.ami_client)
        self.notifications_panel = NotificationsPanel(self.notebook, self.config, self.notification_mgr)
        self.general_panel = GeneralPanel(self.notebook, self.config)

        # Add tabs to notebook
        self.notebook.AddPage(self.connection_panel, "Connection")
        self.notebook.AddPage(self.notifications_panel, "Notifications")
        self.notebook.AddPage(self.general_panel, "General")

        # Create sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        # Center on screen
        self.Center()

        # Bind events
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        """Handle window close event"""
        self.Hide()

class ConnectionPanel(scrolled.ScrolledPanel):
    """Connection settings panel"""

    def __init__(self, parent, config, ami_client):
        """Initialize connection panel"""
        super(ConnectionPanel, self).__init__(parent)

        self.config = config
        self.ami_client = ami_client

        # Create controls
        self.create_controls()

        # Load settings
        self.load_settings()

        # Set up scrolling
        self.SetupScrolling()

    def create_controls(self):
        """Create panel controls"""
        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Server settings
        server_box = wx.StaticBox(self, label="Server Settings")
        server_sizer = wx.StaticBoxSizer(server_box, wx.VERTICAL)

        # Create a grid sizer for better alignment
        grid_sizer = wx.FlexGridSizer(rows=4, cols=2, vgap=10, hgap=10)
        grid_sizer.AddGrowableCol(1, 1)

        # Host
        host_label = wx.StaticText(self, label="Host:")
        self.host_field = wx.TextCtrl(self)
        grid_sizer.Add(host_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.host_field, 0, wx.EXPAND)

        # Port
        port_label = wx.StaticText(self, label="Port:")
        self.port_field = wx.TextCtrl(self)
        grid_sizer.Add(port_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.port_field, 0, wx.EXPAND)

        # Username
        username_label = wx.StaticText(self, label="Username:")
        self.username_field = wx.TextCtrl(self)
        grid_sizer.Add(username_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.username_field, 0, wx.EXPAND)

        # Password
        password_label = wx.StaticText(self, label="Password:")
        self.password_field = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        grid_sizer.Add(password_label, 0, wx.ALIGN_CENTER_VERTICAL)
        grid_sizer.Add(self.password_field, 0, wx.EXPAND)

        server_sizer.Add(grid_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Auto connect
        self.auto_connect_checkbox = wx.CheckBox(self, label="Connect automatically on startup")
        server_sizer.Add(self.auto_connect_checkbox, 0, wx.ALL, 10)

        main_sizer.Add(server_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Extensions settings
        extensions_box = wx.StaticBox(self, label="Extensions")
        extensions_sizer = wx.StaticBoxSizer(extensions_box, wx.VERTICAL)

        # Monitor all checkbox
        self.monitor_all_checkbox = wx.CheckBox(self, label="Monitor all extensions")
        self.monitor_all_checkbox.Bind(wx.EVT_CHECKBOX, self.on_monitor_all)
        extensions_sizer.Add(self.monitor_all_checkbox, 0, wx.ALL, 10)

        # Extensions to monitor
        extensions_label = wx.StaticText(self, label="Extensions to monitor:")
        self.extensions_field = wx.TextCtrl(self)
        self.extensions_field.SetHint("Enter extensions separated by commas")
        extensions_sizer.Add(extensions_label, 0, wx.ALL, 10)
        extensions_sizer.Add(self.extensions_field, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        main_sizer.Add(extensions_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.test_button = wx.Button(self, label="Test Connection")
        self.test_button.Bind(wx.EVT_BUTTON, self.on_test_connection)
        button_sizer.Add(self.test_button, 0, wx.RIGHT, 10)

        self.save_button = wx.Button(self, label="Save")
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)
        button_sizer.Add(self.save_button)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 20)

        self.SetSizer(main_sizer)

    def load_settings(self):
        """Load settings from config"""
        ami_settings = self.config.get_ami_settings()

        self.host_field.SetValue(ami_settings.get('host', 'localhost'))
        self.port_field.SetValue(str(ami_settings.get('port', 5038)))
        self.username_field.SetValue(ami_settings.get('username', 'admin'))
        self.password_field.SetValue(ami_settings.get('secret', ''))
        self.auto_connect_checkbox.SetValue(ami_settings.get('auto_connect', True))

        # Extensions settings
        extensions = self.config.get_extensions_to_monitor()
        monitor_all = self.config.config.get('extensions', {}).get('monitor_all', True)

        self.monitor_all_checkbox.SetValue(monitor_all)
        self.extensions_field.SetValue(', '.join(extensions))
        self.extensions_field.Enable(not monitor_all)

    def on_monitor_all(self, event):
        """Handle monitor all checkbox"""
        monitor_all = self.monitor_all_checkbox.GetValue()
        self.extensions_field.Enable(not monitor_all)

    def on_test_connection(self, event):
        """Handle test connection button"""
        host = self.host_field.GetValue()
        port = self.port_field.GetValue()
        username = self.username_field.GetValue()
        password = self.password_field.GetValue()

        # Disable button during test
        self.test_button.Disable()
        self.test_button.SetLabel("Testing...")

        # Create progress dialog
        progress = wx.ProgressDialog(
            "Testing Connection",
            f"Testing connection to {host}:{port}...",
            maximum=100,
            parent=self,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE
        )
        progress.Update(0)

        # Run test in a separate thread
        def test_connection():
            import socket
            import time

            try:
                # Update progress
                wx.CallAfter(progress.Update, 10, "Creating socket...")

                # Create socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)  # 10 second timeout

                # Connect to server
                wx.CallAfter(progress.Update, 30, f"Connecting to {host}:{port}...")
                sock.connect((host, int(port)))

                # Read welcome message
                wx.CallAfter(progress.Update, 50, "Reading welcome message...")
                welcome = sock.recv(1024).decode('utf-8')

                # Send login command
                wx.CallAfter(progress.Update, 70, "Sending login command...")
                login_cmd = f"Action: Login\r\nUsername: {username}\r\nSecret: {password}\r\n\r\n"
                sock.send(login_cmd.encode('utf-8'))

                # Wait for response
                time.sleep(1)
                wx.CallAfter(progress.Update, 90, "Reading response...")
                response = sock.recv(1024).decode('utf-8')

                # Check if login was successful
                if "Success" in response:
                    # Send logoff command
                    logoff_cmd = "Action: Logoff\r\n\r\n"
                    sock.send(logoff_cmd.encode('utf-8'))

                    # Wait for response
                    time.sleep(1)
                    sock.recv(1024)

                    sock.close()

                    # Show success message
                    wx.CallAfter(self.show_test_result, True, "Connection successful!")
                else:
                    sock.close()

                    # Show error message
                    wx.CallAfter(self.show_test_result, False, f"Login failed: {response}")
            except Exception as e:
                # Show error message
                wx.CallAfter(self.show_test_result, False, f"Connection failed: {e}")

            # Close progress dialog
            wx.CallAfter(progress.Destroy)

            # Re-enable button
            wx.CallAfter(self.test_button.Enable)
            wx.CallAfter(self.test_button.SetLabel, "Test Connection")

        # Start test thread
        threading.Thread(target=test_connection, daemon=True).start()

    def show_test_result(self, success, message):
        """Show test result"""
        if success:
            wx.MessageBox(
                message,
                "Connection Test",
                wx.OK | wx.ICON_INFORMATION
            )
        else:
            wx.MessageBox(
                message,
                "Connection Test",
                wx.OK | wx.ICON_ERROR
            )

    def on_save(self, event):
        """Handle save button"""
        # Save AMI settings
        ami_settings = {
            'host': self.host_field.GetValue(),
            'port': int(self.port_field.GetValue()),
            'username': self.username_field.GetValue(),
            'secret': self.password_field.GetValue(),
            'auto_connect': self.auto_connect_checkbox.GetValue(),
        }
        self.config.set_ami_settings(ami_settings)

        # Save extensions settings
        monitor_all = self.monitor_all_checkbox.GetValue()
        extensions_str = self.extensions_field.GetValue()
        extensions = [ext.strip() for ext in extensions_str.split(',') if ext.strip()]
        self.config.set_extensions_to_monitor(extensions, monitor_all)

        # Show confirmation
        wx.MessageBox(
            "Connection settings have been saved. You may need to restart the application for some changes to take effect.",
            "Settings Saved",
            wx.OK | wx.ICON_INFORMATION
        )

class NotificationsPanel(scrolled.ScrolledPanel):
    """Notifications settings panel"""

    def __init__(self, parent, config, notification_mgr):
        """Initialize notifications panel"""
        super(NotificationsPanel, self).__init__(parent)

        self.config = config
        self.notification_mgr = notification_mgr

        # Create controls
        self.create_controls()

        # Load settings
        self.load_settings()

        # Set up scrolling
        self.SetupScrolling()

    def create_controls(self):
        """Create panel controls"""
        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Notification settings
        notification_box = wx.StaticBox(self, label="Notification Settings")
        notification_sizer = wx.StaticBoxSizer(notification_box, wx.VERTICAL)

        # Sound
        sound_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sound_label = wx.StaticText(self, label="Sound:")
        self.sound_choice = wx.Choice(self, choices=["Default", "None", "Custom..."])
        self.sound_choice.Bind(wx.EVT_CHOICE, self.on_sound_choice)
        sound_sizer.Add(sound_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sound_sizer.Add(self.sound_choice, 1)
        notification_sizer.Add(sound_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Custom sound
        custom_sound_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.custom_sound_label = wx.StaticText(self, label="Custom sound:")
        self.custom_sound_field = wx.TextCtrl(self)
        self.browse_sound_button = wx.Button(self, label="...")
        self.browse_sound_button.Bind(wx.EVT_BUTTON, self.on_browse_sound)
        custom_sound_sizer.Add(self.custom_sound_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        custom_sound_sizer.Add(self.custom_sound_field, 1, wx.RIGHT, 5)
        custom_sound_sizer.Add(self.browse_sound_button, 0)
        notification_sizer.Add(custom_sound_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # Auto dismiss
        self.auto_dismiss_checkbox = wx.CheckBox(self, label="Auto-dismiss notifications")
        self.auto_dismiss_checkbox.Bind(wx.EVT_CHECKBOX, self.on_auto_dismiss)
        notification_sizer.Add(self.auto_dismiss_checkbox, 0, wx.ALL, 5)

        # Auto dismiss timeout
        auto_dismiss_timeout_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.auto_dismiss_timeout_label = wx.StaticText(self, label="Dismiss after (seconds):")
        self.auto_dismiss_timeout_field = wx.TextCtrl(self, size=(50, -1))
        auto_dismiss_timeout_sizer.Add(self.auto_dismiss_timeout_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        auto_dismiss_timeout_sizer.Add(self.auto_dismiss_timeout_field, 0)
        notification_sizer.Add(auto_dismiss_timeout_sizer, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(notification_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.test_button = wx.Button(self, label="Test Notification")
        self.test_button.Bind(wx.EVT_BUTTON, self.on_test_notification)
        button_sizer.Add(self.test_button, 0, wx.RIGHT, 10)

        self.save_button = wx.Button(self, label="Save")
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)
        button_sizer.Add(self.save_button)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(main_sizer)

    def load_settings(self):
        """Load settings from config"""
        notifications = self.config.get_notification_settings()

        # Sound settings
        sound = notifications.get('sound', 'default')
        if sound == 'default':
            self.sound_choice.SetSelection(0)
            self.custom_sound_label.Show(False)
            self.custom_sound_field.Show(False)
            self.browse_sound_button.Show(False)
        elif sound == 'none':
            self.sound_choice.SetSelection(1)
            self.custom_sound_label.Show(False)
            self.custom_sound_field.Show(False)
            self.browse_sound_button.Show(False)
        else:
            self.sound_choice.SetSelection(2)
            self.custom_sound_label.Show(True)
            self.custom_sound_field.Show(True)
            self.browse_sound_button.Show(True)
            self.custom_sound_field.SetValue(notifications.get('custom_sound_path', ''))

        # Show missed calls functionality removed

        auto_dismiss = notifications.get('auto_dismiss', False)
        self.auto_dismiss_checkbox.SetValue(auto_dismiss)

        self.auto_dismiss_timeout_label.Show(auto_dismiss)
        self.auto_dismiss_timeout_field.Show(auto_dismiss)
        self.auto_dismiss_timeout_field.SetValue(str(notifications.get('auto_dismiss_timeout', 10)))

        # Layout update
        self.Layout()

    def on_sound_choice(self, event):
        """Handle sound choice"""
        selection = self.sound_choice.GetSelection()

        if selection == 2:  # Custom
            self.custom_sound_label.Show(True)
            self.custom_sound_field.Show(True)
            self.browse_sound_button.Show(True)
        else:
            self.custom_sound_label.Show(False)
            self.custom_sound_field.Show(False)
            self.browse_sound_button.Show(False)

        self.Layout()

    def on_auto_dismiss(self, event):
        """Handle auto dismiss checkbox"""
        auto_dismiss = self.auto_dismiss_checkbox.GetValue()

        self.auto_dismiss_timeout_label.Show(auto_dismiss)
        self.auto_dismiss_timeout_field.Show(auto_dismiss)

        self.Layout()

    def on_browse_sound(self, event):
        """Handle browse sound button"""
        with wx.FileDialog(
            self,
            "Select Sound File",
            wildcard="Sound files (*.wav;*.mp3)|*.wav;*.mp3",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        ) as file_dialog:

            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return

            path = file_dialog.GetPath()
            self.custom_sound_field.SetValue(path)

    def on_test_notification(self, event):
        """Handle test notification button"""
        self.notification_mgr.show_test_notification()

    def on_save(self, event):
        """Handle save button"""
        # Get sound settings
        sound_selection = self.sound_choice.GetSelection()

        if sound_selection == 0:
            sound_name = 'default'
            custom_sound_path = ''
        elif sound_selection == 1:
            sound_name = 'none'
            custom_sound_path = ''
        else:
            sound_name = 'custom'
            custom_sound_path = self.custom_sound_field.GetValue()

        # Save notification settings
        notifications = self.config.get_notification_settings()
        notifications['sound'] = sound_name
        notifications['custom_sound_path'] = custom_sound_path
        notifications['auto_dismiss'] = self.auto_dismiss_checkbox.GetValue()

        try:
            notifications['auto_dismiss_timeout'] = int(self.auto_dismiss_timeout_field.GetValue())
        except ValueError:
            notifications['auto_dismiss_timeout'] = 10

        self.config.set_notification_settings(notifications)

        # Show confirmation
        wx.MessageBox(
            "Notification settings have been saved.",
            "Settings Saved",
            wx.OK | wx.ICON_INFORMATION
        )

class GeneralPanel(scrolled.ScrolledPanel):
    """General settings panel"""

    def __init__(self, parent, config):
        """Initialize general panel"""
        super(GeneralPanel, self).__init__(parent)

        self.config = config

        # Create controls
        self.create_controls()

        # Load settings
        self.load_settings()

        # Set up scrolling
        self.SetupScrolling()

    def create_controls(self):
        """Create panel controls"""
        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # General settings
        general_box = wx.StaticBox(self, label="General Settings")
        general_sizer = wx.StaticBoxSizer(general_box, wx.VERTICAL)

        # Start at login
        self.start_at_login_checkbox = wx.CheckBox(self, label="Start at login")
        general_sizer.Add(self.start_at_login_checkbox, 0, wx.ALL, 5)


        # Log level
        log_level_sizer = wx.BoxSizer(wx.HORIZONTAL)
        log_level_label = wx.StaticText(self, label="Log level:")
        self.log_level_choice = wx.Choice(self, choices=["DEBUG", "INFO", "WARNING", "ERROR"])
        log_level_sizer.Add(log_level_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        log_level_sizer.Add(self.log_level_choice, 1)
        general_sizer.Add(log_level_sizer, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(general_sizer, 0, wx.EXPAND | wx.ALL, 10)

        # Call history functionality removed

        # Buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.save_button = wx.Button(self, label="Save")
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)
        button_sizer.Add(self.save_button)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)

        self.SetSizer(main_sizer)

    def load_settings(self):
        """Load settings from config"""
        general = self.config.get_general_settings()
        ui = self.config.get_ui_settings()

        self.start_at_login_checkbox.SetValue(general.get('start_at_login', True))

        log_level = general.get('log_level', 'INFO')
        if log_level == 'DEBUG':
            self.log_level_choice.SetSelection(0)
        elif log_level == 'INFO':
            self.log_level_choice.SetSelection(1)
        elif log_level == 'WARNING':
            self.log_level_choice.SetSelection(2)
        elif log_level == 'ERROR':
            self.log_level_choice.SetSelection(3)
        else:
            self.log_level_choice.SetSelection(1)  # Default to INFO

    def on_save(self, event):
        """Handle save button"""
        # Save general settings
        general = self.config.get_general_settings()
        general['start_at_login'] = self.start_at_login_checkbox.GetValue()

        log_level_selection = self.log_level_choice.GetSelection()
        if log_level_selection == 0:
            general['log_level'] = 'DEBUG'
        elif log_level_selection == 1:
            general['log_level'] = 'INFO'
        elif log_level_selection == 2:
            general['log_level'] = 'WARNING'
        elif log_level_selection == 3:
            general['log_level'] = 'ERROR'

        self.config.set_general_settings(general)

        # Implement start at login functionality
        start_at_login = self.start_at_login_checkbox.GetValue()
        self._set_start_at_login(start_at_login)

        # Call history functionality removed

        # Show confirmation
        wx.MessageBox(
            "General settings have been saved.",
            "Settings Saved",
            wx.OK | wx.ICON_INFORMATION
        )

    def _set_start_at_login(self, enable):
        """Set application to start at login"""
        try:
            import os
            import subprocess
            import sys

            # Get the path to the application
            app_path = os.path.abspath(sys.argv[0])

            if platform.system() == 'Darwin':
                # macOS implementation using launchctl and plist
                plist_dir = os.path.expanduser('~/Library/LaunchAgents')
                plist_path = os.path.join(plist_dir, 'com.freepbxpopup.plist')

                if enable:
                    # Create LaunchAgents directory if it doesn't exist
                    if not os.path.exists(plist_dir):
                        os.makedirs(plist_dir)

                    # Create plist file
                    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.freepbxpopup</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>ThrottleInterval</key>
    <integer>30</integer>
    <key>StartInterval</key>
    <integer>300</integer>
</dict>
</plist>
"""

                    # Write plist file
                    with open(plist_path, 'w') as f:
                        f.write(plist_content)

                    # Load the plist
                    try:
                        subprocess.run(['launchctl', 'load', plist_path], check=True)
                        logger.info(f"Added application to login items: {plist_path}")
                    except subprocess.CalledProcessError as e:
                        logger.error(f"Failed to load plist: {e}")
                else:
                    # Remove from login items if plist exists
                    if os.path.exists(plist_path):
                        try:
                            # Unload the plist
                            subprocess.run(['launchctl', 'unload', plist_path], check=False)

                            # Remove the plist file
                            os.remove(plist_path)
                            logger.info(f"Removed application from login items: {plist_path}")
                        except Exception as e:
                            logger.error(f"Failed to remove from login items: {e}")
            else:
                logger.warning(f"Start at login not implemented for platform: {platform.system()}")
        except Exception as e:
            logger.error(f"Failed to set start at login: {e}")

def show_preferences_window(config, ami_client, notification_mgr):
    """Show preferences window"""
    # Get wxPython app
    from asterisk_popup.ui.wx.app import get_wx_app
    app = get_wx_app()

    # Create and show window
    window = PreferencesWindow(config, ami_client, notification_mgr)
    window.Show()

    return window

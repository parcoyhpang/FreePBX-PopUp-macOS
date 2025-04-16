"""
Main Window for FreePBX Popup - Primary application window module.
Provides a tabbed interface for preferences, settings, and about information.
"""

import wx
import logging
import os
import threading
import platform
from datetime import datetime

from asterisk_popup.ui.wx.theme_manager import ThemeManager

from asterisk_popup.ui.wx.preferences_window import ConnectionPanel, NotificationsPanel, GeneralPanel
from asterisk_popup.ui.wx.about_panel import AboutPanel

logger = logging.getLogger('FreePBXPopup.MainWindow')

class MainWindow(wx.Frame):
    """Main window with tabbed interface for FreePBX Popup"""

    def __init__(self, config):
        """
        Initialize main window

        Args:
            config (dict): Configuration dictionary
        """
        width = 500
        height = 600

        super(MainWindow, self).__init__(
            None,
            title="FreePBX Popup",
            size=(width, height),
            style=wx.DEFAULT_FRAME_STYLE
        )

        self.config = config
        self.ami_client = None
        self.notification_mgr = None
        self.config_path = config.get('config_manager')

        # Import required modules
        import json
        import os

        # Load the actual config from the config file if provided
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.config_data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config from {self.config_path}: {e}")
                self.config_data = {}
        else:
            # Use the provided config as is
            self.config_data = config

        # Start command checking timer
        self._start_command_check_timer()

        self._set_icon()

        self.theme_manager = ThemeManager()
        self.is_dark_mode = self.theme_manager.is_dark_mode

        self.theme_manager.apply_to_window(self)

        self._create_ui()

        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.SetSize(wx.Size(550, 600))
        self.Center()

    def _set_icon(self):
        """Set window icon"""
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'resources', 'icon.png')
            if os.path.exists(icon_path):
                icon = wx.Icon(icon_path, wx.BITMAP_TYPE_PNG)
                self.SetIcon(icon)
        except Exception as e:
            logger.error(f"Failed to set icon: {e}")

    def _is_dark_mode(self):
        """Check if system is in dark mode"""
        try:
            if wx.SystemSettings.GetAppearance().IsDark():
                return True
        except:
            pass

        bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        brightness = (bg_color.Red() + bg_color.Green() + bg_color.Blue()) / 3
        return brightness < 128

    def _apply_theme(self):
        """Apply theme based on system settings"""
        if self.is_dark_mode:
            self.SetBackgroundColour(wx.Colour(40, 40, 40))
            self.SetForegroundColour(wx.Colour(255, 255, 255))
        else:
            self.SetBackgroundColour(wx.Colour(240, 240, 240))
            self.SetForegroundColour(wx.Colour(0, 0, 0))

    def _create_ui(self):
        """Create UI elements"""
        self.panel = wx.Panel(self)

        self.panel.SetBackgroundColour(self.GetBackgroundColour())

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        header_panel = self._create_header_panel()
        main_sizer.Add(header_panel, 0, wx.EXPAND | wx.ALL, 0)

        separator = wx.StaticLine(self.panel)
        if self.is_dark_mode:
            separator.SetBackgroundColour(wx.Colour(60, 60, 60))
        else:
            separator.SetBackgroundColour(wx.Colour(200, 200, 200))
        main_sizer.Add(separator, 0, wx.EXPAND)

        notebook_container = wx.Panel(self.panel)
        if self.is_dark_mode:
            notebook_container.SetBackgroundColour(wx.Colour(40, 40, 40))
        else:
            notebook_container.SetBackgroundColour(wx.Colour(245, 245, 245))
        notebook_sizer = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(notebook_container)

        self.notebook.SetBackgroundColour(notebook_container.GetBackgroundColour())

        notebook_sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 10)
        notebook_container.SetSizer(notebook_sizer)

        main_sizer.Add(notebook_container, 1, wx.EXPAND)

        self._create_preferences_tabs()
        self._create_about_tab()

        status_panel = wx.Panel(self.panel)
        if self.is_dark_mode:
            status_panel.SetBackgroundColour(wx.Colour(50, 50, 50))
        else:
            status_panel.SetBackgroundColour(wx.Colour(235, 235, 235))
        status_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.status_bar_text = wx.StaticText(status_panel, label="Disconnected")
        if self.is_dark_mode:
            self.status_bar_text.SetForegroundColour(wx.Colour(180, 180, 180))
        else:
            self.status_bar_text.SetForegroundColour(wx.Colour(80, 80, 80))
        status_sizer.Add(self.status_bar_text, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        status_sizer.Add(1, 1, 1, wx.EXPAND)

        version_text = wx.StaticText(status_panel, label="v1.0.0")
        if self.is_dark_mode:
            version_text.SetForegroundColour(wx.Colour(120, 120, 120))
        else:
            version_text.SetForegroundColour(wx.Colour(150, 150, 150))
        status_sizer.Add(version_text, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        status_panel.SetSizer(status_sizer)
        main_sizer.Add(status_panel, 0, wx.EXPAND)

        self.panel.SetSizer(main_sizer)

        self._start_status_update_timer()

    def _create_header_panel(self):
        """Create header panel with logo and title"""
        header_panel = wx.Panel(self.panel)

        if self.is_dark_mode:
            header_panel.SetBackgroundColour(wx.Colour(45, 45, 45))
        else:
            header_panel.SetBackgroundColour(wx.Colour(240, 240, 240))

        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'resources', 'icon.png')
        if os.path.exists(icon_path):
            logo = wx.Bitmap(icon_path, wx.BITMAP_TYPE_PNG)
            logo = self._scale_bitmap(logo, 24, 24)
            logo_ctrl = wx.StaticBitmap(header_panel, bitmap=logo)
            header_sizer.Add(logo_ctrl, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 12)

        title_font = wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title = wx.StaticText(header_panel, label="FreePBX Popup")
        title.SetFont(title_font)
        if self.is_dark_mode:
            title.SetForegroundColour(wx.Colour(255, 255, 255))
        else:
            title.SetForegroundColour(wx.Colour(80, 80, 80))
        header_sizer.Add(title, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 12)

        header_sizer.Add(1, 1, 1, wx.EXPAND)

        status_sizer = wx.BoxSizer(wx.HORIZONTAL)

        initial_color = self.theme_manager.get_status_indicator("disconnected")
        self.status_indicator = wx.Panel(header_panel, size=(8, 8))
        self.status_indicator.SetBackgroundColour(initial_color)

        logger.debug(f"Created status indicator panel with color: {initial_color}")
        status_sizer.Add(self.status_indicator, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 6)

        self.connection_status = wx.StaticText(header_panel, label="Disconnected")
        if self.is_dark_mode:
            self.connection_status.SetForegroundColour(wx.Colour(200, 200, 200))
        else:
            self.connection_status.SetForegroundColour(wx.Colour(80, 80, 80))
        status_sizer.Add(self.connection_status, 0, wx.ALIGN_CENTER_VERTICAL)

        header_sizer.Add(status_sizer, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 12)

        header_panel.SetSizer(header_sizer)

        return header_panel

    def _scale_bitmap(self, bitmap, width, height):
        """Scale a bitmap to the specified size"""
        image = bitmap.ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image)

    def _create_about_tab(self):
        """Create about tab"""
        about_panel = AboutPanel(self.notebook)
        self.notebook.AddPage(about_panel, "About")

    def _create_preferences_tabs(self):
        """Create preferences tabs"""
        # Import required modules
        from asterisk_popup.config_manager import ConfigManager
        from asterisk_popup.ami_client import AMIClient
        from asterisk_popup.notification_manager import NotificationManager

        # Create config manager if needed
        if not hasattr(self, 'config_manager'):
            if hasattr(self, 'config_path') and self.config_path:
                self.config_manager = ConfigManager(self.config_path)
            else:
                self.config_manager = ConfigManager()
                self.config_manager.config = self.config_data

        # Create AMI client if needed
        if not hasattr(self, 'ami_client') or not self.ami_client:
            # Check if we have AMI settings in the config
            ami_settings = self.config_data.get('ami_settings', {})
            if ami_settings:
                # Create a pre-configured AMI client
                self.ami_client = AMIClient(self.config_manager)

                # If the AMI client is already connected in the main app, set the status
                if ami_settings.get('connected', False):
                    self.ami_client.connected = True
                    self.ami_client.reconnect_attempts = 0
            else:
                # Create a regular AMI client
                self.ami_client = AMIClient(self.config_manager)

        # Create notification manager if needed
        if not hasattr(self, 'notification_mgr') or not self.notification_mgr:
            self.notification_mgr = NotificationManager(self.config_manager)

        # Create panels
        connection_panel = ConnectionPanel(self.notebook, self.config_manager, self.ami_client)
        self.notebook.AddPage(connection_panel, "Connection")

        notifications_panel = NotificationsPanel(self.notebook, self.config_manager, self.notification_mgr)
        self.notebook.AddPage(notifications_panel, "Notifications")

        general_panel = GeneralPanel(self.notebook, self.config_manager)
        self.notebook.AddPage(general_panel, "General")

    def _start_status_update_timer(self):
        """Start timer to update status"""
        self._update_status()

    def _update_status(self):
        """Update status in status bar and header"""
        try:
            # Make sure we have an AMI client
            if not hasattr(self, 'ami_client') or not self.ami_client:
                # Create AMI client if needed
                if hasattr(self, 'config_manager'):
                    from asterisk_popup.ami_client import AMIClient
                    self.ami_client = AMIClient(self.config_manager)

            if hasattr(self, 'ami_client') and self.ami_client:
                status = self.ami_client.get_status()

                if status.get('connected'):
                    status_text = "Connected"
                    status_type = "connected"
                else:
                    reconnect_attempts = status.get('reconnect_attempts', 0)
                    if reconnect_attempts > 0:
                        status_text = f"Reconnecting ({reconnect_attempts})"
                        status_type = "reconnecting"
                    else:
                        status_text = "Disconnected"
                        status_type = "disconnected"
            else:
                status_text = "Initializing"
                status_type = "initializing"

            indicator_color = self.theme_manager.get_status_indicator(status_type)

            if hasattr(self, 'status_bar_text'):
                self.status_bar_text.SetLabel(status_text)

            if hasattr(self, 'connection_status'):
                self.connection_status.SetLabel(status_text)
                if self.is_dark_mode:
                    self.connection_status.SetForegroundColour(wx.Colour(200, 200, 200))
                else:
                    self.connection_status.SetForegroundColour(wx.Colour(80, 80, 80))

            if hasattr(self, 'status_indicator'):
                self.status_indicator.SetBackgroundColour(indicator_color)
                self.status_indicator.Refresh()

            if hasattr(self, 'panel'):
                self.panel.Layout()

        except Exception as e:
            logger.error(f"Failed to update status: {e}")

        self.status_update_timer = threading.Timer(5.0, self._update_status)
        self.status_update_timer.daemon = True
        self.status_update_timer.start()

    def _on_paint_indicator(self, event):
        """Paint the status indicator as a circle"""
        dc = wx.PaintDC(self.status_indicator)
        gc = wx.GraphicsContext.Create(dc)

        if gc:
            w, h = self.status_indicator.GetSize()

            color = self.status_indicator.GetBackgroundColour()

            gc.SetBrush(wx.Brush(color))

            gc.DrawEllipse(0, 0, w, h)

    def _start_command_check_timer(self):
        """Start timer to check for commands"""
        self._check_for_commands()

    def _check_for_commands(self):
        """Check for commands from the menu bar app"""
        try:
            import json
            import os

            # Check if we have a config path
            if hasattr(self, 'config_path') and self.config_path:
                # Check if there's a command file
                command_path = f"{self.config_path}.command"
                if os.path.exists(command_path):
                    try:
                        # Read the command
                        with open(command_path, 'r') as f:
                            command = json.load(f)

                        # Process the command
                        self._process_command(command)

                        # Delete the command file
                        try:
                            os.remove(command_path)
                        except:
                            pass
                    except Exception as e:
                        logger.error(f"Failed to process command: {e}")
        except Exception as e:
            logger.error(f"Failed to check for commands: {e}")

        # Schedule the next check
        self.command_check_timer = threading.Timer(1.0, self._check_for_commands)
        self.command_check_timer.daemon = True
        self.command_check_timer.start()

    def _process_command(self, command):
        """Process a command from the menu bar app"""
        try:
            logger.info(f"Processing command: {command}")

            if command.get('command') == 'quit':
                # Close the window
                wx.CallAfter(self.Close)
            elif command.get('command') == 'show':
                # Show the specified tab
                tab = command.get('tab')
                if tab and hasattr(self, 'notebook'):
                    # Find the tab index
                    for i in range(self.notebook.GetPageCount()):
                        if self.notebook.GetPageText(i).lower() == tab.lower():
                            wx.CallAfter(self.notebook.SetSelection, i)
                            break
            elif command.get('command') == 'update_status':
                # Update the connection status
                status = command.get('status', {})
                status_text = status.get('text', 'Unknown')
                status_type = status.get('type', 'disconnected')

                # Update the UI with the new status
                indicator_color = self.theme_manager.get_status_indicator(status_type)

                if hasattr(self, 'status_bar_text'):
                    wx.CallAfter(self.status_bar_text.SetLabel, status_text)

                if hasattr(self, 'connection_status'):
                    wx.CallAfter(self.connection_status.SetLabel, status_text)
                    if self.is_dark_mode:
                        wx.CallAfter(self.connection_status.SetForegroundColour, wx.Colour(200, 200, 200))
                    else:
                        wx.CallAfter(self.connection_status.SetForegroundColour, wx.Colour(80, 80, 80))

                if hasattr(self, 'status_indicator'):
                    wx.CallAfter(self.status_indicator.SetBackgroundColour, indicator_color)
                    wx.CallAfter(self.status_indicator.Refresh)

                if hasattr(self, 'panel'):
                    wx.CallAfter(self.panel.Layout)
        except Exception as e:
            logger.error(f"Failed to process command: {e}")

    def on_close(self, event):
        """Handle window close event"""
        if hasattr(self, 'status_update_timer') and self.status_update_timer:
            self.status_update_timer.cancel()

        if hasattr(self, 'command_check_timer') and self.command_check_timer:
            self.command_check_timer.cancel()

        self.Hide()

    def show(self):
        """Show the window"""
        self.Show()
        self.Raise()

        if platform.system() == 'Darwin':
            try:
                import AppKit
                AppKit.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
            except ImportError:
                import subprocess
                try:
                    subprocess.run(['osascript', '-e', 'tell application "System Events" to set frontmost of process "Python" to true'], check=False)
                except Exception as e:
                    logger.error(f"Failed to activate app: {e}")

def show_main_window(config):
    """Show main window"""
    from asterisk_popup.ui.wx.app import get_wx_app
    app = get_wx_app()

    window = MainWindow(config)
    window.show()

    return window

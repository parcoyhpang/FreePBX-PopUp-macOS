"""
Call Notification Window for FreePBX Popup - Incoming call notification UI module.
Displays a rich notification window for incoming calls with call control functionality.
"""

import wx
import wx.adv
import logging
import threading
import time
import os
import platform
from datetime import datetime
from ctypes import c_void_p

logger = logging.getLogger('FreePBXPopup.CallNotificationWindow')

class CallNotificationWindow(wx.Frame):
    """Rich notification window for incoming calls"""

    def __init__(self, call_info, config, call_history):
        """
        Initialize call notification window

        Args:
            call_info (dict): Call information
            config (ConfigManager): Configuration manager instance
            call_history (CallHistoryManager): Call history manager instance
        """
        # Get screen size
        display = wx.Display(0)
        screen_rect = display.GetGeometry()

        # Calculate window position (bottom right corner)
        width = 350
        height = 300  # Taller to accommodate the timer, buttons and recording toggle
        x = screen_rect.GetRight() - width - 20
        y = screen_rect.GetBottom() - height - 50

        # Initialize frame - use a normal window with border for native look
        # Use STAY_ON_TOP and FRAME_FLOAT_ON_PARENT for maximum topmost behavior
        super(CallNotificationWindow, self).__init__(
            None,
            title="Incoming Call",
            pos=(x, y),
            size=(width, height),
            style=wx.CAPTION | wx.STAY_ON_TOP | wx.CLOSE_BOX | wx.FRAME_FLOAT_ON_PARENT | wx.FRAME_NO_TASKBAR
        )

        # Set window to be always on top (platform-specific approach)
        self.SetWindowStyleFlag(self.GetWindowStyleFlag() | wx.STAY_ON_TOP)

        self.call_info = call_info
        self.config = config
        self.call_history = call_history
        self.auto_close_timer = None

        # Call state tracking
        self.call_active = False
        self.call_start_time = None
        self.call_timer = None
        self.timer_display = None

        # Store channel for call status tracking
        self.channel = call_info.get('channel', '')

        # AMI connection for call control
        self.ami_socket = None

        # Set background color based on system theme
        self.is_dark_mode = self._is_dark_mode()
        if self.is_dark_mode:
            self.SetBackgroundColour(wx.Colour(40, 40, 40))
            text_color = wx.Colour(255, 255, 255)
        else:
            self.SetBackgroundColour(wx.Colour(240, 240, 240))
            text_color = wx.Colour(0, 0, 0)

        # Create rounded shape
        self._create_rounded_shape()

        # Create UI
        self._create_ui(text_color)

        # Bind events
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)

        # Play sound
        self._play_notification_sound()

        # Set up auto-dismiss
        self._setup_auto_dismiss()

        # Set up call timer
        self._setup_call_timer()

        # Connect to AMI for call control
        self._connect_to_ami()

        # Show window and bring to front
        self.Show()
        self.Raise()

        # On macOS, hide dock icon and ensure window stays on top
        if platform.system() == 'Darwin':
            try:
                # Hide dock icon directly
                try:
                    import objc
                    from Foundation import NSBundle
                    bundle = NSBundle.mainBundle()
                    info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                    info['LSUIElement'] = '1'  # Set to run as agent (no dock icon)
                    logger.info("Hiding dock icon in window initialization")
                except Exception as e:
                    logger.error(f"Failed to hide dock icon: {e}")

                # Try to use PyObjC to set the window level
                self._set_macos_window_level()
            except Exception as e:
                logger.error(f"Failed to set macOS window level: {e}")
                # Fallback to osascript
                self._activate_window_with_osascript()

    def _create_rounded_shape(self):
        """Create rounded shape for the window"""
        # Skip shape creation - we'll use the paint event to draw rounded corners
        # This avoids bitmap access issues on macOS
        pass

    def _create_ui(self, text_color):
        """Create UI elements"""
        # Create main panel
        panel = wx.Panel(self)

        # Set colors based on theme
        if self.is_dark_mode:
            bg_color = wx.Colour(40, 40, 40)
            header_bg_color = wx.Colour(60, 60, 60)
            content_bg_color = wx.Colour(50, 50, 50)
            highlight_color = wx.Colour(0, 120, 215)  # Blue highlight
            button_bg_color = wx.Colour(70, 70, 70)
            hangup_bg_color = wx.Colour(180, 60, 60)  # Red for hang up
            separator_color = wx.Colour(80, 80, 80)
            text_color = wx.Colour(230, 230, 230)  # Light text for dark mode
        else:
            bg_color = wx.Colour(240, 240, 240)
            header_bg_color = wx.Colour(220, 220, 220)
            content_bg_color = wx.Colour(250, 250, 250)
            highlight_color = wx.Colour(0, 120, 215)  # Blue highlight
            button_bg_color = wx.Colour(230, 230, 230)
            hangup_bg_color = wx.Colour(220, 80, 80)  # Red for hang up
            separator_color = wx.Colour(200, 200, 200)
            text_color = wx.Colour(20, 20, 20)  # Dark text for light mode

        # Set panel background color
        panel.SetBackgroundColour(bg_color)

        # Create main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create header panel with background color
        header_panel = wx.Panel(panel)
        header_panel.SetBackgroundColour(header_bg_color)
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Phone icon
        icon_size = 28
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'resources', 'icon.png')
        if os.path.exists(icon_path):
            phone_icon = wx.Bitmap(icon_path, wx.BITMAP_TYPE_PNG)
            phone_icon = self._scale_bitmap(phone_icon, icon_size, icon_size)
            icon_ctrl = wx.StaticBitmap(header_panel, bitmap=phone_icon)
            header_sizer.Add(icon_ctrl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        # Title
        title_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        title = wx.StaticText(header_panel, label="Incoming Call")
        title.SetFont(title_font)
        title.SetForegroundColour(text_color)
        header_sizer.Add(title, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        # Close button
        close_button = wx.Button(header_panel, label="×", size=(30, 30), style=wx.BORDER_NONE)
        close_button.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        close_button.SetForegroundColour(text_color)
        close_button.SetBackgroundColour(header_bg_color)
        close_button.Bind(wx.EVT_BUTTON, self.on_close)
        header_sizer.Add(close_button, 0, wx.ALL, 5)

        header_panel.SetSizer(header_sizer)
        main_sizer.Add(header_panel, 0, wx.EXPAND)

        # Content panel with background color
        content_panel = wx.Panel(panel)
        content_panel.SetBackgroundColour(content_bg_color)
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        # Caller info section
        caller_panel = wx.Panel(content_panel)
        caller_panel.SetBackgroundColour(content_bg_color)
        caller_sizer = wx.BoxSizer(wx.VERTICAL)

        # From label
        from_label = wx.StaticText(caller_panel, label="From:")
        from_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        from_label.SetForegroundColour(text_color)
        caller_sizer.Add(from_label, 0, wx.LEFT | wx.TOP, 5)

        # Add gap between "From:" and caller name
        caller_sizer.AddSpacer(5)

        # Caller name (larger and more prominent)
        caller_name = self.call_info.get('caller_id_name', 'Unknown')
        caller_name_font = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        caller_name_ctrl = wx.StaticText(caller_panel, label=caller_name)
        caller_name_ctrl.SetFont(caller_name_font)
        caller_name_ctrl.SetForegroundColour(highlight_color)
        # Ensure the text wraps if it's too long
        caller_name_ctrl.Wrap(300)  # Set a maximum width for wrapping
        caller_sizer.Add(caller_name_ctrl, 0, wx.LEFT | wx.BOTTOM | wx.RIGHT, 5)

        caller_panel.SetSizer(caller_sizer)
        content_sizer.Add(caller_panel, 0, wx.EXPAND)

        # Add a subtle separator
        separator = wx.StaticLine(content_panel)
        separator.SetBackgroundColour(separator_color)
        content_sizer.Add(separator, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)

        # Call details grid
        details_panel = wx.Panel(content_panel)
        details_panel.SetBackgroundColour(content_bg_color)
        details_sizer = wx.BoxSizer(wx.VERTICAL)

        # Create a grid with less spacing
        details_grid = wx.FlexGridSizer(rows=2, cols=2, vgap=4, hgap=10)
        details_grid.AddGrowableCol(1, 1)  # Make second column expandable

        # Caller number
        caller_number = self.call_info.get('caller_id_num', 'Unknown')
        number_label = wx.StaticText(details_panel, label="Number:")
        number_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        number_label.SetForegroundColour(text_color)
        details_grid.Add(number_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

        number_value = wx.StaticText(details_panel, label=caller_number)
        number_value.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        number_value.SetForegroundColour(text_color)
        # Ensure text wraps if needed
        number_value.Wrap(200)
        details_grid.Add(number_value, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        # Extension
        extension = self.call_info.get('extension', 'Unknown')
        extension_label = wx.StaticText(details_panel, label="To:")
        extension_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        extension_label.SetForegroundColour(text_color)
        details_grid.Add(extension_label, 0, wx.ALIGN_LEFT | wx.ALIGN_CENTER_VERTICAL)

        extension_value = wx.StaticText(details_panel, label=extension)
        extension_value.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        extension_value.SetForegroundColour(text_color)
        # Ensure text wraps if needed
        extension_value.Wrap(200)
        details_grid.Add(extension_value, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL)

        # Add the grid to the details sizer with padding
        details_sizer.Add(details_grid, 0, wx.EXPAND | wx.ALL, 5)

        details_panel.SetSizer(details_sizer)
        content_sizer.Add(details_panel, 0, wx.EXPAND)

        # Call timer section - make it stand out with a different background
        timer_panel = wx.Panel(content_panel)
        if self.is_dark_mode:
            timer_bg_color = wx.Colour(60, 60, 70)  # Slightly different to make it stand out
        else:
            timer_bg_color = wx.Colour(235, 235, 245)  # Slightly different to make it stand out
        timer_panel.SetBackgroundColour(timer_bg_color)
        timer_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Timer label
        timer_label = wx.StaticText(timer_panel, label="Call Duration:")
        timer_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        timer_label.SetForegroundColour(text_color)
        timer_sizer.Add(timer_label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        # Timer display
        self.timer_display = wx.StaticText(timer_panel, label="Ringing...")
        self.timer_display.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.timer_display.SetForegroundColour(highlight_color)
        timer_sizer.Add(self.timer_display, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        timer_panel.SetSizer(timer_sizer)
        content_sizer.Add(timer_panel, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, 5)

        content_panel.SetSizer(content_sizer)
        main_sizer.Add(content_panel, 1, wx.EXPAND | wx.ALL, 5)

        # Recording toggle section
        recording_panel = wx.Panel(panel)
        recording_panel.SetBackgroundColour(content_bg_color)
        recording_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Recording toggle - initially disabled until call is answered
        self.recording_checkbox = wx.CheckBox(recording_panel, label="Force Call Recording")
        self.recording_checkbox.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.recording_checkbox.SetForegroundColour(text_color)
        self.recording_checkbox.Enable(False)  # Initially disabled
        self.recording_checkbox.Bind(wx.EVT_CHECKBOX, self.on_recording_toggle)
        recording_sizer.Add(self.recording_checkbox, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        # Recording status text
        self.recording_status = wx.StaticText(recording_panel, label="")
        self.recording_status.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.recording_status.SetForegroundColour(highlight_color)
        recording_sizer.Add(self.recording_status, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)

        recording_panel.SetSizer(recording_sizer)
        main_sizer.Add(recording_panel, 0, wx.EXPAND | wx.BOTTOM, 5)

        # Buttons panel
        button_panel = wx.Panel(panel)
        button_panel.SetBackgroundColour(bg_color)
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Transfer button
        transfer_button = wx.Button(button_panel, label="Transfer")
        transfer_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        transfer_button.Bind(wx.EVT_BUTTON, self.on_transfer)
        button_sizer.Add(transfer_button, 1, wx.ALL, 5)

        # Hang up button
        hangup_button = wx.Button(button_panel, label="Hang Up")
        hangup_button.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        #hangup_button.SetBackgroundColour(hangup_bg_color)
        hangup_button.SetForegroundColour(wx.WHITE)
        hangup_button.Bind(wx.EVT_BUTTON, self.on_hangup)
        hangup_button.SetWindowStyle(wx.BORDER_NONE)
        hangup_button.SetWindowStyleFlag(hangup_button.GetWindowStyleFlag() | wx.BORDER_NONE)
        hangup_button.SetSize(hangup_button.GetSize() + wx.Size(0, 4))  # Increase height slightly for better appearance
        button_sizer.Add(hangup_button, 1, wx.ALL, 5)

        button_panel.SetSizer(button_sizer)
        main_sizer.Add(button_panel, 0, wx.EXPAND | wx.BOTTOM, 5)

        panel.SetSizer(main_sizer)

    def _scale_bitmap(self, bitmap, width, height):
        """Scale a bitmap to the specified size"""
        image = bitmap.ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image)

    def _is_dark_mode(self):
        """Check if system is in dark mode"""
        # This is a simple check that works on macOS
        # A more robust solution would use platform-specific APIs
        try:
            if wx.SystemSettings.GetAppearance().IsDark():
                return True
        except:
            pass

        # Fallback: check system color
        bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        brightness = (bg_color.Red() + bg_color.Green() + bg_color.Blue()) / 3
        return brightness < 128

    def _play_notification_sound(self):
        """Play notification sound"""
        try:
            # Get sound settings
            notifications = self.config.get_notification_settings()
            sound = notifications.get('sound', 'default')

            if sound == 'default':
                # Use system default sound on macOS
                if platform.system() == 'Darwin':
                    import subprocess
                    try:
                        # Use afplay to play the system sound
                        subprocess.Popen(['afplay', '/System/Library/Sounds/Ping.aiff'])
                    except Exception as e:
                        logger.error(f"Failed to play system sound with afplay: {e}")
                else:
                    # Use wxPython's sound on other platforms
                    wx.adv.Sound.PlaySound("SystemAsterisk")
            elif sound == 'custom':
                # Use custom sound
                custom_sound_path = notifications.get('custom_sound_path', '')
                if custom_sound_path and os.path.exists(custom_sound_path):
                    if platform.system() == 'Darwin':
                        import subprocess
                        try:
                            # Use afplay to play the custom sound
                            subprocess.Popen(['afplay', custom_sound_path])
                        except Exception as e:
                            logger.error(f"Failed to play custom sound with afplay: {e}")
                    else:
                        # Use wxPython's sound on other platforms
                        wx.adv.Sound(custom_sound_path).Play()
        except Exception as e:
            logger.error(f"Failed to play notification sound: {e}")

    def _setup_auto_dismiss(self):
        """Set up auto-dismiss timer if enabled"""
        try:
            # Get notification settings
            notifications = self.config.get_notification_settings()
            auto_dismiss = notifications.get('auto_dismiss', False)

            if auto_dismiss:
                # Get timeout
                timeout = notifications.get('auto_dismiss_timeout', 10)

                # Start timer
                self.auto_close_timer = threading.Timer(timeout, self._auto_close)
                self.auto_close_timer.daemon = True
                self.auto_close_timer.start()
        except Exception as e:
            logger.error(f"Failed to set up auto-dismiss: {e}")

    def _auto_close(self):
        """Auto-close the window"""
        try:
            wx.CallAfter(self.Close)
        except:
            pass

    def on_paint(self, event):
        """Handle paint event to draw rounded corners"""
        dc = wx.PaintDC(self)
        gc = wx.GraphicsContext.Create(dc)

        if gc:
            width, height = self.GetSize()

            # Set brush based on theme
            if self.is_dark_mode:
                bg_color = wx.Colour(40, 40, 40)
            else:
                bg_color = wx.Colour(240, 240, 240)

            # Set brush and pen
            gc.SetBrush(wx.Brush(bg_color))
            gc.SetPen(wx.Pen(bg_color, 1))

            # Draw rounded rectangle
            gc.DrawRoundedRectangle(0, 0, width, height, 15)

    def _setup_call_timer(self):
        """Set up call timer"""
        try:
            # Create a timer that updates every second
            self.call_timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.on_timer, self.call_timer)

            # Initially the call is not active (ringing state)
            self.timer_display.SetLabel("Ringing...")

            # Start a status check timer to check for status updates
            self.status_check_timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.on_status_check, self.status_check_timer)
            self.status_check_timer.Start(1000)  # Check every second
        except Exception as e:
            logger.error(f"Failed to set up call timer: {e}")

    def _connect_to_ami(self):
        """Connect to AMI for call control"""
        try:
            # Get AMI settings from config
            ami_settings = self.config.config.get('ami', {})
            host = ami_settings.get('host', 'localhost')
            port = int(ami_settings.get('port', 5038))
            username = ami_settings.get('username', '')
            secret = ami_settings.get('secret', '')

            # Create socket connection
            import socket
            self.ami_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ami_socket.settimeout(3)  # 3 second timeout

            # Connect and login
            self.ami_socket.connect((host, port))

            # Read welcome message
            welcome = self.ami_socket.recv(1024).decode('utf-8')
            logger.debug(f"AMI welcome: {welcome}")

            # Login
            login_action = f"Action: Login\r\nUsername: {username}\r\nSecret: {secret}\r\n\r\n"
            self.ami_socket.sendall(login_action.encode('utf-8'))

            # Read response
            response = self.ami_socket.recv(1024).decode('utf-8')
            logger.debug(f"AMI login response: {response}")

            if "Success" in response:
                logger.info("Successfully connected to AMI for call control")
            else:
                logger.error(f"Failed to login to AMI: {response}")
                self.ami_socket.close()
                self.ami_socket = None
        except Exception as e:
            logger.error(f"Failed to connect to AMI: {e}")
            if self.ami_socket:
                self.ami_socket.close()
            self.ami_socket = None

    def _update_call_status(self, status):
        """Update call status"""
        try:
            if status == 'answered':
                # Call was answered, start the timer
                self.call_active = True
                self.call_start_time = time.time()
                self.call_timer.Start(1000)  # Update every second
                self.timer_display.SetLabel("00:00")

                # Update window title
                self.SetTitle("Active Call")

                # Enable recording checkbox
                self.recording_checkbox.Enable(True)
            elif status == 'hangup':
                # Call ended, stop the timer
                self.call_active = False
                if self.call_timer.IsRunning():
                    self.call_timer.Stop()

                # Update display
                self.timer_display.SetLabel("Call Ended")

                # Stop recording if active
                if hasattr(self, 'recording_checkbox') and self.recording_checkbox.GetValue():
                    try:
                        # Stop recording
                        if self.ami_socket and self.channel:
                            stopmonitor_action = f"Action: StopMonitor\r\nChannel: {self.channel}\r\n\r\n"
                            self.ami_socket.sendall(stopmonitor_action.encode('utf-8'))
                            logger.info(f"Stopped recording for channel {self.channel} on hangup")
                    except Exception as e:
                        logger.error(f"Error stopping recording on hangup: {e}")

                # Disable recording checkbox
                if hasattr(self, 'recording_checkbox'):
                    self.recording_checkbox.SetValue(False)
                    self.recording_checkbox.Enable(False)
                    self.recording_status.SetLabel("Call ended")

                # Close the window after a short delay
                wx.CallLater(2000, self.Close)
        except Exception as e:
            logger.error(f"Failed to update call status: {e}")

    def on_timer(self, event):
        """Handle timer event to update call duration"""
        try:
            if self.call_active and self.call_start_time:
                # Calculate duration
                duration = int(time.time() - self.call_start_time)
                minutes = duration // 60
                seconds = duration % 60

                # Update display
                self.timer_display.SetLabel(f"{minutes:02d}:{seconds:02d}")
        except Exception as e:
            logger.error(f"Error updating call timer: {e}")

    def on_status_check(self, event):
        """Check for status updates from the notification manager"""
        try:
            if not self.channel:
                return

            # Check for status update file
            import tempfile
            import json
            import os

            status_file = os.path.join(tempfile.gettempdir(), f"call_status_{self.channel.replace('/', '_')}.json")

            if os.path.exists(status_file):
                try:
                    # Read the status update
                    with open(status_file, 'r') as f:
                        status_data = json.load(f)

                    # Delete the file to avoid processing it again
                    os.unlink(status_file)

                    # Process the status update
                    if status_data.get('channel') == self.channel:
                        status = status_data.get('status')
                        logger.info(f"Received status update: {status}")

                        # Update call status
                        self._update_call_status(status)
                except Exception as e:
                    logger.error(f"Error processing status update: {e}")
                    # Delete the file to avoid processing it again
                    try:
                        os.unlink(status_file)
                    except:
                        pass
        except Exception as e:
            logger.error(f"Error checking for status updates: {e}")

    def on_transfer(self, event):
        """Handle transfer button click"""
        try:
            if not self.ami_socket or not self.channel:
                wx.MessageBox(
                    "Cannot transfer call: No connection to AMI or no active channel.",
                    "Transfer Failed",
                    wx.OK | wx.ICON_ERROR
                )
                return

            # Show transfer dialog
            extension = wx.GetTextFromUser(
                "Enter extension to transfer to:",
                "Call Transfer",
                ""
            )

            if not extension:
                return  # User cancelled

            # Send transfer command to AMI
            transfer_action = f"Action: Redirect\r\nChannel: {self.channel}\r\nExten: {extension}\r\nContext: from-internal\r\nPriority: 1\r\n\r\n"
            self.ami_socket.sendall(transfer_action.encode('utf-8'))

            # Read response
            response = self.ami_socket.recv(1024).decode('utf-8')
            logger.debug(f"AMI transfer response: {response}")

            if "Success" in response:
                wx.MessageBox(
                    f"Call transferred to extension {extension}.",
                    "Transfer Successful",
                    wx.OK | wx.ICON_INFORMATION
                )
                # Close the window
                self.Close()
            else:
                wx.MessageBox(
                    f"Failed to transfer call: {response}",
                    "Transfer Failed",
                    wx.OK | wx.ICON_ERROR
                )
        except Exception as e:
            logger.error(f"Error transferring call: {e}")
            wx.MessageBox(
                f"Error transferring call: {e}",
                "Transfer Failed",
                wx.OK | wx.ICON_ERROR
            )

    def on_hangup(self, event):
        """Handle hang up button click"""
        try:
            if not self.ami_socket or not self.channel:
                # Just close the window if we can't hang up the call
                self.Close()
                return

            # Send hangup command to AMI
            hangup_action = f"Action: Hangup\r\nChannel: {self.channel}\r\n\r\n"
            self.ami_socket.sendall(hangup_action.encode('utf-8'))

            # Read response
            response = self.ami_socket.recv(1024).decode('utf-8')
            logger.debug(f"AMI hangup response: {response}")

            # Close the window regardless of response
            self.Close()
        except Exception as e:
            logger.error(f"Error hanging up call: {e}")
            # Just close the window if there's an error
            self.Close()

    def on_close(self, event):
        """Handle close event"""
        # Cancel auto-close timer
        if self.auto_close_timer:
            self.auto_close_timer.cancel()

        # Stop timers
        if self.call_timer and self.call_timer.IsRunning():
            self.call_timer.Stop()

        if hasattr(self, 'status_check_timer') and self.status_check_timer.IsRunning():
            self.status_check_timer.Stop()

        # Close AMI connection
        if self.ami_socket:
            try:
                self.ami_socket.close()
            except:
                pass

        # Hide and destroy
        self.Hide()
        self.Destroy()

    def on_left_down(self, event):
        """Handle mouse left button down for dragging"""
        self.CaptureMouse()
        pos = self.ClientToScreen(event.GetPosition())
        origin = self.GetPosition()
        self.delta = wx.Point(pos.x - origin.x, pos.y - origin.y)

    def on_motion(self, event):
        """Handle mouse motion for dragging"""
        if event.Dragging() and event.LeftIsDown() and self.HasCapture():
            pos = self.ClientToScreen(event.GetPosition())
            new_pos = (pos.x - self.delta.x, pos.y - self.delta.y)
            self.Move(new_pos)

    def on_left_up(self, event):
        """Handle mouse left button up for dragging"""
        if self.HasCapture():
            self.ReleaseMouse()

    def on_recording_toggle(self, event):
        """Handle recording toggle"""
        try:
            if not self.ami_socket or not self.channel:
                wx.MessageBox(
                    "Cannot record call: No connection to AMI or no active channel.",
                    "Recording Failed",
                    wx.OK | wx.ICON_ERROR
                )
                self.recording_checkbox.SetValue(False)
                return

            # Get the checkbox state
            is_recording = self.recording_checkbox.GetValue()

            if is_recording:
                # Start recording
                monitor_action = f"Action: Monitor\r\nChannel: {self.channel}\r\nFile: call_{int(time.time())}\r\nFormat: wav\r\nMix: true\r\n\r\n"
                self.ami_socket.sendall(monitor_action.encode('utf-8'))

                # Read response - AMI might send multiple events, so we need to read until we get a response
                # or until we timeout
                response = ""
                start_time = time.time()
                timeout = 2.0  # 2 second timeout

                # Set socket to non-blocking mode
                self.ami_socket.setblocking(0)

                try:
                    while time.time() - start_time < timeout:
                        try:
                            chunk = self.ami_socket.recv(1024).decode('utf-8')
                            if chunk:
                                response += chunk
                                if "Response: Success" in response or "Response: Error" in response:
                                    break
                            time.sleep(0.1)
                        except Exception:
                            # Socket would block, no data available
                            time.sleep(0.1)
                finally:
                    # Set socket back to blocking mode
                    self.ami_socket.setblocking(1)

                logger.debug(f"AMI monitor response: {response}")

                # Consider it a success if we don't get an explicit error
                if "Response: Error" not in response:
                    self.recording_status.SetLabel("Recording active")
                    self.recording_status.Show()  # Show status when recording starts
                    logger.info(f"Started recording for channel {self.channel}")
                else:
                    self.recording_checkbox.SetValue(False)
                    self.recording_status.SetLabel("Recording failed")
                    self.recording_status.Show()  # Show status on failure
                    logger.error(f"Failed to start recording: {response}")
            else:
                # Stop recording
                stopmonitor_action = f"Action: StopMonitor\r\nChannel: {self.channel}\r\n\r\n"
                self.ami_socket.sendall(stopmonitor_action.encode('utf-8'))

                # Read response - AMI might send multiple events, so we need to read until we get a response
                # or until we timeout
                response = ""
                start_time = time.time()
                timeout = 2.0  # 2 second timeout

                # Set socket to non-blocking mode
                self.ami_socket.setblocking(0)

                try:
                    while time.time() - start_time < timeout:
                        try:
                            chunk = self.ami_socket.recv(1024).decode('utf-8')
                            if chunk:
                                response += chunk
                                if "Response: Success" in response or "Response: Error" in response:
                                    break
                            time.sleep(0.1)
                        except Exception:
                            # Socket would block, no data available
                            time.sleep(0.1)
                finally:
                    # Set socket back to blocking mode
                    self.ami_socket.setblocking(1)

                logger.debug(f"AMI stop monitor response: {response}")

                # Consider it a success if we don't get an explicit error
                if "Response: Error" not in response:
                    self.recording_status.SetLabel("Recording stopped")
                    self.recording_status.Show()  # Show status when recording stops
                    logger.info(f"Stopped recording for channel {self.channel}")
                else:
                    self.recording_status.SetLabel("Failed to stop recording")
                    self.recording_status.Show()  # Show status on failure
                    logger.error(f"Failed to stop recording: {response}")

                # Hide the status after 3 seconds
                wx.CallLater(3000, self.recording_status.Hide)
        except Exception as e:
            logger.error(f"Error toggling recording: {e}")
            self.recording_checkbox.SetValue(False)
            self.recording_status.SetLabel("Recording error")
            self.recording_status.Show()  # Show error status
            # Hide the status after 3 seconds
            wx.CallLater(3000, self.recording_status.Hide)

    def _set_macos_window_level(self):
        """Set macOS window level to ensure it stays on top and hide dock icon"""
        try:
            # Try to import PyObjC modules
            import objc
            from Foundation import NSAutoreleasePool, NSBundle
            from AppKit import NSApplication, NSApp, NSWindow, NSFloatingWindowLevel

            # Hide dock icon
            bundle = NSBundle.mainBundle()
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            info['LSUIElement'] = '1'  # Set to run as agent (no dock icon)
            logger.info("Hiding dock icon from window")

            # Get the window handle
            window_handle = self.GetHandle()

            # Create an autorelease pool
            pool = NSAutoreleasePool.alloc().init()

            # Get the NSWindow instance
            ns_window = objc.objc_object(c_void_p=window_handle)

            # Set the window level to floating (above normal windows)
            ns_window.setLevel_(NSFloatingWindowLevel)

            # Make the window visible and bring it to front
            ns_window.makeKeyAndOrderFront_(None)

            # Release the pool
            del pool

            logger.info("Set macOS window level to floating")
        except Exception as e:
            logger.error(f"Error setting macOS window level: {e}")
            raise

    def _activate_window_with_osascript(self):
        """Use osascript to activate the window and bring it to front"""
        try:
            import subprocess
            import os

            # Get the process ID
            pid = os.getpid()

            # Use osascript to activate the application
            script = f"""
            tell application "System Events"
                set frontmost of every process whose unix id is {pid} to true
            end tell
            """

            # Execute the script
            subprocess.Popen(['osascript', '-e', script])

            logger.info("Activated window with osascript")
        except Exception as e:
            logger.error(f"Error activating window with osascript: {e}")

def show_call_notification(call_info, config, call_history):
    """Show call notification window"""
    # Get wxPython app
    from asterisk_popup.ui.wx.app import get_wx_app
    app = get_wx_app()

    # Create and show window
    window = CallNotificationWindow(call_info, config, call_history)

    return window

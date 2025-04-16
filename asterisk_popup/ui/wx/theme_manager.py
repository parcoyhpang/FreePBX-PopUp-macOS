"""
Theme Manager for FreePBX Popup - UI theming module.
Handles theme detection and application of consistent styling across the application.
"""

import wx
import logging
import platform

logger = logging.getLogger('FreePBXPopup.ThemeManager')

class ThemeManager:
    """Theme manager for FreePBX Popup"""

    def __init__(self):
        """Initialize theme manager"""
        self.is_dark_mode = self._detect_dark_mode()

 
        if self.is_dark_mode:
            # Dark mode colors
            self.bg_color = wx.Colour(40, 40, 40)
            self.fg_color = wx.Colour(230, 230, 230)
            self.accent_color = wx.Colour(52, 152, 219)  # Blue
            self.header_bg_color = wx.Colour(30, 30, 30)
            self.header_fg_color = wx.Colour(230, 230, 230)
            self.status_bar_bg_color = wx.Colour(30, 30, 30)
            self.status_bar_fg_color = wx.Colour(180, 180, 180)
            self.separator_color = wx.Colour(60, 60, 60)
            self.button_bg_color = wx.Colour(60, 60, 60)
            self.button_fg_color = wx.Colour(230, 230, 230)
            self.grid_bg_color = wx.Colour(50, 50, 50)
            self.grid_fg_color = wx.Colour(230, 230, 230)
            self.grid_line_color = wx.Colour(70, 70, 70)
            self.grid_header_bg_color = wx.Colour(60, 60, 60)
            self.grid_header_fg_color = wx.Colour(230, 230, 230)
            self.grid_selection_bg_color = wx.Colour(70, 130, 180)  # Steel blue
            self.grid_selection_fg_color = wx.Colour(255, 255, 255)
            self.tab_bg_color = wx.Colour(50, 50, 50)
            self.tab_fg_color = wx.Colour(230, 230, 230)
            self.tab_active_bg_color = wx.Colour(70, 70, 70)
            self.tab_active_fg_color = wx.Colour(255, 255, 255)
        else:
            # Light mode colors
            self.bg_color = wx.Colour(245, 245, 245)
            self.fg_color = wx.Colour(50, 50, 50)
            self.accent_color = wx.Colour(52, 152, 219)  # Blue
            self.header_bg_color = wx.Colour(235, 235, 235)
            self.header_fg_color = wx.Colour(50, 50, 50)
            self.status_bar_bg_color = wx.Colour(235, 235, 235)
            self.status_bar_fg_color = wx.Colour(80, 80, 80)
            self.separator_color = wx.Colour(200, 200, 200)
            self.button_bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE)
            self.button_fg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNTEXT)
            self.grid_bg_color = wx.Colour(255, 255, 255)
            self.grid_fg_color = wx.Colour(50, 50, 50)
            self.grid_line_color = wx.Colour(220, 220, 220)
            self.grid_header_bg_color = wx.Colour(240, 240, 240)
            self.grid_header_fg_color = wx.Colour(50, 50, 50)
            self.grid_selection_bg_color = wx.Colour(200, 220, 240)
            self.grid_selection_fg_color = wx.Colour(0, 0, 0)
            self.tab_bg_color = wx.Colour(235, 235, 235)
            self.tab_fg_color = wx.Colour(50, 50, 50)
            self.tab_active_bg_color = wx.Colour(255, 255, 255)
            self.tab_active_fg_color = wx.Colour(0, 0, 0)

        logger.info(f"Theme initialized: {'Dark' if self.is_dark_mode else 'Light'} mode")

    def _detect_dark_mode(self):
        """Detect if system is in dark mode"""
        try:
            if wx.SystemSettings.GetAppearance().IsDark():
                return True
        except:
            pass

        bg_color = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)
        brightness = (bg_color.Red() + bg_color.Green() + bg_color.Blue()) / 3
        return brightness < 128

    def apply_to_window(self, window):
        """Apply theme to a window"""
        window.SetBackgroundColour(self.bg_color)
        window.SetForegroundColour(self.fg_color)

    def apply_to_grid(self, grid):
        """Apply theme to a grid"""
        
        grid.SetDefaultCellBackgroundColour(self.grid_bg_color)
        grid.SetDefaultCellTextColour(self.grid_fg_color)
        grid.SetLabelBackgroundColour(self.grid_header_bg_color)
        grid.SetLabelTextColour(self.grid_header_fg_color)
        grid.SetGridLineColour(self.grid_line_color)

        grid.SetSelectionBackground(self.grid_selection_bg_color)
        grid.SetSelectionForeground(self.grid_selection_fg_color)

    def apply_to_notebook(self, notebook):
        """Apply theme to a notebook"""
        notebook.SetBackgroundColour(self.bg_color)
        notebook.SetForegroundColour(self.fg_color)

        try:
            art = notebook.GetArtProvider()

            if hasattr(art, 'SetColour'):
                art.SetColour(wx.aui.AUI_DOCKART_BACKGROUND_COLOUR, self.bg_color)
                art.SetColour(wx.aui.AUI_DOCKART_INACTIVE_CAPTION_COLOUR, self.tab_bg_color)
                art.SetColour(wx.aui.AUI_DOCKART_INACTIVE_CAPTION_TEXT_COLOUR, self.tab_fg_color)
                art.SetColour(wx.aui.AUI_DOCKART_ACTIVE_CAPTION_COLOUR, self.tab_active_bg_color)
                art.SetColour(wx.aui.AUI_DOCKART_ACTIVE_CAPTION_TEXT_COLOUR, self.tab_active_fg_color)
        except Exception as e:
            logger.error(f"Failed to set notebook colors: {e}")

    def get_status_indicator(self, status):
        """Get color for status indicator"""
        if status == "connected":
            return wx.Colour(0, 200, 0)  # Green
        elif status == "reconnecting":
            return wx.Colour(255, 165, 0)  # Orange
        elif status == "disconnected":
            return wx.Colour(255, 50, 50)  # Red
        else:
            return wx.Colour(100, 100, 100)  # Gray

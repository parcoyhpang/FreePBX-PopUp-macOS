"""
About Panel for FreePBX Popup - Application information display module.
Displays developer information, open source details, and system information.
"""

import wx
import wx.adv
import wx.lib.scrolledpanel as scrolled
import platform
import os
from datetime import datetime

class AboutPanel(scrolled.ScrolledPanel):

    def __init__(self, parent):
        super(AboutPanel, self).__init__(parent)

        self.SetBackgroundColour(wx.Colour(245, 245, 245) if not self._is_dark_mode() else wx.Colour(40, 40, 40))

        self.create_controls()

        self.SetupScrolling(scroll_x=False)

    def _is_dark_mode(self):
        if platform.system() == 'Darwin':
            try:
                import subprocess
                result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'],
                                      capture_output=True, text=True)
                return result.stdout.strip() == 'Dark'
            except:
                return False
        return False

    def create_controls(self):
        is_dark = self._is_dark_mode()
        text_color = wx.Colour(240, 240, 240) if is_dark else wx.Colour(20, 20, 20)
        link_color = wx.Colour(0, 120, 215)

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        header_panel = self.create_header_panel(is_dark, text_color)
        main_sizer.Add(header_panel, 0, wx.EXPAND | wx.BOTTOM, 20)

        content_panel = wx.Panel(self)
        content_panel.SetBackgroundColour(self.GetBackgroundColour())
        content_sizer = wx.BoxSizer(wx.VERTICAL)

        developer_panel = self.create_developer_panel(content_panel, is_dark, text_color)
        content_sizer.Add(developer_panel, 0, wx.EXPAND | wx.BOTTOM, 20)

        opensource_panel = self.create_opensource_panel(content_panel, is_dark, text_color)
        content_sizer.Add(opensource_panel, 0, wx.EXPAND | wx.BOTTOM, 20)

        system_panel = self.create_system_panel(content_panel, is_dark, text_color)
        content_sizer.Add(system_panel, 0, wx.EXPAND)

        content_panel.SetSizer(content_sizer)
        main_sizer.Add(content_panel, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 20)

        self.SetSizer(main_sizer)

    def create_header_panel(self, is_dark, text_color):
        header_panel = wx.Panel(self)
        header_panel.SetBackgroundColour(wx.Colour(30, 30, 30) if is_dark else wx.Colour(230, 230, 230))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'resources', 'icon.png')
        if os.path.exists(icon_path):
            bitmap = wx.Bitmap(icon_path, wx.BITMAP_TYPE_PNG)
            bitmap = self._scale_bitmap(bitmap, 64, 64)
            icon = wx.StaticBitmap(header_panel, bitmap=bitmap)
            header_sizer.Add(icon, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 15)

        title_sizer = wx.BoxSizer(wx.VERTICAL)

        app_name = wx.StaticText(header_panel, label="FreePBX Popup")
        app_name.SetFont(wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        app_name.SetForegroundColour(wx.Colour(240, 240, 240) if is_dark else wx.Colour(20, 20, 20))
        title_sizer.Add(app_name, 0, wx.BOTTOM, 5)

        version_copyright = wx.StaticText(header_panel, label=f"Version 1.0.0 | © {datetime.now().year}")
        version_copyright.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        version_copyright.SetForegroundColour(wx.Colour(200, 200, 200) if is_dark else wx.Colour(80, 80, 80))
        title_sizer.Add(version_copyright, 0, wx.BOTTOM, 5)

        description = wx.StaticText(header_panel, label="A macOS popup client for FreePBX")
        description.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL))
        description.SetForegroundColour(wx.Colour(200, 200, 200) if is_dark else wx.Colour(80, 80, 80))
        title_sizer.Add(description, 0)

        header_sizer.Add(title_sizer, 1, wx.ALL | wx.EXPAND, 15)
        header_panel.SetSizer(header_sizer)
        return header_panel

    def create_developer_panel(self, parent, is_dark, text_color):
        developer_panel = wx.Panel(parent)
        developer_panel.SetBackgroundColour(wx.Colour(45, 45, 45) if is_dark else wx.Colour(255, 255, 255))
        developer_sizer = wx.BoxSizer(wx.VERTICAL)

        dev_title = wx.StaticText(developer_panel, label="Developer Information")
        dev_title.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        dev_title.SetForegroundColour(text_color)
        developer_sizer.Add(dev_title, 0, wx.ALL, 15)

        dev_name = wx.StaticText(developer_panel, label="Developed by Parco Y.H. Pang")
        dev_name.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        dev_name.SetForegroundColour(text_color)
        developer_sizer.Add(dev_name, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        links = [
            ("GitHub", "@parcoyhpang", "https://github.com/parcoyhpang"),
            ("Website", "parcopang.com", "https://parcopang.com"),
            ("Repository", "FreePBX Popup", "https://github.com/parcoyhpang/freepbx-popup")
        ]

        for label, text, url in links:
            link_sizer = wx.BoxSizer(wx.HORIZONTAL)
            link_label = wx.StaticText(developer_panel, label=f"{label}:")
            link_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            link_label.SetForegroundColour(text_color)
            link_sizer.Add(link_label, 0, wx.RIGHT, 10)

            link = wx.adv.HyperlinkCtrl(developer_panel, wx.ID_ANY, text, url)
            link.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            link.SetNormalColour(wx.Colour(0, 122, 255) if is_dark else wx.Colour(0, 88, 208))
            link.SetHoverColour(wx.Colour(0, 150, 255) if is_dark else wx.Colour(0, 108, 228))
            link.SetVisitedColour(wx.Colour(0, 122, 255) if is_dark else wx.Colour(0, 88, 208))
            link_sizer.Add(link, 0)

            developer_sizer.Add(link_sizer, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        developer_panel.SetSizer(developer_sizer)
        return developer_panel

    def create_opensource_panel(self, parent, is_dark, text_color):
        opensource_panel = wx.Panel(parent)
        opensource_panel.SetBackgroundColour(wx.Colour(45, 45, 45) if is_dark else wx.Colour(255, 255, 255))
        opensource_sizer = wx.BoxSizer(wx.VERTICAL)

        os_title = wx.StaticText(opensource_panel, label="Open Source Information")
        os_title.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        os_title.SetForegroundColour(text_color)
        opensource_sizer.Add(os_title, 0, wx.ALL, 15)

        for text in ["This software is open source and available under the MIT License.",
                     "Contributions, bug reports, and feature requests are welcome on GitHub."]:
            info_text = wx.StaticText(opensource_panel, label=text)
            info_text.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            info_text.SetForegroundColour(text_color)
            info_text.Wrap(350)
            opensource_sizer.Add(info_text, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 15)

        opensource_panel.SetSizer(opensource_sizer)
        return opensource_panel

    def create_system_panel(self, parent, is_dark, text_color):
        system_panel = wx.Panel(parent)
        system_panel.SetBackgroundColour(wx.Colour(45, 45, 45) if is_dark else wx.Colour(255, 255, 255))
        system_sizer = wx.BoxSizer(wx.VERTICAL)

        sys_title = wx.StaticText(system_panel, label="System Information")
        sys_title.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sys_title.SetForegroundColour(text_color)
        system_sizer.Add(sys_title, 0, wx.ALL, 15)

        info_grid = wx.FlexGridSizer(rows=3, cols=2, vgap=10, hgap=15)
        info_grid.AddGrowableCol(1, 1)

        for label, value in [
            ("Operating System:", f"{platform.system()} {platform.release()}"),
            ("Python Version:", platform.python_version()),
            ("wxPython Version:", wx.version())
        ]:
            info_label = wx.StaticText(system_panel, label=label)
            info_label.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
            info_label.SetForegroundColour(text_color)
            info_value = wx.StaticText(system_panel, label=value)
            info_value.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
            info_value.SetForegroundColour(text_color)
            info_grid.Add(info_label, 0, wx.ALIGN_CENTER_VERTICAL)
            info_grid.Add(info_value, 0, wx.EXPAND)

        system_sizer.Add(info_grid, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 15)
        system_panel.SetSizer(system_sizer)
        return system_panel

    def _scale_bitmap(self, bitmap, width, height):
        image = bitmap.ConvertToImage()
        image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
        return wx.Bitmap(image)

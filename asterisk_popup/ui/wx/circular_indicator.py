"""
Circular Indicator for FreePBX Popup
A simple circular indicator that can be used to show status
"""

import wx
import logging

logger = logging.getLogger('FreePBXPopup.CircularIndicator')

class CircularIndicator(wx.Panel):
    """A simple circular indicator that can be used to show status"""

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.Size(14, 14),
                 style=wx.NO_BORDER, color=wx.Colour(255, 0, 0)):
        """Initialize the indicator"""
        super(CircularIndicator, self).__init__(parent, id, pos, size, style)

        self._color = color

        self.Bind(wx.EVT_PAINT, self.on_paint)

        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)

        logger.debug(f"CircularIndicator initialized with color: {color}")

    def set_color(self, color):
        """Set the indicator color"""
        logger.debug(f"CircularIndicator color changing from {self._color} to {color}")

        if not color.IsOk():
            logger.warning(f"Invalid color provided to set_color: {color}")
            color = wx.Colour(255, 0, 0)

        if self._color == color:
            logger.debug(f"Color unchanged: {color}")
            return

        self._color = color

        self.Show(True)

        self.Refresh()
        self.Update()

        logger.debug(f"CircularIndicator updated: visible={self.IsShown()}, color={self._color}")

    def get_color(self):
        """Get the indicator color"""
        return self._color

    def on_paint(self, event):
        """Paint the indicator"""
        try:
            dc = wx.BufferedPaintDC(self)
            gc = wx.GraphicsContext.Create(dc)

            if not gc:
                self._paint_with_dc(dc)
                return

            w, h = self.GetSize()

            parent_color = self.GetParent().GetBackgroundColour()
            gc.SetBrush(wx.Brush(parent_color))
            gc.DrawRectangle(0, 0, w, h)

            color = self._color
            if not color.IsOk():
                color = wx.Colour(255, 0, 0)
                logger.warning(f"Invalid color detected, using fallback: {color}")

            gc.SetBrush(wx.Brush(color))

            border_color = wx.Colour(
                max(0, color.Red() - 30),
                max(0, color.Green() - 30),
                max(0, color.Blue() - 30)
            )
            gc.SetPen(wx.Pen(border_color, 1))

            diameter = min(w, h) - 2
            x = (w - diameter) / 2
            y = (h - diameter) / 2
            gc.DrawEllipse(x, y, diameter, diameter)

            logger.debug(f"CircularIndicator painted with color: {self._color}")
        except Exception as e:
            logger.error(f"Error painting indicator: {e}")

    def _paint_with_dc(self, dc):
        """Paint the indicator using a basic DC (fallback)"""
        try:
            w, h = self.GetSize()

            parent_color = self.GetParent().GetBackgroundColour()
            dc.SetBackground(wx.Brush(parent_color))
            dc.Clear()

            color = self._color
            if not color.IsOk():
                color = wx.Colour(255, 0, 0)
                logger.warning(f"Invalid color detected in DC fallback, using fallback: {color}")

            dc.SetBrush(wx.Brush(color))

            border_color = wx.Colour(
                max(0, color.Red() - 30),
                max(0, color.Green() - 30),
                max(0, color.Blue() - 30)
            )
            dc.SetPen(wx.Pen(border_color, 1))

            diameter = min(w, h) - 2
            x = (w - diameter) // 2
            y = (h - diameter) // 2
            dc.DrawCircle(x + diameter//2, y + diameter//2, diameter//2)

            logger.debug(f"CircularIndicator painted with DC fallback, color: {self._color}")
        except Exception as e:
            logger.error(f"Error painting indicator with DC: {e}")

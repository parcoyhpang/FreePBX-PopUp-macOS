"""
wxPython App for FreePBX Popup - Application initialization module.
Handles wxPython application initialization and provides a shared app instance.
"""

import wx
import logging
import threading

logger = logging.getLogger('FreePBXPopup.WxApp')

# Global wxPython app instance
_wx_app = None
_wx_app_lock = threading.Lock()

def get_wx_app():
    """
    Get the wxPython app instance, creating it if necessary

    Returns:
        wx.App: The wxPython app instance
    """
    global _wx_app

    with _wx_app_lock:
        if _wx_app is None:
            logger.info("Creating wxPython app")

            # Hide dock icon on macOS
            import platform
            if platform.system() == 'Darwin':
                import objc
                from Foundation import NSBundle
                bundle = NSBundle.mainBundle()
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                info['LSUIElement'] = '1'  # Set to run as agent (no dock icon)

            _wx_app = wx.App(False)

        return _wx_app

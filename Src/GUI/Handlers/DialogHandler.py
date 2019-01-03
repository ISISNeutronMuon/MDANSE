import logging

import wx

from MDANSE import REGISTRY
from MDANSE.Framework.Handlers.IHandler import IHandler

class DialogHandler(IHandler, logging.Handler):
        
    ICONS = {"DEBUG"    : wx.ICON_INFORMATION,
             "CRITICAL" : wx.ICON_ERROR,
             "ERROR"    : wx.ICON_ERROR,
             "INFO"     : wx.ICON_INFORMATION,
             "WARNING"  : wx.ICON_WARNING,
             }
    
    def emit(self, record):

        icon = DialogHandler.ICONS[record.levelname]
            
        d = wx.MessageDialog(None, message=self.format(record), style=wx.OK|wx.STAY_ON_TOP|icon)

        d.ShowModal()

REGISTRY["dialog"] = DialogHandler                

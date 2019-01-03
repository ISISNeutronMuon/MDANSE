import logging

import wx

from MDANSE import REGISTRY
from MDANSE.Framework.Handlers.IHandler import IHandler
from MDANSE.Logging.Formatters import Formatter
  
class ConsoleHandler(IHandler, logging.Handler):
    """Sets up a GUI handler for the MDANSE logger.
    
    Emits the logging message to the MDANSE GUI console.

    @note: inherits from logging.Handler class that sets a generic handler.
    """
        
    COLORS = {'DEBUG'    : wx.GREEN,
              'INFO'     : wx.BLACK,
              'WARNING'  : wx.BLUE,
              'ERROR'    : wx.RED,
              'CRITICAL' : wx.RED,
              'FATAL'    : wx.RED}
    
    def __init__(self, window):
        '''
        The constructor.
        
        @param console: the parent widget for the textctrl.
        @type console: wx widget
        '''

        logging.Handler.__init__(self)
        
        self.setFormatter(Formatter())
         
        self._window = window

        # Creates a wx text attribute.        
        self.style = wx.TextAttr()

        # Set its font to a non proporiotnal font.
        self.style.SetFont(wx.Font(10, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.NORMAL))
        
            
    def emit(self, record):
        """
        Send the log message to a wx.TextCtrl widget.
        
        @param record: the log message.
        @type record: logging.LogRecord        
        """
        
        record.msg = record.msg.strip()
        if not record.msg:
            return
        
        self.style.SetTextColour(ConsoleHandler.COLORS.get(record.levelname,wx.BLACK))
                                    
        # Set the the created text attribute as the default style for the text ctrl.                            
        self._window.SetDefaultStyle(self.style)        
        
        # Append the log message to the text ctrl.
        self._window.AppendText(self.format(record))

        self._window.AppendText("\n")
        
    def write(self,message):
        
        record = logging.LogRecord("console",logging.INFO,None,None,message,None,None,None)
        
        self.emit(record)
        
REGISTRY["console"] = ConsoleHandler

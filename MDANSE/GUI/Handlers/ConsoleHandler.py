#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on Apr 14, 2015

:author: Eric C. Pellegrini
'''

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
        
        self.style.SetTextColour(ConsoleHandler.COLORS.get(record.levelname,wx.BLACK))
                                    
        # Set the the created text attribute as the default style for the text ctrl.                            
        self._window.SetDefaultStyle(self.style)        
        
        # Append the log message to the text ctrl.
        self._window.AppendText(self.format(record))

        self._window.AppendText("\n")

REGISTRY["console"] = ConsoleHandler
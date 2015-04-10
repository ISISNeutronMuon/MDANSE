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
Created on Apr 10, 2015

@author: pellegrini
'''

import collections
import ctypes
import logging
import logging.handlers
import os
import sys
import time
import traceback

try:
    import wx
except ImportError:
    HAS_WX = False
else:
    HAS_WX = True

from nMOLDYN.Core.Singleton import Singleton

# A copy of the except_hook function from sys module.
__sys_except_hook = sys.excepthook

class Formatter(logging.Formatter):
    '''
    Converts the log record to a string. 
    '''
    
    FORMATS = {'DEBUG'    : '%(asctime)s - %(levelname)-8s - %(message)s --- %(pathname)s %(funcName)s line %(lineno)s',
               'INFO'     : '%(asctime)s - %(levelname)-8s - %(message)s',
               'WARNING'  : '%(asctime)s - %(levelname)-8s - %(message)s',
               'ERROR'    : '%(asctime)s - %(levelname)-8s - %(message)s',
               'CRITICAL' : '%(asctime)s - %(levelname)-8s - %(message)s',
               'FATAL'    : '%(asctime)s - %(levelname)-8s - %(message)s'}

                                            
    def formatTime(self, record, datefmt=None):
        '''
        Return the creation time of the specified LogRecord as formatted text.

        This method should be called from format() by a formatter which
        wants to make use of a formatted time. This method can be overridden
        in formatters to provide for any specific requirement, but the
        basic behaviour is as follows: if datefmt (a string) is specified,
        it is used with time.strftime() to format the creation time of the
        record. Otherwise, the ISO8601 format is used. The resulting
        string is returned. This function uses a user-configurable function
        to convert the creation time to a tuple. By default, time.localtime()
        is used; to change this for a particular formatter instance, set the
        'converter' attribute to a function with the same signature as
        time.localtime() or time.gmtime(). To change it for all formatters,
        for example if you want all logging times to be shown in GMT,
        set the 'converter' attribute in the Formatter class.
        
        @param record: the log record.
        @type record: logging.LogRecord
        
        @param datefmt: the date format.
        @type datefmt: string.
        '''
                
        # The log time is converted to local time.
        ct = self.converter(record.created)
        
        # Case where datefmt was set, use it. 
        if datefmt:
            s = time.strftime(datefmt, ct)
            
        # Otherwise use a default format.
        else:
            s = time.strftime("%Y-%m-%d %H:%M:%S", ct)

        return s
    
                        
    def format(self, record):
        '''
        Format the logging record to a string that will further throw to the logger's handlers.

        The record's attribute dictionary is used as the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record is computed
        using LogRecord.getMessage(). If the formatting string uses the
        time (as determined by a call to usesTime(), formatTime() is
        called to format the event time. If there is exception information,
        its value are used to overwrite the pathname, lineno and funcName 
        attribute of the record being processed and appended to the message.
        
        @param record: the loggign record to be formatted.
        @type record: logging.LogRecord
        '''
        
        # The format is set according to the record level.        
        fmt = Formatter.FORMATS[record.levelname]
        
        # Get the record message.
        record.message = record.getMessage()
                
        if not record.message:
            s = record.message

        else: 
            record.asctime = self.formatTime(record, self.datefmt)                      
            # Creates the actual output string.  
            s = fmt % record.__dict__
            s = s.replace('\n', '\n' + ' '*33)
        
        return s

class LogFileHandler(logging.handlers.RotatingFileHandler):
    
    def __init__(self, filename, mode='a', maxBytes=1e7, backupCount=9, delay=True):
                
        logging.handlers.RotatingFileHandler.__init__(self,filename, mode=mode, maxBytes=maxBytes, backupCount=backupCount, delay=delay)
        
        self.setFormatter(Formatter())       
          
class ColorizingStreamHandler(logging.StreamHandler):
    """
    A stream handler which supports colorizing of console streams
    under Windows, Linux and Mac OS X.

    :param strm: The stream to colorize - typically ``sys.stdout``
                 or ``sys.stderr``.
    """
    
    # color names to indices
    color_map = {
        'black': 0,
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 5,
        'cyan': 6,
        'white': 7,
    }

    #levels to (background, foreground, bold/intense)
    if os.name == 'nt':
        level_map = {
            logging.DEBUG: (None, 'blue', True),
            logging.INFO: (None, 'white', False),
            logging.WARNING: (None, 'yellow', True),
            logging.ERROR: (None, 'red', True),
            logging.CRITICAL: ('red', 'white', True),
        }
    else:
        "Maps levels to colour/intensity settings."
        level_map = {
            logging.DEBUG: (None, 'blue', False),
            logging.INFO: (None, 'white', False),
            logging.WARNING: (None, 'yellow', False),
            logging.ERROR: (None, 'red', False),
            logging.CRITICAL: ('red', 'white', True),
        }

    csi = '\x1b['
    reset = '\x1b[0m'

    @property
    def is_tty(self):
        "Returns true if the handler's stream is a terminal."
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if unicode and isinstance(message, unicode):
                enc = getattr(stream, 'encoding', 'utf-8')
                message = message.encode(enc, 'replace')
            if not self.is_tty:
                stream.write(message)
            else:
                self.output_colorized(message)
            stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    if os.name != 'nt':
        def output_colorized(self, message):
            """
            Output a colorized message.

            On Linux and Mac OS X, this method just writes the
            already-colorized message to the stream, since on these
            platforms console streams accept ANSI escape sequences
            for colorization. On Windows, this handler implements a
            subset of ANSI escape sequence handling by parsing the
            message, extracting the sequences and making Win32 API
            calls to colorize the output.

            :param message: The message to colorize and output.
            """
            self.stream.write(message)
    else:
        import re
        ansi_esc = re.compile(r'\x1b\[((?:\d+)(?:;(?:\d+))*)m')

        nt_color_map = {
            0: 0x00,    # black
            1: 0x04,    # red
            2: 0x02,    # green
            3: 0x06,    # yellow
            4: 0x01,    # blue
            5: 0x05,    # magenta
            6: 0x03,    # cyan
            7: 0x07,    # white
        }

        def output_colorized(self, message):
            """
            Output a colorized message.

            On Linux and Mac OS X, this method just writes the
            already-colorized message to the stream, since on these
            platforms console streams accept ANSI escape sequences
            for colorization. On Windows, this handler implements a
            subset of ANSI escape sequence handling by parsing the
            message, extracting the sequences and making Win32 API
            calls to colorize the output.

            :param message: The message to colorize and output.
            """
            parts = self.ansi_esc.split(message)
            write = self.stream.write
            h = None
            fd = getattr(self.stream, 'fileno', None)
            if fd is not None:
                fd = fd()
                if fd in (1, 2): # stdout or stderr
                    h = ctypes.windll.kernel32.GetStdHandle(-10 - fd)
            while parts:
                text = parts.pop(0)
                if text:
                    write(text)
                if parts:
                    params = parts.pop(0)
                    if h is not None:
                        params = [int(p) for p in params.split(';')]
                        color = 0
                        for p in params:
                            if 40 <= p <= 47:
                                color |= self.nt_color_map[p - 40] << 4
                            elif 30 <= p <= 37:
                                color |= self.nt_color_map[p - 30]
                            elif p == 1:
                                color |= 0x08 # foreground intensity on
                            elif p == 0: # reset to default color
                                color = 0x07
                            else:
                                pass # error condition ignored
                        ctypes.windll.kernel32.SetConsoleTextAttribute(h, color)

    def colorize(self, message, record):
        """
        Colorize a message for a logging event.

        This implementation uses the ``level_map`` class attribute to
        map the LogRecord's level to a colour/intensity setting, which is
        then applied to the whole message.

        :param message: The message to colorize.
        :param record: The ``LogRecord`` for the message.
        """
        if record.levelno in self.level_map:
            bg, fg, bold = self.level_map[record.levelno]
            params = []
            if bg in self.color_map:
                params.append(str(self.color_map[bg] + 40))
            if fg in self.color_map:
                params.append(str(self.color_map[fg] + 30))
            if bold:
                params.append('1')
            if params:
                message = ''.join((self.csi, ';'.join(params),
                                   'm', message, self.reset))
        return message

    def format(self, record):
        """
        Formats a record for output.

        This implementation colorizes the message line, but leaves
        any traceback unolorized.
        """
        message = logging.StreamHandler.format(self, record)
        if self.is_tty:
            parts = message.split('\n', 1)
            message = '\n'.join([self.colorize(p, record) for p in parts])
        return message
if HAS_WX:
  
    class ConsoleHandler(logging.Handler):
        """Sets up a GUI handler for the nMOLDYN logger.
        
        Emits the logging message to the nMOLDYN GUI console.
    
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

class DialogHandler(logging.Handler):
    
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
                
_sys_excepthook = sys.excepthook

class CaselessDict(dict):

    def __getitem__(self,item):

        if isinstance(item,basestring):
            return dict.__getitem__(self,item.lower())
        else:
            return dict.__getitem__(self,item)

    def __setitem__(self,item,value):

        if isinstance(item,basestring):
            dict.__setitem__(self,item.lower(),value)
        else:
            dict.__setitem__(self,item,value)

    def get(self,item,default):

        try:
            return self.__getitem__(item)
        except KeyError:
            return default
                    
class Logger(object):

    levels = CaselessDict([["debug",logging.DEBUG],
                           ["info",logging.INFO],
                           ["warning",logging.WARNING],
                           ["error",logging.ERROR],
                           ["critical",logging.CRITICAL]])


    def __call__(self,message,level="info",loggers=None):

        lvl = Logger.levels.get(level,None)

        if lvl is None:
            return

        if loggers is None:
            loggers=logging.Logger.manager.loggerDict.keys()
        else:
            loggers = [n for n in loggers if logging.Logger.manager.loggerDict.has_key(n)]

        for n in loggers:
            logging.getLogger(n).log(lvl,message)
        
    def start(self):
        
        from nMOLDYN import _nmoldyn_excepthook
        
        sys.excepthook = _nmoldyn_excepthook

        for logger in logging.Logger.manager.loggerDict.values():
            logger.disabled=False

    def stop(self):

        sys.excepthook = _sys_excepthook

        for logger in logging.Logger.manager.loggerDict.values():
            logger.disabled=True

    def set_level(self,level,loggers=None):
        
        lvl = Logger.levels.get(level,None)
        if lvl is None:
            return

        if loggers is None:
            loggers = logging.Logger.manager.loggerDict.keys()
        else:
            loggers = [n for n in loggers if logging.Logger.manager.loggerDict.has_key(n)]

        for loggerName in loggers:
            logging.getLogger(loggerName).setLevel(lvl)

    def add_logger(self,name,handler,level="error"):

        if logging.Logger.manager.loggerDict.has_key(name):
            return

        logging.getLogger(name).addHandler(handler)
                
        self.set_level(level,loggers=[name])

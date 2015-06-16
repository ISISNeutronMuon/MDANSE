'''
MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
------------------------------------------------------------------------------------------
Copyright (C)
2015- Eric C. Pellegrini Institut Laue-Langevin
BP 156
6, rue Jules Horowitz
38042 Grenoble Cedex 9
France
pellegrini[at]ill.fr

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 
Created on Mar 23, 2015

:author: Eric C. Pellegrini
'''

import logging

from MDANSE.Core.Singleton import Singleton
                                        
class Logger(object):

    __metaclass__ = Singleton

    levels = {"debug"    : logging.DEBUG,
              "info"     : logging.INFO,
              "warning"  : logging.WARNING,
              "error"    : logging.ERROR,
              "fatal"    : logging.CRITICAL,
              "critical" : logging.FATAL
              }

    def __call__(self,message,level="info",loggers=None):

        lvl = Logger.levels.get(level,None)

        # If the logging level is unkwnown, skip that log
        if lvl is None:
            return
    
        if loggers is None:
            loggers=logging.Logger.manager.loggerDict.keys()
        else:
            loggers = [n for n in loggers if logging.Logger.manager.loggerDict.has_key(n)]

        for n in loggers:
            logging.getLogger(n).log(lvl,message)

    def start(self, loggers=None):
        
        if loggers is None:
            loggers=logging.Logger.manager.loggerDict.keys()
        else:
            loggers = [n for n in loggers if logging.Logger.manager.loggerDict.has_key(n)]

        for n in loggers:
            logging.getLogger(n).disabled=False

    def stop(self, loggers=None):

        if loggers is None:
            loggers=logging.Logger.manager.loggerDict.keys()
        else:
            loggers = [n for n in loggers if logging.Logger.manager.loggerDict.has_key(n)]

        for n in loggers:
            logging.getLogger(n).disabled=True

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

    def add_handler(self,name,handler,level="error",start=True):

        if logging.Logger.manager.loggerDict.has_key(name):
            return
                        
        logging.getLogger(name).addHandler(handler)
                
        logging.getLogger(name).disabled = not start                
        
        self.set_level(level,loggers=[name])
        
LOGGER = Logger()
# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Logging/Logger.py
# @brief     Implements module/class/test Logger
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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

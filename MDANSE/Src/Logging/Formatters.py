# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/Logging/Formatters.py
# @brief     Implements module/class/test Formatters
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import logging

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
        
        :param record: the log record.
        :type record: logging.LogRecord
        
        :param datefmt: the format that will be used to produce the stringified date.
        :type datefmt: str
        '''

        import time
                
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


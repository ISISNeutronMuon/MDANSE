"""
This class implements the MDANSE error handler.

It inherits from the Exception class. It can be used to filter the exceptions
raised within the MDANSE framework
"""

class Error(Exception):
    
    def __init__(self, msg=None):
            
            self._msg = msg
            
    def __str__(self):
                
        return repr(self._msg)
    

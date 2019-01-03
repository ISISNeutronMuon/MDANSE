class Error(Exception):
    '''
    Base class for handling exception occurring in MDANSE.
    
    Any exception defined in MDANSE should derive from it in order to be properly handled
    in the GUI application.
    '''
    
    def __init__(self, msg=None):
            
            self._msg = msg
            
    def __str__(self):
                
        return repr(self._msg)
    

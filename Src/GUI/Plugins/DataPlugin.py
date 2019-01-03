import wx

from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Plugins.IPlugin import IPlugin 

def get_data_plugin(window):
                               
    if isinstance(window,DataPlugin):
        return window
     
    else:
        
        try:                
            return get_data_plugin(window.Parent)
        except AttributeError:
            return None
                    
class DataPlugin(IPlugin):
            
    ancestor = []
    
    def __init__(self, parent, datakey, **kwargs):
        
        IPlugin.__init__(self, parent, wx.ID_ANY, **kwargs)

        self._datakey = datakey
        
        self._dataProxy = DATA_CONTROLLER[self._datakey]
                                                                 
    def build_panel(self):
        pass

    def plug(self, standalone=False):
        pass

    @property
    def datakey(self):
        return self._datakey

    @datakey.setter
    def datakey(self, key):
        self._datakey = key

    @property
    def dataproxy(self):
        
        return self._dataProxy
    
    @property
    def dataplugin(self):
        return self
        

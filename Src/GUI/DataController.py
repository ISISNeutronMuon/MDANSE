import collections
import weakref

from MDANSE.Core.Singleton import Singleton

from MDANSE.GUI import PUBLISHER

class DataController(collections.OrderedDict):
    
    __metaclass__ = Singleton
    
    def __delitem__(self, item):
        
        if not self.has_key(item):
            return
        
        if self.has_proxy(item):
            return
        else:
            collections.OrderedDict.__delitem__(self,item)
            PUBLISHER.sendMessage("msg_delete_input_data", message=item)
    
    def __getitem__(self, key):
        
        data = collections.OrderedDict.__getitem__(self, key)
        
        return weakref.proxy(data)        

    def __setitem__(self, item, value):
        
        if self.has_key(item):
            return
        
        collections.OrderedDict.__setitem__(self, item,value)
        
        PUBLISHER.sendMessage("msg_load_input_data", message=value)
                    
    def has_proxy(self, item):
        '''
        Return the number of weak references related to a data stored in the data controller
        '''

        return (weakref.getweakrefcount(collections.OrderedDict.__getitem__(self,item))!=0)

DATA_CONTROLLER = DataController()

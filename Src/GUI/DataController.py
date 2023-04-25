# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/DataController.py
# @brief     Implements module/class/test DataController
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

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

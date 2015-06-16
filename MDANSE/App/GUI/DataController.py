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

:author: Eric C. Pellegrini
'''

import collections
import weakref

from MDANSE.Core.Singleton import Singleton
from MDANSE.Externals.pubsub import pub as Publisher

class DataController(collections.OrderedDict):
    
    __metaclass__ = Singleton
    
    def __delitem__(self, item):
        
        if not self.has_key(item):
            return
        
        if self.has_proxy(item):
            return
        else:
            collections.OrderedDict.__delitem__(self,item)
            Publisher.sendMessage("delete_input_data", message = item)
    
    def __getitem__(self, key):
        
        data = collections.OrderedDict.__getitem__(self, key)
        
        return weakref.proxy(data)        

    def __setitem__(self, item, value):
        
        if self.has_key(item):
            return
        
        collections.OrderedDict.__setitem__(self, item,value)
        
        Publisher.sendMessage("load_input_data", message = value)
                    
    def has_proxy(self, item):
        '''
        Return the number of weak references related to a data stored in the data controller
        '''

        return (weakref.getweakrefcount(collections.OrderedDict.__getitem__(self,item))!=0)

DATA_CONTROLLER = DataController()
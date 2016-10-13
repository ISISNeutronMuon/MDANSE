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
Created on Mar 30, 2015

:author: Gael Goret, Eric C. Pellegrini
'''

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
    
    type = None
        
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
        
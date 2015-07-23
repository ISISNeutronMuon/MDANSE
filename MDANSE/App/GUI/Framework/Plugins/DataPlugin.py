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
import wx.aui as wxaui

from MDANSE import REGISTRY
from MDANSE.Externals.pubsub import pub

from MDANSE.App.GUI import DATA_CONTROLLER
from MDANSE.App.GUI.Framework.Plugins.IPlugin import IPlugin, plugin_parent 

def get_data_plugin(window):
                               
    if isinstance(window,DataPlugin):
        return window
     
    else:
        
        try:                
            return get_data_plugin(window.Parent)
        except AttributeError:
            return None
                    
class DataPlugin(IPlugin):
    
    type = 'data'
        
    ancestor = None
    
    def __init__(self, parent, datakey, **kwargs):
        
        IPlugin.__init__(self, parent, wx.ID_ANY, **kwargs)

        self._datakey = datakey
        
        self._dataProxy = DATA_CONTROLLER[self._datakey]
                                                
        self._mgr.Bind(wx.EVT_CHILD_FOCUS, self.on_changing_pane)
        
        self._currentWindow = self
         
    def build_panel(self):
        pass

    def plug(self, standalone=False):
        pass

    @property
    def currentWindow(self):
        return self._currentWindow

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
    
    def drop(self, pluginName):
                                        
        # If no plugin match the name of the dropped plugin, do nothing.
        plugin = REGISTRY["plugin"].get(pluginName,None)        
        if plugin is None:
            return
        
        if not issubclass(self.__class__,REGISTRY['plugin'][plugin.ancestor]):
            return
                                                    
        plugin = plugin(self)

        self._mgr.AddPane(plugin, wxaui.AuiPaneInfo().Caption(getattr(plugin, "label", pluginName)))

        self._mgr.Update()
        
        plugin.plug()
        
        plugin.SetFocus()
        
        self._currentWindow = plugin
    
    def on_changing_pane(self, event):
        
        window = plugin_parent(event.GetWindow())
                
        if window is None:
            return
        
        self._currentWindow = window
                                    
        pub.sendMessage(('msg_set_plugins_tree'), message=window)

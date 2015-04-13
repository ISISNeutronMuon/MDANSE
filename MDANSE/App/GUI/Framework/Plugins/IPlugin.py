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

@author: Gael Goret, Eric C. Pellegrini
'''

import abc
import cPickle

import wx
import wx.aui as aui

from MDANSE import REGISTRY

def plugin_parent(window):
                          
    if window == window.TopLevelParent:
        return None
     
    if isinstance(window,IPlugin):
        return window
     
    else:
        return plugin_parent(window.Parent)

class PluginDropTarget(wx.DropTarget):

    def __init__(self, targetPanel):

        wx.DropTarget.__init__(self)
        self._targetPanel = targetPanel
        
        self._data = wx.CustomDataObject("Plugin")
        self.SetDataObject(self._data)
        
    @property
    def target_panel(self):
        return self._targetPanel

    def OnDrop(self, x, y):
        return True

    def OnDragOver(self, x, y, d):
        return wx.DragCopy

    def OnData(self, x, y, d):

        if self.GetData():
            pluginName = cPickle.loads(self._data.GetData())
            self._targetPanel.drop(pluginName)

        return d

class IPlugin(wx.Panel):
    
    __metaclass__ = REGISTRY
    
    type = "plugin"
        
    ancestor = None
    
    def __init__(self, parent, *args, **kwargs):
        
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self._parent = parent
        
        self.SetDropTarget(PluginDropTarget(self))
        
        self.build_dialog()
        
        self._mgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.on_close_pane)
                                                        
    @abc.abstractmethod
    def build_panel(self):
        pass
    
    @abc.abstractmethod
    def plug(self, standalone=False):
        pass
    
    @property
    def mgr(self):
        return self._mgr
    
    @property
    def parent(self):
        return self._parent
    
    def close_children(self):

        childrenPlugins = [p.window for p in self._mgr.GetAllPanes()]
        
        for plugin in childrenPlugins:
            try:
                plugin.close_children()
            except AttributeError:
                continue
            
        self.close()
        
    def close(self):
        pass
        
    def on_close_pane(self, event):
        
        plugin = event.GetPane().window
        
        try:
            plugin.close_children()
        except AttributeError:
            plugin.Close()
                                
    def build_dialog(self):

        self.Freeze()

        self._mgr = aui.AuiManager(self)

        self.build_panel()  
         
        self._mgr.Update()
        
        self.Thaw()
        
    def drop(self, pluginName):
                                        
        # If no plugin match the name of the dropped plugin, do nothing.
        plugin = REGISTRY["plugin"].get(pluginName,None)        
        if plugin is None:
            return
        
        if not issubclass(self.__class__,REGISTRY['plugin'][plugin.ancestor]):
            self.parent.drop(pluginName)
            return
                                               
        plugin = plugin(self)

        self._mgr.AddPane(plugin, aui.AuiPaneInfo().Caption(getattr(plugin, "label", pluginName)))

        self._mgr.Update()
        
        plugin.plug()
        
        plugin.SetFocus()
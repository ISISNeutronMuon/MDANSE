# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/IPlugin.py
# @brief     Implements module/class/test IPlugin
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import abc
import cPickle

import wx
import wx.aui as aui

from MDANSE import REGISTRY

from MDANSE.GUI import PUBLISHER

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
        
    _registry = "plugin"
        
    ancestor = []
    
    def __init__(self, parent, *args, **kwargs):
        
        wx.Panel.__init__(self, parent, *args, **kwargs)
        
        self._parent = parent

        self._currentWindow = self
        
        self.SetDropTarget(PluginDropTarget(self))
        
        self.build_dialog()
        
        self._mgr.Bind(wx.EVT_CHILD_FOCUS, self.on_changing_pane)
                
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
    
    def is_parent(self,window):
                        
        if window == self:
            return True

        if window is None:
            return False
    
        return self.is_parent(window.Parent)    

    @property
    def currentWindow(self):
        
        return self._currentWindow
    
    def close(self):
        
        pass
                
    def on_close_pane(self, event):

        d = wx.MessageDialog(None, 'Closing this plugin will also close all the other ones you plugged in in so far. Do you really want to close ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_NO:
            event.Veto()
            return
                
        window = event.GetPane().window
                
        # Call the 'close' method the plugin to be closed
        window.close()
        
        self._mgr.DetachPane(window)
        window.Destroy()
        self._mgr.Update()
            
        self.SetFocus()
        
        self._currentWindow = self
        
        PUBLISHER.sendMessage('msg_set_plugins_tree', message=self)
                                            
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
                                                               
        plugin = plugin(self)

        self._mgr.AddPane(plugin, aui.AuiPaneInfo().Caption(getattr(plugin, "label", pluginName)))

        self._mgr.Update()
        
        plugin.plug()
        
        plugin.SetFocus()
        
    def on_changing_pane(self, event):
        
        window = plugin_parent(event.GetWindow())
                
        if window is None:
            return
        
        self._currentWindow = window

        PUBLISHER.sendMessage('msg_set_plugins_tree', message=window)
                
        

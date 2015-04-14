import abc
import cPickle

import wx
import wx.aui as aui

from nMOLDYN import DATA_CONTROLLER, REGISTRY
from nMOLDYN.Externals.pubsub import pub as Publisher
from nMOLDYN.Framework.ExtendableObject import ExtendableObject

def plugin_parent(window):
                          
    if window == window.TopLevelParent:
        return None
     
    if isinstance(window,Plugin):
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

class Plugin(wx.Panel):
    
    __metaclass__ = ExtendableObject
        
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


    def has_parent(self, window):
        
        if window == self.TopLevelParent:
            return False
        
        if self.Parent != window:
            self.Parent.has_parent(window)
        
        else:
            return True
                    
class DataPlugin(Plugin):
    
    type = 'data'
        
    ancestor = None
    
    def __init__(self, parent, datakey):
        
        Plugin.__init__(self, parent, wx.ID_ANY)

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
    
    def drop(self, pluginName):
                                        
        # If no plugin match the name of the dropped plugin, do nothing.
        plugin = REGISTRY["plugin"].get(pluginName,None)        
        if plugin is None:
            return
        
        if not issubclass(self.__class__,REGISTRY['plugin'][plugin.ancestor]):
            return
                                                    
        plugin = plugin(self)

        self._mgr.AddPane(plugin, aui.AuiPaneInfo().Caption(getattr(plugin, "label", pluginName)))

        self._mgr.Update()
        
        plugin.plug()
        
        plugin.SetFocus()

    def has_parent(self, window):
        return False
    
    def on_changing_pane(self, event):
                        
        window = plugin_parent(event.GetWindow())
                                        
        if window is None:
            return
        
        self._currentWindow = window
                                    
        Publisher.sendMessage(('set_plugins_tree'), message= window)
             
class ComponentPlugin(Plugin):
    
    type = None

    @property
    def datakey(self):
        return self.parent.datakey

    @property
    def dataproxy(self):
        return self.parent.dataproxy


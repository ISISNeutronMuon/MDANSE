# Standards imports.
import collections

# The wx imports.
import wx
import wx.aui as aui


# The numpy imports.
import numpy as np

# The nmoldyn imports.
from nMOLDYN import REGISTRY, USER_DEFINITIONS
from nMOLDYN.Core.Error import Error
from nMOLDYN.Framework.Plugins.Plugin import ComponentPlugin

class RegistryViewerPluginError(Error):
    pass

class RegistryViewerPlugin(ComponentPlugin):

    type = "registry_viewer"
    
    label = "Registry Viewer"
    
    ancestor = "empty_data"
    
    def __init__(self, parent, *args, **kwargs):

        self.currentFilename = None        
        self._udTree = {}

        ComponentPlugin.__init__(self, parent, size = parent.GetSize(), *args, **kwargs)
        
        self.build_plugins_tree()
        

    def build_panel(self):
        
        self._treePanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
        
        treeSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._tree = wx.TreeCtrl(self._treePanel, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)
        
        treeSizer.Add( self._tree, 1, wx.ALL|wx.EXPAND, 5)
        
        self._treePanel.SetSizer(treeSizer)  
        
        
        self._infoPanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
        
        infoSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self._info = wx.TextCtrl(self._infoPanel, wx.ID_ANY, style=wx.TE_MULTILINE|wx.TE_READONLY)

        infoSizer.Add(self._info, 1, wx.ALL|wx.EXPAND, 5)
        
        self._infoPanel.SetSizer(infoSizer)   
        
        
        self._mgr.AddPane(self._infoPanel, aui.AuiPaneInfo().Center().Dock().CaptionVisible(False).CloseButton(False))
        self._mgr.AddPane(self._treePanel, aui.AuiPaneInfo().Left().Dock().CaptionVisible(False).CloseButton(False))
        self._mgr.Update()
        
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_double_click_data)
    
         
    def build_plugins_tree(self):
 
        self._root = self._tree.AddRoot("root")
        self.set_plugins_tree(self._root, REGISTRY._registry)          
            
            
    def set_plugins_tree(self, node, data):
        
        for k, v in data.items():
            
            if isinstance(v, dict):
                subnode = self._tree.AppendItem(node, str(k), data=None)
                self.set_plugins_tree(subnode, v)  
            
            else:
                dataItem = wx.TreeItemData(v)
                self._tree.AppendItem(node, str(k), data=dataItem)
                
    def on_double_click_data(self, event):
        
        ItemData = self._tree.GetItemData(event.GetItem())
        
        if ItemData is None:
            return
        
        if ItemData.GetData() is None:
            return
        
        containerStr = ''
        containerStr += str(ItemData.GetData()) + '\n'
        containerStr += str(ItemData.GetData().__doc__)
       
        self._info.SetValue(containerStr)       
    
    def close(self):
        pass
    
    def plug(self):
        self.parent.mgr.GetPane(self).Float().CloseButton(True).BestSize((800, 300))
        self.parent.mgr.Update()


class RegistryViewerFrame(wx.Frame):
    
    def __init__(self, parent, title="Registry Viewer Plugin"):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, size = (800,400), title = title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)

        self.build_dialog()

        
    def build_dialog(self):
        
        
        mainPanel = wx.Panel(self, wx.ID_ANY, size = self.GetSize())
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        
        self._registryViewerPlugin = RegistryViewerPlugin(mainPanel, wx.ID_ANY)
        
        mainSizer.Add(self._registryViewerPlugin, 1, wx.ALL|wx.EXPAND)

        mainPanel.SetSizer(mainSizer)        
        mainSizer.Fit(mainPanel)
        mainPanel.Layout()

        


    def on_quit(self, event):
        
        d = wx.MessageDialog(None,
                             'Do you really want to quit ?',
                             'Question',
                             wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()   

if __name__ == "__main__":
    app = wx.App(False)
    f = RegistryViewerFrame(None)
    f.Show()
    app.MainLoop()    
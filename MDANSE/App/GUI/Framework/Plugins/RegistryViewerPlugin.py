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
Created on Apr 14, 2015

:author: Gael Goret, Eric C. Pellegrini
'''

import wx
import wx.aui as wxaui

from MDANSE import REGISTRY
from MDANSE.Core.Error import Error

from MDANSE.App.GUI.Framework.Plugins.ComponentPlugin import ComponentPlugin

class RegistryViewerError(Error):
    pass

class RegistryViewerPlugin(ComponentPlugin):

    type = "registry_viewer"
    
    label = "Registry Viewer"
    
    ancestor = None
    
    def __init__(self, parent, *args, **kwargs):

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
        
        self._mgr.AddPane(self._infoPanel, wxaui.AuiPaneInfo().Center().Dock().CaptionVisible(False).CloseButton(False))
        self._mgr.AddPane(self._treePanel, wxaui.AuiPaneInfo().Left().Dock().CaptionVisible(False).CloseButton(False))
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

        self.Bind(wx.EVT_CLOSE, self.on_quit)

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
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

@author: Gael Goret
'''

import wx
import wx.aui as wxaui

from MDANSE.Core.Error import Error
from MDANSE.Framework.UserDefinitions.IUserDefinition import IUserDefinition
from MDANSE.Framework.UserDefinitionsStore import UD_STORE

from MDANSE.App.GUI.Framework.Plugins.ComponentPlugin import ComponentPlugin

class UserDefinitionViewerPluginError(Error):
    pass

class UserDefinitionViewerPlugin(ComponentPlugin):

    type = "user_definition_viewer"
    
    label = "User Definition Viewer"
    
    ancestor = None
    
    def __init__(self, parent, *args, **kwargs):

        self._udTree = {}

        ComponentPlugin.__init__(self, parent, size = parent.GetSize(), *args, **kwargs)
        
        self.build_plugins_tree()
     
    def build_panel(self):
                
        self._treePanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
        
        treeSizer = wx.BoxSizer(wx.VERTICAL)
        
        self._tree = wx.TreeCtrl(self._treePanel, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_EDIT_LABELS)        
        
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
        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_show_info )
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.on_delete_from_key, self._tree)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_rename, self._tree)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.on_try_rename, self._tree)
    
    def build_plugins_tree(self):
        
        for k,v in UD_STORE.iteritems():
            self._udTree.setdefault(v.target,{}).setdefault(v.type,{})[k] = v
        
        self._root = self._tree.AddRoot("root")
        self.set_plugins_tree(self._root, self._udTree)     
        
            
    def set_plugins_tree(self, node, data):
        
        for k, v in data.items():

            dataItem = wx.TreeItemData(v)
            subnode = self._tree.AppendItem(node, str(k), data=dataItem)
            
            if isinstance(v, IUserDefinition):
                self.set_plugins_tree(subnode, v) 
                self._tree.SetItemTextColour(subnode, 'red') 
            
            elif isinstance(v, dict):
                self.set_plugins_tree(subnode, v)
                self._tree.SetItemTextColour(subnode, 'blue')  
            
            else:
                self._tree.SetItemTextColour(subnode, 'green')
               
    def on_show_info(self, event):
        
        ItemData = self._tree.GetItemData(event.GetItem())
        
        if ItemData is None:
            return
        
        containerStr = str(ItemData.GetData())
       
        self._info.SetValue(containerStr)       
    
    def on_delete_from_key(self, event):

        keycode = event.GetKeyCode()
        
        if keycode == wx.WXK_DELETE:
            
            item = self._tree.GetSelection()
            itemData = self._tree.GetItemData(item)
            itemText = str(self._tree.GetItemText(item))
            
            if itemData is None:
                return
            
            data  = itemData.GetData()
            if isinstance(data, IUserDefinition):
                d = wx.MessageDialog(None, 'Do you really want to delete this definition ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
                if d.ShowModal() == wx.ID_YES:
                    del  UD_STORE[itemText]
                    UD_STORE.save()
                    self._tree.DeleteAllItems()
                    self._udTree.clear()
                    self.build_plugins_tree()
                    self._info.Clear()
   
    def on_try_rename(self, event):
        item = self._tree.GetSelection()
        itemData = self._tree.GetItemData(item)
        if itemData is None:
            event.Veto()
            return
        
        data  = itemData.GetData()
        if not isinstance(data, IUserDefinition):
            event.Veto()
         
    def on_rename(self, event):
        newtext = self._tree.GetEditControl().GetValue()
        item = self._tree.GetSelection()
        oldtext = str(self._tree.GetItemText(item))
        itemData = self._tree.GetItemData(item)
               
        if itemData is None:
            return
        
        data  = itemData.GetData()
        if isinstance(data, IUserDefinition):
            UD_STORE[newtext] = UD_STORE.pop(oldtext)
            UD_STORE.save()
            self.build_plugins_tree()
    
    def close(self):
        pass
    
    def plug(self):
        self.parent.mgr.GetPane(self).Float().CloseButton(True).BestSize((800, 300))
        self.parent.mgr.Update()


class UserDefinitionViewerFrame(wx.Frame):
    
    def __init__(self, parent, title="User Definition Viewer"):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, size = (800,400), title = title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)

        self.build_dialog()

    def build_dialog(self):
        
        
        mainPanel = wx.Panel(self, wx.ID_ANY, size = self.GetSize())
        
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        
        self._userDefinitionViewerPlugin = UserDefinitionViewerPlugin(mainPanel, wx.ID_ANY)
        
        mainSizer.Add(self._userDefinitionViewerPlugin, 1, wx.ALL|wx.EXPAND)

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
    f = UserDefinitionViewerFrame(None)
    f.Show()
    app.MainLoop()    
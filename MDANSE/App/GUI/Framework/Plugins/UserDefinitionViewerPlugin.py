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

:author: Gael Goret and Eric C. Pellegrini
'''

import wx
import wx.aui as wxaui

from MDANSE.Core.Error import Error
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
                
        self._root = self._tree.AddRoot("root")
        self.set_plugins_tree(self._root, UD_STORE)     
        
    def set_plugins_tree(self, node, data):
        
        for k, v in data.items():

            dataItem = wx.TreeItemData(v)
            subnode = self._tree.AppendItem(node, str(k), data=dataItem)

            self._tree.SetItemTextColour(subnode, 'blue')  
            
            if isinstance(v, dict):
                self.set_plugins_tree(subnode, v)
            
    def on_show_info(self, event):
        
        ItemData = self._tree.GetItemData(event.GetItem())
        
        if ItemData is None:
            return
        
        containerStr = str(ItemData.GetData())
       
        self._info.SetValue(containerStr)       
    
    def on_delete_from_key(self, event):

        keycode = event.GetKeyCode()
        
        if keycode == wx.WXK_DELETE:
            
            currentItem = self._tree.GetSelection()

            level = self.get_item_level(currentItem)
            
            if level > 3:
                return
                                                                        
            d = wx.MessageDialog(None, 'Do you really want to delete this definition ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
            if d.ShowModal() == wx.ID_YES:

                currentItemName = str(self._tree.GetItemText(currentItem))

                if level == 1:
                    UD_STORE.remove_target(currentItemName)                
                elif level == 2:
                    targetItem = self._tree.GetParent(currentItem)
                    targetItemName = str(self._tree.GetItemText(targetItem))
                    UD_STORE.remove_section(targetItemName,currentItemName)
                elif level == 3:
                    sectionItem = self._tree.GetParent(currentItem)
                    sectionItemName = str(self._tree.GetItemText(sectionItem))
                    targetItem = self._tree.GetParent(sectionItem)
                    targetItemName = str(self._tree.GetItemText(targetItem))
                    UD_STORE.remove_definition(targetItemName,sectionItemName,currentItemName)
                else:
                    return
                
                UD_STORE.save()
                self._tree.DeleteAllItems()
                self._udTree.clear()
                self.build_plugins_tree()
                self._info.Clear()
   
    def on_try_rename(self, event):

        currentItem = self._tree.GetSelection()
        level = self.get_item_level(currentItem)

        if level != 3:
            event.Veto()
            return
        
    def on_rename(self, event):
        
        currentItem = self._tree.GetSelection()
        
        currentItemName = str(self._tree.GetItemText(currentItem))   
        newItemName = self._tree.GetEditControl().GetValue()
        
        if currentItemName == newItemName:
            return
        
        sectionItem = self._tree.GetItemParent(currentItem)
        sectionItemName = str(self._tree.GetItemText(sectionItem))
        targetItem = self._tree.GetItemParent(sectionItem)
        targetItemName = str(self._tree.GetItemText(targetItem))

        currentItemData = self._tree.GetItemData(currentItem)
                
        UD_STORE.set_definition(targetItemName,sectionItemName,newItemName,currentItemData.GetData())
        UD_STORE.remove_definition(targetItemName,sectionItemName,currentItemName)
        UD_STORE.save()
            
    def close(self):
        pass
    
    def plug(self):
        self.parent.mgr.GetPane(self).Float().CloseButton(True).BestSize((800, 300))
        self.parent.mgr.Update()
        
    def get_item_level(self,item):
        
        parent = self._tree.GetItemParent(item)
        
        if parent == self._tree.GetRootItem():
            return 1
        else: 
            return 1 + self.get_item_level(parent)


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
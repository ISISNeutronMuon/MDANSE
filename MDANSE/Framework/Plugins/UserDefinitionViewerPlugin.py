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

from MDANSE import LOGGER
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.UserDefinitionsStore import UD_STORE

class UserDefinitionViewerFrame(wx.Frame):
    
    def __init__(self, parent, title="User Definition Viewer", ud=None):
        
        wx.Frame.__init__(self, parent, wx.ID_ANY, size = (800,400), title = title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)

        self._udTree = {}
        
        mainPanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
        
        self._tree = wx.TreeCtrl(mainPanel, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_EDIT_LABELS)        

        self._root = self._tree.AddRoot("root")

        self.set_plugins_tree(self._root, UD_STORE)     

        self._info = wx.TextCtrl(mainPanel, wx.ID_ANY, style=wx.TE_MULTILINE|wx.TE_READONLY)
        
        self._save  = wx.Button(mainPanel, wx.ID_ANY, label="Save user definitions")

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        infoSizer = wx.BoxSizer(wx.HORIZONTAL)
        infoSizer.Add(self._tree, 1, wx.ALL|wx.EXPAND, 5)
        infoSizer.Add(self._info, 2, wx.ALL|wx.EXPAND, 5)
                        
        mainSizer.Add(infoSizer,1,wx.ALL|wx.EXPAND,5)                      
        mainSizer.Add(self._save,0,wx.ALL|wx.EXPAND,5)                      
        mainPanel.SetSizer(mainSizer)
                
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.on_show_info )
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.on_delete_from_key, self._tree)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_rename, self._tree)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.on_try_rename, self._tree)

        self.Bind(wx.EVT_BUTTON, self.on_save_ud, self._save)

        self.Bind(wx.EVT_CLOSE, self.on_quit)
        
        if ud is not None:
            self.expand_ud(ud)

    def get_item_level(self,item):
        
        parent = self._tree.GetItemParent(item)
        
        if parent == self._tree.GetRootItem():
            return 1
        else: 
            return 1 + self.get_item_level(parent)

    def set_plugins_tree(self, node, data):
        
        for k, v in data.items():
            
            dataItem = wx.TreeItemData(v)
            subnode = self._tree.AppendItem(node, str(k), data=dataItem)

            self._tree.SetItemTextColour(subnode, 'blue')  
            
            if isinstance(v, dict):
                self.set_plugins_tree(subnode, v)
                
    def find_ud(self,baseitem,itemNames):

        if not itemNames:
            return baseitem
        
        name = itemNames.pop(0)

        item, cookie = self._tree.GetFirstChild(baseitem)
        
        while item.IsOk():
            if self._tree.GetItemText(item) == name:
                baseitem = item
                return self.find_ud(baseitem,itemNames)
            item, cookie = self._tree.GetNextChild(baseitem,cookie)
            
        return None

    def expand_ud(self,ud):

        item = self.find_ud(self._root, ud)
        
        if item is None:
            return

        self._tree.SelectItem(item,True)

        while item != self._root:
            item = self._tree.GetItemParent(item)
            self._tree.Expand(item)            
        
    def on_show_info(self, event=None):
        
        ItemData = self._tree.GetItemData(self._tree.GetSelection())
        
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
            if d.ShowModal() == wx.ID_NO:
                return

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
            
            self._tree.DeleteAllItems()
            self._udTree.clear()
            self.build_plugins_tree()
            self._info.Clear()
            
            pub.sendMessage("msg_set_ud")

    def on_save_ud(self,event):

        UD_STORE.save()

        LOGGER('User definitions successfully saved.','info',['console'])
        
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

    def on_quit(self, event):
        
        d = wx.MessageDialog(None,'Do you really want to quit ?','Question',wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_YES:
            self.Destroy()   

if __name__ == "__main__":
    app = wx.App(False)
    f = UserDefinitionViewerFrame(None,ud=['protein_in_periodic_universe.nc','atom_selection',"sfdfdfsd"])
    f.Show()
    app.MainLoop()    
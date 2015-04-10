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
Created on Apr 10, 2015

@author: pellegrini
'''

import wx

from MDANSE.Externals.pubsub import pub

from MDANSE.App.GUI.DataController import DATA_CONTROLLER

class DataObject(wx.TextDataObject):

    def __init__(self, pluginStr):
        wx.TextDataObject.__init__(self)
                
        self.SetText(pluginStr)   
        
class DataTreePanel(wx.Panel):
    
    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self.build_panel()
        
        self.build_layout()

        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_double_click_data)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.on_drag_data)
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.on_delete_data, self._tree)

        pub.subscribe(self.msg_load_input_data, ('load_input_data'))       
        pub.subscribe(self.msg_delete_input_data, ('delete_input_data'))       
        
    @property
    def tree(self):
        return self._tree
    
    def msg_load_input_data(self, message):
        
        if message is None:
            return
        
        self.add_data(message)

    def msg_delete_input_data(self, message):

        
        item = self.get_tree_item(self._root, message)
        
        if item is None:
            return
        
        parentItem = self._tree.GetItemParent(item)
         
        self._tree.Delete(item)
         
        if not self._tree.ItemHasChildren(parentItem):
            self._tree.Delete(parentItem)
    
    def get_tree_item(self, node, name):
                
        for item in self.get_children(node):
            if self._tree.GetItemData(item).GetData() == name:
                return item
            else:
                return self.get_tree_item(item, name)
        
        return None
    
    def get_children(self, item):
        
        item, _ = self._tree.GetFirstChild(item)
        
        while item.IsOk():
            yield item
            item = self._tree.GetNextSibling(item)
                
    def add_data(self, data):
                
        dataItem = wx.TreeItemData(data.filename)

        item = None
        for cItem in self.get_children(self._root):
            if data.type == self._tree.GetItemText(cItem):
                item = cItem
                break
        if item is None:    
            item = self._tree.AppendItem(self._root, data.type, data=None)

        self._tree.AppendItem(item, data.basename, data=dataItem)

        self._tree.ExpandAll()
          
    def build_panel(self):
        
        self._tree = wx.TreeCtrl(self, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE^wx.TR_HIDE_ROOT)
        
        self._root = self._tree.AddRoot("root")
                     
    def build_layout(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self._tree, 1, wx.EXPAND, 0)
        
        self.SetSizer(sizer)
         
    def on_delete_data(self, event):
        
        keycode = event.GetKeyCode()
        
        if keycode == wx.WXK_DELETE:
            
            item = self._tree.GetSelection()
            itemData = self._tree.GetItemData(item)
            
            if itemData.GetData() is None:
                return

            del DATA_CONTROLLER[itemData.GetData()]
                                    
    def on_double_click_data(self, event):
        
        itemData = self._tree.GetItemData(event.GetItem())
        
        if itemData.GetData() is None:
            return
        
        containerStr = itemData.GetData()
       
        self.TopLevelParent.panels["working"].drop(containerStr)
                                           
    def on_drag_data(self, event):

        containerStr = self._tree.GetItemData(event.GetItem()).GetData()
        
        if containerStr is None:
            return            
        
        dropSource = wx.DropSource(self)

        data = DataObject(containerStr)
        
        dropSource.SetData(data)
        
        dropSource.DoDragDrop(wx.Drag_AllowMove)

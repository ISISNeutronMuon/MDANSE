# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/DataTreePanel.py
# @brief     Implements module/class/test DataTreePanel
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.DataController import DATA_CONTROLLER

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
        
        self.Bind(wx.EVT_WINDOW_DESTROY,self.OnDestroy)

        PUBLISHER.subscribe(self.msg_load_input_data, 'msg_load_input_data')       
        PUBLISHER.subscribe(self.msg_delete_input_data, 'msg_delete_input_data')       
        
    @property
    def tree(self):
        return self._tree
    
    def OnDestroy(self,event):
        
        PUBLISHER.unsubscribe(self.msg_load_input_data, 'msg_load_input_data')       
        PUBLISHER.unsubscribe(self.msg_delete_input_data, 'msg_delete_input_data')       
        event.Skip()
    
    def msg_load_input_data(self,message):
        
        if message is None:
            return
                        
        self.add_data(message)

    def msg_delete_input_data(self,message):

        if message is None:
            return

        item = self.get_tree_item(self._root,message)
        
        if item is None:
            return
        
        parentItem = self._tree.GetItemParent(item)
         
        self._tree.Delete(item)
         
        if not self._tree.ItemHasChildren(parentItem):
            self._tree.Delete(parentItem)
    
    def get_tree_item(self, node, name):
                
        for item in self.get_children(node):
            data = self._tree.GetItemData(item)
            if data is not None:
                if data.GetData() == name:
                    return item
            match = self.get_tree_item(item, name)
            if match is not None:
                return match  
        
        return None
    
    def get_children(self, item):
        
        item, _ = self._tree.GetFirstChild(item)
        
        while item.IsOk():
            yield item
            item = self._tree.GetNextSibling(item)
                
    def add_data(self,data):
                
        dataItem = wx.TreeItemData(data.name)

        item = None
        for cItem in self.get_children(self._root):
            if data._type == self._tree.GetItemText(cItem):
                item = cItem
                break
        if item is None:    
            item = self._tree.AppendItem(self._root, data._type, data=None)

        self._tree.AppendItem(item, data.shortname, data=dataItem)

        self._tree.ExpandAll()
          
    def build_panel(self):
        
        self._tree = wx.TreeCtrl(self, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)
        
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

            if itemData is None:
                return
            
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
        
        dropSource.DoDragDrop(wx.Drag_CopyOnly)

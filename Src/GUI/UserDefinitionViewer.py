# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/UserDefinitionViewer.py
# @brief     Implements module/class/test UserDefinitionViewer
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

from MDANSE import LOGGER
from MDANSE.Framework.UserDefinitionStore import UD_STORE

from MDANSE.GUI import PUBLISHER

class UserDefinitionViewer(wx.Dialog):
    
    def __init__(self, parent, title="User Definition Viewer", ud=None,editable=True):
        
        wx.Dialog.__init__(self, parent, wx.ID_ANY, size = (800,400), title = title, style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)

        self._udTree = {}
        
        dialogSizer = wx.BoxSizer(wx.VERTICAL)
        
        mainPanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
        
        self._tree = wx.TreeCtrl(mainPanel, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT|wx.TR_EDIT_LABELS)
        
        self._root = self._tree.AddRoot("root")

        self.build_tree(self._root, UD_STORE.definitions)     

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
        self.Bind(wx.EVT_TREE_KEY_DOWN, self.on_delete, self._tree)
        self.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.on_rename, self._tree)
        self.Bind(wx.EVT_TREE_BEGIN_LABEL_EDIT, self.on_try_rename, self._tree)
        self.Bind(wx.EVT_CLOSE, self.on_close,self)

        self.Bind(wx.EVT_BUTTON, self.on_save_ud, self._save)
        
        if ud is not None:
            self.expand_ud(ud)
        
        self.set_editable(editable)
        
        dialogSizer.Add(mainPanel,1,wx.EXPAND)
        
        self.SetSizer(dialogSizer)
            
    def set_editable(self,editable=True):
        
        self._editable = editable
        
        self._save.Show(self._editable)
                                        
    def get_item_level(self,item):
        
        parent = self._tree.GetItemParent(item)
        
        if parent == self._tree.GetRootItem():
            return 1
        else: 
            return 1 + self.get_item_level(parent)

    def build_tree(self, node, data):
                
        for k, v in sorted(data.items()):
            
            dataItem = wx.TreeItemData(v)
            subnode = self._tree.AppendItem(node, str(k), data=dataItem)

            self._tree.SetItemTextColour(subnode, 'blue')  
            
            if isinstance(v, dict):
                self.build_tree(subnode, v)
                
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

        while True:
            item = self._tree.GetItemParent(item)
            if item == self._root:
                break
            self._tree.Expand(item)

    def on_close(self,event):

        self.EndModal(wx.CANCEL)

        self.Destroy()

    def on_show_info(self, event=None):

        currentItem = self._tree.GetSelection()

        itemData = self._tree.GetItemData(currentItem)
        
        if itemData is None:
            return
        
        data = itemData.GetData()
        
        level = self.get_item_level(currentItem)

        if level <= 3:
            self._info.SetValue("Contains the followings definitions: %s" % data.keys())
            return
                       
        self._info.SetValue(str(itemData.GetData()))       

    def on_delete(self, event):

        if not self._editable:
            return

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
                UD_STORE.remove_definition(currentItemName)                
            elif level == 2:
                targetItem = self._tree.GetItemParent(currentItem)
                targetItemName = str(self._tree.GetItemText(targetItem))
                UD_STORE.remove_definition(targetItemName,currentItemName)
            elif level == 3:
                sectionItem = self._tree.GetItemParent(currentItem)
                sectionItemName = str(self._tree.GetItemText(sectionItem))
                targetItem = self._tree.GetItemParent(sectionItem)
                targetItemName = str(self._tree.GetItemText(targetItem))
                UD_STORE.remove_definition(targetItemName,sectionItemName,currentItemName)
            else:
                return
            
            self._tree.DeleteChildren(currentItem)
            self._tree.Delete(currentItem)
            self._udTree.clear()
            self._info.Clear()
            
            PUBLISHER.sendMessage("msg_set_ud",message=None)

    def on_save_ud(self,event):

        UD_STORE.save()

        LOGGER('User definitions successfully saved.','info',['console'])
        
    def on_try_rename(self, event):
        
        if not self._editable:
            event.Veto()
            return

        currentItem = self._tree.GetSelection()
        level = self.get_item_level(currentItem)

        if level != 3:
            event.Veto()
            return

    def on_rename(self, event):
        
        if not self._editable:
            return
        
        currentItem = event.GetItem()
        
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
            
if __name__ == "__main__":
    app = wx.App(False)
    f = UserDefinitionViewer(None,ud=['protein_in_periodic_universe.nc','atom_selection',"sfdfdfsd"],editable=True)
    f.ShowModal()
    f.Destroy()
    app.MainLoop()

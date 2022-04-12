# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/RegistryViewer.py
# @brief     Implements module/class/test RegistryViewer
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

import wx
import wx.html as wxhtml

from MDANSE import PLATFORM, REGISTRY

class RegistryViewer(wx.Dialog):
    
    def __init__(self, parent, *args, **kwargs):

        wx.Dialog.__init__(self, parent, wx.ID_ANY, size = (800,400), title="Registry viewer", style=wx.DEFAULT_DIALOG_STYLE|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX|wx.RESIZE_BORDER)

        dialogSizer = wx.BoxSizer(wx.VERTICAL)

        mainPanel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())

        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
                        
        self._tree = wx.TreeCtrl(mainPanel,wx.ID_ANY,style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)
        self._root = self._tree.AddRoot("root")
        
        mainSizer.Add( self._tree, 1, wx.ALL|wx.EXPAND, 5)
                                
        self._info = wxhtml.HtmlWindow(mainPanel, wx.ID_ANY, size=self.GetSize())        

        mainSizer.Add(self._info, 1, wx.ALL|wx.EXPAND, 5)
        
        mainPanel.SetSizer(mainSizer)        

        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_double_click_data)

        self.set_plugins_tree(self._root, REGISTRY._registry)
        
        dialogSizer.Add(mainPanel,1,wx.EXPAND)
        
        self.SetSizer(dialogSizer)           
            
    def set_plugins_tree(self, node, data):
        
        for k, v in sorted(data.items()):
            
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

        moduleFullName = PLATFORM.full_dotted_module(ItemData.GetData())
        
        if moduleFullName is None:            
            moduleDocPath = ''
        else:        
            moduleDocPath = os.path.join(PLATFORM.help_path(), moduleFullName+'.html')
                
        self._info.LoadPage(moduleDocPath)
        
if __name__ == "__main__":
    app = wx.App(False)
    f = RegistryViewer(None)
    f.ShowModal()
    f.Destroy()
    app.MainLoop()    

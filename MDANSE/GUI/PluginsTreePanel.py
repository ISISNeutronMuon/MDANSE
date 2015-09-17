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

:author: Eric C. Pellegrini
'''

import collections
import cPickle

import wx

from MDANSE import REGISTRY
from MDANSE.Externals.pubsub import pub

class DataObject(wx.TextDataObject):

    def __init__(self, pluginStr):
        wx.TextDataObject.__init__(self)
                
        self.SetText(pluginStr)   
        
class PluginsTreePanel(wx.Panel):
    
    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self.build_panel()
        
        self.build_layout()
        
        self.build_plugins_tree()
        
        self.Bind(wx.EVT_TREE_BEGIN_DRAG, self.on_drag, self._tree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_double_click)
        
        pub.subscribe(self.msg_set_plugins_tree, 'msg_set_plugins_tree')  
        
    @property
    def tree(self):
        return self._tree

    def build_panel(self):
        
        self._tree = wx.TreeCtrl(self, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)
        
        self._root = self._tree.AddRoot("root")
         
    def build_layout(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self._tree, 1, wx.EXPAND|wx.ALL, 5)
        
        self.SetSizer(sizer)
        
    def build_plugins_tree(self):
        
        self._hierarchy = collections.OrderedDict()
            
        for kls in REGISTRY["plugin"].values():
            
            ancestor = getattr(kls,"ancestor",[])

            if not ancestor:
                continue
            
            category = getattr(kls, "category", ("Miscellaneous",))
                            
            ancestors = []
            for anc in ancestor:
                ancestors.append(anc)
                ancestors.extend([c.type for c in REGISTRY['plugin'][anc].__subclasses__()])
            
            for a in ancestors:

                d = self._hierarchy.setdefault(a,collections.OrderedDict())
                
                for cat in category:
                    d = d.setdefault(cat,collections.OrderedDict())
                        
                d[kls.type] = True
                            
    def on_double_click(self, event):
        
        data = self._tree.GetPyData(event.GetItem())
        
        self.TopLevelParent.panels["working"].active_page.currentWindow.drop(data)
        
    def on_drag(self, event=None):

        if event is None:
            return
        
        data = self._tree.GetPyData(event.GetItem())

        if data is None:
            return

        draginfo = cPickle.dumps(data)
        
        tdo = wx.CustomDataObject(wx.CustomDataFormat("Plugin"))
        
        tdo.SetData(draginfo)
        
        tds = wx.DropSource(self._tree)
        
        tds.SetData(tdo)
        
        tds.DoDragDrop(True)

        event.Skip()

    def set_plugins_tree(self, node, data):
        
        if not data:
            self._tree.AppendItem(node, "No plugins available")
            return
                
        for k, v in data.items():
            
            plugin = REGISTRY["plugin"].get(k, None)
            
            if plugin is None:
                label = k
                data = None
            else:
                label = getattr(plugin,"label",plugin.type)
                data = wx.TreeItemData(k)
                
            subnode = self._tree.AppendItem(node, label, data=data)
            
            if v is True:
                continue
            
            self.set_plugins_tree(subnode, v)
        
    def msg_set_plugins_tree(self, plugin):
                        
        if self._tree.GetCount() !=0:
            self._tree.DeleteChildren(self._root)
                                                                
        if plugin is None:
            return
        
        self.set_plugins_tree(self._root, self._hierarchy.get(plugin.type,{}))
        
        self.TopLevelParent._mgr.Update()

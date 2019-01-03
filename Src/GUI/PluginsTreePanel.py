import collections
import cPickle

import wx

from MDANSE import REGISTRY

from MDANSE.GUI import PUBLISHER

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
        
        PUBLISHER.subscribe(self.msg_set_plugins_tree, 'msg_set_plugins_tree')
        
        self.Bind(wx.EVT_WINDOW_DESTROY,self.OnDestroy)
        
    @property
    def tree(self):
        return self._tree

    def OnDestroy(self,event):
        
        PUBLISHER.subscribe(self.msg_set_plugins_tree, 'msg_set_plugins_tree')
        event.Skip()

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
                ancestors.extend([c._type for c in REGISTRY['plugin'][anc].__subclasses__()])
            
            for a in ancestors:

                d = self._hierarchy.setdefault(a,collections.OrderedDict())
                
                for cat in category:
                    d = d.setdefault(cat,collections.OrderedDict())
                        
                d[kls._type] = True
                            
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
                
        for k, v in sorted(data.items()):
            
            plugin = REGISTRY["plugin"].get(k, None)
            
            if plugin is None:
                label = k
                data = None
            else:
                label = getattr(plugin,"label",plugin._type)
                data = wx.TreeItemData(k)
                
            subnode = self._tree.AppendItem(node, label, data=data)
            
            if v is True:
                continue
            
            self.set_plugins_tree(subnode, v)
        
    def msg_set_plugins_tree(self,message):
                        
        if self._tree.GetCount() !=0:
            self._tree.DeleteChildren(self._root)
                    
        plugin = message                                            
        if plugin is None:
            return
        
        self.set_plugins_tree(self._root, self._hierarchy.get(plugin._type,{}))
        
        self.TopLevelParent._mgr.Update()

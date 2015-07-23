import collections

import wx
import wx.aui as wxaui
import wx.py as wxpy

from MDANSE.GUI.JobControllerPanel import JobControllerPanel
from MDANSE.GUI.Icons import ICONS

class ControllerPanel(wx.Panel):

    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)  
                                                                     
        self.build_panel()
        
        self.build_layout()
    
    @property
    def pages(self):
        return self._pages
    
    def build_panel(self):

        self._notebook = wxaui.AuiNotebook(self, style=wxaui.AUI_NB_DEFAULT_STYLE & ~wxaui.AUI_NB_CLOSE_ON_ACTIVE_TAB)

        self._pages = collections.OrderedDict()
        self._pages["logger"] = wx.TextCtrl(self, style=wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_BESTWRAP|wx.HSCROLL|wx.TE_AUTO_URL)
        self._pages["console"] = wxpy.shell.Shell(self)
        self._pages["jobs"] = JobControllerPanel(self)

        #wxpython 2.9 compatibility
        if wx.VERSION[:2] > (2,8):
            il = wx.ImageList(16, 16)
            il.Add(ICONS["log",16,16])
            il.Add(ICONS["shell",16,16])
            il.Add(ICONS["hourglass",16,16])
            self._notebook.AssignImageList(il)
    
            self._notebook.AddPage(self._pages["logger"], 'Logger')                   
            self._notebook.AddPage(self._pages["console"], 'Console')
            self._notebook.AddPage(self._pages["jobs"], 'Jobs')
            
            self._notebook.SetPageImage(0, 0)
            self._notebook.SetPageImage(1, 1)
            self._notebook.SetPageImage(2, 2)

        else:
            self._notebook.AddPage(self._pages["logger"], 'Logger', bitmap=ICONS["log",16,16])                   
            self._notebook.AddPage(self._pages["console"], 'Console', bitmap=ICONS["shell",16,16])
            self._notebook.AddPage(self._pages["jobs"], 'Jobs', bitmap=ICONS["hourglass",16,16])
    
    def build_layout(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self._notebook, 1, wx.EXPAND, 0)
        
        self.SetSizer(sizer)

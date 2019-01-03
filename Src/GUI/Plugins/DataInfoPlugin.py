# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/DataInfoPlugin.py
# @brief     Implements module/class/test DataInfoPlugin
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx
import wx.aui as aui

from MDANSE import REGISTRY
from MDANSE.GUI.Plugins.ComponentPlugin import ComponentPlugin

class DataInfoPlugin(ComponentPlugin):
        
    label = "Data info"
    
    ancestor = REGISTRY["input_data"].keys()

    def __init__(self, parent, *args, **kwargs):
        
        ComponentPlugin.__init__(self, parent, size=(-1,50), *args, **kwargs)
                           
    def build_panel(self):
        
        panel = wx.Panel(self, wx.ID_ANY, size=self.GetSize())
 
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._info = wx.TextCtrl(panel, wx.ID_ANY, style=wx.TE_MULTILINE|wx.TE_READONLY)

        sizer.Add(self._info, 1, wx.ALL|wx.EXPAND, 5)
                
        panel.SetSizer(sizer)
        sizer.Fit(panel)        
        panel.Layout()
                
        self._mgr.AddPane(panel, aui.AuiPaneInfo().Center().Dock().CaptionVisible(False).CloseButton(False).MinSize(self.GetSize()))

        self._mgr.Update()

    def on_close(self, event):
        
        self.parent.mgr.ClosePane(self.parent.mgr.GetPane(self))

    def plug(self):
        
        self._info.SetValue(self.dataproxy.info())
        
        self._parent._mgr.GetPane(self).Float().CloseButton(True).BestSize((600,600))            
        self._parent._mgr.Update()

REGISTRY["data_info"] = DataInfoPlugin

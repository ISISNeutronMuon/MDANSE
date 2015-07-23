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

:author: Eric C. Pellegrini
'''

import wx
import wx.aui as aui

from MDANSE.Framework.Plugins.ComponentPlugin import ComponentPlugin

class DataInfoPlugin(ComponentPlugin):
    
    type = "data_info"
    
    label = "Data info"
    
    ancestor = "data"
    
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


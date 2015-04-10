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
import wx.aui as wxaui

from MDANSE.Externals.pubsub import pub as Publisher

from MDANSE import REGISTRY
from MDANSE.App.GUI import DATA_CONTROLLER

class DropTarget(wx.TextDropTarget):

    def __init__(self, targetPanel):

        wx.TextDropTarget.__init__(self)
        self._targetPanel = targetPanel

    def OnDropText(self, x, y, pluginName):
        self._targetPanel.drop(pluginName)

    @property
    def target_panel(self):
        return self._targetPanel

class WorkingPanel(wx.Panel):
    
    def __init__(self, parent):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        
        self._data = None
        
        self.build_panel()
                
        self.SetDropTarget(DropTarget(self))

        self._notebook.Bind(wxaui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.on_changing_page)        
        self._notebook.Bind(wx.EVT_CHILD_FOCUS, self.on_changing_page)

    @property
    def active_page(self):
        
        return self._notebook.GetPage(self._notebook.GetSelection())

    def build_panel(self):

        self._notebook = wxaui.AuiNotebook(self)
                
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self._notebook, 1, wx.EXPAND, 0)
        
        self.SetSizer(sizer)
        
        self._notebook.Bind(wxaui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_close_page, self._notebook)
        
    def drop(self, filename):
                
        data = DATA_CONTROLLER.get(filename, None)
        
        if data is None:
            return
                                        
        container = REGISTRY["plugin"].get(data.type,None)
                        
        if container is None:
            return
                
        container = container(self, filename)
                        
        self._notebook.AddPage(container, data.basename)
        
        self._notebook.SetFocus()
        
    def add_empty_data(self):
        
        container = REGISTRY["plugin"].get("empty_data")
                                        
        container = container(self, "empty_data")
                        
        self._notebook.AddPage(container, "Empty data")
        
        self._notebook.SetFocus()
        
    def on_changing_page(self, event=None):
                
        if self._notebook.GetPageCount() == 0:
            return
        
        dataPlugin = self._notebook.GetPage(self._notebook.GetSelection())
               
        Publisher.sendMessage(('set_plugins_tree'), message=dataPlugin)
        
    def on_close_page(self, event):

        dataPlugin = self._notebook.GetPage(event.GetSelection())
        
        dataPlugin.close_children()
        
        if self._notebook.GetPageCount() == 1:
            Publisher.sendMessage(('set_plugins_tree'), message = None)
        
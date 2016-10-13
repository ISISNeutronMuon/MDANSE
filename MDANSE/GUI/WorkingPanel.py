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

import wx
import wx.aui as wxaui

from MDANSE import REGISTRY

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.DataController import DATA_CONTROLLER

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

        self._notebook.AddPage(container, data.shortname)
        
        self._notebook.SetFocus()
        
        self._notebook.SetSelection(self._notebook.GetPageCount()-1)
                
    def add_empty_data(self):
        
        container = REGISTRY["plugin"].get("empty_data")
                                        
        container = container(self, "empty_data")
                        
        self._notebook.AddPage(container, "Empty data")
        
        self._notebook.SetFocus()
        
    def on_changing_page(self, event=None):
                
        if self._notebook.GetPageCount() == 0:
            return
        
        dataPlugin = self._notebook.GetPage(self._notebook.GetSelection())
               
        PUBLISHER.sendMessage('msg_set_plugins_tree', data=dataPlugin)
        
    def on_close_page(self, event):

        d = wx.MessageDialog(None, 'Closing this data will also close all the other plugins you plugged in in so far. Do you really want to close ?', 'Question', wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
        if d.ShowModal() == wx.ID_NO:
            event.Veto()
            return
        
        if self._notebook.GetPageCount() == 1:
            PUBLISHER.sendMessage('msg_set_plugins_tree', data=None)
        
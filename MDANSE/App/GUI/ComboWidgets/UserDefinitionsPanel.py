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

class UserDefinitionsPanel(wx.Panel):
    
    def __init__(self, parent, *args, **kwargs):
        
        wx.Panel.__init__(self, parent, wx.ID_ANY, *args, **kwargs)
        
        self._parent = parent
        
        sb = wx.StaticBox(self, wx.ID_ANY)
        actionsSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
                        
        self._cancelButton  = wx.Button(self, wx.ID_ANY, label="Cancel")
        self._udName = wx.TextCtrl(self, wx.ID_ANY, style = wx.TE_PROCESS_ENTER)
        self._saveButton  = wx.Button(self, wx.ID_ANY, label="Save")
        
        actionsSizer.Add(self._cancelButton, 0, wx.ALL, 5)
        actionsSizer.Add(self._udName, 1, wx.ALL|wx.EXPAND, 5)
        actionsSizer.Add(self._saveButton, 0, wx.ALL, 5)
        
        self.SetSizer(actionsSizer)
        
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.on_close, self._cancelButton)
        self.Bind(wx.EVT_BUTTON, self.on_save, self._saveButton)    
        
    def get_selection_name(self):
        
        return self._udName.GetValue()

    def on_close(self, event):
        
        self._parent.Parent.on_close()

    def on_save(self, event):
        
        self._parent.Parent.on_save()
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
Created on Mar 30, 2015

@author: pellegrini
'''

import os

import wx.combo

from MDANSE.Framework.UserDefinitions.IUserDefinition import UD_STORE

from MDANSE.App.GUI.Framework.Widgets.IWidget import IWidget
from MDANSE.App.GUI.ComboWidgets.ComboCheckbox import ComboCheckbox

class UserDefinitionWidget(IWidget):
    
    type = None    
    
    def __init__(self, *args, **kwargs):
        
        IWidget.__init__(self, *args, **kwargs)
        
        self._filename = None
        self._basename = None
    
    def initialize(self):
        pass
    
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        comboCtrl = wx.combo.ComboCtrl(self._widgetPanel, value="Available definitions", style=wx.CB_READONLY)
        
        self._selections = ComboCheckbox(items=[])

        comboCtrl.SetPopupControl(self._selections)
        
        sizer.Add(comboCtrl, 1, wx.ALL|wx.EXPAND, 5)

        return sizer

    def msg_new_definition(self, message):
        
        filename, name = message
        
        if filename != self._basename:
            return
        
        if name in self._selections.items:
            idx = self._selections.items.index(name)
            self._selections.GetControl().Check(idx,False)
        else:
            self._selections.GetControl().AppendItems([name])   


    def msg_set_trajectory(self, message):

        window, self._filename = message
                        
        if not window in self.Parent.widgets.values():
            return

        self._selections.GetControl().Clear()
        
        self._basename = os.path.basename(self._filename)
        
        try:
            names = UD_STORE.filter(self._basename,self.type)
        except KeyError:
            names = []
        
        self._selections.GetControl().SetItems(names)

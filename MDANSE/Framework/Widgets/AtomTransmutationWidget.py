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

:author: Eric C. Pellegrini
'''

import wx

from MDANSE import ELEMENTS

from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.Widgets.AtomSelectionWidget import AtomSelectionWidget
from MDANSE.GUI.Icons import ICONS

class AtomTransmutationWidget(AtomSelectionWidget):
         
    type = "atom_transmutation"
    
    udType = "atom_selection"
  
    def on_add_definition(self,event):
        
        panel = wx.Panel(self._widgetPanel,wx.ID_ANY)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
 
        availableUDs = wx.Choice(panel, wx.ID_ANY,style=wx.CB_SORT)
        uds = UD_STORE.filter(self._basename, "atom_selection")
        availableUDs.SetItems(uds)
         
        view = wx.Button(panel, wx.ID_ANY, label="View selected definition")
        elements = wx.ComboBox(panel, wx.ID_ANY, value="Transmutate to", choices=ELEMENTS.elements)
        remove = wx.BitmapButton(panel, wx.ID_ANY, ICONS["minus",16,16])
 
        sizer.Add(availableUDs, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(view, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(elements, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(remove, 0, wx.ALL|wx.EXPAND, 5)
         
        panel.SetSizer(sizer)
         
        self._sizer.Add(panel,1,wx.ALL|wx.EXPAND,5)
         
        self._widgetPanel.GrandParent.Layout()
 
        self.Bind(wx.EVT_BUTTON, self.on_view_definition, view)
        self.Bind(wx.EVT_BUTTON, self.on_remove_definition, remove)
          
    def get_widget_value(self):

        sizerItemList = list(self._sizer.GetChildren())
        del sizerItemList[0]

        uds = []
        for sizerItem in sizerItemList:
            
            panel = sizerItem.GetWindow()
            children = panel.GetChildren()
            udName = children[0]
            element = children[2]
            oldSelection = udName.GetStringSelection()            
            udName.SetItems(uds)
            udName.SetStringSelection(oldSelection)
            
            uds.append([udName,element.GetStringSelection])
                  
        if not uds:
            return None
        else:
            return uds
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

from MDANSE import ELEMENTS, LOGGER

from MDANSE.Framework.Widgets.UserDefinitionWidget import UserDefinitionWidget
from MDANSE.Framework.Widgets.AtomSelectionWidget import AtomSelectionPlugin

class AtomTransmutationPlugin(AtomSelectionPlugin):
    
    type = 'atom_transmutation'

    label = "Atom transmutation"
    
    ancestor = ["molecular_viewer"]
    
    def build_dialog(self):
        
        AtomSelectionPlugin.build_dialog(self)
                
        self._elements = wx.ComboBox(self._mainPanel, wx.ID_ANY, value="Transmutate to", choices=ELEMENTS.elements)
        
        self._selectionExpressionSizer.Add(self._elements, pos=(0,3), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        self._mainPanel.Layout()
        
    def validate(self):
        
        if not self._selection:
            LOGGER("The current selection is empty", "error", ["dialog"])
            return None

        element = self._elements.GetStringSelection()
        
        if not element:
            LOGGER("No target element selected to be transmutated to", "error", ["dialog"])
            return None
        
        ud = {}
        ud['element'] = element
        ud['indexes'] = self._selection
        
        return ud
        
class AtomTransmutationWidget(UserDefinitionWidget):
         
    type = "atom_transmutation"
  
    def get_widget_value(self):
         
        ud = self._availableUDs.GetStringSelection()
         
        if not ud:
            return None
        else:
            return str(ud)    
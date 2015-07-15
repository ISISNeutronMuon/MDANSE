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

from MDANSE.App.GUI.Framework.Widgets.UserDefinitionWidget import UserDefinitionWidget
from MDANSE.App.GUI.Framework.Widgets.AtomSelectionWidget import AtomSelectionDialog

class AtomTransmutationDialog(AtomSelectionDialog):
    
    type = 'atom_transmutation'
    
    def build_dialog(self):
        
        AtomSelectionDialog.build_dialog(self)
        
        self.SetTitle("Atom transmutation dialog")
        
        self._elements = wx.ComboBox(self._mainPanel, wx.ID_ANY, value="Transmutate to", choices=ELEMENTS.elements)
        
        self._selectionExpressionSizer.Add(self._elements, pos=(0,3), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        self._mainPanel.Layout()
        
    def validate(self):
        
        if not self._selection:
            LOGGER("The current selection is empty", "error", ["dialog"])
            return None

        element = self._elements.GetStringSelection()
        
        self._ud['element'] = element
        self._ud['indexes'] = self._selection
        
        return self._ud
        
class AtomTransmutationWidget(UserDefinitionWidget):
        
    type = "atom_transmutation"

    def on_new_user_definition(self,event):
        
        dlg = AtomTransmutationDialog(self,self._trajectory)
        
        dlg.Show()

    def get_widget_value(self):
        
        ud = self._availableUDs.GetStringSelection()
        
        if not ud:
            return None
        else:
            return str(ud)    
                                            
if __name__ == "__main__":
    
    from MMTK.Trajectory import Trajectory
    
    t = Trajectory(None,"../../../../../Data/Trajectories/MMTK/protein_in_periodic_universe.nc","r")
    
    app = wx.App(False)
                
    p = AtomTransmutationDialog(None,t)
        
    p.SetSize((800,800))
            
    p.ShowModal()
    
    p.Destroy()
    
    app.MainLoop()
            
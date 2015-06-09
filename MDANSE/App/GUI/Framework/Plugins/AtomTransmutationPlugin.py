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

@author: Eric C. Pellegrini
'''
import os

import wx

from MDANSE import ELEMENTS, LOGGER, REGISTRY
from MDANSE.Externals.pubsub import pub as Publisher
from MDANSE.Framework.UserDefinitionsStore import UD_STORE

from MDANSE.App.GUI.Framework.Plugins.AtomSelectionPlugin import AtomSelectionPlugin

class AtomTransmutationPlugin(AtomSelectionPlugin):

    type = "atom_transmutation"
    
    label = "Atom transmutation"
    
    ancestor = "molecular_viewer"
    
    def build_panel(self):
        
        AtomSelectionPlugin.build_panel(self)

        label = wx.StaticText(self._mainPanel, wx.ID_ANY, style=wx.ALIGN_LEFT, label="Transmute to") 
        
        self._elements = wx.Choice(self._mainPanel, wx.ID_ANY, choices=ELEMENTS.elements)
        self._elements.SetStringSelection("H[2]")
        
        self._selectionExpressionSizer.Add(label, pos=(1,0), flag=wx.ALIGN_CENTER_VERTICAL)
        self._selectionExpressionSizer.Add(self._elements, pos=(1,1), flag=wx.EXPAND|wx.ALIGN_CENTER_VERTICAL)
        
        self._mainPanel.Layout()
        
    def on_save(self, event=None):
        '''
        Event handler: validate the selection. 
        
        @param event: the event binder
        @type event: wx event
        '''
                
        if not self._selection:
            LOGGER("The current selection is empty", "warning", ["dialog"])
            return
                       
        name = self._udPanel.get_selection_name()

        if not name:
            LOGGER("You must enter a value for the user definition", "error", ["dialog"])
            return

        path = os.path.basename(self.parent.trajectory.filename)

        element = self._elements.GetStringSelection()
        
        ud = REGISTRY['user_definition']['atom_transmutation'](path,expression=self._expression,indexes=self._selection,element=element)            
        UD_STORE[name] = ud
        UD_STORE.save()
        
        Publisher.sendMessage("new_transmutation", message = (path, name))
        
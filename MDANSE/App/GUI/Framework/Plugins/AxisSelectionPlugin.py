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

import os

import wx
import wx.aui as wxaui

from MDANSE import LOGGER, REGISTRY
from MDANSE.Externals.pubsub import pub
from MDANSE.Framework.UserDefinitionsStore import UD_STORE

from MDANSE.App.GUI.Framework.Plugins.ComponentPlugin import ComponentPlugin
from MDANSE.App.GUI.ComboWidgets.UserDefinitionsPanel import UserDefinitionsPanel
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule, get_chemical_objects_dict

class AxisSelectionPlugin(ComponentPlugin):
    
    type = "axis_selection"
    
    label = "Axis selection"
    
    ancestor = "molecular_viewer"
        
    def __init__(self, parent, *args, **kwargs):
        
        ComponentPlugin.__init__(self, parent, size=(-1,50), *args, **kwargs)
                           
    def build_panel(self):

        panel = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        panel.SetScrollbars(20,20,50,50)
        
        bSizer = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(panel, wx.ID_ANY, label = "Axis definition")
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        
        gbSizer = wx.GridBagSizer(5,5)
        
        label1 = wx.StaticText(panel, wx.ID_ANY, label="Molecules")
        label2 = wx.StaticText(panel, wx.ID_ANY, label="Endpoint 1")
        label3 = wx.StaticText(panel, wx.ID_ANY, label="Endpoint 2")

        gbSizer.Add(label1, (0,0), flag=wx.EXPAND)
        gbSizer.Add(label2, (0,1), flag=wx.EXPAND)
        gbSizer.Add(label3, (0,2), flag=wx.EXPAND)
    
        self._moleculeNames = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_SINGLE|wx.LB_NEEDED_SB)
        self._atomNames1 = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_MULTIPLE|wx.LB_NEEDED_SB)
        self._atomNames2 = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_MULTIPLE|wx.LB_NEEDED_SB)
        
        gbSizer.Add(self._moleculeNames, (1,0), flag=wx.EXPAND)
        gbSizer.Add(self._atomNames1   , (1,1), flag=wx.EXPAND)
        gbSizer.Add(self._atomNames2   , (1,2), flag=wx.EXPAND)
        
        gbSizer.AddGrowableRow(1)
        gbSizer.AddGrowableCol(0)
        gbSizer.AddGrowableCol(1)
        gbSizer.AddGrowableCol(2)
        
        sbSizer.Add(gbSizer, 1, wx.EXPAND|wx.ALL, 5)

        bSizer.Add(sbSizer, 1, wx.EXPAND|wx.ALL, 5)
                
        self._udPanel = UserDefinitionsPanel(panel)                

        bSizer.Add(self._udPanel, 0, wx.EXPAND|wx.ALL, 5)
        
        panel.SetSizer(bSizer)
        bSizer.Layout()
        panel.Fit()
        
        self._mgr.AddPane(panel, wxaui.AuiPaneInfo().Center().Dock().CaptionVisible(False).CloseButton(False))

        self._mgr.Update()
        
        self.Bind(wx.EVT_LISTBOX, self.on_select_molecule, self._moleculeNames)
        self.Bind(wx.EVT_LISTBOX, self.on_select_atom, self._atomNames1)
        self.Bind(wx.EVT_LISTBOX, self.on_select_atom, self._atomNames2)
        
    def plug(self):

        self.parent.mgr.GetPane(self).DestroyOnClose().Float().CloseButton(True).BestSize((600,300))
        
        self.parent.mgr.Update()        
        
        self._trajectory = self.dataproxy.data
        
        self._molecularContents = get_chemical_objects_dict(self._trajectory.universe)
                                
        self._moleculeNames.SetItems(sorted(self._molecularContents.keys()))        
        
    def on_close(self, event=None):
        
        self.parent.clear_selection()
        self.parent.mgr.ClosePane(self.parent.mgr.GetPane(self))
                        
    def on_save(self, event=None):
        
        atomIndexes1 = self._atomNames1.GetSelections()
        atomIndexes2 = self._atomNames2.GetSelections()
                
        if (not atomIndexes1) or (not atomIndexes2):
            LOGGER("One of the endpoints atom selection is empty. Please select some values.", "error", ["dialog"])
            return

        
        if atomIndexes1 == atomIndexes2:
            LOGGER("An axis can not be set from identical endpoints selections.", "error", ["dialog"])
            return
        
        target = os.path.basename(self._trajectory.filename)
        
        name = self._udPanel.get_selection_name()

        if not name:
            LOGGER("You must enter a value for the user definition", "error", ["dialog"])
            return
            
        molName = self._moleculeNames.GetStringSelection()        
        atomNames1 = tuple([self._atomNames1.GetString(idx) for idx in atomIndexes1])
        atomNames2 = tuple([self._atomNames2.GetString(idx) for idx in atomIndexes2])
        
        ud = REGISTRY['user_definition']['axis_selection'](target,molecule=molName,endpoint1=atomNames1,endpoint2=atomNames2)            
            
        UD_STORE.set_definition(target,ud.type,name,ud)
        UD_STORE.save()
        
        pub.sendMessage("new_axis", message = (target, name))        
        
    def on_select_atom(self, event):
        
        atomNames1 = tuple([self._atomNames1.GetString(idx) for idx in self._atomNames1.GetSelections()])
        atomNames2 = tuple([self._atomNames2.GetString(idx) for idx in self._atomNames2.GetSelections()])

        indexes1 = [idx for sublist in find_atoms_in_molecule(self._trajectory.universe,self._moleculeNames.GetStringSelection(), atomNames1, True) for idx in sublist]
        indexes2 = [idx for sublist in find_atoms_in_molecule(self._trajectory.universe,self._moleculeNames.GetStringSelection(), atomNames2, True) for idx in sublist]

        self.parent.show_selected_atoms({"axis1":indexes1,"axis2":indexes2})
                
    def on_select_molecule(self, event):
        
        atomsList = self._molecularContents[event.GetString()][0].atomList()
        atomNames = sorted(set([at.name for at in atomsList]))
        
        self._atomNames1.SetItems(atomNames)
        self._atomNames2.SetItems(atomNames)
        

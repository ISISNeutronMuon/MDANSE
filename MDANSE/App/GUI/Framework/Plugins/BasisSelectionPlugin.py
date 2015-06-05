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

@author: pellegrini
'''

import os

import wx
import wx.aui as wxaui

from MDANSE import LOGGER, REGISTRY, UD_STORE
from MDANSE.Externals.pubsub import pub
from MDANSE.App.GUI.Framework.Plugins.ComponentPlugin import ComponentPlugin
from MDANSE.App.GUI.ComboWidgets.UserDefinitionsPanel import UserDefinitionsPanel
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule, get_chemical_objects_dict

class BasisSelectionPlugin(ComponentPlugin):
    
    type = "basis_selection"
    
    label = "Basis selection"
    
    ancestor = "molecular_viewer"
        
    def __init__(self, parent, *args, **kwargs):
        
        ComponentPlugin.__init__(self, parent, size=(-1,50), *args, **kwargs)
                           
    def build_panel(self):

        panel = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        panel.SetScrollbars(20,20,50,50)
        
        bSizer = wx.BoxSizer(wx.VERTICAL)

        sb = wx.StaticBox(panel, wx.ID_ANY, label = "Basis definition")
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        
        gbSizer = wx.GridBagSizer(5,5)
        
        label1 = wx.StaticText(panel, wx.ID_ANY, label="Molecules")
        label2 = wx.StaticText(panel, wx.ID_ANY, label="Origin")
        label3 = wx.StaticText(panel, wx.ID_ANY, label="X axis")
        label4 = wx.StaticText(panel, wx.ID_ANY, label="Y axis")

        gbSizer.Add(label1, (0,0), flag=wx.EXPAND)
        gbSizer.Add(label2, (0,1), flag=wx.EXPAND)
        gbSizer.Add(label3, (0,2), flag=wx.EXPAND)
        gbSizer.Add(label4, (0,3), flag=wx.EXPAND)
    
        self._moleculeNames = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_SINGLE|wx.LB_NEEDED_SB)
        self._origin = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_MULTIPLE|wx.LB_NEEDED_SB)
        self._xAxis = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_MULTIPLE|wx.LB_NEEDED_SB)
        self._yAxis = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_MULTIPLE|wx.LB_NEEDED_SB)
        
        gbSizer.Add(self._moleculeNames, (1,0), flag=wx.EXPAND)
        gbSizer.Add(self._origin   , (1,1), flag=wx.EXPAND)
        gbSizer.Add(self._xAxis   , (1,2), flag=wx.EXPAND)
        gbSizer.Add(self._yAxis   , (1,3), flag=wx.EXPAND)
        
        gbSizer.AddGrowableRow(1)
        gbSizer.AddGrowableCol(0)
        gbSizer.AddGrowableCol(1)
        gbSizer.AddGrowableCol(2)
        gbSizer.AddGrowableCol(3)
        
        sbSizer.Add(gbSizer, 1, wx.EXPAND|wx.ALL, 5)

        bSizer.Add(sbSizer, 1, wx.EXPAND|wx.ALL, 5)

        self._udPanel = UserDefinitionsPanel(panel)                

        bSizer.Add(self._udPanel, 0, wx.EXPAND|wx.ALL, 5)
                        
        panel.SetSizer(bSizer)
        bSizer.Layout()
        panel.Fit()
        
        self.Bind(wx.EVT_LISTBOX, self.on_select_molecule, self._moleculeNames)
        self.Bind(wx.EVT_LISTBOX, self.on_select_atom, self._origin)
        self.Bind(wx.EVT_LISTBOX, self.on_select_atom, self._xAxis)
        self.Bind(wx.EVT_LISTBOX, self.on_select_atom, self._yAxis)
        
        self._mgr.AddPane(panel, wxaui.AuiPaneInfo().Center().Dock().CaptionVisible(False).CloseButton(False))

        self._mgr.Update()

    def plug(self):

        self._parent._mgr.GetPane(self).Float().CloseButton(True).BestSize((600,300))
        
        self._parent._mgr.Update()        
        
        self._trajectory = self.dataproxy.data
                
        self._molecularContents = get_chemical_objects_dict(self._trajectory.universe)
                
        self._moleculeNames.SetItems(sorted(self._molecularContents.keys()))        
        
    def on_close(self, event):
        
        self.parent.clear_selection()
        self.parent.mgr.ClosePane(self.parent.mgr.GetPane(self))
        
    def on_save(self, event=None):
        
        origin = self._origin.GetSelections()
        xAxis = self._xAxis.GetSelections()
        yAxis = self._yAxis.GetSelections()
                
        if (not origin) or (not xAxis) or (not yAxis):
            LOGGER("One of the atom selection is empty. Please select some values.", "error", ["dialog"])
            return

        
        if (origin == xAxis) or (origin == yAxis) or (xAxis == yAxis):
            LOGGER("A basis can not be set from identical atom selections.", "error", ["dialog"])
            return
                
        name = self._udPanel.get_selection_name()

        if not name:
            LOGGER("You must enter a value for the user definition", "error", ["dialog"])
            return

        path = os.path.basename(self._trajectory.filename)
            
        molName = self._moleculeNames.GetStringSelection()        
        origin = tuple([self._origin.GetString(idx) for idx in origin])
        xAxis = tuple([self._xAxis.GetString(idx) for idx in xAxis])
        yAxis = tuple([self._yAxis.GetString(idx) for idx in yAxis])

        ud = REGISTRY['user_definition']['basis_selection'](path,molecule=molName,origin=origin,x_axis=xAxis,y_axis=yAxis)            
                    
        UD_STORE[name] = ud
        UD_STORE.save()
        
        pub.sendMessage("new_basis", message = (path, name))

    def on_select_atom(self, event):

        atomNames1 = tuple([self._origin.GetString(idx) for idx in self._origin.GetSelections()])
        atomNames2 = tuple([self._xAxis.GetString(idx) for idx in self._xAxis.GetSelections()])
        atomNames3 = tuple([self._yAxis.GetString(idx) for idx in self._yAxis.GetSelections()])

        indexes1 = [idx for sublist in find_atoms_in_molecule(self._trajectory.universe,self._moleculeNames.GetStringSelection(), atomNames1, True) for idx in sublist]
        indexes2 = [idx for sublist in find_atoms_in_molecule(self._trajectory.universe,self._moleculeNames.GetStringSelection(), atomNames2, True) for idx in sublist]
        indexes3 = [idx for sublist in find_atoms_in_molecule(self._trajectory.universe,self._moleculeNames.GetStringSelection(), atomNames3, True) for idx in sublist]

        self.parent.show_selected_atoms({"basis1":indexes1,"basis2":indexes2,"basis3":indexes3})
        
    def on_select_molecule(self, event):
        
        atomsList = self._molecularContents[event.GetString()][0].atoms
        
        self._origin.SetItems([at.name for at in atomsList])
        self._xAxis.SetItems([at.name for at in atomsList])
        self._yAxis.SetItems([at.name for at in atomsList])
        

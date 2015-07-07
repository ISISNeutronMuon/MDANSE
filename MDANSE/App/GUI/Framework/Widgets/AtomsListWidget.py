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
Created on Jun 30, 2015

:author: Eric C. Pellegrini
'''

import os

import wx

from MDANSE import LOGGER
from MDANSE.App.GUI.Framework.Widgets.UserDefinitionWidget import UserDefinitionsDialog, UserDefinitionWidget
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule, get_chemical_objects_dict

class AtomsListDialog(UserDefinitionsDialog):

    def __init__(self, parent, trajectory, nAtoms):
        
        self._parent = parent

        self._trajectory = trajectory
    
        self._nAtoms = nAtoms
        
        self._selectedAtoms = []
        
        self._selection = []
                
        target = os.path.basename(self._trajectory.filename)
        
        section = "%d_atoms_list" % self._nAtoms

        UserDefinitionsDialog.__init__(self, parent, target, section, wx.ID_ANY, title="%d Atoms selection dialog" % nAtoms,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
                        
    def build_dialog(self):

        panel = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        panel.SetScrollbars(20,20,50,50)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        sb = wx.StaticBox(panel, wx.ID_ANY, label = "Atom selection")
        sbSizer = wx.StaticBoxSizer(sb, wx.HORIZONTAL)
        
        gbSizer = wx.GridBagSizer(5,5)
        
        label1 = wx.StaticText(panel, wx.ID_ANY, label="Molecules")
        label2 = wx.StaticText(panel, wx.ID_ANY, label="Atoms")

        gbSizer.Add(label1, (0,0), flag=wx.EXPAND)
        gbSizer.Add(label2, (0,1), flag=wx.EXPAND)
    
        self._molecules = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_SINGLE|wx.LB_NEEDED_SB)
        self._molecularContents = get_chemical_objects_dict(self._trajectory.universe)
        self._molecules.SetItems(sorted(self._molecularContents.keys()))        

        self._atoms = wx.ListBox(panel, wx.ID_ANY, style = wx.LB_MULTIPLE|wx.LB_NEEDED_SB)
        
        gbSizer.Add(self._molecules, (1,0), flag=wx.EXPAND)
        gbSizer.Add(self._atoms    , (1,1), flag=wx.EXPAND)
        
        gbSizer.AddGrowableRow(1)
        gbSizer.AddGrowableCol(0)
        gbSizer.AddGrowableCol(1)
        
        sbSizer.Add(gbSizer, 1, wx.EXPAND|wx.ALL, 5)

        setButton  = wx.Button(panel, wx.ID_ANY, label="Set")
        self._resultsTextCtrl  = wx.TextCtrl(panel, wx.ID_ANY, style=wx.TE_READONLY|wx.TE_MULTILINE)

        sizer.Add(sbSizer,1,wx.EXPAND|wx.ALL,5)
        sizer.Add(setButton,0,wx.EXPAND|wx.ALL,5)
        sizer.Add(self._resultsTextCtrl,1,wx.EXPAND|wx.ALL,5)

        panel.SetSizer(sizer)

        self._mainSizer.Add(panel, 1, wx.EXPAND|wx.ALL, 5)
                
        self.Bind(wx.EVT_BUTTON, self.on_set_user_definition, setButton)
        self.Bind(wx.EVT_LISTBOX, self.on_select_molecule, self._molecules)
        self.Bind(wx.EVT_LISTBOX, self.on_select_atom, self._atoms)

    def set_user_definition(self):

        self._selection = []

        if len(self._selectedAtoms) != self._nAtoms:
            LOGGER('You must select %d atoms.' % self._nAtoms,'error',['dialog'])
            return

        molecule = str(self._molecules.GetStringSelection())
        atoms = tuple(str(self._atoms.GetString(idx)) for idx in self._selectedAtoms)

        self._selection = find_atoms_in_molecule(self._trajectory.universe,molecule, atoms, True)
                        
    def on_set_user_definition(self,event=None):

        self._resultsTextCtrl.Clear()
        
        self.set_user_definition()
        if not self._selection:
            return
            
        self._resultsTextCtrl.AppendText('Number of selected %d-tuplets: %d\n' % (self._nAtoms,len(self._selection)))
        for idxs in self._selection:
            line = "   ;   ".join(["Atom %d : %s" % (i,v) for i,v in enumerate(idxs)])
            self._resultsTextCtrl.AppendText(line)
            self._resultsTextCtrl.AppendText('\n')
        
    def on_select_atom(self, event):
        
        selection = self._atoms.GetSelections()
                
        if len(selection) > self._nAtoms:
            self._atoms.DeselectAll()
            for idx in self._selectedAtoms:
                self._atoms.SetSelection(idx,True)
        else:
            self._selectedAtoms = selection
                            
    def on_select_molecule(self, event):
        
        atomsList = self._molecularContents[event.GetString()][0].atomList()
        atomNames = sorted(set([at.name for at in atomsList]))
        
        self._atoms.SetItems(atomNames)
            
    def validate(self):

        if not self._selection:
            return None
                        
        return {'selection' : self._selection}

class AtomListWidget(UserDefinitionWidget):
        
    type = "atoms_list"
    
    def initialize(self):
        
        UserDefinitionWidget.initialize(self)
        
        self.type = "%d_atoms_list" % self.configurator.nAtoms
        
    def on_new_user_definition(self,event):
        
        atomsListDlg = AtomsListDialog(self,self._trajectory,self.configurator.nAtoms)
        
        atomsListDlg.ShowModal()
            
        atomsListDlg.Destroy()
        
if __name__ == "__main__":
    
    from MMTK.Trajectory import Trajectory
    
    t = Trajectory(None,"../../../../../Data/Trajectories/MMTK/waterbox_in_periodic_universe.nc","r")
    
    app = wx.App(False)
                
    p = AtomsListDialog(None,t,2)
                
    p.ShowModal()
    
    p.Destroy()
    
    app.MainLoop()            
                    
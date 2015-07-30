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
from MDANSE.Framework.Widgets.UserDefinitionWidget import UserDefinitionsDialog, UserDefinitionWidget
from MDANSE.MolecularDynamics.Trajectory import find_atoms_in_molecule, get_chemical_objects_dict

class AtomNameDropTarget(wx.TextDropTarget):

    def __init__(self, molTree,atList):
        
        wx.TextDropTarget.__init__(self)
        self._molecules = molTree
        self._atoms = atList
        self._currentMolecule = None

    def OnDropText(self, x, y, data):

        listedAtoms = [self._atoms.GetItem(idx).GetText() for idx in range(self._atoms.GetItemCount())]
                
        if data in listedAtoms:
            return

        atTreeItem = self._molecules.GetSelection()
        molTreeItem = self._molecules.GetItemParent(atTreeItem)
        
        molname = self._molecules.GetItemText(molTreeItem)
        
        if self._atoms.GetItemCount() > 0:
            if (molname != self._currentMolecule):
                LOGGER("The dragged atoms does not belong to the same molecule than the current selection.",'error',['dialog'])
                return
        else:
            self._currentMolecule = molname
                
        self._atoms.Append([data])
                
class AtomsListDialog(UserDefinitionsDialog):
    
    def __init__(self, parent, trajectory, nAtoms):
        
        self._parent = parent

        self._trajectory = trajectory
    
        self._nAtoms = nAtoms
        
        self._selectedAtoms = []
        
        self._selection = []
                
        target = os.path.basename(self._trajectory.filename)

        self.type = "%d_atoms_list" % self._nAtoms
        
        UserDefinitionsDialog.__init__(self, parent, target, wx.ID_ANY, title="%d Atoms selection dialog" % nAtoms,style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER|wx.MINIMIZE_BOX|wx.MAXIMIZE_BOX)
        
        self.SetSize((400,400))
                                
    def build_dialog(self):

        panel = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        panel.SetScrollbars(20,20,50,50)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
                
        gbSizer = wx.GridBagSizer(5,5)
        
        label1 = wx.StaticText(panel, wx.ID_ANY, label="Molecules")
        label2 = wx.StaticText(panel, wx.ID_ANY, label="Selected atoms")

        gbSizer.Add(label1, (0,0), flag=wx.EXPAND)
        gbSizer.Add(label2, (0,1), flag=wx.EXPAND)
    
        self._molecules = wx.TreeCtrl(panel, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE|wx.LB_HSCROLL|wx.LB_NEEDED_SB^wx.TR_HIDE_ROOT)
        self._molecularContents = get_chemical_objects_dict(self._trajectory.universe)
        
        root = self._molecules.AddRoot('')
        
        for mname in sorted(self._molecularContents.keys()):
            molnode = self._molecules.AppendItem(root,mname)
            atomsList = self._molecularContents[mname][0].atomList()
            atomNames = sorted(set([at.name for at in atomsList]))
            for aname in atomNames:
                self._molecules.AppendItem(molnode,aname)

        self._atoms = wx.ListCtrl(panel, wx.ID_ANY, style=wx.LC_LIST)
        
        dt = AtomNameDropTarget(self._molecules,self._atoms)
        self._atoms.SetDropTarget(dt)
                
        gbSizer.Add(self._molecules, (1,0), flag=wx.EXPAND)
        gbSizer.Add(self._atoms    , (1,1), flag=wx.EXPAND)
        
        gbSizer.AddGrowableRow(1)
        gbSizer.AddGrowableCol(0)
        gbSizer.AddGrowableCol(1)

        setButton  = wx.Button(panel, wx.ID_ANY, label="Set")
        self._resultsTextCtrl  = wx.TextCtrl(panel, wx.ID_ANY, style=wx.TE_READONLY|wx.TE_MULTILINE)

        sizer.Add(gbSizer, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(setButton,0,wx.EXPAND|wx.ALL,5)
        sizer.Add(self._resultsTextCtrl,1,wx.EXPAND|wx.ALL,5)

        panel.SetSizer(sizer)

        self._mainSizer.Add(panel, 1, wx.EXPAND|wx.ALL, 5)
                
        self.Bind(wx.EVT_BUTTON, self.on_set_user_definition, setButton)
        self.Bind(wx.EVT_TREE_BEGIN_DRAG,self.on_drag_atom_name,self._molecules)
        self.Bind(wx.EVT_LIST_KEY_DOWN,self.on_delete_atom_name,self._atoms)

    def on_delete_atom_name(self,event):
        
        keycode = event.GetKeyCode()
        if keycode != wx.WXK_DELETE:
            return
        
        item = self._atoms.GetFirstSelected()        
        selectedItems = []
        while item != -1:
            selectedItems.append(item)
            item = self._atoms.GetNextSelected(item)
            
        if not selectedItems:
            return
        
        selectedItems.reverse()
        for it in selectedItems:
            self._atoms.DeleteItem(it)
            
    def on_drag_atom_name(self,event):
                        
        item = event.GetItem()
        
        parentItem = self._molecules.GetItemParent(item)
        if parentItem == self._molecules.GetRootItem():
            return            
                        
        text = self._molecules.GetItemText(item)        
        tdo = wx.TextDataObject(text)
        tds = wx.DropSource(self._molecules)
        tds.SetData(tdo)
        tds.DoDragDrop(wx.Drag_CopyOnly)                        
        
    def set_user_definition(self):

        self._selection = []

        if self._atoms.GetItemCount() != self._nAtoms:
            LOGGER('You must select %d atoms.' % self._nAtoms,'error',['dialog'])
            return

        atTreeItem = self._molecules.GetSelection()
        molTreeItem = self._molecules.GetItemParent(atTreeItem)        
        molecule = self._molecules.GetItemText(molTreeItem)        
        self._selectedAtoms = [self._atoms.GetItem(idx).GetText() for idx in range(self._atoms.GetItemCount())]
        self._selection = find_atoms_in_molecule(self._trajectory.universe,molecule, self._selectedAtoms, True)
                        
    def on_set_user_definition(self,event=None):

        self._resultsTextCtrl.Clear()
        
        self.set_user_definition()
        if not self._selection:
            return
            
        self._resultsTextCtrl.AppendText('Number of selected %d-tuplets: %d\n' % (self._nAtoms,len(self._selection)))
        for idxs in self._selection:
            line = "  ;  ".join(["Atom %5d : %s" % (v,self._selectedAtoms[i]) for i,v in enumerate(idxs)])
            self._resultsTextCtrl.AppendText(line)
            self._resultsTextCtrl.AppendText('\n')
        
    def validate(self):

        if not self._selection:
            LOGGER("The current selection is empty", "error", ["dialog"])
            return None
        
        self._ud['indexes'] = self._selection
                        
        return self._ud

class AtomListWidget(UserDefinitionWidget):
    
    type = 'atoms_list'
            
    def initialize(self):

        self.type = "%d_atoms_list" % self._configurator._nAtoms
        
        UserDefinitionWidget.initialize(self)
                
    def on_new_user_definition(self,event):
        
        atomsListDlg = AtomsListDialog(self,self._trajectory,self._configurator._nAtoms)
                
        atomsListDlg.ShowModal()
            
        atomsListDlg.Destroy()
        
if __name__ == "__main__":
    
    from MMTK.Trajectory import Trajectory
    
    from MDANSE import PLATFORM,REGISTRY
    
    LOGGER.add_handler("dialog", REGISTRY['handler']['dialog'](), level="error", start=True)
            
    t = Trajectory(None,os.path.join(os.path.dirname(PLATFORM.package_directory()),"Data","Trajectories","MMTK","nagma_in_periodic_universe.nc"),"r")
    
    app = wx.App(False)
                
    p = AtomsListDialog(None,t,10)
                
    p.ShowModal()
    
    p.Destroy()
    
    app.MainLoop()            
                    
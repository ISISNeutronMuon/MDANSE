# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/AtomsListPlugin.py
# @brief     Implements module/class/test AtomsListPlugin
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-2021
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import os

import wx

from MDANSE import LOGGER, REGISTRY
from MDANSE.GUI.Plugins.UserDefinitionPlugin import UserDefinitionPlugin
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
                
class AtomsListPlugin(UserDefinitionPlugin):
        
    label = "Atoms list"
    
    ancestor = ["molecular_viewer"]
    
    def __init__(self, parent, *args, **kwargs):
        
        self._parent = parent

        self._nAtoms = 1
            
        self._selectedAtoms = []
        
        self._selection = []
                                
        UserDefinitionPlugin.__init__(self,parent,size=(600,600))
                                                
    def build_panel(self):

        self._mainPanel = wx.ScrolledWindow(self, wx.ID_ANY, size=self.GetSize())
        self._mainPanel.SetScrollbars(20,20,50,50)
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._nAtomsSelectionSizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self._mainPanel, wx.ID_ANY, label="Number of atoms")
        
        self._nAtomsSpinCtrl = wx.SpinCtrl(self._mainPanel,wx.ID_ANY,style=wx.SP_ARROW_KEYS|wx.SP_WRAP)
        self._nAtomsSpinCtrl.SetRange(1,100)
        self._nAtomsSpinCtrl.SetValue(self._nAtoms)
        
        self._nAtomsSelectionSizer.Add(label,0,wx.ALL|wx.ALIGN_CENTRE_VERTICAL,5)
        self._nAtomsSelectionSizer.Add(self._nAtomsSpinCtrl,1,wx.ALL|wx.EXPAND,5)
                                    
        gbSizer = wx.GridBagSizer(5,5)
        
        label1 = wx.StaticText(self._mainPanel, wx.ID_ANY, label="Molecules")
        label2 = wx.StaticText(self._mainPanel, wx.ID_ANY, label="Selected atoms")

        gbSizer.Add(label1, (0,0), flag=wx.EXPAND)
        gbSizer.Add(label2, (0,1), flag=wx.EXPAND)
    
        self._molecules = wx.TreeCtrl(self._mainPanel, wx.ID_ANY, style=wx.TR_DEFAULT_STYLE|wx.TR_HIDE_ROOT)
                
        self._atoms = wx.ListCtrl(self._mainPanel, wx.ID_ANY)
        
        self._dt = AtomNameDropTarget(self._molecules,self._atoms)
        self._atoms.SetDropTarget(self._dt)
                
        gbSizer.Add(self._molecules, (1,0), flag=wx.EXPAND)
        gbSizer.Add(self._atoms    , (1,1), flag=wx.EXPAND)
        
        gbSizer.AddGrowableRow(1)
        gbSizer.AddGrowableCol(0)
        gbSizer.AddGrowableCol(1)

        self._resultsTextCtrl  = wx.TextCtrl(self._mainPanel, wx.ID_ANY, style=wx.TE_READONLY|wx.TE_MULTILINE)

        sizer.Add(self._nAtomsSelectionSizer, 0, wx.EXPAND|wx.ALL, 5)
        sizer.Add(gbSizer, 1, wx.EXPAND|wx.ALL, 5)
        sizer.Add(self._resultsTextCtrl,1,wx.EXPAND|wx.ALL,5)

        self._mainPanel.SetSizer(sizer)

        self._mainSizer = wx.BoxSizer(wx.VERTICAL)                                                                              
        self._mainSizer.Add(self._mainPanel, 1, wx.EXPAND|wx.ALL, 5)        
        self.SetSizer(self._mainSizer)            
        
        self.Bind(wx.EVT_SPINCTRL,self.on_define_list_size,self._nAtomsSpinCtrl)                
        self.Bind(wx.EVT_TREE_BEGIN_DRAG,self.on_add_atom,self._molecules)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.on_add_atom)
        self.Bind(wx.EVT_LIST_KEY_DOWN,self.on_keypress_atom,self._atoms)

    def plug(self):
        
        self.parent.mgr.GetPane(self).Float().Dockable(False).CloseButton(True).BestSize((600,600))
        
        self.parent.mgr.Update()
        
        self.set_trajectory(self.dataproxy.data)
        
    def enable_natoms_selection(self,state):
        
        self._nAtomsSelectionSizer.ShowItems(state)

    def set_natoms(self,nAtoms):
        
        self._nAtoms = nAtoms
        
        self._nAtomsSpinCtrl.SetValue(nAtoms)
                                
    def set_trajectory(self,trajectory):

        self._trajectory = trajectory 

        self._target = os.path.basename(self._trajectory.filename)
        
        self._molecularContents = get_chemical_objects_dict(self._trajectory.universe)

        root = self._molecules.AddRoot('')
        
        for mname in sorted(self._molecularContents.keys()):
            molnode = self._molecules.AppendItem(root,mname)
            atomsList = self._molecularContents[mname][0].atomList()
            atomNames = sorted(set([at.name for at in atomsList]))
            for aname in atomNames:
                self._molecules.AppendItem(molnode,aname)
        
    def on_define_list_size(self,event):

        self._nAtoms = event.GetInt()
        
        self._atoms.ClearAll()
        
        self._resultsTextCtrl.Clear()      
    
    def on_keypress_atom(self,event):
        
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_DELETE:
        
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
                
            self._selection = []
            self._resultsTextCtrl.Clear()
        
        # This is the ASCII value for Ctrl+A key
        elif keycode == 1:
            for i in range(self._atoms.GetItemCount()):
                item = self._atoms.GetItem(i)
                self._atoms.SetItemState(item.GetId(),wx.LIST_STATE_SELECTED,wx.LIST_STATE_SELECTED)
            
    def on_add_atom(self,event):
                        
        item = event.GetItem()
        
        parentItem = self._molecules.GetItemParent(item)
        if parentItem == self._molecules.GetRootItem():
            return            

        if self._atoms.GetItemCount() >= self._nAtoms:
            return
                    
        text = self._molecules.GetItemText(item)
        tdo = wx.TextDataObject(text)
        tds = wx.DropSource(self._molecules)
        tds.SetData(tdo)
        
        # Case of a drag and drop event
        if event.GetEventType() == wx.wxEVT_COMMAND_TREE_BEGIN_DRAG:
            tds.DoDragDrop(wx.Drag_CopyOnly)
        # Case of a double click event
        else:
            self._dt.OnDropText(-1,-1,text)

        if self._atoms.GetItemCount() == self._nAtoms:
            self._resultsTextCtrl.Clear()
            self._selection = []
            atTreeItem = self._molecules.GetSelection()
            molTreeItem = self._molecules.GetItemParent(atTreeItem)        
            molecule = self._molecules.GetItemText(molTreeItem)        
            self._selectedAtoms = [self._atoms.GetItem(idx).GetText() for idx in range(self._atoms.GetItemCount())]
            self._selection = find_atoms_in_molecule(self._trajectory.universe,molecule, self._selectedAtoms, True)

            self._resultsTextCtrl.AppendText('Number of selected %d-tuplets: %d\n' % (self._nAtoms,len(self._selection)))
            for idxs in self._selection:
                line = "  ;  ".join(["Atom %5d : %s" % (v,self._selectedAtoms[i]) for i,v in enumerate(idxs)])
                self._resultsTextCtrl.AppendText(line)
                self._resultsTextCtrl.AppendText('\n')
                                                
    def validate(self):

        if not self._selection:
            LOGGER("The current selection is empty", "error", ["dialog"])
            return None
                                
        return {'indexes' : self._selection, "natoms" : self._nAtoms}
    
REGISTRY["atoms_list"] = AtomsListPlugin
        

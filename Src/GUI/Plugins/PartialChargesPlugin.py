# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Plugins/PartialChargesPlugin.py
# @brief     Implements module/class/test PartialChargesPlugin
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections
import os

import wx
import wx.grid as wxgrid

from MDANSE import LOGGER, REGISTRY
from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster,Molecule,NucleotideChain,PeptideChain,Protein
from MDANSE.GUI.Plugins.UserDefinitionPlugin import UserDefinitionPlugin

class PartialChargesPlugin(UserDefinitionPlugin):

    label = "Partial charges"
    
    ancestor = ["hdf_trajectory"]

    def __init__(self, parent, *args, **kwargs):
        
        self._parent = parent
    
        self._selectedAtoms = []
                        
        UserDefinitionPlugin.__init__(self, parent,size=(600,600))
                        
    def build_panel(self):

        self._mainPanel = wx.Panel(self,wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._grid = wxgrid.Grid(self._mainPanel)

        sizer.Add(self._grid, 1, wx.ALL|wx.EXPAND, 5)

        self._mainPanel.SetSizer(sizer)
                                                
    def plug(self):
                
        self.parent.mgr.GetPane(self).Float().Dockable(False).CloseButton(True)
        
        self.parent.mgr.Update()
        
        self.set_trajectory(self.dataproxy.data)
                
        self._mgr.Update()

    def set_trajectory(self,trajectory):

        self._trajectory = trajectory 

        self._target = os.path.basename(self._trajectory.filename)

        self._contents = collections.OrderedDict()
        for at in self._trajectory.chemical_system.atom_list():
            self._contents[at.full_name()] = 0.0
            
        self._grid.CreateGrid(0,2)
        
        self._grid.SetRowLabelSize(1)
        
        self._grid.SetColFormatNumber(1)
                
        roAttr = wxgrid.GridCellAttr()
        roAttr.SetReadOnly(True)
        roAttr.SetBackgroundColour(wx.Colour(220,220,220))
        self._grid.SetColAttr(0,roAttr)
        
        floatAttr = wxgrid.GridCellAttr()
        floatAttr.SetRenderer(wxgrid.GridCellFloatRenderer())
        floatAttr.SetEditor(wxgrid.GridCellFloatEditor())
        self._grid.SetColAttr(1,floatAttr)
        
        self._grid.SetColLabelValue(0,'name')
        self._grid.SetColLabelValue(1,'charge')

        for i,(k,v) in enumerate(self._contents.items()):
            self._grid.AppendRows(1)
            self._grid.SetCellValue(i,0,k)
            self._grid.SetCellValue(i,1,str(v))
            
        self._grid.Bind(wx.EVT_SIZE, self.OnSize)
 
    def OnSize(self, event):
         
        width,_ = self._grid.GetClientSizeTuple()
        w = 4*width/5
        if w > 0:
            self._grid.SetColSize(0, w)
            self._grid.SetColSize(1, width-w-5)
        
            self._grid.ForceRefresh()
                                            
    def validate(self):
        
        charges = {}
        for i in range(self._grid.GetNumberRows()):
            name = tuple(self._grid.GetCellValue(i,0).split('.'))
            charge = self._grid.GetCellValue(i,1)
            
            val = self._contents.get(name,None)
            if val is None:
                continue
            for idx in val[1]:
                charges[idx] = float(charge)
                
        if not charges:
            LOGGER("No partial charges defined.", "error", ["dialog"])
            return None
        
        return {'charges' : charges}
    
REGISTRY["partial_charges"] = PartialChargesPlugin

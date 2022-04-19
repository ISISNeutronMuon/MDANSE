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

import os

import wx
import wx.grid as wxgrid

from MMTK import AtomCluster, Molecule
from MMTK.NucleicAcids import NucleotideChain
from MMTK.Proteins import PeptideChain, Protein

from MDANSE import LOGGER, REGISTRY
from MDANSE.GUI.Plugins.UserDefinitionPlugin import UserDefinitionPlugin

class PartialChargesPlugin(UserDefinitionPlugin):

    label = "Partial charges"
    
    ancestor = ["mmtk_trajectory"]

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

        self._contents = {}
        for obj in self._trajectory.universe.objectList():
        
            objname = obj.name
            if isinstance(obj, (PeptideChain,Protein,NucleotideChain)):
                for res in obj.residues():
                    resname = res.type.symbol.strip()
                    for at in res.atomList():
                        descr = (objname,resname,at.name)
                        d = self._contents.setdefault(descr,[0.0,[]])
                        d[1].append(at.index)
            elif isinstance(obj, (Molecule,AtomCluster)):
                for at in obj.atomList():
                    descr = (objname,at.name)
                    d = self._contents.setdefault(descr,[0.0,[]])
                    d[1].append(at.index)
            else:
                descr = (obj.name,)
                d = self._contents.setdefault(descr,[0.0,[]])
                d[1].append(obj.index)
            
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

        for i,(k,v) in enumerate(sorted(self._contents.items())):
            self._grid.AppendRows(1)
            self._grid.SetCellValue(i,0,".".join(k))
            self._grid.SetCellValue(i,1,str(v[0]))
            
        self._grid.Bind(wx.EVT_SIZE, self.OnSize)
 
    def OnSize(self, event):
         
        width,_ = self._grid.GetClientSizeTuple()
        w = 4*width/5
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

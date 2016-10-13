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
Created on Jul 2, 2015

:author: Eric C. Pellegrini
'''

import os

import wx
import wx.aui as wxaui
import wx.grid as wxgrid

from MMTK import AtomCluster, Molecule
from MMTK.NucleicAcids import NucleotideChain
from MMTK.Proteins import PeptideChain, Protein

from MDANSE import LOGGER
from MDANSE.GUI.Plugins.UserDefinitionPlugin import UserDefinitionPlugin

class PartialChargesPlugin(UserDefinitionPlugin):

    type = 'partial_charges'

    label = "Partial charges"
    
    ancestor = ["mmtk_trajectory"]

    def __init__(self, parent, *args, **kwargs):
        
        self._parent = parent
    
        self._selectedAtoms = []
                        
        UserDefinitionPlugin.__init__(self, parent)
                        
    def build_panel(self):

        self._mainPanel = wx.Panel(self,wx.ID_ANY)

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._grid = wxgrid.Grid(self._mainPanel)

        sizer.Add(self._grid, 1, wx.ALL|wx.EXPAND, 5)

        self._mainPanel.SetSizer(sizer)
                                                
        self._mgr.AddPane(self._mainPanel, wxaui.AuiPaneInfo().DestroyOnClose().Center().Dock().CaptionVisible(False).CloseButton(False).BestSize(self.GetSize()))
        self._mgr.Update()

    def plug(self):
                
        self.parent.mgr.GetPane(self).Float().Dockable(False).CloseButton(True).BestSize((600,600))
        
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
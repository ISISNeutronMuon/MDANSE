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

import operator
import os

import wx
import wx.aui as wxaui
import wx.grid as wxgrid

from MDANSE import LOGGER
from MDANSE.Framework.Widgets.UserDefinitionWidget import UDPlugin, UDDialog, UserDefinitionWidget

class PartialChargesPlugin(UDPlugin):

    type = 'partial_charges'

    label = "Partial charges settings"
    
    ancestor = ["molecular_viewer"]

    def __init__(self, parent, *args, **kwargs):
        
        self._parent = parent
    
        self._selectedAtoms = []
                        
        UDPlugin.__init__(self, parent)
                        
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

    def set_trajectory(self,trajectory):

        self._trajectory = trajectory 

        self._target = os.path.basename(self._trajectory.filename)

        self._grid.CreateGrid(self._trajectory.universe.numberOfAtoms(),3)

        self._grid.SetRowLabelSize(1)
        
        self._grid.SetColFormatNumber(0)
        self._grid.SetColFormatNumber(1)
        self._grid.SetColFormatNumber(2)
                
        roAttr = wxgrid.GridCellAttr()
        roAttr.SetReadOnly(True)
        roAttr.SetBackgroundColour(wx.Colour(220,220,220))
        self._grid.SetColAttr(0,roAttr)
        self._grid.SetColAttr(1,roAttr)
        
        floatAttr = wxgrid.GridCellAttr()
        floatAttr.SetRenderer(wxgrid.GridCellFloatRenderer())
        floatAttr.SetEditor(wxgrid.GridCellFloatEditor())
        self._grid.SetColAttr(2,floatAttr)
        
        self._grid.SetColLabelValue(0,'index')
        self._grid.SetColLabelValue(1,'name')
        self._grid.SetColLabelValue(2,'charge')

        atoms = sorted(self._trajectory.universe.atomList(), key=operator.attrgetter('index'))
        for idx, at in enumerate(atoms):
            self._grid.SetCellValue(idx,0,str(idx))
            self._grid.SetCellValue(idx,1,at.name)
        
    def validate(self):
        
        charges = {}
        for i in range(self._trajectory.universe.numberOfAtoms()):
            val = self._grid.GetCellValue(i,2)
            if val:
                charges[i] = float(val)
                
        if not charges:
            LOGGER("No partial charges defined.", "error", ["dialog"])
            return None
        
        return {'charges' : charges} 


class PartialChargesWidget(UserDefinitionWidget):
        
    type = "partial_charges"
                            
if __name__ == "__main__":
    
    from MMTK.Trajectory import Trajectory
    
    from MDANSE import PLATFORM
    
    t = Trajectory(None,os.path.join(PLATFORM.example_data_directory(),"Trajectories","MMTK","protein_in_periodic_universe.nc"),"r")
    
    app = wx.App(False)
    
    p = UDDialog(None,t,'partial_charges')
        
    p.SetSize((800,800))
            
    p.ShowModal()
    
    p.Destroy()
    
    app.MainLoop()                    
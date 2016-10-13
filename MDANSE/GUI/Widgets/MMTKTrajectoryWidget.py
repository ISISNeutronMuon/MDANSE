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
Created on Mar 30, 2015

:author: Eric C. Pellegrini
'''

import wx

from MMTK.Trajectory import Trajectory

from MDANSE.Framework.Configurable import ConfigurationError
from MDANSE.Framework.Widgets.IWidget import IWidget
from MDANSE.GUI.DataController import DATA_CONTROLLER

class MMTKTrajectoryWidget(IWidget):
    
    type = "mmtk_trajectory"
        
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._trajectory = wx.StaticText(self._widgetPanel, wx.ID_ANY)

        sizer.Add(self._trajectory, 1, wx.ALL|wx.EXPAND, 5)
                        
        return sizer
            
    def set_data(self, datakey):
                        
        data = DATA_CONTROLLER[datakey].data
        
        if not isinstance(data, Trajectory):
            return

        self._trajectory.SetLabel(datakey)
                        
    def get_widget_value(self):
        
        filename = self._trajectory.GetLabelText()
        
        if not filename:
            raise ConfigurationError("No MMTK trajectory file selected", self)
        
        return filename
# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/TrajectoryVariableWidget.py
# @brief     Implements module/class/test TrajectoryVariableWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

from MDANSE import REGISTRY

from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Widgets.IWidget import IWidget
                            
class TrajectoryVariableWidget(IWidget):
    
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.VERTICAL)

        self._variable = wx.Choice(self._widgetPanel, wx.ID_ANY, choices=[])
                
        sizer.Add(self._variable, 1, wx.ALL|wx.EXPAND, 5)
        
        return sizer
        
    def get_widget_value(self):
        
        return self._variable.GetStringSelection()

    def set_data(self, datakey):

        trajectory = DATA_CONTROLLER[datakey].data
        self._variable.SetItems([v for v in trajectory['/configuration']])
        self._variable.SetSelection(0)

REGISTRY["trajectory_variable"] = TrajectoryVariableWidget

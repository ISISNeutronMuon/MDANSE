# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/BooleanWidget.py
# @brief     Implements module/class/test BooleanWidget
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx

from MDANSE import REGISTRY
from MDANSE.GUI.Widgets.IWidget import IWidget

class BooleanWidget(IWidget):
        
    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        self._boolean = wx.CheckBox(self._widgetPanel, wx.ID_ANY, label="Yes")
        self._boolean.SetValue(self._configurator.default)

        sizer.Add(self._boolean, 1, wx.ALL|wx.EXPAND, 5)
        
        return sizer
                
    def get_widget_value(self):
                
        return self._boolean.GetValue()

REGISTRY["boolean"] = BooleanWidget

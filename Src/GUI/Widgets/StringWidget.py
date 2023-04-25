# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/StringWidget.py
# @brief     Implements module/class/test StringWidget
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

from MDANSE.GUI.Widgets.IWidget import IWidget

class StringWidget(IWidget):

    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._string = wx.TextCtrl(self._widgetPanel, wx.ID_ANY, value=self._configurator.default)

        sizer.Add(self._string, 0, wx.ALL, 5)

        return sizer
            
    def get_widget_value(self):
                
        val = self._string.GetValue()

        return val

REGISTRY["string"] = StringWidget

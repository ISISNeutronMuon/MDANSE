# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/IntegerWidget.py
# @brief     Implements module/class/test IntegerWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx
import wx.lib.intctrl as wxintctrl

from MDANSE import REGISTRY
from MDANSE.GUI.Widgets.IWidget import IWidget

class IntegerWidget(IWidget):
        
    def add_widgets(self):
        
        sizer = wx.BoxSizer(wx.VERTICAL)

        cfg = self._configurator
                
        if self._configurator.choices:
            self._integer = wx.SpinCtrl(self._widgetPanel, wx.ID_ANY, min=cfg.choices[0], max=cfg.choices[-1], initial=cfg.default, style=wx.SP_ARROW_KEYS|wx.SP_WRAP)
        else:
            self._integer = wxintctrl.IntCtrl(self._widgetPanel, wx.ID_ANY, value=cfg.default, min=cfg.mini, max=cfg.maxi, limited=True, allow_none=False, style=wx.ALIGN_RIGHT)
        
        sizer.Add(self._integer, 0, wx.ALL, 5)
        
        return sizer
                        
    def get_widget_value(self):
                
        val = self._integer.GetValue()

        return val

REGISTRY["integer"] = IntegerWidget

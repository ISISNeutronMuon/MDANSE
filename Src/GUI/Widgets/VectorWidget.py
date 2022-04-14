# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/VectorWidget.py
# @brief     Implements module/class/test VectorWidget
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
from MDANSE.Framework.Configurable import ConfigurationError

from MDANSE.GUI.Widgets.IWidget import IWidget
    
class VectorWidget(IWidget):
        
    def add_widgets(self):

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        gbSizer = wx.GridBagSizer(5,5)
        
        xLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="x-component")
        yLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="y-component")
        zLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="z-component")

        self._x = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
        self._y = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
        self._z = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
            
        cfg = self._configurator

        self._x.SetValue(str(cfg.default[0]))
        self._y.SetValue(str(cfg.default[1]))
        self._z.SetValue(str(cfg.default[2]))

        gbSizer.Add(xLabel, (0,0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(yLabel, (0,3), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(zLabel,  (0,6), flag=wx.ALIGN_CENTER_VERTICAL)

        gbSizer.Add(self._x, (0,1), flag=wx.EXPAND)
        gbSizer.Add(self._y,  (0,4), flag=wx.EXPAND)
        gbSizer.Add(self._z,  (0,7), flag=wx.EXPAND)

        sizer.Add(gbSizer, 1, wx.ALL|wx.EXPAND, 5)

        return sizer      
    
    def get_widget_value(self):
        
        try:
            
            val = (self._configurator.valueType(self._x.GetValue()),
                   self._configurator.valueType(self._y.GetValue()),
                   self._configurator.valueType(self._z.GetValue()))
        except ValueError:
            raise ConfigurationError("Invalid value for %r entry" % self.name)
        else:        
            return val

REGISTRY["vector"] = VectorWidget

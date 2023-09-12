# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/RangeWidget.py
# @brief     Implements module/class/test RangeWidget
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
from MDANSE.Framework.Configurable import ConfigurationError

from MDANSE.GUI.Widgets.IWidget import IWidget


class RangeWidget(IWidget):
    def add_widgets(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        gbSizer = wx.GridBagSizer(5, 5)

        firstLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="from")
        labelLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="to")
        stepLabel = wx.StaticText(self._widgetPanel, wx.ID_ANY, label="by step of")

        self._first = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
        self._last = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)
        self._step = wx.TextCtrl(self._widgetPanel, wx.ID_ANY)

        first, last, step = self._configurator.default

        self._first.SetValue(str(first))
        self._last.SetValue(str(last))
        self._step.SetValue(str(step))

        gbSizer.Add(firstLabel, (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(labelLabel, (0, 3), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(stepLabel, (0, 6), flag=wx.ALIGN_CENTER_VERTICAL)

        gbSizer.Add(self._first, (0, 1), flag=wx.EXPAND)
        gbSizer.Add(self._last, (0, 4), flag=wx.EXPAND)
        gbSizer.Add(self._step, (0, 7), flag=wx.EXPAND)

        sizer.Add(gbSizer, 1, wx.ALL | wx.EXPAND, 5)

        return sizer

    def get_widget_value(self):
        try:
            val = (
                self._configurator.valueType(self._first.GetValue()),
                self._configurator.valueType(self._last.GetValue()),
                self._configurator.valueType(self._step.GetValue()),
            )
        except ValueError:
            raise ConfigurationError("Invalid value for %r entry" % self.name)
        else:
            return val


REGISTRY["range"] = RangeWidget

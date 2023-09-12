# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/McStasParametersWidget.py
# @brief     Implements module/class/test McStasParametersWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import collections

import wx

from MDANSE import REGISTRY
from MDANSE.Framework.Configurable import ConfigurationError
from MDANSE.Framework.Configurable import Configurable

from MDANSE.GUI import PUBLISHER
from MDANSE.GUI.ComboWidgets.ConfigurationPanel import ConfigurationPanel
from MDANSE.GUI.Widgets.IWidget import IWidget


class McStasParametersWidget(IWidget):
    _mcStasTypes = {"double": "float", "int": "integer", "string": "input_file"}

    def initialize(self):
        self._configurationPanel = None

    def add_widgets(self):
        self._sizer = wx.BoxSizer(wx.VERTICAL)

        PUBLISHER.subscribe(self.msg_set_instrument, "msg_set_instrument")

        return self._sizer

    def OnDestroy(self, event):
        PUBLISHER.unsubscribe(self.msg_set_instrument, "msg_set_instrument")

        IWidget.OnDestroy(self, event)

    def msg_set_instrument(self, message):
        widget, parameters = message

        if not widget.Parent == self.Parent:
            return

        for k in self._configurator.exclude:
            parameters.pop(k)

        self._parameters = Configurable()

        settings = collections.OrderedDict()
        for name, value in list(parameters.items()):
            typ, default = value
            settings[name] = (self._mcStasTypes[typ], {"default": default})

        self._parameters.set_settings(settings)

        self._sizer.Clear(deleteWindows=True)

        self._widgetPanel.Freeze()
        self._configurationPanel = ConfigurationPanel(
            self._widgetPanel, self._parameters, None
        )

        for name, value in list(parameters.items()):
            typ, default = value
            if typ == "string":
                self._configurationPanel.widgets[name]._browser.SetLabel(
                    "Text/File Entry"
                )

        self._sizer.Add(self._configurationPanel, 1, wx.ALL | wx.EXPAND, 5)

        self._widgetPanel.Thaw()

        self.Parent.Layout()

        # Trick to show the scrollbar after updating the configuration panel.
        self.Parent.Parent.SendSizeEvent()

    def get_widget_value(self):
        if self._configurationPanel is None:
            raise ConfigurationError("McStas instrument is not yet defined")

        val = self._configurationPanel.get_value()

        return val


REGISTRY["mcstas_parameters"] = McStasParametersWidget

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/RunningModeWidget.py
# @brief     Implements module/class/test RunningModeWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import multiprocessing

import wx

from MDANSE import REGISTRY

from MDANSE.GUI.Widgets.IWidget import IWidget


class RunningModeWidget(IWidget):
    def initialize(self):
        self._totalNumberOfProcessors = multiprocessing.cpu_count()

    def add_widgets(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        panel = wx.Panel(self._widgetPanel, wx.ID_ANY, style=wx.BORDER_SUNKEN)

        gbSizer = wx.GridBagSizer(5, 5)

        self._radiobuttons = []
        self._radiobuttons.append(
            wx.RadioButton(
                panel,
                wx.ID_ANY,
                label="monoprocessor",
                style=wx.RB_GROUP,
                name="monoprocessor",
            )
        )
        self._radiobuttons.append(
            wx.RadioButton(
                panel, wx.ID_ANY, label="multiprocessor", name="multiprocessor"
            )
        )
        self._radiobuttons[0].SetValue(True)

        self._processors = wx.SpinCtrl(
            panel,
            wx.ID_ANY,
            initial=1,
            min=1,
            max=multiprocessing.cpu_count(),
            style=wx.SP_WRAP | wx.SP_ARROW_KEYS,
        )
        self._processors.Enable(False)

        gbSizer.Add(self._radiobuttons[0], (0, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self._radiobuttons[1], (1, 0), flag=wx.ALIGN_CENTER_VERTICAL)
        gbSizer.Add(self._processors, (1, 1))

        panel.SetSizer(gbSizer)

        sizer.Add(panel, 1, wx.ALL | wx.EXPAND, 5)

        for rb in self._radiobuttons:
            rb.Bind(wx.EVT_RADIOBUTTON, self.on_select_running_mode)

        return sizer

    def get_widget_value(self):
        name = [rb for rb in self._radiobuttons if rb.GetValue()][0].GetName()

        if name == "monoprocessor":
            value = ("monoprocessor",)

        elif name == "multiprocessor":
            value = ("multiprocessor", self._processors.GetValue())

        return value

    def on_select_running_mode(self, event):
        btn = event.GetEventObject()

        name = btn.GetName()

        self._processors.Enable(name == "multiprocessor")


REGISTRY["running_mode"] = RunningModeWidget

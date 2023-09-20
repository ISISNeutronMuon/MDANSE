# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/MultipleChoicesWidget.py
# @brief     Implements module/class/test MultipleChoicesWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx.combo

from MDANSE import REGISTRY
from MDANSE.GUI.ComboWidgets.ComboCheckbox import ComboCheckbox
from MDANSE.GUI.Widgets.IWidget import IWidget


class MultipleChoicesWidget(IWidget):
    def add_widgets(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        cfg = self._configurator

        self._choices = wx.combo.ComboCtrl(
            self._widgetPanel, value=cfg.label, style=wx.CB_READONLY
        )
        tcp = ComboCheckbox(cfg.choices, cfg.nChoices)
        self._choices.SetPopupControl(tcp)
        tcp.checklistbox.SetCheckedStrings(cfg.default)

        sizer.Add(self._choices, 1, wx.ALL | wx.EXPAND, 5)

        return sizer

    def get_widget_value(self):
        return self._choices.GetStringSelection()


REGISTRY["multiple_choices"] = MultipleChoicesWidget

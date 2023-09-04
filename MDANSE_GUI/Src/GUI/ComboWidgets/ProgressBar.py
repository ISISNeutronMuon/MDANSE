# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/ComboWidgets/ProgressBar.py
# @brief     Implements module/class/test ProgressBar
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import wx
import wx.lib.agw.pygauge as pygauge

from MDANSE.Framework.Status import Status
from MDANSE.GUI.Icons import ICONS


class ProgressBar(wx.Panel, Status):
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        Status.__init__(self)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._progress = pygauge.PyGauge(self, wx.ID_ANY)
        self._stop = wx.BitmapButton(self, wx.ID_ANY, ICONS["stop", 24, 24])

        sizer.Add(self._progress, 1, wx.ALL | wx.EXPAND, 5)
        sizer.Add(self._stop, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(sizer)

        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.on_stop, self._stop)

    def finish_status(self):
        self._progress.SetBarColor(wx.BLUE)
        self._progress.Refresh()
        self._stop.Disable()

    def on_stop(self, event):
        d = wx.MessageDialog(
            None,
            "This will stop the current task. Do you really want to stop it ?",
            "Question",
            wx.YES_NO | wx.YES_DEFAULT | wx.ICON_WARNING,
        )

        if d.ShowModal() == wx.ID_NO:
            return

        self._stop.Disable()
        self.stop()

    def start_status(self):
        self._stop.Enable()
        self._progress.SetValue(0)
        self._progress.SetRange(self.nSteps)
        self._progress.SetBarColor(wx.GREEN)

    def stop_status(self):
        self._progress.SetBarColor(wx.RED)
        self._progress.Refresh()

    def update_status(self):
        self._progress.SetValue(self.currentStep)
        self._progress.Refresh()

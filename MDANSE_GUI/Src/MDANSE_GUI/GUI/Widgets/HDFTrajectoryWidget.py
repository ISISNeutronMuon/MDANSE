# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/GUI/Widgets/HDFTrajectoryWidget.py
# @brief     Implements module/class/test HDFTrajectoryWidget
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
from MDANSE.MolecularDynamics.Trajectory import Trajectory

from MDANSE.GUI.DataController import DATA_CONTROLLER
from MDANSE.GUI.Widgets.IWidget import IWidget


class HDFTrajectoryWidget(IWidget):
    def add_widgets(self):
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._trajectory = wx.StaticText(self._widgetPanel, wx.ID_ANY)

        sizer.Add(self._trajectory, 1, wx.ALL | wx.EXPAND, 5)

        return sizer

    def set_data(self, datakey):
        data = DATA_CONTROLLER[datakey].data

        if not isinstance(data, Trajectory):
            return

        self._trajectory.SetLabel(datakey)

    def get_widget_value(self):
        filename = self._trajectory.GetLabelText()

        if not filename:
            raise ConfigurationError("No trajectory file selected", self)

        return filename


REGISTRY["hdf_trajectory"] = HDFTrajectoryWidget

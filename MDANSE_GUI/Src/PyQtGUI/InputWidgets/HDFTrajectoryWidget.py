# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/HDFTrajectoryWidget.py
# @brief     Implements module/class/test HDFTrajectoryWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QLineEdit, QSpinBox, QLabel
from qtpy.QtCore import Slot, Signal
from qtpy.QtGui import QIntValidator

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE_GUI.PyQtGUI.InputWidgets.WidgetBase import WidgetBase


class HDFTrajectoryWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        source_object = kwargs.get("source_object", None)
        try:
            filename = source_object.filename
        except AttributeError:
            filename = None
        if filename is not None:
            trajectory = HDFTrajectoryInputData(filename)
            self._layout.addWidget(QLabel(filename, self._base))
            self._configurator.configure(filename)
        else:
            self._layout.addWidget(QLabel("No Trajectory available", self._base))
        self._trajectory = trajectory

    def get_value(self):
        return self._configurator["value"]

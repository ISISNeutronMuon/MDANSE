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
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class DummyWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        source_object = kwargs.get("source_object", None)
        self._layout.addWidget(QLabel("content is missing here", self._base))
        self._configurator = {"value": "Oops!"}
        self.default_labels()
        self.update_labels()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "DummyWidget"
        if self._tooltip == "":
            self._tooltip = "A placeholder which tells us that a real widget is missing"

    def get_value(self):
        return self._configurator["value"]

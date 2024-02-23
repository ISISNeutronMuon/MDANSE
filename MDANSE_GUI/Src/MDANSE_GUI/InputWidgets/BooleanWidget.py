# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/BooleanWidget.py
# @brief     Implements module/class/test BooleanWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QCheckBox
from qtpy.QtCore import Slot, Qt

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class BooleanWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_option = self._configurator.default
        field = QCheckBox(self._base)
        field.setTristate(False)
        field.setChecked(default_option)
        field.stateChanged.connect(self.updateValue)
        field.setToolTip(self._tooltip)
        self._field = field
        self._layout.addWidget(field)
        self.default_labels()
        self.update_labels()
        self.updateValue()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "BooleanWidget"
        if self._tooltip == "":
            self._tooltip = "A single logical value that can be True of False"

    def configure_using_default(self):
        """No need to anything for Boolean"""

    def get_widget_value(self):
        return self._field.checkState() == Qt.CheckState.Checked

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/StringWidget.py
# @brief     Implements module/class/test StringWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QLineEdit
from qtpy.QtCore import Slot

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class StringWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_option = self._configurator.default
        field = QLineEdit(self._base)
        field.setText(default_option)
        field.setPlaceholderText(default_option)
        field.textChanged.connect(self.updateValue)
        field.setToolTip(self._tooltip)
        self._field = field
        self._default_value = default_option
        self._layout.addWidget(field)
        self.default_labels()
        self.update_labels()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "StringWidget"
        if self._tooltip == "":
            self._tooltip = "A text string variable. Do you know what to type in?"

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        strval = self._field.text().strip()
        if len(strval) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return strval

    def configure_using_default(self):
        default = self._configurator.default
        self._field.setPlaceholderText(default)
        self._configurator.configure(default)

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/BackupWidget.py
# @brief     BackupWidget is used when a specialised widget is missing
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from icecream import ic
from qtpy.QtWidgets import QLineEdit
from qtpy.QtCore import Slot, Signal

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class BackupWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        source_object = kwargs.get("source_object", None)
        self.field = QLineEdit(str(self._configurator.default))
        self._layout.addWidget(self.field)

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        temp_text = self.field.text().strip()
        if temp_text == "None" or temp_text == "":
            result = None
        else:
            result = temp_text
        return result

    @Slot()
    def updateValue(self):
        current_value = self.get_widget_value()
        self._configurator.configure(current_value)

    def get_value(self):
        self.updateValue()
        return self._configurator["value"]
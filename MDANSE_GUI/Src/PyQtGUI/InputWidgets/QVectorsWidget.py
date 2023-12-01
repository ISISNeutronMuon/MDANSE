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

from qtpy.QtWidgets import QLineEdit, QLabel
from qtpy.QtCore import Slot, Signal
from qtpy.QtGui import QIntValidator

from MDANSE_GUI.PyQtGUI.InputWidgets.WidgetBase import WidgetBase


class QVectorsWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        source_object = kwargs.get("source_object", None)
        self.field = QLineEdit(str(self._configurator.default))
        self._layout.addWidget(self.field)

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        oneline = self.field.text()
        oneline = oneline.strip(" ()")
        toks = oneline.split(",")
        qvector_type = toks[0].strip("'\"")
        param_dictionary = ",".join(toks[1:]).strip(" \{\}")
        newtoks = param_dictionary.split(":")
        keys, values = [], []
        keys.append(newtoks[0])
        for part in newtoks[1:]:
            toks = part.split(",")
            keys.append(toks[-1])
            values.append(",".join(toks[:-1]))
        values.append(newtoks[-1])
        pardict = {keys[x].strip("'\""): values[x] for x in range(len(keys))}
        return (qvector_type, pardict)

    @Slot()
    def updateValue(self):
        current_value = self.get_widget_value()
        self._configurator.configure(current_value)

    def get_value(self):
        self.updateValue()
        return self._configurator["value"]

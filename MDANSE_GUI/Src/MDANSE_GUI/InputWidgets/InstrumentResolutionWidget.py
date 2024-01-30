# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/InstrumentResolutionWidget.py
# @brief     Implements module/class/test InstrumentResolutionWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


from qtpy.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QComboBox,
)
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QDoubleValidator

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


init_parameters = {
    "ideal": {},
    "Gaussian": {"mu": 0.0, "sigma": 1.0},
    "Lorentzian": {"mu": 0.0, "sigma": 1.0},
    "triangular": {"mu": 0.0, "sigma": 1.0},
    "square": {"mu": 0.0, "sigma": 1.0},
    "pseudo-Voigt": {
        "mu_gaussian": 0.0,
        "sigma_gaussian": 1.0,
        "eta": 0.5,
        "mu_lorentzian": 0.0,
        "sigma_lorentzian": 1.0,
    },
}


class InstrumentResolutionWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        kwargs["layout_type"] = "QGridLayout"
        super().__init__(*args, **kwargs)
        self._layout.addWidget(QLabel("Resolution function", self._base), 0, 0)
        self._type_combo = QComboBox(parent=self._base)
        self._layout.addWidget(self._type_combo, 0, 1)
        self._labels = []
        self._fields = []
        # first row
        for num in range(1, 3):
            label = QLabel("", parent=self._base)
            field = QLineEdit("0.0", parent=self._base)
            field.setEnabled(False)
            self._layout.addWidget(label, 0, 2 * num)
            self._layout.addWidget(field, 0, 2 * num + 1)
            self._labels.append(label)
            self._fields.append(field)
            val = QDoubleValidator(field)
            field.setValidator(val)
        # first row
        for num in range(0, 3):
            label = QLabel("", parent=self._base)
            field = QLineEdit("0.0", parent=self._base)
            field.setEnabled(False)
            self._layout.addWidget(label, 1, 2 * num)
            self._layout.addWidget(field, 1, 2 * num + 1)
            self._labels.append(label)
            self._fields.append(field)
            val = QDoubleValidator(field)
            if num == 0:  # this is the pseudoVoigt eta
                val.setBottom(0.0)
                val.setTop(1.0)
            field.setValidator(val)
        self._type_combo.addItems([str(x) for x in init_parameters.keys()])
        self._type_combo.setEditable(False)
        self._type_combo.currentTextChanged.connect(self.change_function)

    @Slot(str)
    def change_function(self, function: str):
        new_params = init_parameters[function]
        np = list(new_params.items())
        for index in range(5):
            try:
                kv = np[index]
                self._fields[index].setEnabled(True)
                self._labels[index].setText(str(kv[0]))
                self._fields[index].setText(str(kv[1]))
            except IndexError:
                self._labels[index].setText("")
                self._fields[index].setText("")
                self._fields[index].setEnabled(False)

    def get_widget_value(self):
        function = self._type_combo.currentText()
        params = {}
        for index in range(5):
            key = self._labels[index].text()
            if len(key) > 0:
                value = float(self._fields[index].text())
                params[key] = value
        return (function, params)

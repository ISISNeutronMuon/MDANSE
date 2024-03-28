#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#


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


widget_text_map = {
    "ideal": "ideal",
    "Gaussian": "gaussian",
    "Lorentzian": "lorentzian",
    "triangular": "triangular",
    "square": "square",
    "pseudo-Voigt": "pseudovoigt",
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
        self._defaults = []
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The peak function used for smearing/smooting the results. Pick 'ideal' for no smearing."
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
            self._defaults.append(0.0)
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
            self._defaults.append(0.0)
        self._type_combo.addItems([str(x) for x in init_parameters.keys()])
        self._type_combo.setEditable(False)
        self._type_combo.currentTextChanged.connect(self.change_function)
        for field in self._fields:
            field.textChanged.connect(self.updateValue)
            field.setToolTip(tooltip_text)
        self.updateValue()

    def configure_using_default(self):
        """This is too complex to have a default value"""

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
                self._fields[index].setPlaceholderText(str(kv[1]))
                self._defaults[index] = float(kv[1])
            except IndexError:
                self._labels[index].setText("")
                self._fields[index].setText("")
                self._fields[index].setPlaceholderText("N/A")
                self._fields[index].setEnabled(False)
                self._defaults[index] = 0.0

    def get_widget_value(self):
        function = widget_text_map[self._type_combo.currentText()]
        params = {}
        for index in range(5):
            key = self._labels[index].text()
            if len(key) > 0:
                try:
                    value = float(self._fields[index].text())
                except ValueError:
                    value = self._defaults[index]
                    self._fields[index].setStyleSheet(
                        "background-color:rgb(180,20,180); font-weight: bold"
                    )
                else:
                    self._fields[index].setStyleSheet("")
                params[key] = value
        return (function, params)

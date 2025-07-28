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
from __future__ import annotations

from qtpy.QtCore import Slot
from qtpy.QtGui import QDoubleValidator
from qtpy.QtWidgets import (
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
)

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Widgets.ResolutionDialog import ResolutionDialog
from MDANSE_GUI.Widgets.ResolutionWidget import widget_text_map

reverse_text_map = {value: key for key, value in widget_text_map.items()}


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
        # self._layout.addWidget(QLabel("Resolution function", self._base), 0, 0)
        self._type_combo = QComboBox(parent=self._base)
        self._dialog_button = QPushButton("Helper Dialog", self._base)
        self._dialog_button.clicked.connect(self.helper_dialog)
        self._dialog_button.setEnabled(True)
        self.helper = ResolutionDialog(self._base)
        self.helper._panel.parameters_changed.connect(self.set_parameters_from_dialog)
        self._layout.addWidget(self._type_combo, 0, 1)
        self._layout.addWidget(self._dialog_button, 0, 0)
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
            field = QLineEdit("N/A", parent=self._base)
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
            field = QLineEdit("N/A", parent=self._base)
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

    def set_field_values(self, new_params: dict):
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

    @Slot(str)
    def change_function(self, function: str, optional_parameters: dict = None):
        # need to disconnect textChanged otherwise updateValue will
        # be called multiple times as the field data will be changed
        # during the function change
        [field.textChanged.disconnect() for field in self._fields]
        if optional_parameters is None:
            if function in init_parameters.keys():
                new_params = init_parameters[function]
            else:
                new_params = init_parameters[widget_text_map[function]]
        else:
            new_params = optional_parameters
        self._type_combo.blockSignals(True)
        if function in widget_text_map.keys():
            self._type_combo.setCurrentText(widget_text_map[function])
        elif function in reverse_text_map.keys():
            self._type_combo.setCurrentText(reverse_text_map[function])
        else:
            self._type_combo.setCurrentText(function)
        self._type_combo.blockSignals(False)
        self.set_field_values(new_params)
        self.updateValue()
        [field.textChanged.connect(self.updateValue) for field in self._fields]

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
                else:
                    self._fields[index].setStyleSheet("")
                params[key] = value
        self.helper._panel.update_fields((function, params))
        return (function, params)

    @Slot(dict)
    def set_parameters_from_dialog(self, input: dict):
        peak_function = input.get("function", None)
        if peak_function is None:
            return
        self._type_combo.setCurrentText(peak_function)
        temp_parameters = init_parameters[peak_function]
        for key in temp_parameters.keys():
            temp_parameters[key] = input.get(key, 0.0)
        self.set_field_values(temp_parameters)

    @Slot()
    def helper_dialog(self):
        if self.helper.isVisible():
            geometry = self.helper.saveGeometry()
            self.helper.previous_geometry = geometry
            self.helper.close()
        else:
            if hasattr(self.helper, "previous_geometry"):
                self.helper.restoreGeometry(self.helper.previous_geometry)
            self.helper.show()

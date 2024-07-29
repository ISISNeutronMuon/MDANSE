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
from typing import Optional

import numpy as np
from qtpy.QtWidgets import (
    QPushButton,
    QFileDialog,
    QLabel,
    QWidget,
    QLineEdit,
    QComboBox,
    QGridLayout,
    QTextEdit,
)
from qtpy.QtCore import Signal, Slot

from MDANSE.MLogging import LOG
from MDANSE.Framework.Jobs.IJob import IJob


class SimpleInstrument:

    sample_options = ["isotropic", "crystal"]
    technique_options = ["QENS", "INS"]
    resolution_options = ["Gaussian", "Lorentzian", "ideal"]
    energy_units = ["meV", "1/cm", "THz"]
    momentum_units = ["1/ang", "1/nm", "1/Bohr"]

    def __init__(self) -> None:
        self._name = "Generic neutron instrument"
        self._sample = "isotropic"
        self._technique = "QENS"
        self._resolution_type = "Gaussian"
        self._resolution_fwhm = 0.1
        self._resolution_unit = "meV"
        self._q_min = 0.1
        self._q_max = 10.0
        self._q_unit = "1/ang"

    @classmethod
    def inputs(cls):
        input_list = [
            ["_sample", "QComboBox", "sample_options"],
            ["_technique", "QComboBox", "technique_options"],
            ["_resolution_type", "QComboBox", "resolution_options"],
            ["_resolution_fwhm", "QLineEdit", "float"],
            ["_resolution_unit", "QComboBox", "energy_units"],
            ["_q_min", "QLineEdit", "float"],
            ["_q_max", "QLineEdit", "float"],
            ["_q_unit", "QComboBox", "momentum_units"],
        ]
        return input_list

    def create_resolution_params(self):
        pass

    def create_q_vector_params(self):
        pass


class InstrumentDetails(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QGridLayout(self))
        self._widgets = {}
        self._values = {}
        self._current_instrument = None
        self.populate_panel(SimpleInstrument)

    def create_widget(self, entry):
        layout = self.layout()
        next_row = layout.rowCount()
        attribute = entry[0]
        widget = entry[1]
        value = entry[2]
        label = attribute.strip(" _")
        if widget == "QComboBox":
            instance = QComboBox(self)
            instance.addItems(getattr(SimpleInstrument, value))
            instance.currentTextChanged.connect(self.update_values)
        elif widget == "QLineEdit":
            instance = QLineEdit(self)
            instance.setText("0")
            instance.textChanged.connect(self.update_values)
        qlabel = QLabel(label, self)
        layout.addWidget(qlabel, next_row, 0)
        layout.addWidget(instance, next_row, 1)
        self._widgets[attribute] = instance

    @Slot()
    def update_values(self):
        for key, value in self._widgets.items():
            try:
                new_val = value.text()
            except AttributeError:
                try:
                    new_val = value.currentText()
                except AttributeError:
                    new_val = None
            self._values[key] = new_val
        self.commit_changes()

    def commit_changes(self):
        if self._current_instrument is None:
            return
        for key, value in self._values.items():
            setattr(self._current_instrument, key, value)

    def populate_panel(self, instrument: SimpleInstrument):
        for entry in instrument.inputs():
            self.create_widget(entry)

    @Slot(object)
    def update_panel(self, instrument_instance):
        self._values = {}
        self._current_instrument = None
        for key, widget in self._widgets.items():
            new_value = getattr(instrument_instance, key, "Nothing!")
            try:
                widget.setText(str(new_value))
            except AttributeError:
                try:
                    widget.setCurrentText(str(new_value))
                except Exception as e:
                    LOG.error(f"In InstrumentDetails: {e}")
        self._current_instrument = instrument_instance
        self.update_values()

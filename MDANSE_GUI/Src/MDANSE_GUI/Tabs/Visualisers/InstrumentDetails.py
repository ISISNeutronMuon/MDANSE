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

from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QDoubleValidator, QIntValidator
from qtpy.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QWidget,
)

from MDANSE.MLogging import LOG
from MDANSE_GUI.Tabs.Visualisers.InstrumentInfo import InstrumentInfo, SimpleInstrument
from MDANSE_GUI.Widgets.VectorWidget import VectorWidget


class InstrumentDetails(QWidget):
    instrument_details_changed = Signal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QGridLayout(self))
        self._widgets = {}
        self._values = {}
        self._current_instrument = None
        self.populate_panel(SimpleInstrument)
        self.add_visualiser()
        for attr in ["_sample", "_technique"]:
            self._widgets[attr].currentTextChanged.connect(self.reset_qvector_combobox)

    def add_visualiser(self):
        layout = self.layout()
        next_row = layout.rowCount()
        self._inner_visualiser = InstrumentInfo(self)
        layout.addWidget(self._inner_visualiser, next_row, 0, 1, 2)

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
            if value == "float":
                instance.setValidator(QDoubleValidator())
                instance.setText("1.0")
                instance.setPlaceholderText("1.0")
            elif value == "int":
                instance.setValidator(QIntValidator())
                instance.setText("1")
                instance.setPlaceholderText("1")
            else:
                instance.setText("text")
            instance.textChanged.connect(self.update_values)
        elif widget == "VectorWidget":
            instance = VectorWidget(self)
            instance.set_value([0, 0, 0])
            instance.value_changed.connect(self.update_values)
        qlabel = QLabel(label, self)
        layout.addWidget(qlabel, next_row, 0)
        layout.addWidget(instance, next_row, 1)
        self._widgets[attribute] = instance
        for widg in self._widgets.values():
            widg.setEnabled(False)

    @Slot()
    def reset_qvector_combobox(self):
        if self._current_instrument is None:
            return
        qvec_combo = self._widgets["_qvector_type"]
        last_option = qvec_combo.currentText()
        new_options = self._current_instrument.filter_qvector_generator()
        qvec_combo.clear()
        if len(new_options) == 0:
            return
        qvec_combo.addItems(new_options)
        if last_option in new_options:
            qvec_combo.setCurrentText(last_option)
        else:
            qvec_combo.setCurrentText(new_options[0])

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
            if len(new_val) == 0:
                try:
                    new_val = value.placeholderText()
                except AttributeError:
                    new_val = ""
            self._values[key] = new_val
        self.commit_changes()
        self.toggle_axis_fields()

    def commit_changes(self):
        if self._current_instrument is None:
            return
        for key, value in self._values.items():
            setattr(self._current_instrument, key, value)
        self._current_instrument._configured = True
        self._current_instrument.update_item()
        self._inner_visualiser.update_panel(self._current_instrument)
        self.instrument_details_changed.emit(self._current_instrument._model_index)

    def populate_panel(self, instrument: SimpleInstrument):
        for entry in instrument.inputs():
            self.create_widget(entry)

    def toggle_axis_fields(self):
        if self._current_instrument is None:
            return
        for name, widget in self._widgets.items():
            if "axis_1" in name:
                if not (
                    "Linear" in self._current_instrument._qvector_type
                    or "Circular" in self._current_instrument._qvector_type
                ):
                    widget.setEnabled(False)
                else:
                    widget.setEnabled(True)
            if "axis_2" in name:
                if "Circular" not in self._current_instrument._qvector_type:
                    widget.setEnabled(False)
                else:
                    widget.setEnabled(True)

    def clear_panel(self):
        for widget in self._widgets.values():
            widget.setEnabled(False)

    @Slot(object)
    def update_panel(self, instrument_instance):
        if instrument_instance is None:
            self._current_instrument = None
            self.clear_panel()
            return
        for widg in self._widgets.values():
            widg.setEnabled(True)
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
        self.reset_qvector_combobox()
        if instrument_instance._name_is_fixed:
            self._widgets["_name"].setEnabled(False)
        else:
            self._widgets["_name"].setEnabled(True)

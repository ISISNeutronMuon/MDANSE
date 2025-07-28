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

from qtpy.QtCore import Qt, Signal, Slot
from qtpy.QtGui import QBrush, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import QComboBox, QSizePolicy, QTableView

from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class VectorModel(QStandardItemModel):
    type_changed = Signal()
    input_is_valid = Signal(bool)

    def __init__(self, *args, trajectory=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._generator = None
        self._defaults = []
        self._trajectory = trajectory

    @Slot(str)
    def switch_qvector_type(self, vector_type: str, optional_settings: dict = None):
        self.clear()
        self._defaults = []
        self._generator = IQVectors.create(
            vector_type, self._trajectory.configuration(0)
        )
        settings = self._generator.settings
        for kv in settings.items():
            name = kv[0]  # dictionary key
            if optional_settings is None:
                value = kv[1][1]["default"]  # tuple value 1: dictionary
            else:
                try:
                    value = optional_settings[name]
                except KeyError:
                    value = kv[1][1]["default"]  # tuple value 1: dictionary
            self._defaults.append(value)
            vtype = kv[1][0]  # tuple value 0: type
            items = [QStandardItem(str(x)) for x in [name, value, vtype]]
            for it in items[0::2]:
                it.setEditable(False)
            for it in items[1::2]:
                it.setData(value, role=Qt.ItemDataRole.ToolTipRole)
            self.appendRow(items)
        self.type_changed.emit()

    def params_summary(self) -> dict:
        params = {}
        all_inputs_are_valid = True
        for rownum in range(self.rowCount()):
            name = str(self.item(rownum, 0).text())
            value = str(self.item(rownum, 1).text())
            vtype = str(self.item(rownum, 2).text())
            try:
                params[name] = self.parse_vtype(vtype, value, name)
            except ValueError:
                params[name] = "failed"
            if params[name] == "failed":
                self.item(rownum, 1).setData(
                    QBrush(Qt.GlobalColor.red), role=Qt.ItemDataRole.BackgroundRole
                )
                all_inputs_are_valid = False
            else:
                self.item(rownum, 1).setData(0, role=Qt.ItemDataRole.BackgroundRole)
        self.input_is_valid.emit(all_inputs_are_valid)
        return params

    def parse_vtype(self, vtype: str, value: str, vname: str):
        if vtype == "RangeConfigurator":
            inner_type = self._generator.settings[vname][1]["valueType"]
            tempstring = value.strip("()[] ")
            result = [inner_type(x) for x in tempstring.split(",")]
            if len(result) == 3:
                return result
        elif vtype == "VectorConfigurator":
            inner_type = self._generator.settings[vname][1]["valueType"]
            tempstring = value.strip("()[] ")
            result = [inner_type(x) for x in tempstring.split(",")]
            if len(result) == 3:
                return result
        elif vtype == "FloatConfigurator":
            return float(value)
        elif vtype == "IntegerConfigurator":
            return int(value)
        else:
            return value

        return "failed"


class QVectorsWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        kwargs["layout_type"] = "QVBoxLayout"
        super().__init__(*args, **kwargs)
        self._relative_size = 3
        trajectory_configurator = kwargs.get("trajectory_configurator", None)
        trajectory = None
        if trajectory_configurator is not None:
            trajectory = trajectory_configurator["instance"]
        self._selector = QComboBox(self._base)
        self._selector.addItems(IQVectors.indirect_subclasses())
        self._model = VectorModel(self._base, trajectory=trajectory)
        self._view = QTableView(self._base)
        self._layout.addWidget(self._selector)
        self._layout.addWidget(self._view)
        self._view.setModel(self._model)
        self._selector.currentTextChanged.connect(self._model.switch_qvector_type)
        self._selector.setCurrentIndex(1)
        self._model.itemChanged.connect(self.updateValue)
        self._model.type_changed.connect(self.type_change_update)
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The parameters needed by the specific q-vector generator can be input here"
        self._view.setToolTip(tooltip_text)
        self._selector.setToolTip(
            "The q vectors will be generated using the method chosen here."
        )
        self._model.input_is_valid.connect(self.validate_model_parameters)
        policy = self._view.sizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        self._view.setSizePolicy(policy)
        self._view.horizontalHeader().hide()

    def type_change_update(self):
        # need to disconnect itemChanged otherwise updateValue will
        # be called multiple times as the item data has been changed
        # during the type update
        self._model.itemChanged.disconnect()
        self.updateValue()
        self._model.itemChanged.connect(self.updateValue)

    @Slot(bool)
    def validate_model_parameters(self, all_are_correct: bool):
        if all_are_correct:
            self.clear_error()
        else:
            self.mark_error("Some entries in the parameter table are invalid.")

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        qvector_type = self._selector.currentText()
        pardict = self._model.params_summary()
        return (qvector_type, pardict)

    def configure_using_default(self):
        """This is too complex to have a default value"""

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/UnitsEditor.py
# @brief     Shows the physical unit editor. Can run standalone.
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import copy

from qtpy.QtWidgets import (
    QDialog,
    QPushButton,
    QFrame,
    QGridLayout,
    QLabel,
    QApplication,
    QLineEdit,
    QListView,
)
from qtpy.QtCore import (
    Signal,
    Slot,
    QModelIndex,
)
from qtpy.QtGui import (
    QStandardItem,
    QStandardItemModel,
    QDoubleValidator,
)

from MDANSE.Framework.Units import _UNAMES, UNITS_MANAGER

from MDANSE_GUI.Widgets.GeneralWidgets import InputVariable, InputDialog


class UnitVisualiser(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QGridLayout(self)
        self.setLayout(layout)

        components = ["factor", "kg", "m", "s", "K", "mol", "A", "cd", "rad", "sr"]
        self.lines = {}

        validator = QDoubleValidator()

        for n, item in enumerate(components):
            label = QLabel(item, self)
            entry = QLineEdit("0", self)
            entry.setValidator(validator)
            layout.addWidget(label, n, 0)
            layout.addWidget(entry, n, 1)
            self.lines[item] = entry

    @Slot(dict)
    def newValues(self, val_dict: dict):
        for key, value in val_dict.items():
            entry = self.lines[key]
            entry.setReadOnly(False)
            entry.setText(str(value))
            entry.setReadOnly(True)


class UnitModel(QStandardItemModel):
    unit_info = Signal(dict)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._defaultUnits = copy.deepcopy(UNITS_MANAGER.units)

        self.populateUnitList()

    def populateUnitList(self):
        for unit in self._defaultUnits:
            item = QStandardItem(unit)
            item.setData(unit)
            self.appendRow(item)

    @Slot(QModelIndex)
    def passValue(self, index: QModelIndex):
        label = self.itemFromIndex(index)
        unit = UNITS_MANAGER.units[label.text()]
        info = {}
        info["factor"] = unit._factor
        info["kg"] = unit._dimension[0]
        info["m"] = unit._dimension[1]
        info["s"] = unit._dimension[2]
        info["K"] = unit._dimension[3]
        info["mol"] = unit._dimension[4]
        info["A"] = unit._dimension[5]
        info["cd"] = unit._dimension[6]
        info["rad"] = unit._dimension[7]
        info["sr"] = unit._dimension[8]
        self.unit_info.emit(info)

    @Slot(dict)
    def addNewUnit(self, info: dict):
        unit_name = info["name"]
        if UNITS_MANAGER.has_unit(unit_name):
            return None
        else:
            UNITS_MANAGER.add_unit(
                unit_name,
                *[
                    info[key]
                    for key in [
                        "factor",
                        "kg",
                        "m",
                        "s",
                        "K",
                        "mol",
                        "A",
                        "cd",
                        "rad",
                        "sr",
                    ]
                ],
            )
            UNITS_MANAGER.save()
            item = QStandardItem(unit_name)
            item.setData(unit_name)
            self.appendRow(item)


class UnitsEditor(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Physical Units Editor")

        self.model = UnitModel()

        layout = QGridLayout(self)
        self.setLayout(layout)

        self.view = QListView(self)
        self.view.setModel(self.model)

        self.visualiser = UnitVisualiser(self)

        self.view.clicked.connect(self.model.passValue)
        self.model.unit_info.connect(self.visualiser.newValues)

        new_unit_button = QPushButton("New unit", self)
        new_unit_button.clicked.connect(self.newUnitDialog)

        layout.addWidget(self.view, 0, 0)
        layout.addWidget(self.visualiser, 0, 1)
        layout.addWidget(new_unit_button, 1, 0)

    @Slot()
    def newUnitDialog(self):
        dialog_variables = [
            InputVariable(
                input_dict={
                    "keyval": "name",
                    "format": str,
                    "label": "Unit name",
                    "tooltip": "Type the name of the new physical unit here.",
                    "values": [""],
                }
            ),
            InputVariable(
                input_dict={
                    "keyval": "factor",
                    "format": float,
                    "label": "Scaling factor",
                    "tooltip": "Type the scaling factor of the new unit here.",
                    "values": [1.0],
                }
            ),
        ] + [
            InputVariable(
                input_dict={
                    "keyval": tag,
                    "format": int,
                    "label": tag,
                    "tooltip": "Type the power to which the component should be raised.",
                    "values": [0],
                }
            )
            for tag in ["kg", "m", "s", "K", "mol", "A", "cd", "rad", "sr"]
        ]
        nu_dialog = InputDialog(fields=dialog_variables)
        nu_dialog.got_values.connect(self.model.addNewUnit)
        nu_dialog.show()
        result = nu_dialog.exec()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = UnitsEditor()
    root.show()
    app.exec()

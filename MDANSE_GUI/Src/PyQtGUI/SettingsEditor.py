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

import collections
import copy

from icecream import ic

from qtpy.QtWidgets import (
    QDialog,
    QPushButton,
    QFrame,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QApplication,
    QSizePolicy,
    QMenu,
    QLineEdit,
    QTableView,
)
from qtpy.QtCore import (
    Signal,
    Slot,
    Qt,
    QPoint,
    QSize,
    QSortFilterProxyModel,
    QModelIndex,
)
from qtpy.QtGui import (
    QFont,
    QEnterEvent,
    QStandardItem,
    QStandardItemModel,
    QDoubleValidator,
)

from MDANSE import LOGGER
from MDANSE.Framework.Session.Settings import CascadingSettings

from MDANSE_GUI.PyQtGUI.Widgets.GeneralWidgets import InputVariable, InputDialog


class SettingsVisualiser(QFrame):
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


class SettingsModel(QStandardItemModel):
    unit_info = Signal(dict)

    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop("settings", None)
        self.filename = kwargs.pop("filename", None)
        super().__init__()

        if self.settings is None:
            self.settings = CascadingSettings()
            ic(
                "SettingsModel received no CascadingSettings. Creating a fresh instance."
            )
            if self.filename is not None:
                self.settings.load_from_file(self.filename)

        self.populateList()
        self.dataChanged.connect(self.updateSettings)

    def populateList(self):
        for key, value in self.settings._settings.items():
            item = [QStandardItem(str(key)), QStandardItem(str(value))]
            self.appendRow(item)

    @Slot()
    def addLine(self):
        item = [QStandardItem("entry"), QStandardItem("value")]
        self.appendRow(item)

    @Slot()
    def updateSettings(self):
        for n in range(self.rowCount()):
            key, value = self.item(n, 0).text(), self.item(n, 1).text()
            self.settings[key] = value
        ic(f"SettingsModel updated values. Got {self.settings._settings.items()}")
        self.settings.writeChanges()


class SettingsEditor(QDialog):
    def __init__(self, *args, **kwargs):
        ic(f"kwargs of SettingsEditor: {kwargs}")
        settings_object = kwargs.pop("settings", None)
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Settings Editor")
        ic(f"settings_object is {settings_object}")
        self.model = SettingsModel(*args, **{"settings": settings_object})

        layout = QGridLayout(self)
        self.setLayout(layout)

        self.view = QTableView(self)
        self.view.setModel(self.model)

        # self.visualiser = SettingsVisualiser(self)

        # self.view.clicked.connect(self.model.passValue)
        # self.model.unit_info.connect(self.visualiser.newValues)

        new_unit_button = QPushButton("New entry", self)
        new_unit_button.clicked.connect(self.model.addLine)

        layout.addWidget(self.view, 0, 0)
        # layout.addWidget(self.visualiser, 0, 1)
        layout.addWidget(new_unit_button, 1, 0)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = SettingsEditor()
    root.show()
    app.exec()

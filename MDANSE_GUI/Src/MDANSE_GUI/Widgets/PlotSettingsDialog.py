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

import traceback
from typing import Any

from matplotlib import rcParams
from qtpy.QtCore import QObject, Signal, Slot
from qtpy.QtGui import QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QApplication,
    QDialog,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)

from MDANSE.MLogging import LOG


def parse_string(param_str: str) -> Any:
    if "[" in param_str:
        toks = param_str.strip("[]").split(",")
        try:
            result = [float(x) for x in toks]
        except ValueError:
            result = toks
    elif param_str == "None":
        result = None
    else:
        result = param_str
    return result


EXPOSE_KEYS = [
    "legend.fontsize",
    "legend.borderpad",
    "legend.labelspacing",
    "xtick.labelsize",
    "ytick.labelsize",
    "axes.titlesize",
    "axes.labelsize",
    "axes.grid",
    "font.size",
]


class PlotSettingsModel(QStandardItemModel):
    def __init__(self, *args, par_dict: dict[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.par_dict = rcParams
        if par_dict is not None:
            for key, value in par_dict.items():
                self.par_dict[key] = value
        self.populate_model(self.par_dict)
        self.dataChanged.connect(self.update_values)
        self.setHorizontalHeaderLabels(["Parameters", "Values"])

    def populate_model(self, par_dict: dict[str, str]):
        for key, value in par_dict.items():
            if key not in EXPOSE_KEYS:
                continue
            left_item = QStandardItem(str(key))
            right_item = QStandardItem(str(value))
            left_item.setEditable(False)
            self.appendRow([left_item, right_item])

    @Slot()
    def update_values(self):
        bad_keys = []
        for row in range(self.rowCount()):
            key = self.item(row, 0).text()
            value = self.item(row, 1).text()
            try:
                self.par_dict[key] = parse_string(value)
            except ValueError as err:
                LOG.error(
                    "Could not set %s to the value %s. Traceback: %s",
                    key,
                    value,
                    traceback.format_exc(),
                )
                bad_keys.append(key)


class PlotSettingsEditor(QDialog):
    def __init__(self, *args, settings=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Plot Settings Editor")

        layout = QVBoxLayout(self)

        self.setLayout(layout)

        self.viewer = QTreeView(self)
        self.viewer.setAnimated(True)
        layout.addWidget(self.viewer)
        if settings:
            pardict = settings.group("rcParams")._settings
            self.model = PlotSettingsModel(par_dict=pardict)
        else:
            self.model = PlotSettingsModel()
        self.viewer.setModel(self.model)

        self.writeout_button = QPushButton("Save settings", self)
        layout.addWidget(self.writeout_button)
        self.writeout_button.clicked.connect(self.save_changes)
        self.viewer.expanded.connect(self.expand_columns)
        self.viewer.resizeColumnToContents(0)
        self.settings = settings

    @Slot()
    def expand_columns(self):
        for ncol in range(3):
            self.viewer.resizeColumnToContents(ncol)

    def save_changes(self):
        """Save changes to a file."""
        if self.settings is None:
            return
        rcparams_group = self.settings.group("rcParams")
        rcparams_group.populate(self.model.par_dict, {})
        for key, item in self.model.par_dict.items():
            rcparams_group.set(key, item)
        self.settings.save_values()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = PlotSettingsEditor()
    root.show()
    app.exec()

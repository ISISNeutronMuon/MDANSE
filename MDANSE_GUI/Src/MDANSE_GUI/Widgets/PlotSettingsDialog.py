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

from matplotlib import rc, rc_file, rcdefaults, rcParams, rcParamsDefault
from qtpy.QtCore import QObject, Qt, Signal, Slot
from qtpy.QtGui import QColor, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QApplication,
    QDialog,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)

from MDANSE import PLATFORM
from MDANSE.MLogging import LOG

ERROR_COLOR = QColor(255, 0, 0)


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

BAD_KEYS = [
    "axes.prop_cycle",
    "lines.dash_capstyle",
    "lines.dash_joinstyle",
    "lines.marker",
    "lines.solid_capstyle",
    "lines.solid_joinstyle",
]


class PlotSettingsModel(QStandardItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.par_dict = rcParams
        self.populate_model(self.par_dict)
        self.dataChanged.connect(self.update_values)
        self.setHorizontalHeaderLabels(["Parameters", "Values", "Default"])

    def populate_model(self, par_dict: dict[str, str]):
        for key, value in par_dict.items():
            if key in BAD_KEYS:
                continue
            left_item = QStandardItem(str(key))
            right_item = QStandardItem(str(value))
            def_item = QStandardItem(str(rcParamsDefault[key]))
            for item in (left_item, def_item):
                item.setEditable(False)
            self.appendRow([left_item, right_item, def_item])

    def reset_model(self):
        for row in range(self.rowCount()):
            key = self.item(row, 0).text()
            self.item(row, 1).setText(str(self.par_dict[key]))

    @Slot()
    def update_values(self):
        bad_keys = []
        bad_indices = []
        for row in range(self.rowCount()):
            key = self.item(row, 0).text()
            value = self.item(row, 1).text()
            try:
                self.par_dict[key] = parse_string(value)
            except ValueError:
                LOG.error(
                    "Could not set %s to the value %s. Traceback: %s",
                    key,
                    value,
                    traceback.format_exc(),
                )
                bad_keys.append(key)
                bad_indices.append(row)
        self.blockSignals(True)
        for row in range(self.rowCount()):
            if row in bad_indices:
                self.item(row, 1).setData(
                    ERROR_COLOR, role=Qt.ItemDataRole.BackgroundRole
                )
            else:
                self.item(row, 1).setData(None, role=Qt.ItemDataRole.BackgroundRole)
        self.blockSignals(False)


class PlotSettingsEditor(QDialog):
    values_changed = Signal()

    def __init__(self, *args, settings=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Plot Settings Editor")

        layout = QVBoxLayout(self)

        self.setLayout(layout)

        self.viewer = QTreeView(self)
        self.viewer.setAnimated(True)
        layout.addWidget(self.viewer)
        try:
            rc_file(PLATFORM.application_directory() / "matplotlibrc")
        except FileNotFoundError:
            LOG.warning("MDANSE settings do not contain a matplotlibrc file.")
        else:
            LOG.info("Plotting parameters loaded from MDANSE's matplotlibrc.")
        self.model = PlotSettingsModel()
        self.viewer.setModel(self.model)

        self.writeout_button = QPushButton("Save settings", self)
        self.reset_button = QPushButton("Reset values", self)
        layout.addWidget(self.writeout_button)
        layout.addWidget(self.reset_button)
        self.writeout_button.clicked.connect(self.save_changes)
        self.reset_button.clicked.connect(self.reset_values)
        self.viewer.expanded.connect(self.expand_columns)
        self.viewer.resizeColumnToContents(0)
        self.settings = settings

    @Slot()
    def expand_columns(self):
        for ncol in range(3):
            self.viewer.resizeColumnToContents(ncol)

    def save_changes(self):
        """Save changes to a file."""
        with open(PLATFORM.application_directory() / "matplotlibrc", "w") as target:
            for key, item in self.model.par_dict.items():
                target.write(f"{key}: {item}\n")
        self.values_changed.emit()

    def reset_values(self):
        rcdefaults()
        self.values_changed.emit()
        self.model.reset_model()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = PlotSettingsEditor()
    root.show()
    app.exec()

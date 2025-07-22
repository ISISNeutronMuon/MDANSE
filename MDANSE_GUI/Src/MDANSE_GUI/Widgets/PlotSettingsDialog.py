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
    param_str = str(param_str).replace("\\", "")
    param_str = param_str.replace("'", "")
    if "[" in param_str:
        toks = param_str.strip("[]").split(",")
        try:
            result = [float(x) for x in toks]
        except ValueError:
            result = toks
    elif param_str == "None":
        return None
    else:
        result = param_str
    return result


def convert_to_string(param_str: str) -> Any:
    result = str(param_str).replace("\\", "")
    result = result.replace("'", "")
    if "cycler" in result:
        result = result.strip("[]")
    if "['']" in result:
        result = result.replace["['']", "[]"]
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
        self.populate_model(rcParams)
        self.dataChanged.connect(self.update_values)
        self.setHorizontalHeaderLabels(["Parameters", "Values", "Default"])

    def populate_model(self, par_dict: dict[str, str]):
        for key, value in par_dict.items():
            if key in BAD_KEYS:
                continue
            left_item = QStandardItem(str(key))
            right_item = QStandardItem(str(value))
            right_item.setData(key, role=Qt.ItemDataRole.UserRole)
            def_item = QStandardItem(str(rcParamsDefault[key]))
            for item in (left_item, def_item):
                item.setEditable(False)
            self.appendRow([left_item, right_item, def_item])

    def reset_model(self):
        for row in range(self.rowCount()):
            key = self.item(row, 0).text()
            self.item(row, 1).setText(str(rcParams[key]))

    @Slot()
    def update_values(self):
        bad_keys = []
        bad_indices = []
        for row in range(self.rowCount()):
            key = self.item(row, 0).text()
            value = self.item(row, 1).text()
            try:
                rcParams[key] = parse_string(value)
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
        self._changed_keys = {}
        self.load_settings()
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
        self.model.itemChanged.connect(self.register_item_change)

    @Slot()
    def expand_columns(self):
        for ncol in range(3):
            self.viewer.resizeColumnToContents(ncol)

    def load_settings(self):
        settings_file = PLATFORM.application_directory() / "matplotlib.txt"
        if not settings_file.exists():
            LOG.info(
                "File %s does not exist. Using standard matplotlib settings.",
                str(settings_file),
            )
        with open(settings_file) as source:
            for line in source:
                no_comment = line.split("#")[0]
                if ":" not in no_comment:
                    continue
                toks = no_comment.split(":")
                key, value = toks[0], toks[1]
                try:
                    rcParams[key] = value
                except ValueError:
                    LOG.warning(
                        "Invald matplotlib setting %s: %s. Skipping", key, value
                    )
                else:
                    self._changed_keys[key] = value

    @Slot("QStandardItem*")
    def register_item_change(self, item: QStandardItem):
        key = item.data(Qt.ItemDataRole.UserRole)
        value = item.text()
        self._changed_keys[key] = value

    def save_changes(self):
        """Save changes to a file."""
        with open(PLATFORM.application_directory() / "matplotlib.txt", "w") as target:
            for key, item in self._changed_keys.items():
                target.write(f"{key}: {convert_to_string(item)}\n")
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

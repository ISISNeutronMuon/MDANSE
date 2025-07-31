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
from __future__ import annotations

import traceback
from typing import Any

from matplotlib import rc, rc_file, rcdefaults, rcParams, rcParamsDefault
from qtpy.QtCore import QObject, QSortFilterProxyModel, Qt, Signal, Slot
from qtpy.QtGui import QColor, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeView,
    QVBoxLayout,
)

from MDANSE import PLATFORM
from MDANSE.IO.IOUtils import strip_comments
from MDANSE.MLogging import LOG

ERROR_COLOR = QColor(255, 0, 0)


def parse_string(param_str: str) -> Any:
    """Convert a matplotlib rcParams value to a Python object.

    Parameters
    ----------
    param_str : str
        String obtained from rcParams.values()

    Returns
    -------
    Any
        Typically a string, list[float], list[str] or None
    """
    param_str = str(param_str).strip().replace("\\", "")
    param_str = param_str.replace("'", "")
    if param_str.startswith("["):
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


def convert_to_string(param_str: str) -> str | None:
    """Convert a Python string to a matplotlib-friendly representation.

    In matplotlib settings, lists should not have brackets around them,
    and strings have no quotes.

    Parameters
    ----------
    param_str : str
        String obtained from a Python object (i.e. a value from rcParams)

    Returns
    -------
    str | None
        a simplified string for matplotlib, or None is input is "None"
    """
    result = str(param_str).replace("\\", "")
    result = result.replace("'", "")
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

ALL_MAJOR_KEYS = {key.split(".")[0] for key in rcParams}
PREFERRED_SORT_KEYS = [
    "axes",
    "grid",
    "figure",
    "font",
    "lines",
    "legend",
    "savefig",
    "xtick",
    "ytick",
]
SORT_MAJOR_KEYS = [key for key in sorted(PREFERRED_SORT_KEYS) if key in ALL_MAJOR_KEYS]


class PlotSettingsModel(QStandardItemModel):
    """Interface between matplotlib's rcParams and QTreeView."""

    plots_need_updating = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._row_lookup = {}
        self.populate_model(rcParams)
        self.itemChanged.connect(self.update_single_value)
        self.setHorizontalHeaderLabels(["Parameters", "Values", "Default"])

    def populate_model(self, par_dict: dict[str, Any]):
        """Put entries from rcParams into the Qt model.

        Skips a few entries which are difficult to parse, because
        they require instances of specific matplotlib classes.

        Parameters
        ----------
        par_dict : dict[str, Any]
            key:value pairs from rcParams, converted to string.
        """
        for key, value in par_dict.items():
            if key in BAD_KEYS:
                continue
            left_item = QStandardItem(key)
            right_item = QStandardItem(str(value))
            right_item.setData(key, role=Qt.ItemDataRole.UserRole)
            def_item = QStandardItem(str(rcParamsDefault[key]))
            for item in (left_item, def_item):
                item.setEditable(False)
            self._row_lookup[key] = self.rowCount()
            self.appendRow([left_item, right_item, def_item])

    def reset_model(self):
        """Replace all values with default values."""
        for row in range(self.rowCount()):
            key = self.item(row, 0).text()
            self.item(row, 1).setText(str(rcParams[key]))

    @Slot("QStandardItem*")
    def update_single_value(self, item: QStandardItem):
        """Assign a new value from the model to rcParams."""
        key = item.data(Qt.ItemDataRole.UserRole)
        value = item.text()
        try:
            rcParams[key] = parse_string(value)
        except ValueError:
            LOG.error(
                "Could not set %s to the value %s. Traceback: %s",
                key,
                value,
                traceback.format_exc(),
            )
            mark_error = True
        else:
            mark_error = False
        self.blockSignals(True)
        row = self._row_lookup.get(key)
        if mark_error:
            self.item(row, 1).setData(ERROR_COLOR, role=Qt.ItemDataRole.BackgroundRole)
        else:
            self.item(row, 1).setData(None, role=Qt.ItemDataRole.BackgroundRole)
        self.blockSignals(False)
        self.plots_need_updating.emit()

    @Slot()
    def update_values(self):
        """Assign all values from the model to rcParams."""
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
    """Dialog allowing MDANSE to modify matplotlib settings."""

    values_changed = Signal()

    def __init__(self, *args, settings=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("MDANSE Plot Settings Editor")

        layout = QVBoxLayout(self)

        self.setLayout(layout)
        self.viewer = QTreeView(self)
        self.viewer.setAnimated(True)
        self.filter_combo = QComboBox(self)
        self.filter_box = QLineEdit(self)
        layout.addWidget(self.filter_combo)
        mid_hbox = QHBoxLayout(self)
        mid_hbox.addWidget(QLabel("Filter entries by:"))
        mid_hbox.addWidget(self.filter_box)
        mid_hbox.addWidget(QLabel("Set filter to keyword:"))
        mid_hbox.addWidget(self.filter_combo)
        layout.addLayout(mid_hbox)
        layout.addWidget(self.viewer)
        self._changed_keys = {}
        self.load_settings()
        self.model = PlotSettingsModel()
        self.filter_proxy_model = QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.viewer.setModel(self.filter_proxy_model)
        self.filter_combo.addItems(["all"] + SORT_MAJOR_KEYS)
        self.filter_combo.setCurrentText("all")
        self.filter_combo.currentTextChanged.connect(self.filter_box.setText)
        self.filter_box.textChanged.connect(self.filter_entries)

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
        self.model.plots_need_updating.connect(self.values_changed)

    @Slot(str)
    def filter_entries(self, search_string: str):
        """Hide rcParams keys which do not contain the search string.

        Parameters
        ----------
        search_string : str
            String to be found in valid dictionary keys.
        """
        if search_string == "all":
            self.filter_proxy_model.setFilterFixedString("")
        else:
            self.filter_proxy_model.setFilterFixedString(search_string)

    @Slot()
    def expand_columns(self):
        """Resize columns to the current amount of text in items."""
        for ncol in range(3):
            self.viewer.resizeColumnToContents(ncol)

    def load_settings(self):
        """Load previously saved plot settings from an MDANSE config file."""
        settings_file = PLATFORM.application_directory() / "matplotlib.txt"
        if not settings_file.exists():
            LOG.info(
                "File %s does not exist. Using standard matplotlib settings.",
                str(settings_file),
            )
            return
        rc_file(settings_file)
        with settings_file.open(encoding="utf-8") as source:
            for line in strip_comments(source):
                if ":" not in line:
                    continue
                key, value = line.split(":", maxsplit=1)
                self._changed_keys[key] = value

    @Slot("QStandardItem*")
    def register_item_change(self, item: QStandardItem):
        """Note down that an entry has been changed by the user."""
        key = item.data(Qt.ItemDataRole.UserRole)
        value = item.text()
        self._changed_keys[key] = value

    def save_changes(self):
        """Save the changed settings to an MDANSE config file."""
        with (PLATFORM.application_directory() / "matplotlib.txt").open(
            mode="w", encoding="utf-8"
        ) as target:
            for key, item in self._changed_keys.items():
                target.write(f"{key}: {convert_to_string(item)}\n")

    def reset_values(self):
        """Bring back all the default matplotlib settings."""
        rcdefaults()
        self.values_changed.emit()
        self.model.reset_model()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    root = PlotSettingsEditor()
    root.show()
    app.exec()

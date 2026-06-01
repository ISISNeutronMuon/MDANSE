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

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QComboBox, QFileDialog, QLabel, QLineEdit, QPushButton

from MDANSE.Framework.Parameters.OutputFiles import ASEOutputFormat
from MDANSE.MLogging import LOG, LogLevels
from MDANSE_GUI.InputWidgets import ComboWidget
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class OutputStructureWidget(WidgetBase[ASEOutputFormat]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)

        try:
            self.default_path = Path(self._parent._default_path)
        except (KeyError, AttributeError) as err:
            self.default_path = Path.cwd()
            LOG.error(
                "%s in %s - can't get default path.",
                type(err).__name__,
                type(self).__name__,
            )

        try:
            guess_name = self.default_path / "Result"
        except Exception:
            guess_name = self.default_path / "Result"
            LOG.error("It was not possible to get the job name from the parent")
        else:
            self._session = self._parent._parent_tab._session

        self.file_association = "Output file name (*)"

        self._value = guess_name
        self._field = QLineEdit(str(guess_name), self._base)
        self._field.setPlaceholderText(str(guess_name))

        self.format_box = ComboWidget(
            parent=self._base,
            base_type="QWidget",
            label="Output format",
            tooltip="Data will be dumped in the format here.",
            parent_widget=self,
            configurable=self.parameter,
            prop="out_format",
            parameter=self.parameter.descriptors["out_format"],
        )

        browse_button = QPushButton("Browse", self._base)
        browse_button.clicked.connect(self.file_dialog)

        label = QLabel("Log file output:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.logs_combo = QComboBox(self._base)
        self.logs_combo.addItems([level.name for level in LogLevels])

        self._layout.addWidget(self._field, 0, 0)
        self._layout.addWidget(self.format_box._base, 0, 1)
        self._layout.addWidget(browse_button, 0, 2)
        self._layout.addWidget(label, 1, 0)
        self._layout.addWidget(self.logs_combo, 1, 1)
        self._default_value = guess_name
        self._field.textChanged.connect(self.updateValue)

        self.default_labels()
        self.update_labels()
        self.updateValue()

        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = (
                "The average structure of the trajectory"
                "will be saved under this name,"
                "using the selected format"
            )
        self._field.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if not self._label_text:
            self._label_text = "OutputStructureWidget"
        if not self._tooltip:
            self._tooltip = (
                "The average structure of the trajectory"
                "will be saved under this name,"
                "using the selected format"
            )

    @Slot()
    def file_dialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        new_value = QFileDialog.getSaveFileName(
            self._base,  # the parent of the dialog
            "Load a file",  # the label of the window
            str(self.default_path),  # the initial search path
            self.file_association,  # text string specifying the file name filter.
        )

        if new_value[0]:
            self._field.setText(str(Path(new_value[0])))
            self.updateValue()

    def set_parameter(self):
        filename = self._field.text()

        if not filename:
            filename = self.default_value

        self.parameter.path = filename
        self.parameter.out_format = self.format_box.value
        self.parameter.log_level = self.logs_combo.currentText()

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

from itertools import count
from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import QComboBox, QFileDialog, QLabel, QLineEdit, QPushButton

from MDANSE.Framework.Parameters import OutputFile
from MDANSE.IO.IOUtils import unused_standard_output_filename
from MDANSE.MLogging import LOG, LogLevels
from MDANSE_GUI.InputWidgets.CheckableComboBox import CheckableComboBox
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class OutputFilesWidget(WidgetBase[OutputFile]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)

        default_value = self.parameter.descriptors["path"].default

        try:
            self.default_path = Path(self._parent._default_path)
        except (KeyError, AttributeError) as err:
            self.default_path = Path.cwd()
            LOG.error(
                f"{type(err).__name__} in {type(self).__name__} - can't get default path."
            )
        else:
            self._session = self._parent._parent_tab._session

        try:
            jobname = str(self._parent._job_instance.label).replace(" ", "")
        except Exception:
            jobname = default_value
            LOG.error("It was not possible to get the job name from the parent")

        self.default_path /= "output"
        guess_name = unused_standard_output_filename(self.default_path, jobname)
        self.file_association = "Output file name (*)"

        self._value = guess_name
        self._field = QLineEdit(str(guess_name), self._base)
        self._field.setPlaceholderText(str(guess_name))

        self.type_box = CheckableComboBox(self._base)
        self.type_box.addItems(
            [
                fmt_string
                for fmt_string in sorted(
                    x.name for x in self.parameter.descriptors["out_format"].choices
                )
                if fmt_string != "FileInMemory"
            ]
        )
        self.type_box.set_default("MDAFormat")

        browse_button = QPushButton("Browse", self._base)
        browse_button.clicked.connect(self.file_dialog)
        label = QLabel("Log file output:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.logs_combo = QComboBox(self._base)
        self.logs_combo.addItems([level.name for level in LogLevels])

        self._layout.addWidget(self._field, 0, 0)
        self._layout.addWidget(self.type_box, 0, 1)
        self._layout.addWidget(browse_button, 0, 2)
        self._layout.addWidget(label, 1, 0)
        self._layout.addWidget(self.logs_combo, 1, 1)

        self._default_value = guess_name
        self._field.textChanged.connect(self.updateValue)
        self.type_box.lineEdit().textChanged.connect(self.updateValue)
        self.default_labels()
        self.update_labels()
        self.updateValue()

        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "Analysis output will be saved under this name, and using the selected file types"

        self._field.setToolTip(tooltip_text)
        self.type_box.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if not self._label_text:
            self._label_text = "OutputFilesWidget"
        if not self._tooltip:
            self._tooltip = "Analysis output will be saved under this name, and using the selected file types"

    @Slot()
    def file_dialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        try:
            self.default_path = Path(self._parent._default_path)
        except AttributeError:
            self.default_path = Path.cwd()

        new_value = QFileDialog.getSaveFileName(
            self._base,  # the parent of the dialog
            "Save files",  # the label of the window
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
        self.parameter.out_format = self.type_box.checked_values()
        self.parameter.log_level = self.logs_combo.currentText()

    def trajectory_changed(self) -> None:
        self._field.setText(str(self.parameter.path))
        self.updateValue()

    def get_widget_value(self):
        self._configurator.forbidden_files = self._session.reserved_filenames()
        filename = self._field.text()
        if not filename:
            filename = self._default_value

        formats = self.type_box.checked_values()
        log_level = self.logs_combo.currentText()

        return (str(Path(filename).absolute()), formats, log_level)

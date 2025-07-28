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

import os
import os.path
from pathlib import PurePath

from qtpy.QtCore import Qt, Slot
from qtpy.QtWidgets import (
    QComboBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

from MDANSE.Framework.Configurators.OutputTrajectoryConfigurator import (
    OutputTrajectoryConfigurator,
)
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase

dtype_lookup = {"float16": 16, "float32": 32, "float64": 64}


class OutputTrajectoryWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)
        default_value = self._configurator.default
        try:
            self._parent = kwargs.get("parent", None)
            self.default_path = PurePath(self._parent._default_path)
        except KeyError:
            self.default_path = PurePath(os.path.abspath("."))
            LOG.error("KeyError in OutputTrajectoryWidget - can't get default path.")
        except AttributeError:
            self.default_path = PurePath(os.path.abspath("."))
            LOG.error(
                "AttributeError in OutputTrajectoryWidget - can't get default path."
            )
        else:
            self._session = self._parent._parent_tab._session
        try:
            self._parent = kwargs.get("parent", None)
            jobname = str(self._parent._job_instance.label).replace(" ", "")
            guess_name = str(
                PurePath(os.path.join(self.default_path, jobname + "_trajectory1"))
            )
        except Exception:
            guess_name = str(PurePath(default_value[0]))
            LOG.error("It was not possible to get the job name from the parent")
        while os.path.exists(guess_name + ".mdt"):
            prefix, number = guess_name.split("_trajectory")
            guess_name = str(PurePath(prefix + "_trajectory" + str(1 + int(number))))
        self.file_association = "MDT trajectory (*.mdt)"
        self._value = default_value
        self._field = QLineEdit(str(guess_name), self._base)
        self._field.setPlaceholderText(str(guess_name))
        self.dtype_box = QComboBox(self._base)
        self.dtype_box.addItems(["float16", "float32", "float64"])
        self.dtype_box.setCurrentText("float64")
        self.chunk_box = QSpinBox(self._base)
        self.chunk_box.setMinimum(1)
        self.chunk_box.setMaximum(0xFFFF)
        self.chunk_box.setValue(128)
        self.chunk_box.setSingleStep(32)
        self.chunk_box.setToolTip(
            "Specifies the size of a single chunk in the HDF5 file."
            "Affects the performance of reading and writing the trajectory."
        )
        self.compression_box = QComboBox(self._base)
        self.compression_box.addItems(["none", "gzip"])
        self.compression_box.setCurrentText("gzip")
        # self.type_box.setCurrentText(default_value[1])
        browse_button = QPushButton("Browse", self._base)
        browse_button.clicked.connect(self.file_dialog)
        label = QLabel("Log file output:")
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label2 = QLabel("Atoms per chunk")
        label2.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label2.setToolTip(
            "Specifies the size of a single chunk in the HDF5 file."
            "Affects the performance of reading and writing the trajectory."
        )
        self.logs_combo = QComboBox(self._base)
        self.logs_combo.addItems(OutputTrajectoryConfigurator.log_options)
        self._layout.addWidget(self._field, 0, 0)
        self._layout.addWidget(self.dtype_box, 0, 1)
        self._layout.addWidget(self.compression_box, 0, 2)
        self._layout.addWidget(browse_button, 0, 3)
        self._layout.addWidget(label, 1, 0)
        self._layout.addWidget(self.logs_combo, 1, 1)
        self._layout.addWidget(label2, 1, 2)
        self._layout.addWidget(self.chunk_box, 1, 3)
        self._default_value = default_value
        self._field.textChanged.connect(self.updateValue)
        self.default_labels()
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = (
                "The output trajectory will be saved under this name, "
                "with the selected floating point number precision "
                "and compression type"
            )
        self._field.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "OutputTrajectoryWidget"
        if self._tooltip == "":
            self._tooltip = (
                "The output trajectory will be saved under this name,"
                "with the selected floating point number precision"
                "and compression type"
            )

    @Slot()
    def file_dialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        self.default_path = self._parent._default_path
        new_value = QFileDialog.getSaveFileName(
            self._base,  # the parent of the dialog
            "Save file",  # the label of the window
            str(self.default_path),  # the initial search path
            self.file_association,  # text string specifying the file name filter.
        )
        if len(new_value[0]) > 0:
            self._field.setText(str(PurePath(new_value[0])))
            self.updateValue()

    def get_widget_value(self):
        self._configurator.forbidden_files = self._session.reserved_filenames()
        filename = self._field.text()
        if len(filename) < 1:
            filename = self._default_value[0]
        dtype = dtype_lookup[self.dtype_box.currentText()]
        chunk_size = self.chunk_box.value()
        compression = self.compression_box.currentText()
        logs = self.logs_combo.currentText()
        return (filename, dtype, chunk_size, compression, logs)

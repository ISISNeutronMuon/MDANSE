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
from typing import NamedTuple

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
from MDANSE.IO.IOUtils import unused_standard_output_filename
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase

dtype_lookup = {"float16": 16, "float32": 32, "float64": 64}


class SpinBoxDefaults(NamedTuple):
    minimum: int = 1
    maximum: int = 0xFFFFFF
    step: int = 1
    start_value: int = 1
    tooltip: str = "Input spin box"


SPIN_BOX_SETTINGS = {
    "frames": SpinBoxDefaults(
        tooltip="Specifies the number of frames in a single chunk of the HDF5 file. "
        "Affects the performance of reading and writing the trajectory."
    ),
    "atoms": SpinBoxDefaults(
        step=32,
        start_value=128,
        tooltip="Specifies the number of atoms in a single chunk of the HDF5 file. "
        "Affects the performance of reading and writing the trajectory.",
    ),
    "meta_block": SpinBoxDefaults(
        minimum=0,
        maximum=0x80000,
        step=2048,
        start_value=4096,
        tooltip="Size of a single metadata block in the HDF5 file. "
        "Larger values (e.g. 32768) may work better on cloud-based virtual machines (Ada, VISA, etc.).",
    ),
}


class OutputTrajectoryWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)
        default_value = self._configurator.default
        try:
            self._parent = kwargs.get("parent")
            self.default_path = Path(self._parent._default_path)
        except (KeyError, AttributeError) as e:
            self.default_path = Path(".").absolute()
            LOG.error("%s in OutputTrajectoryWidget - can't get default path.", str(e))
        else:
            self._session = self._parent._parent_tab._session
        try:
            self._parent = kwargs.get("parent")
            jobname = str(self._parent._job_instance.label).replace(" ", "")
        except Exception:
            jobname = "converted_trajectory"
            LOG.error("It was not possible to get the job name from the parent")
        self.default_path = self.default_path / "trajectory"
        guess_name = unused_standard_output_filename(
            self.default_path, jobname, extra_text="_trajectory", extension=".mdt"
        )
        self.file_association = "MDT trajectory (*.mdt)"
        self._value = default_value
        self._field = QLineEdit(str(guess_name), self._base)
        self._field.setPlaceholderText(str(guess_name))
        self.dtype_box = QComboBox(self._base)
        self.dtype_box.addItems(["float16", "float32", "float64"])
        self.dtype_box.setCurrentText("float64")
        self.chunk_atom_box = QSpinBox(self._base)
        self.chunk_frame_box = QSpinBox(self._base)
        self.meta_block_box = QSpinBox(self._base)
        for typ, chunk_box in zip(
            ("atoms", "frames", "meta_block"),
            (self.chunk_atom_box, self.chunk_frame_box, self.meta_block_box),
            strict=True,
        ):
            settings = SPIN_BOX_SETTINGS[typ]
            chunk_box.setMinimum(settings.minimum)
            chunk_box.setMaximum(settings.maximum)
            chunk_box.setValue(settings.start_value)
            chunk_box.setSingleStep(settings.step)
            chunk_box.setToolTip(settings.tooltip)
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
        label2.setToolTip(SPIN_BOX_SETTINGS["atoms"].tooltip)
        label3 = QLabel("Frames per chunk")
        label3.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label3.setToolTip(SPIN_BOX_SETTINGS["frames"].tooltip)
        label4 = QLabel("HDF5 meta_block_size")
        label4.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label4.setToolTip(SPIN_BOX_SETTINGS["meta_block"].tooltip)
        self.logs_combo = QComboBox(self._base)
        self.logs_combo.addItems(OutputTrajectoryConfigurator.log_options)
        self._layout.addWidget(self._field, 0, 0)
        self._layout.addWidget(self.dtype_box, 0, 1)
        self._layout.addWidget(self.compression_box, 0, 2)
        self._layout.addWidget(browse_button, 0, 3)
        self._layout.addWidget(label2, 1, 0)
        self._layout.addWidget(self.chunk_atom_box, 1, 1)
        self._layout.addWidget(label3, 1, 2)
        self._layout.addWidget(self.chunk_frame_box, 1, 3)
        self._layout.addWidget(label4, 2, 0)
        self._layout.addWidget(self.meta_block_box, 2, 1)
        self._layout.addWidget(label, 2, 2)
        self._layout.addWidget(self.logs_combo, 2, 3)
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
            self._field.setText(str(Path(new_value[0])))
            self.updateValue()

    def get_widget_value(self):
        self._configurator.forbidden_files = self._session.reserved_filenames()
        filename = self._field.text()
        if len(filename) < 1:
            filename = self._default_value[0]
        dtype = dtype_lookup[self.dtype_box.currentText()]
        chunk_size = (self.chunk_frame_box.value(), self.chunk_atom_box.value())
        compression = self.compression_box.currentText()
        logs = self.logs_combo.currentText()
        meta_block_size = self.meta_block_box.value()
        return (filename, dtype, chunk_size, compression, logs, meta_block_size)

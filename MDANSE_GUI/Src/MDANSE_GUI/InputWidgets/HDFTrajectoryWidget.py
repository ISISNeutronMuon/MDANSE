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

import html
import os
from pathlib import PurePath

from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from MDANSE.Framework.Configurators.HDFTrajectoryConfigurator import (
    HDF5_DRIVERS,
    PRIMES,
    guess_hdf5_trajectory_parameters,
)
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class HDFTrajectoryWidget(WidgetBase):
    def __init__(self, *args, trajectory_instance: Trajectory | None = None, **kwargs):
        super().__init__(*args, layout_type="QVBoxLayout", **kwargs)
        filename = kwargs.get("source_object")
        if trajectory_instance:
            self._configurator._instance = trajectory_instance
            self._configurator.configure_from_instance()
            filename = trajectory_instance.filename
        elif filename is not None:
            self._configurator.configure(str(filename))
        if not filename:
            label = QLabel("No Trajectory available", self._base)
            self._layout.addWidget(label)
        else:
            label = QLabel(html.escape(str(filename)), self._base)
            self._layout.addWidget(label)
            trajectory_path, _ = os.path.split(filename)
            self.default_path = PurePath(trajectory_path)
        self.build_fields()
        hdf5_info_text = QLabel(
            "Check https://docs.h5py.org/en/stable/high/file.html#chunk-cache for parameter details.\n"
            "Uncheck the boxes to use the default values (old behaviour)."
        )
        hdf5_info_text.setWordWrap(True)
        self._layout.addWidget(hdf5_info_text)
        self.default_labels()
        self.update_labels()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A single logical value that can be True of False"
        label.setToolTip(tooltip_text)
        self._label = label

    def build_fields(self):
        bar_layout = QHBoxLayout()
        combobox_inputs = [
            ("HDF5 driver", "None"),
        ]
        spinbox_inputs = [
            ("rdcc_nbytes (MB)", -1, QSpinBox, 8, 4096, 4),
            ("rdcc_nslots", -1, QSpinBox, 8191, 2147483647, 1000),
            ("rdcc_w0", 1.0, QDoubleSpinBox, 0, 1.0, 0.05),
        ]
        for label, init_value in combobox_inputs:
            sublayout = QVBoxLayout()
            sublayout.addWidget(QLabel(label))
            widget = QComboBox()
            widget.addItems(HDF5_DRIVERS)
            widget.addItem(init_value)
            widget.setCurrentText(init_value)
            sublayout.addWidget(widget)
            bar_layout.addLayout(sublayout)
        for label, init_value, widget_type, minval, maxval, step in spinbox_inputs:
            sublayout = QVBoxLayout()
            sublayout.addWidget(QLabel(label))
            checkbox = QCheckBox("Set value manually")
            sublayout.addWidget(checkbox)
            checkbox.setChecked(True)
            widget = widget_type()
            widget.setValue(init_value)
            widget.setMinimum(minval)
            widget.setMaximum(maxval)
            widget.setSingleStep(step)
            checkbox.stateChanged.connect(widget.setEnabled)
            sublayout.addWidget(widget)
            bar_layout.addLayout(sublayout)
        self._layout.addLayout(bar_layout)

    def configure_using_default(self):
        """This is too static to have a default value"""

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "HDFTrajectoryWidget"
        if self._tooltip == "":
            self._tooltip = "The input trajectory to be processed"

    def get_value(self):
        return self._configurator["value"]

    def get_widget_value(self):
        result = self.get_value()
        if not self._configurator.valid:
            self.mark_error(self._configurator.error_status)
        elif self._configurator.warning_status:
            self._label.setToolTip(self._configurator.warning_status)
        else:
            self._label.setToolTip(self._tooltip)
        return result

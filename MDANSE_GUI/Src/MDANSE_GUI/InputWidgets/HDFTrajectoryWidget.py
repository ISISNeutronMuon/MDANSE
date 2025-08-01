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
from pathlib import PurePath

from qtpy.QtWidgets import QLabel

from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class HDFTrajectoryWidget(WidgetBase):
    def __init__(self, *args, trajectory_instance: Trajectory | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        filename = kwargs.get("source_object", None)
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
            label = QLabel(str(filename), self._base)
            self._layout.addWidget(label)
            trajectory_path, _ = os.path.split(filename)
            self.default_path = PurePath(trajectory_path)
        self.default_labels()
        self.update_labels()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A single logical value that can be True of False"
        label.setToolTip(tooltip_text)
        self._label = label

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
        else:
            self.mark_warning(self._configurator.warning_status)
            if self._configurator.warning_status:
                self._label.setToolTip(self._configurator.warning_status)
            else:
                self._label.setToolTip(self._tooltip)
            self.value_updated.emit()
        return result

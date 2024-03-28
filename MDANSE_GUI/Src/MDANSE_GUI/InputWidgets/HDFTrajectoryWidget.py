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
# Copyright (C)  Institut Laue Langevin 2013-now
# Copyright (C)  ISIS Neutron and Muon Source, STFC, UKRI 2021-now
import os

from qtpy.QtWidgets import QLabel

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class HDFTrajectoryWidget(WidgetBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        source_object = kwargs.get("source_object", None)
        try:
            filename = source_object
        except AttributeError:
            filename = None
        if filename is not None:
            self._configurator.configure(filename)
            label = QLabel(filename, self._base)
            self._layout.addWidget(label)
            trajectory_path, _ = os.path.split(filename)
            self.default_path = trajectory_path
        else:
            label = QLabel("No Trajectory available", self._base)
            self._layout.addWidget(label)
        self.default_labels()
        self.update_labels()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A single logical value that can be True of False"
        label.setToolTip(tooltip_text)

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
        return self.get_value()

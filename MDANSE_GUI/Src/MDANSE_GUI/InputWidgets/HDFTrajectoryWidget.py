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
from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtWidgets import QLabel

from MDANSE.Framework.Parameters import MDANSEResult, MDANSETrajectory
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class HDFTrajectoryWidget(WidgetBase[MDANSETrajectory | MDANSEResult]):
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        if not self.valid:
            label = QLabel("No Trajectory available.", self._base)
            self._layout.addWidget(label)
            self.mark_error("No trajectory available.")
        else:
            filename = Path(self.raw)
            label = QLabel(html.escape(str(filename)), self._base)
            self._layout.addWidget(label)
            self.default_path = filename.parent

        self.default_labels()
        self.update_labels()

        tooltip_text = self._tooltip or "A trajectory"

        label.setToolTip(tooltip_text)
        self._label = label

    def trajectory_changed(self) -> None:
        self._label.setText(self.raw)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if not self._label_text:
            self._label_text = "HDFTrajectoryWidget"
        if not self._tooltip:
            self._tooltip = "The input trajectory to be processed"

    def get_widget_value(self):
        return self.value

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

from qtpy.QtWidgets import QLabel

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class DummyWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _source_object = kwargs.get("source_object", None)
        self._layout.addWidget(QLabel("content is missing here", self._base))
        self._configurator = {"value": "Oops!"}
        self.default_labels()
        self.update_labels()
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The real widget that should have been here is missing! Let the authors know about it."
        self._base.setToolTip(tooltip_text)

    def configure_using_default(self):
        """This is too simple to have a default value"""

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "DummyWidget"
        if self._tooltip == "":
            self._tooltip = "A placeholder which tells us that a real widget is missing"

    def get_value(self):
        return self._configurator["value"]

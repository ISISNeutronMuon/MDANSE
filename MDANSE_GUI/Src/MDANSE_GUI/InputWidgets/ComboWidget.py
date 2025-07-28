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

from qtpy.QtWidgets import QComboBox

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Widgets.DefaultCombobox import highlight_default_value


class ComboWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configurator = kwargs.get("configurator", None)
        if configurator is None:
            option_list = kwargs.get("choices", [])
        else:
            option_list = configurator.choices
            default_option = configurator.default
        field = QComboBox(self._base)
        field.addItems(sorted(option_list))
        field.setCurrentText(default_option)
        field.currentTextChanged.connect(self.updateValue)
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = (
                "A single option can be picked out of all the options listed."
            )
        field.setToolTip(tooltip_text)
        highlight_default_value(field)
        self._field = field
        self._layout.addWidget(field)
        self._configurator = configurator
        self.default_labels()
        self.update_labels()
        self.updateValue()

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "ComboWidget"
        if self._tooltip == "":
            self._tooltip = "You only have one option. Choose wisely."

    def get_widget_value(self):
        return self._field.currentText()

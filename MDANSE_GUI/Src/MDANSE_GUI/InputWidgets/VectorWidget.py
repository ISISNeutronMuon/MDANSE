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
from qtpy.QtWidgets import QLineEdit, QLabel

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class VectorWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._changing_label = QLabel("Vector", parent=self._base)
        self._layout.addWidget(self._changing_label)
        vfields = []
        for val in ["0", "0", "1"]:
            temp = QLineEdit(val, self._base)
            self._layout.addWidget(temp)
            vfields.append(temp)
        self._vector_fields = vfields
        self._mode = 0
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The spatial properties in the analysis can be projected on a plane or on an axis, as chosen here."
        for wid in vfields:
            wid.setToolTip(tooltip_text)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        try:
            vector = [float(x.text()) for x in self._vector_fields]
        except:
            vector = [0, 0, 0]
        return vector

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

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QButtonGroup, QLabel, QLineEdit, QRadioButton

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class ProjectionWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _source_object = kwargs.get("source_object", None)
        bgroup = QButtonGroup(self._base)
        for id, blabel in enumerate(["None", "Axial", "Planar"]):
            rbutton = QRadioButton(blabel, parent=self._base)
            bgroup.addButton(rbutton, id=id)
            self._layout.addWidget(rbutton)
            if id == 0:
                rbutton.setChecked(True)
        self._changing_label = QLabel("N/A", parent=self._base)
        self._layout.addWidget(self._changing_label)
        vfields = []
        for _ in range(3):
            temp = QLineEdit("0", self._base)
            self._layout.addWidget(temp)
            vfields.append(temp)
        self._button_group = bgroup
        self._vector_fields = vfields
        self._mode = 0
        self._button_group.idClicked.connect(self.button_switched)
        self.updateValue()
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "The spatial properties in the analysis can be projected on a plane or on an axis, as chosen here."
        for wid in vfields:
            wid.setToolTip(tooltip_text)
        for wid in self._button_group.buttons():
            wid.setToolTip(tooltip_text)
        self.button_switched(0)
        self._button_group.buttonClicked.connect(self.updateValue)
        for vfield in self._vector_fields:
            vfield.textChanged.connect(self.updateValue)

    def configure_using_default(self):
        """This is too complex to have a default value"""

    @Slot(int)
    def button_switched(self, button_number: int):
        button_id = self._button_group.checkedId()
        if button_id == 0:
            self._changing_label.setText("N/A")
            for field in self._vector_fields:
                field.setEnabled(False)
        elif button_id == 1:
            self._changing_label.setText("Axis direction")
            for field in self._vector_fields:
                field.setEnabled(True)
        else:
            self._changing_label.setText("Plane normal")
            for field in self._vector_fields:
                field.setEnabled(True)
        self._mode = button_id

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        if self._mode == 0:
            return ("NullProjector", [])
        vector = [x.text() for x in self._vector_fields]
        if self._mode == 1:
            return ("AxialProjector", vector)
        else:
            return ("PlanarProjector", vector)

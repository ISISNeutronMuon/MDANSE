# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/ProjectionWidget.py
# @brief     Implements module/class/test ProjectionWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QLineEdit, QRadioButton, QButtonGroup, QLabel, QHBoxLayout
from qtpy.QtCore import Slot, Signal

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class ProjectionWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        source_object = kwargs.get("source_object", None)
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
        vector = [float(x.text()) for x in self._vector_fields]
        if self._mode == 1:
            return ("AxialProjector", vector)
        else:
            return ("PlanarProjector", vector)

    @Slot()
    def updateValue(self):
        current_value = self.get_widget_value()
        self._configurator.configure(current_value)

    def get_value(self):
        self.updateValue()
        return self._configurator["value"]

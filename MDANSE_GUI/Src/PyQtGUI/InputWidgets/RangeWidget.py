# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/FramesWidget.py
# @brief     Implements module/class/test FramesWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QLineEdit, QSpinBox, QLabel
from qtpy.QtCore import Slot, Signal
from qtpy.QtGui import QDoubleValidator, QIntValidator

from MDANSE_GUI.PyQtGUI.InputWidgets.WidgetBase import WidgetBase


class RangeWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)
        source_object = kwargs.get("source_object", None)
        num_type = kwargs.get("valueType", int)
        if num_type is int:
            step_val = 1
        else:
            step_val = 0.1
        labels = [
            QLabel("From", self._base),
            QLabel("to", self._base),
            QLabel("in steps of", self._base),
        ]
        fields = [
            QLineEdit(str(num_type(0)), self._base),
            QLineEdit(str(num_type(5)), self._base),
            QLineEdit(str(num_type(step_val)), self._base),
        ]
        if num_type is int:
            validators = [QIntValidator(parent_field) for parent_field in fields]
        else:
            validators = [QDoubleValidator(parent_field) for parent_field in fields]
        for field_num in range(3):
            self._layout.addWidget(labels[field_num], 0, 2 * field_num)
            self._layout.addWidget(fields[field_num], 0, 2 * field_num + 1)
            fields[field_num].setValidator(validators[field_num])
            fields[field_num].textChanged.connect(self.updateValue)
        self._fields = fields
        self._validators = validators
        self._num_type = num_type
        self.default_labels()
        self.update_labels()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "RangeWidget"
        if self._tooltip == "":
            self._tooltip = "Values to be used, given as (First, Last, StepSize)"

    def value_from_configurator(self):
        if self._configurator.check_dependencies():
            minval, maxval = self._configurator._mini, self._configurator._maxi
            print(f"Configurator min/max: {minval}, {maxval}")
            if maxval is None:
                return
            for val in self._validators:
                val.setBottom(-abs(maxval))
                val.setTop(abs(maxval))

    def get_widget_value(self):
        val = [self._num_type(field.text()) for field in self._fields]
        return val

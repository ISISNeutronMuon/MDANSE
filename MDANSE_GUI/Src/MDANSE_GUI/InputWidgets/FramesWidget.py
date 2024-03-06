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
from qtpy.QtGui import QIntValidator

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class FramesWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QGridLayout", **kwargs)
        trajectory_configurator = kwargs.get("trajectory_configurator", None)
        if trajectory_configurator is not None:
            try:
                self._last_frame = trajectory_configurator["length"]
            except:
                self._last_frame = -1
        else:
            self._last_frame = -1
        labels = [
            QLabel("First frame", self._base),
            QLabel("Last frame", self._base),
            QLabel("in steps of", self._base),
        ]
        fields = [
            QLineEdit("0", self._base),
            QLineEdit(str(self._last_frame), self._base),
            QLineEdit("1", self._base),
        ]
        placeholders = ["0", str(self._last_frame), "1"]
        validators = [QIntValidator(parent_field) for parent_field in fields]
        for field_num in range(3):
            self._layout.addWidget(labels[field_num], 0, 2 * field_num)
            self._layout.addWidget(fields[field_num], 0, 2 * field_num + 1)
            fields[field_num].setValidator(validators[field_num])
            fields[field_num].textChanged.connect(self.updateValue)
            fields[field_num].setPlaceholderText(placeholders[field_num])
        self._fields = fields
        self._validators = validators
        self._default_values = placeholders
        self.default_labels()
        self.update_labels()
        self.updateValue()        
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "A single logical value that can be True of False"
        for field in fields:
            field.setToolTip(tooltip_text)

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "FramesWidget"
        if self._tooltip == "":
            self._tooltip = (
                "Trajectory frames to be used, given as (First, Last, StepSize)"
            )

    def value_from_configurator(self):
        if self._last_frame > 0:
            for val in self._validators:
                val.setBottom(-abs(self._last_frame))
                val.setTop(abs(self._last_frame))
        elif self._configurator.check_dependencies():
            minval, maxval = self._configurator._mini, self._configurator._maxi
            print(f"Configurator min/max: {minval}, {maxval}")
            for val in self._validators:
                val.setBottom(-abs(maxval))
                val.setTop(abs(maxval))

    def get_widget_value(self):
        result = []
        for n, field in enumerate(self._fields):
            strval = field.text()
            try:
                val = int(strval)
            except:
                val = int(self._default_values[n])
            result.append(val)
        return result

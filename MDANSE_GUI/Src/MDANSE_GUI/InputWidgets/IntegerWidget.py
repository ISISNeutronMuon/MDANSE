# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/IntegerWidget.py
# @brief     Implements module/class/test IntegerWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************


from qtpy.QtWidgets import QLineEdit, QSpinBox
from qtpy.QtCore import Slot, Signal
from qtpy.QtGui import QIntValidator

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class IntegerWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = 0
        try:
            default_option = int(self._configurator.default)
        except ValueError:
            default_option = 0
        if self._configurator.choices:
            field = QSpinBox(self._base)
            field.setMinimum(self._configurator.choices[0])
            field.setMaximum(self._configurator.choices[-1])
            field.setValue(default_option)
            field.valueChanged.connect(self.newInt)
        else:
            field = QLineEdit(self._base)
            validator = QIntValidator(field)
            minval, maxval = self._configurator.mini, self._configurator.maxi
            if minval is not None:
                validator.setBottom(minval)
            if maxval is not None:
                validator.setTop(maxval)
            field.setValidator(validator)
            field.setText(str(default_option))
            field.textChanged.connect(self.newText)
        self._value = default_option
        field.setToolTip(self._tooltip)
        self._field = field
        self._layout.addWidget(field)
        self.default_labels()
        self.update_labels()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "IntegerWidget"
        if self._tooltip == "":
            self._tooltip = "A single integer number"

    @Slot(str)
    def newText(self, text: str):
        self._value = int(text)
        self.updateValue()

    @Slot(int)
    def newInt(self, num: int):
        self._value = num
        self.updateValue()

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        return int(self._field.text())
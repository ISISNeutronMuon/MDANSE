# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/FloatWidget.py
# @brief     Implements module/class/test FloatWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QLineEdit, QDoubleSpinBox
from qtpy.QtCore import Slot, Signal
from qtpy.QtGui import QDoubleValidator

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class FloatWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            default_option = float(self._configurator.default)
        except ValueError:
            default_option = 0.0
        if self._configurator.choices:
            field = QDoubleSpinBox(self._base)
            field.setMinimum(self._configurator.choices[0])
            field.setMaximum(self._configurator.choices[-1])
            if len(self._configurator.choices) > 1:
                field.setSingleStep(
                    self._configurator.choices[1] - self._configurator.choices[0]
                )
            field.setValue(default_option)
        else:
            field = QLineEdit(self._base)
            validator = QDoubleValidator(field)
            minval, maxval = self._configurator.mini, self._configurator.maxi
            if minval is not None:
                validator.setBottom(minval)
            if maxval is not None:
                validator.setTop(maxval)
            field.setValidator(validator)
            field.setText(str(default_option))
        field.setToolTip(self._tooltip)
        self._layout.addWidget(field)
        self._field = field
        self.default_labels()
        self.update_labels()

    def default_labels(self):
        """Each Widget should have a default tooltip and label,
        which will be set in this method, unless specific
        values are provided in the settings of the job that
        is being configured."""
        if self._label_text == "":
            self._label_text = "FloatWidget"
        if self._tooltip == "":
            self._tooltip = "A single floating-point number"

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        strval = self._field.text().strip()
        if len(strval) < 1:
            self._empty = True
        else:
            self._empty = False
        return strval

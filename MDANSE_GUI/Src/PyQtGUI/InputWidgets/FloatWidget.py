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

from MDANSE_GUI.PyQtGUI.InputWidgets.WidgetBase import WidgetBase


class FloatWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = 0
        configurator = kwargs.get("configurator", None)
        if configurator is None:
            option_list = kwargs.get("choices", [])
        else:
            option_list = configurator.choices
            try:
                default_option = int(configurator.default)
            except ValueError:
                default_option = 0
        if self._configurator.choices:
            field = QDoubleSpinBox(self._base)
            field.setMinimum(self._configurator.choices[0])
            field.setMaximum(self._configurator.choices[-1])
            if len(self._configurator.choices) > 1:
                field.setSingleStep(
                    self._configurator.choices[1] - self._configurator.choices[0]
                )
            field.setValue(default_option)
            field.valueChanged.connect(self.newFloat)
        else:
            field = QLineEdit(self._base)
            validator = QDoubleValidator(field)
            validator.setBottom(self._configurator.mini)
            validator.setTop(self._configurator.maxi)
            field.setValidator(validator)
            field.setText(str(default_option))
            field.textChanged.connect(self.newText)
        self._value = default_option
        field.setToolTip(self._tooltip)
        self._field = field
        self._layout.addWidget(field)
        self._configurator = configurator

    @Slot(str)
    def newText(self, text: str):
        self._value = int(text)
        self.updateValue()

    @Slot(float)
    def newFloat(self, num: float):
        self._value = num
        self.updateValue()

    @Slot()
    def updateValue(self):
        self._configurator.configure(self._value)

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/InterpolationOrderWidget.py
# @brief     Implements module/class/test InterpolationOrderWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QSpinBox, QLabel
from qtpy.QtCore import Slot, Signal
from qtpy.QtGui import QIntValidator

from MDANSE_GUI.PyQtGUI.InputWidgets.WidgetBase import WidgetBase


suffix_dict = {
    "0": "th order - no interpolation",
    "1": "st order",
    "2": "nd order",
    "3": "rd order",
    "4": "th order",
    "5": "th order",
}


class InterpolationOrderWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, layout_type="QHBoxLayout", **kwargs)
        source_object = kwargs.get("source_object", None)

        self.field = QSpinBox(self._base)
        self.field.setValue(1)
        label = QLabel("Interpolation order", self._base)
        self.numerator = QLabel("st order")

        self.field.valueChanged.connect(self.adjust_numerator)

        self._layout.addWidget(label)
        self._layout.addWidget(self.field)
        self._layout.addWidget(self.numerator)

    @Slot(int)
    def adjust_numerator(self, order: int):
        text_order = str(order)
        new_numerator = suffix_dict.get(text_order[-1], " - no interpolation")
        self.numerator.setText(new_numerator)

    def get_widget_value(self):
        value = self.field.value()

        return value

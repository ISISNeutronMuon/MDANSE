# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/RunningModeWidget.py
# @brief     Implements module/class/test RunningModeWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import multiprocessing

from qtpy.QtWidgets import QComboBox, QSpinBox
from qtpy.QtCore import Qt, Slot

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class RunningModeWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._totalNumberOfProcessors = multiprocessing.cpu_count()
        self._last_numproc = None
        default_value = self._configurator.default
        self._value = default_value
        self.mode_box = QComboBox(self._base)
        self.mode_box.addItems(self._configurator.availablesModes)
        self.mode_box.setCurrentText(self._configurator.availablesModes[0])
        self.field = QSpinBox(self._base)
        self.field.setValue(1)
        self.field.setMinimum(1)
        self._layout.addWidget(self.mode_box)
        self._layout.addWidget(self.field)
        self.mode_box.currentIndexChanged.connect(self.mode_changed)
        self.field.valueChanged.connect(self.numproc_changed)
        self.default_labels()
        self.update_labels()

    @Slot()
    def mode_changed(self):
        mode = self.mode_box.currentText()
        if self._last_numproc is None:
            nextval = self._totalNumberOfProcessors
        else:
            nextval = self._last_numproc
        if mode == "monoprocessor":
            self.field.setValue(1)
            self.field.setEnabled(False)
        else:
            self.field.setEnabled(True)
            self.field.setValue(nextval)

    @Slot()
    def numproc_changed(self):
        mode = self.mode_box.currentText()
        numproc = self.field.value()
        if mode == "monoprocessor":
            return
        self._last_numproc = numproc

    def get_widget_value(self):
        mode = self.mode_box.currentText()
        numproc = self.field.value()
        if mode == "monoprocessor":
            value = (mode,)
        else:
            value = (mode, numproc)
        return value

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/AtomSelectionWidget.py
# @brief     Implements module/class/test AtomSelectionWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

import glob
import itertools
import os
import os.path

from qtpy.QtWidgets import QComboBox, QLabel, QLineEdit, QPushButton, QDialog
from qtpy.QtCore import Qt, Slot
from qtpy.QtGui import QStandardItemModel, QStandardItem

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class SelectionDialog(QDialog):
    """Generates a string that specifies the atom selection."""


class AtomSelectionWidget(WidgetBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_value = '{"all": true}'
        self._value = default_value
        self.field = QLineEdit(default_value, self._base)
        browse_button = QPushButton("Atom selection creator", self._base)
        browse_button.clicked.connect(self.selection_dialog)
        self.field.textChanged.connect(self.check_valid_field)
        self._layout.addWidget(self.field)
        self._layout.addWidget(browse_button)
        self.update_labels()

    @Slot()
    def selection_dialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        new_value = SelectionDialog()
        if len(new_value) > 0:
            self.field.setText(new_value)
            self.updateValue()

    def check_valid_field(self, value):
        if self._configurator.check_valid_settings(value):
            self.field.setStyleSheet("color: black;")
        else:
            self.field.setStyleSheet("color: red;")

    def get_widget_value(self):
        selection_string = self.field.text()
        return selection_string

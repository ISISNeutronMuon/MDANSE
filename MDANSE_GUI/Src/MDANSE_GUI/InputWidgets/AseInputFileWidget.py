# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/InputWidgets/InputFileWidget.py
# @brief     Implements module/class/test InputFileWidget
#
# @homepage  https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

from qtpy.QtWidgets import QLineEdit, QPushButton, QFileDialog, QComboBox
from qtpy.QtCore import Slot
from ase.io.formats import filetype

from MDANSE.Framework.Configurators.AseInputFileConfigurator import (
    AseInputFileConfigurator,
)

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Widgets.GeneralWidgets import translate_file_associations


class AseInputFileWidget(WidgetBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configurator = kwargs.get("configurator", None)
        if configurator is not None:
            default_value = configurator.default
        else:
            default_value = ""
        try:
            parent = kwargs.get("parent", None)
            self.default_path = parent.default_path
        except KeyError:
            self.default_path = "."
            print("KeyError in InputFileWidget - can't get default path.")
        except AttributeError:
            self.default_path = "."
            print("AttributeError in InputFileWidget - can't get default path.")
        default_value = kwargs.get("default", "")
        if self._tooltip:
            tooltip_text = self._tooltip
        else:
            tooltip_text = "Specify a path to an existing file."
        file_association = kwargs.get("wildcard", "")
        self._qt_file_association = translate_file_associations(file_association)
        combo = QComboBox(self._base)
        combo.addItems(AseInputFileConfigurator._allowed_formats)
        combo.setEditable(False)
        self._type_combo = combo
        field = QLineEdit(self._base)
        self._field = field
        field.textChanged.connect(self.updateValue)
        field.setText(str(default_value))
        field.setToolTip(tooltip_text)
        self._layout.addWidget(field)
        self._layout.addWidget(combo)
        button = QPushButton("Browse", self._base)
        button.clicked.connect(self.valueFromDialog)
        self._layout.addWidget(button)
        self._configurator = configurator
        self._file_dialog = QFileDialog.getOpenFileName
        self.updateValue()

    @Slot()
    def valueFromDialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        new_value = self._file_dialog(
            self.parent(),  # the parent of the dialog
            "Load a file",  # the label of the window
            self.default_path,  # the initial search path
            self._qt_file_association,  # text string specifying the file name filter.
        )
        if new_value is not None:
            self._field.setText(new_value[0])
            self.updateValue()
            try:
                type_guess = filetype(new_value[0])
            except:
                type_guess = "guess"
            self._type_combo.setCurrentText(type_guess)

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        return self._field.text(), self._type_combo.currentText()

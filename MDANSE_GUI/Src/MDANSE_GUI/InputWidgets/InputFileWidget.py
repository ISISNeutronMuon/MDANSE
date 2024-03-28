#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

from qtpy.QtWidgets import QLineEdit, QPushButton, QFileDialog
from qtpy.QtCore import Slot

from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Widgets.GeneralWidgets import translate_file_associations


class InputFileWidget(WidgetBase):
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
        try:
            file_association = configurator.wildcard
        except AttributeError:
            file_association = kwargs.get("wildcard", "")
        self._qt_file_association = translate_file_associations(file_association)
        field = QLineEdit(self._base)
        self._field = field
        field.textChanged.connect(self.updateValue)
        field.setText(str(default_value))
        field.setPlaceholderText(str(default_value))
        field.setToolTip(tooltip_text)
        self._layout.addWidget(field)
        button = QPushButton("Browse", self._base)
        button.clicked.connect(self.valueFromDialog)
        self._default_value = default_value
        self._layout.addWidget(button)
        self._configurator = configurator
        self._file_dialog = QFileDialog.getOpenFileName
        self.updateValue()

    def configure_using_default(self):
        """This is too specific to have a default value"""

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
            if new_value[0]:
                self._field.setText(new_value[0])
                self.updateValue()

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        strval = self._field.text()
        if len(strval) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return strval

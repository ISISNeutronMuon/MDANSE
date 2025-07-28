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
from __future__ import annotations

import os
from pathlib import PurePath

from qtpy.QtCore import Slot
from qtpy.QtWidgets import QFileDialog, QLineEdit, QPushButton

from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase


class InputFileWidget(WidgetBase):
    def __init__(self, *args, file_dialog=QFileDialog.getOpenFileName, **kwargs):
        super().__init__(*args, **kwargs)
        configurator = kwargs.get("configurator", None)
        if configurator is not None:
            default_value = configurator.default
        else:
            default_value = ""
        parent = kwargs.get("parent", None)
        self._parent = parent
        if parent is not None:
            self._job_name = parent._job_name
            self._settings = parent._settings
        try:
            parent = kwargs.get("parent", None)
            self.default_path = PurePath(parent._default_path)
        except KeyError:
            self.default_path = PurePath(os.path.abspath("."))
            LOG.error("KeyError in OutputFilesWidget - can't get default path.")
        except AttributeError:
            self.default_path = PurePath(os.path.abspath("."))
            LOG.error("AttributeError in OutputFilesWidget - can't get default path.")
        default_value = kwargs.get("default", "")
        if self._tooltip:
            self._tooltip_text = self._tooltip
        else:
            self._tooltip_text = "Specify a path to an existing file."
        try:
            file_association = configurator.wildcard
        except AttributeError:
            file_association = kwargs.get("wildcard", "")
        self._qt_file_association = file_association
        self._default_value = default_value
        self.add_widgets_to_layout()
        self._configurator = configurator
        self._file_dialog = file_dialog
        self.updateValue()

    def add_widgets_to_layout(self):
        field = QLineEdit(self._base)
        self._field = field
        field.textChanged.connect(self.updateValue)
        field.setText(str(self._default_value))
        field.setPlaceholderText(str(self._default_value))
        field.setToolTip(self._tooltip_text)
        self._layout.addWidget(field)

        button = QPushButton("Browse", self._base)
        button.clicked.connect(self.valueFromDialog)
        self._layout.addWidget(button)

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
            "Load file",  # the label of the window
            str(self._parent._default_path),  # the initial search path
            self._qt_file_association,  # text string specifying the file name filter.
        )
        if new_value is not None and new_value[0]:
            self._field.setText(str(PurePath(new_value[0])))
            self.updateValue()
            try:
                LOG.info(
                    f"Settings path of {self._job_name} to {os.path.split(new_value[0])[0]}"
                )
                if self._parent is not None:
                    self._parent._default_path = str(
                        PurePath(os.path.split(new_value[0])[0])
                    )
            except Exception:
                LOG.error(
                    f"session.set_path failed for {self._job_name}, {os.path.split(new_value[0])[0]}"
                )

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        strval = self._field.text()
        if len(strval) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return strval

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

from pathlib import Path
from typing import TYPE_CHECKING

from more_itertools import first
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QFileDialog, QLineEdit, QPushButton

from MDANSE.Framework.Parameters import MDANSEResult, MDANSETrajectory
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Utils import block_signals


class InputFileWidget(WidgetBase[MDANSETrajectory | MDANSEResult]):
    def __init__(
        self,
        *args,
        file_dialog=QFileDialog.getOpenFileName,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self._field = QLineEdit(self._base)
        self._default_value = self.default

        if self._default_value == "N/A":
            default_extension = first(self.parameter.extension.values()).lstrip("*")
            self._default_value = self._parent._job_name + default_extension

        if self._parent is not None:
            self._job_name = self._parent._job_name
            self._settings = self._parent._settings

        try:
            self.default_path = Path(self._parent._default_path)
        except (KeyError, AttributeError) as err:
            self.default_path = Path.cwd()
            LOG.error(
                f"{type(err).__name__} in {type(self).__name__} - can't get default path."
            )

        if self._tooltip:
            self._tooltip_text = self._tooltip
        else:
            self._tooltip_text = "Specify a path to an existing file."

        self._qt_file_association = ";;".join(
            f"{name} ({wildcard})"
            for name, wildcard in self.parameter.extension.items()
        )

        self.add_widgets_to_layout()
        if self._default_value is None:
            self._field.setText("")
        self._file_dialog = file_dialog
        self.toggle_widgets()
        self.updateValue()

    def add_widgets_to_layout(self):
        self._field.textChanged.connect(self.updateValue)
        self._field.setText(str(self._default_value))
        self._field.setPlaceholderText(str(self._default_value))
        self._field.setToolTip(self._tooltip_text)
        self._layout.addWidget(self._field)

        button = QPushButton("Browse", self._base)
        button.clicked.connect(self.valueFromDialog)
        self._layout.addWidget(button)

    def set_value(self, value: Path | str) -> None:
        pth = Path(value)
        with block_signals(self._field):
            self._field.setText(str(pth))
        self.updateValue()

        try:
            LOG.info(f"Settings path of {self._job_name} to {pth.parent}")
            if self._parent is not None:
                self._parent._default_path = str(pth.parent)

        except Exception:
            LOG.error(f"session.set_path failed for {self._job_name}, {pth.parent}")

    @Slot()
    def valueFromDialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        new_value = self._file_dialog(
            self._parent,  # the parent of the dialog
            "Load file",  # the label of the window
            str(self._parent._default_path),  # the initial search path
            self._qt_file_association,  # text string specifying the file name filter.
        )

        if new_value is not None and new_value[0]:
            self.value = new_value[0]

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        strval = self._field.text()
        self._empty = not strval

        if self._empty:
            return self._default_value

        return strval

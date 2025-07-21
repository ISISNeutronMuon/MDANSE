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
from pathlib import Path
from typing import Optional

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from qtpy.QtCore import QObject, Slot
from qtpy.QtWidgets import QFileDialog, QLineEdit, QPushButton


class InputFileWidget(WidgetBase):
    def __init__(
        self,
        parent: Optional[QObject] = None,
        *args,
        wildcard: str = "",
        file_dialog=QFileDialog.getOpenFileName,
        default: str = "",
        **kwargs,
    ):
        super().__init__(parent=parent, *args, default=default, **kwargs)

        default_value = self._configurator.default

        self._parent = parent
        self.default_path = Path().absolute()

        if parent is not None:
            self._job_name = parent._job_name
            self._settings = parent._settings

            try:
                self.default_path = Path(parent._default_path)
            except (KeyError, AttributeError) as err:
                LOG.error(f"{type(err).__name__} in InputFileWidget - can't get default path.")

        default_value = default
        if self._tooltip:
            self._tooltip_text = self._tooltip
        else:
            self._tooltip_text = "Specify a path to an existing file."

        try:
            file_association = self._configurator.wildcard
        except AttributeError:
            file_association = wildcard

        self._qt_file_association = file_association
        self._default_value = default_value
        self.add_widgets_to_layout()
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
            str(self._default_path),  # the initial search path
            self._qt_file_association,  # text string specifying the file name filter.
        )
        if new_value is not None and new_value[0]:
            val = Path(new_value[0])

            self._field.setText(str(val))
            self.updateValue()
            try:
                if self._parent is not None:
                    LOG.info(f"Setting path of {self._job_name} to {val.parent}")
                    self._parent._default_path = str(val.parent)
            except Exception:
                LOG.error(f"session.set_path failed for {self._job_name}, {val.parent}")

    def get_widget_value(self):
        """Collect the results from the input widgets and return the value."""
        strval = self._field.text()
        self._empty = not strval.strip()
        if self._empty:
            return self._default_value

        return strval

class OptionalInputFileWidget(InputFileWidget):
    """Optional file doesn't need to care if underlying file is valid until you try to load."""
    def __init__(self, *args, button_label: str, **kwargs):
        super().__init__(*args, **kwargs)

        self.button_label = button_label

    def add_widgets_to_layout(self):
        super().add_widgets_to_layout()

        button = QPushButton(self.button_label, self._base)
        button.clicked.connect(self.load_file)
        self._layout.addWidget(button)

    def load_file(self):
        current_value = self.get_widget_value()
        if self._empty:
            self.clear_error()
            return

        try:
            self._configurator.configure(current_value)
        except Exception:
            self.mark_error(
                "COULD NOT SET THIS VALUE - you may need to change the values in other widgets"
            )
        self.value_changed.emit()
        if self._configurator.valid:
            self.clear_error()
            self.value_updated.emit()
        else:
            self.mark_error(self._configurator.error_status)

    @Slot()
    def updateValue(self):
        pass

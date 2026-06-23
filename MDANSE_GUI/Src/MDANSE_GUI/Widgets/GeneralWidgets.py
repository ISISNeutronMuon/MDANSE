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

import copy
from pathlib import PurePath
from typing import TYPE_CHECKING, Union

from qtpy.QtCore import QObject, Qt, Signal, Slot
from qtpy.QtGui import (
    QDoubleValidator,
    QIntValidator,
    QPalette,
    QValidator,
)
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from collections.abc import Iterable

# I think that a Trajectory Converter should, in general,
# create a Wizard and not a single Dialog.
# This way LAMMPS could give the user a chance to verify which
# elements were in the system, instead of just failing.
# The idea is similar to Origin and the way Origin creates
# a lengthy wizard interface just to load data from a file.
# The wizard should have a number of stages, which can be
# used or left empty.

# I need to have several stages of processing
# 1. The initial Dialog is created based on settings from the Converter
# 2. The user specifies the input files
# 3. The converter tries to get as much information as possible from the files
# 4. The information gathered is shown to the user,
# with a possibility of correcting the entries.
# 5. The corrected parameters are passed to the converter, and the job is started.


class WhitespaceValidator(QValidator):
    """Does not allow empty or whitespace names."""

    EXCLUDED_CHARACTERS = [" ", "\n", "\t", "\\"]

    def __init__(self, *args, default_name: str = "DEFAULT", **kwargs):
        super().__init__(*args, **kwargs)
        self.default_name = default_name

    def validate(self, input_string: str, position: int):
        state = (
            QValidator.State.Invalid
            if not input_string
            or any(char in input_string for char in self.EXCLUDED_CHARACTERS)
            else QValidator.State.Acceptable
        )
        return state, input_string, position

    def fixup(self, invalid_string: str):
        invalid_string = self.default_name
        return super().fixup(invalid_string)


# the following code was useful at first - but could it be replaced by
# the widgets and dialogs above?
# The InputVariable/InputDialog combo seems to be offering a subset
# of what InputFactory and GeneralInput can do.


class InputVariable(QObject):
    """A general-purpose input field, used by the InputDialog."""

    def __init__(self, *args, input_dict: dict | None = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.label = "Variable"
        self.keyval = "var1"
        self.format = float
        self.value = 0.0
        self.helper_dialog = None
        self.tooltip = ""
        self.invalid_tooltip = ""
        self.placeholder = ""
        for key, item in input_dict.items():
            self.__setattr__(str(key), item)

        if isinstance(self.value, list):
            self.widget = QComboBox
        else:
            self.widget = QLineEdit

        self.input_widget = None

    def returnValue(self) -> float | int | str:
        """
        Returns
        -------
        Union[float, int, str]
            The results from the input widget.
        """
        if isinstance(self.input_widget, QComboBox):
            text = self.input_widget.currentText()
        else:
            text = self.input_widget.text()
        try:
            result = self.format(text)
        except ValueError:
            result = text
        return result

    def inputValid(self) -> bool:
        """Should be overridden to allow for more complex input
        validation checks.

        Returns
        -------
        bool
            True if the input is valid.
        """
        return True

    def setValidState(self):
        """The input widget is return to its valid state."""
        if not self.input_widget or isinstance(self.input_widget, QComboBox):
            return

        self.input_widget.setToolTip(self.tooltip)
        self.input_widget.setPalette(QPalette())

    def setInvalidState(self):
        """Puts the input widget into an invalid state. The widget
        background is changed."""
        if not self.input_widget or isinstance(self.input_widget, QComboBox):
            return

        self.input_widget.setToolTip(self.invalid_tooltip)
        pallette = QPalette()
        pallette.setColor(QPalette.Base, Qt.GlobalColor.red)
        self.input_widget.setPalette(pallette)


class InputDialog(QDialog):
    """A simple dialog designed to contain a number of input fields.
    It is used by the UnitsEditor and ElementsDatabaseEditor.
    """

    got_values = Signal(dict)

    def __init__(
        self, *args, fields: Iterable[InputVariable] = (), title: str = "", **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.setModal(True)
        self.setWindowTitle(title)

        self.fields = fields  #  we need to store it for later
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        # now some basic elements
        var_base = QWidget(self)
        var_layout = QFormLayout(var_base)
        var_base.setLayout(var_layout)
        button_base = QWidget(self)
        button_layout = QHBoxLayout(button_base)
        button_base.setLayout(button_layout)
        layout.addWidget(var_base)
        layout.addWidget(button_base)
        # the most important part: handling the variables
        for var in fields:
            label = var.label
            format = var.format
            value = var.value
            widget = var.widget
            _helper_dialog = var.helper_dialog
            placeholder = var.placeholder
            # set up widgets
            temp_base = QWidget(var_base)
            temp_layout = QHBoxLayout(temp_base)
            temp_base.setLayout(temp_layout)
            widget_instance = widget(var_base)
            if isinstance(value, list):
                widget_instance.addItems(value)
            else:
                if format is int:
                    validator = QIntValidator(temp_base)
                elif format is float:
                    validator = QDoubleValidator(temp_base)
                elif hasattr(var, "default_text"):
                    validator = WhitespaceValidator(
                        temp_base, default_name=var.default_text
                    )
                else:
                    validator = None
                widget_instance.setText(str(value))
                widget_instance.setPlaceholderText(str(placeholder))
                if validator is not None:
                    widget_instance.setValidator(validator)
                widget_instance.textChanged.connect(self.check_values)
            temp_layout.addWidget(widget_instance)
            var.input_widget = widget_instance
            var_layout.addRow(label, temp_base)
        # optinally we can add other buttons here...
        #
        # final button, always there
        self.button = QPushButton("Accept!", self)
        self.button.clicked.connect(self.accept)
        self.accepted.connect(self.return_values)
        button_layout.addWidget(self.button)
        self.check_values()

    @Slot()
    def return_values(self):
        """Emits the results from the input widgets."""
        result = {}
        for var in self.fields:
            result[var.keyval] = var.returnValue()
        self.got_values.emit(result)

    def check_values(self):
        """Checks if the values in the input widget are valid. If not
        the Accept! button is deactivated and the widget may change
        color to alert the user.
        """
        for var in self.fields:
            if not var.inputValid():
                self.button.setEnabled(False)
                var.setInvalidState()
                return
            var.setValidState()
        self.button.setEnabled(True)

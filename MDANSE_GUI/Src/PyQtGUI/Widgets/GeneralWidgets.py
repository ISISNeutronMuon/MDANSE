# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Src/PyQtGUI/MainWindow.py
# @brief     Base widget for the MDANSE GUI
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# **************************************************************************

from typing import Union, Iterable
from collections import OrderedDict
import copy
import abc
from PyQt6.QtCore import QObject

from icecream import ic
import numpy as np
from qtpy.QtWidgets import (
    QDialog,
    QPushButton,
    QFileDialog,
    QGridLayout,
    QVBoxLayout,
    QWidget,
    QLabel,
    QApplication,
    QComboBox,
    QMenu,
    QLineEdit,
    QTableView,
    QFormLayout,
    QHBoxLayout,
    QCheckBox,
)
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel, QObject
from qtpy.QtGui import (
    QFont,
    QEnterEvent,
    QStandardItem,
    QStandardItemModel,
    QIntValidator,
    QDoubleValidator,
    QValidator,
)

from MDANSE.Framework.Jobs.IJob import IJob


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


class GeneralInput(QObject):
    """
    This is a standard object for storing information from input fields.
    It inherits QObject, and so it is able to use the signal/slot mechanism.
    For any input variable, the idea is to attach a GeneralInput to the
    corresponding GUI element to allow the software to handle all the
    data flow in a standardised way.
    """

    final_value = Signal(object)
    string_value = Signal(str)
    value_changed = Signal()

    def __init__(self, *args, data_type=None, **kwargs):
        new_kwargs = copy.copy(kwargs)
        for kkey in InputFactory.reserved_keywords:
            if kkey in new_kwargs.keys():
                new_kwargs.pop(kkey)
        super().__init__(*args, **{})

        self.default_path = kwargs.get("path", None)
        self.data_type = data_type
        self.default_value = kwargs.get("default", None)
        self.current_value = self.default_value
        self.file_association = kwargs.get("file_association", None)
        self.file_direction = kwargs.get("file_direction", "none")
        self.file_format = kwargs.get("format", "")
        if self.file_association is not None:
            if len(self.file_association) < 1 and len(self.file_format) > 1:
                self.file_association = "*." + self.file_format
        if self.file_direction == "in":
            self.file_dialog = QFileDialog.getOpenFileName
        elif self.file_direction == "out":
            self.file_dialog = QFileDialog.getSaveFileName
        else:
            self.file_dialog = None
        ic(kwargs)

    @Slot(str)
    def updatePath(self, newpath: str):
        """Interesting only to the variables using a FileDialog,
        this slot allows the Dialog to update the default path
        to be used for finding the input/output files.

        Arguments:
            newpath -- the new path in the filesystem to be used
            in new instances of FileDialog.
        """
        self.default_path = newpath

    @Slot(str)
    @Slot(int)
    @Slot(object)
    def updateValue(self, newone, emit=False):
        """This slot allows the GeneralInput to receive a new value
        from the corresponding GUI element. In principle, the GUI
        should have produced a valid input, but tests for valid
        conversion are still being performed here.

        Arguments:
            newone -- new value to be stored by the GeneralInput instance

        Keyword Arguments:
            emit -- if True, the GeneralInput instance will broadcast
            the new value as a signal.
        """
        try:
            converted = self.data_type(newone)
        except ValueError:
            converted = self.default_value
            ic(f"ValueError converting {newone} using {self.data_type}")
        except TypeError:
            converted = self.default_value
            ic(f"TypeError converting {newone} using {self.data_type}")
        self.current_value = converted
        self.value_changed.emit()
        if emit:
            self.string_value.emit(self.current_value)

    def returnValue(self):
        """Returns the value stored by this instance.
        Typically used when the Dialog has been filled out,
        and the inputs have to be summarised.

        Returns:
            The value revceived from the GUI, in the format
            that was specified in the constructor.
        """
        if self.file_dialog is not None:
            ic(f"File Field Return Value: {self.current_value}")
        self.final_value.emit(self.current_value)
        if self.file_direction == "out":
            return (self.current_value, "hdf")
        return self.current_value

    @Slot()
    def valueFromDialog(self):
        """A Slot defined to allow the GUI to be updated based on
        the new path received from a FileDialog.
        This will start a FileDialog, take the resulting path,
        and emit a signal to update the value show by the GUI.
        """
        new_value = self.file_dialog(
            self.parent(),  # the parent of the dialog
            "Load a file",  # the label of the window
            self.default_path,  # the initial search path
            self.file_association,  # text string specifying the file name filter.
        )
        if new_value is not None:
            self.updateValue(new_value[0], emit=True)


# class MultipleInput(GeneralInput):
#     """
#     This class is more specifically designed for handling variables
#     with multiple values of the same type.
#     """

#     def __init__(self, *args, data_type=None, **kwargs):
#         super().__init__(*args, data_type=data_type, **kwargs)
#         self.length = kwargs.get("length", 1)
#         if isinstance(self.default_value, Iterable) and not isinstance(self.default_value, str):
#             if len(self.default_value) == self.length:
#                 self.default_value = np.array(list(self.default_value), dtype=self.data_type)
#             elif len(self.default_value) > self.length:
#                 self.default_value = np.array(list(self.default_value)[:self.length], dtype=self.data_type)
#             else:
#                 padding = self.length - len(self.default_value)
#                 self.default_value = np.array(list(self.default_value) + padding*[0]).astype(self.data_type)
#         else:
#             self.default_value = np.array(self.length*[self.default_value], dtype=self.data_type)
#         self.current_value = self.default_value


class InputGroup(QObject):
    final_value = Signal(object)
    string_value = Signal(str)

    def __init__(self, parent: QObject | None = ...) -> None:
        super().__init__(parent)
        self.fields = []
        self.values = []

    @Slot()
    def valueChanged(self):
        """This slot is triggered when one of the inputs
        changes its value. It then checks ALL the inputs
        and outputs their values put together."""
        result = []
        for field in self.fields:
            result.append(field.returnValue())
        self.final_value.emit(result)
        self.string_value.emit(str(result))

    def register_value(self, field: GeneralInput):
        """Adds an input field to the list of fields"""
        self.fields.append(field)
        field.value_changed.connect(self.valueChanged)


def translate_file_associations(input_str: str):
    """Takes the string describing valid file formats, as specified for
    wxWidgets in the MDANSE framework, and converts it to an equivalent
    string for Qt.

    Arguments:
        input_str -- string specifying the file formats for the FileDialog,
        in the text format from wxWidgets

    Returns:
        String of the valid file formats in the FileDialog, in the format
        valid for Qt.
    """
    toks = input_str.split("|")[::2]
    basic_replacement = ";;".join(toks[:-1] + ["All files (*.*)"])
    return basic_replacement


class InputFactory:
    """Factory generating input fields for Dialogs. It is meant to standardise
    the way inputs are hanlded, so that any kind of variable can be processed
    using the same methods.
    """

    reserved_keywords = [
        "kind",
        "default",
        "label",
        "tooltip",
        "wildcard",
        "mini",
        "choices",
        "file_association",
        "file_direction",
    ]

    def createInputField(*args, **kwargs):
        """Creates an input field for the specified kind of variable.
        The returned base widget is a QWidget with its own layout and
        children, which should be placed in the layout of the Dialog.
        The variables themselves are passed to the Dialog by the
        GeneralInput object, to make the exchange independent of the
        type of widgets used to construct the input field.

        Returns:
            [QWidget, GeneralInput] pair
        """
        kind = kwargs.get("kind", "str")

        if kind == "str":
            result = InputFactory.createSingle(*args, **kwargs)
        elif kind == "int" or kind == "integer":
            result = InputFactory.createSingle(*args, **kwargs)
        elif kind == "range" or kind == "intrange":
            result = InputFactory.createMultiple(*args, **kwargs)
        elif kind == "arange" or kind == "floatrange":
            result = InputFactory.createMultiple(*args, **kwargs)
        elif kind == "float":
            result = InputFactory.createSingle(*args, **kwargs)
        elif kind == "single_choice":
            result = InputFactory.createCombo(*args, **kwargs)
        elif kind == "bool" or kind == "boolean":
            result = InputFactory.createBool(*args, **kwargs)
        elif kind == "input_file":
            result = InputFactory.createFile(*args, direction="in", **kwargs)
        elif kind == "single_output_file":
            result = InputFactory.createFile(*args, direction="out", **kwargs)
        else:
            result = InputFactory.createBlank(*args, **kwargs)

        return result

    def createBase(*args, **kwargs):
        """Some parts of the input will always be the same,
        so we handle them in one function that will be called
        before we get to the specific details

        Returns:
            [base, layout] pair of QWidget and associated layout
        """
        parent = kwargs.get("parent", None)
        label_text = kwargs.get("label", None)
        tooltip_text = kwargs.get("tooltip", None)
        base = QWidget(parent)
        layout = QHBoxLayout(base)
        base.setLayout(layout)
        label = QLabel(label_text, base)
        label.setToolTip(tooltip_text)
        layout.addWidget(label)
        return [base, layout]

    def createBlank(*args, **kwargs):
        """This method creates a placeholder which will inform
        the users that the requested input field could not
        be constructed.
        """
        kind = kwargs.get("kind", "str")
        base, layout = InputFactory.createBase(
            label=f"<b>MISSING TYPE</b>:{kind}",
            tooltip="This is not handled by the MDANSE GUI correctly! Please report the problem to the authors.",
        )
        return [base, GeneralInput()]

    def createFile(*args, direction="in", **kwargs):
        """Creates an input field with an additional button which
        creates a FileDialog, to allow the user to browse the file system.

        Keyword Arguments:
            direction -- if 'in', create a FileDialog for an exisitng file,
              if 'out', a FileDialog for creating a new file.
        """
        kind = kwargs.get("kind", "str")
        default_value = kwargs.get("default", "")
        tooltip_text = kwargs.get("tooltip", "Specify a path to an existing file.")
        file_association = kwargs.get("wildcard", "")
        qt_file_association = translate_file_associations(file_association)
        ic(kind)
        ic(default_value)
        ic(tooltip_text)
        ic(file_association)
        ic(kwargs)
        base, layout = InputFactory.createBase(*args, **kwargs)
        field = QLineEdit(base)
        data_handler = GeneralInput(
            data_type=str,
            file_association=qt_file_association,
            file_direction=direction,
            **kwargs,
        )
        data_handler.string_value.connect(field.setText)
        field.textChanged.connect(data_handler.updateValue)
        field.setText(str(default_value))
        field.setToolTip(tooltip_text)
        layout.addWidget(field)
        button = QPushButton("Browse", base)
        button.clicked.connect(data_handler.valueFromDialog)
        layout.addWidget(button)
        return [base, data_handler]

    def createBool(*args, **kwargs):
        """Creates an input field for a logical variable,
        which is currently implemented as a check box.
        """
        kind = kwargs.get("kind", "bool")
        default_value = kwargs.get("default", False)
        tooltip_text = kwargs.get("tooltip", None)
        ic(kind)
        ic(default_value)
        ic(tooltip_text)
        ic(kwargs)
        base, layout = InputFactory.createBase(*args, **kwargs)
        field = QCheckBox(base)
        field.setTristate(False)
        data_handler = GeneralInput(data_type=bool, **kwargs)
        field.stateChanged.connect(data_handler.updateValue)
        field.setChecked(bool(default_value))
        field.setToolTip(tooltip_text)
        layout.addWidget(field)
        return [base, data_handler]

    def createSingle(*args, **kwargs):
        """Creates a LineEdit input for a single variable.
        Can be used to handle int, float or str variables.
        For numerical values, it adds a QValidator instance
        to filter out invalid inputs.
        """
        kind = kwargs.get("kind", "str")
        default_value = kwargs.get("default", None)
        tooltip_text = kwargs.get("tooltip", None)
        minval = kwargs.get("mini", None)
        ic(kind)
        ic(default_value)
        ic(tooltip_text)
        ic(kwargs)
        base, layout = InputFactory.createBase(*args, **kwargs)
        field = QLineEdit(base)
        if kind == "int" or kind == "integer":
            data_handler = GeneralInput(data_type=int, **kwargs)
            validator = QIntValidator(field)
        elif kind == "float":
            data_handler = GeneralInput(data_type=float, **kwargs)
            validator = QDoubleValidator(field)
        elif kind == "str":
            data_handler = GeneralInput(data_type=str, **kwargs)
            validator = None
        if validator is not None:
            field.setValidator(validator)
            if minval is not None:
                validator.setBottom(minval)
        field.textChanged.connect(data_handler.updateValue)
        field.setText(str(default_value))
        field.setToolTip(tooltip_text)
        layout.addWidget(field)
        return [base, data_handler]

    def createMultiple(*args, **kwargs):
        """Creates a number of LineEdit fields, for
        input of multiple values.
        Can be used to handle int, float or str variables.
        For numerical values, it adds a QValidator instance
        to filter out invalid inputs.
        """
        kind = kwargs.get("kind", "str")
        default_value = kwargs.get("default", None)
        tooltip_text = kwargs.get("tooltip", None)
        minval = kwargs.get("mini", None)
        number_of_fields = kwargs.get("howmany", None)
        if number_of_fields is None:
            number_of_fields = len(default_value)
        ic(kind)
        ic(default_value)
        ic(tooltip_text)
        ic(kwargs)
        base, layout = InputFactory.createBase(*args, **kwargs)
        main_handler = InputGroup(base)
        for nfield in range(number_of_fields):
            field = QLineEdit(base)
            if kind == "int" or kind == "integer":
                data_handler = GeneralInput(data_type=int, **kwargs)
                validator = QIntValidator(field)
            elif kind == "float":
                data_handler = GeneralInput(data_type=float, **kwargs)
                validator = QDoubleValidator(field)
            elif kind == "str":
                data_handler = GeneralInput(data_type=str, **kwargs)
                validator = None
            if validator is not None:
                field.setValidator(validator)
                if minval is not None:
                    validator.setBottom(minval)
            field.textChanged.connect(data_handler.updateValue)
            field.setText(str(default_value[nfield]))
            field.setToolTip(tooltip_text)
            main_handler.register_value(data_handler)
        layout.addWidget(field)
        return [base, main_handler]

    def createCombo(*args, **kwargs):
        """For the variable where one option has to be picked from
        a list of possible values, we create a ComboBox"""
        kind = kwargs.get("kind", "str")
        default_value = kwargs.get("default", False)
        tooltip_text = kwargs.get("tooltip", None)
        option_list = kwargs.get("choices", [])
        ic(kind)
        ic(default_value)
        ic(tooltip_text)
        ic(kwargs)
        base, layout = InputFactory.createBase(*args, **kwargs)
        field = QComboBox(base)
        field.addItems(option_list)
        data_handler = GeneralInput(data_type=bool, **kwargs)
        field.currentTextChanged.connect(data_handler.updateValue)
        field.setToolTip(tooltip_text)
        layout.addWidget(field)
        return [base, data_handler]


# the following code was useful at first - but could it be replaced by
# the widgets and dialogs above?
# The InputVariable/InputDialog combo seems to be offering a subset
# of what InputFactory and GeneralInput can do.


class InputVariable(QObject):
    """A general-purpose input field, used by the InputDialog."""

    def __init__(self, *args, input_dict: dict = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.label = "Variable"
        self.keyval = "var1"
        self.format = float
        self.values = [0.0]
        self.widget = QLineEdit
        self.number_of_inputs = 1
        self.helper_dialog = None
        self.tooltip = ""
        self.placeholder = ""
        for key, item in input_dict.items():
            self.__setattr__(str(key), item)

        self.input_widgets = []

    def returnValues(self):
        result = []
        for widget in self.input_widgets:
            try:
                temp = self.format(widget.text())
            except ValueError:
                temp = widget.text()
            result.append(temp)
        return result


class InputDialog(QDialog):
    """A simple dialog designed to contain a number of input fields.
    It is used by the UnitsEditor and ElementsDatabaseEditor.
    """

    got_values = Signal(dict)

    def __init__(self, *args, fields: Iterable["InputVariable"] = None, **kwargs):
        super().__init__(*args, **kwargs)

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
            values = var.values
            widget = var.widget
            helper_dialog = var.helper_dialog
            tooltip = var.tooltip
            placeholder = var.placeholder
            number_of_inputs = var.number_of_inputs
            # set up widgets
            temp_base = QWidget(var_base)
            temp_layout = QHBoxLayout(temp_base)
            temp_base.setLayout(temp_layout)
            if format is int:
                validator = QIntValidator(temp_base)
            elif format is float:
                validator = QDoubleValidator(temp_base)
            else:
                validator = None
            for ni in range(number_of_inputs):
                widget_instance = widget(var_base)
                widget_instance.setText(str(values[ni]))
                widget_instance.setToolTip(tooltip)
                widget_instance.setPlaceholderText(placeholder)
                if validator is not None:
                    widget_instance.setValidator(validator)
                temp_layout.addWidget(widget_instance)
                var.input_widgets.append(widget_instance)
            var_layout.addRow(label, temp_base)
        # optinally we can add other buttons here...
        #
        # final button, always there
        self.button = QPushButton("Accept!", self)
        self.button.clicked.connect(self.accept)
        self.accepted.connect(self.return_value)
        button_layout.addWidget(self.button)

    @Slot()
    def return_value(self):
        result = {}
        for var in self.fields:
            temp = var.returnValues()
            if var.number_of_inputs == 1:
                value = temp[0]
            else:
                value = temp
            result[var.keyval] = value
        self.got_values.emit(result)

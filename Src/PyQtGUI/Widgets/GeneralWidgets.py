
from typing import Union, Iterable
from collections import OrderedDict
import copy

from icecream import ic
from qtpy.QtWidgets import QDialog, QPushButton, QFileDialog, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QSizePolicy, QMenu, QLineEdit, QTableView,\
                           QFormLayout, QHBoxLayout, QCheckBox
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel,\
                        QObject
from qtpy.QtGui import QFont, QEnterEvent, QStandardItem, QStandardItemModel,\
                    QIntValidator, QDoubleValidator, QValidator

from MDANSE.Framework.Jobs.IJob import IJob


class InputVariable(QObject):

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


class GeneralInput(QObject):

    final_value = Signal(object)
    string_value = Signal(str)

    def __init__(self, *args, data_type = None, **kwargs):
        new_kwargs = copy.copy(kwargs)
        for kkey in InputFactory.reserved_keywords:
            if kkey in new_kwargs.keys():
                new_kwargs.pop(kkey)
        super().__init__(*args, **{})

        self.default_path = kwargs.get('path', None)
        self.data_type = data_type
        self.default_value = kwargs.get('default', None)
        self.current_value = self.default_value
        self.file_association = kwargs.get('file_association', None)
        self.file_direction = kwargs.get('file_direction', 'none')
        self.file_format = kwargs.get('format','')
        if self.file_association is not None:
            if len(self.file_association) < 1 and len(self.file_format) > 1:
                self.file_association = '*.' + self.file_format
        if self.file_direction == 'in':
            self.file_dialog = QFileDialog.getOpenFileName
        elif self.file_direction == 'out':
            self.file_dialog = QFileDialog.getSaveFileName
        else:
            self.file_dialog = None
        ic(kwargs)
    
    @Slot(str)
    def updatePath(self, newpath: str):
        self.default_path = newpath

    @Slot(str)
    @Slot(int)
    @Slot(object)
    def updateValue(self, newone, emit = False):
        try:
            converted = self.data_type(newone)
        except ValueError:
            converted = self.default_value
            ic(f"ValueError converting {newone} using {self.data_type}")
        except TypeError:
            converted = self.default_value
            ic(f"TypeError converting {newone} using {self.data_type}")
        self.current_value = converted
        if emit:
            self.string_value.emit(self.current_value)

    def returnValue(self):
        if self.file_dialog is not None:
            ic(f"File Field Return Value: {self.current_value}")
        self.final_value.emit(self.current_value)
        if self.file_direction == 'out':
            return (self.current_value, 'hdf')
        return self.current_value

    @Slot()
    def valueFromDialog(self):
        new_value = self.file_dialog(self.parent(),  # the parent of the dialog
                                    "Load a file",  # the label of the window
                                    self.default_path,  # the initial search path
                                    self.file_association  # text string specifying the file name filter.
                                    )
        if new_value is not None:
            self.updateValue(new_value[0], emit = True)


def translate_file_associations(input_str: str):
    toks = input_str.split('|')[::2]
    basic_replacement = ";;".join(toks[:-1] + ["All files (*.*)"])
    return basic_replacement


class InputFactory():

    reserved_keywords = ['kind', 'default', 'label', 'tooltip', 'wildcard',
                         'mini',
                         'file_association', 'file_direction']

    def createInputField(*args, **kwargs):
        kind = kwargs.get('kind', 'str')

        if kind == 'str':
            result = InputFactory.createSingle(*args, **kwargs)
        elif kind == 'int' or kind == 'integer':
            result = InputFactory.createSingle(*args, **kwargs)
        elif kind == 'float':
            result = InputFactory.createSingle(*args, **kwargs)
        elif kind == 'bool' or kind == 'boolean':
            result = InputFactory.createBool(*args, **kwargs)
        elif kind == 'input_file':
            result = InputFactory.createFile(*args, direction = 'in', **kwargs)
        elif kind == 'single_output_file':
            result = InputFactory.createFile(*args, direction = 'out', **kwargs)
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
        parent = kwargs.get('parent', None)
        label_text = kwargs.get('label', None)
        tooltip_text = kwargs.get('tooltip', None)
        base = QWidget(parent)
        layout = QHBoxLayout(base)
        base.setLayout(layout)
        label = QLabel(label_text, base)
        label.setToolTip(tooltip_text)
        layout.addWidget(label)
        return [base, layout]
    
    def createBlank(*args, **kwargs):
        kind = kwargs.get('kind', 'str')
        base, layout = InputFactory.createBase(
            label = f"<b>MISSING TYPE</b>:{kind}",
            tooltip = 'This is not handled by the MDANSE GUI correctly! Please report the problem to the authors.')
        return [base, GeneralInput()]

    def createFile(*args, direction = 'in', **kwargs):
        kind = kwargs.get('kind', 'str')
        default_value = kwargs.get('default', "")
        tooltip_text = kwargs.get('tooltip', "Specify a path to an existing file.")
        file_association = kwargs.get('wildcard', "")
        qt_file_association = translate_file_associations(file_association)
        ic(kind)
        ic(default_value)
        ic(tooltip_text)
        ic(file_association)
        ic(kwargs)
        base, layout = InputFactory.createBase(*args, **kwargs)
        field = QLineEdit(base)
        data_handler = GeneralInput(data_type=str, file_association = qt_file_association, file_direction = direction, **kwargs)
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
        kind = kwargs.get('kind', 'bool')
        default_value = kwargs.get('default', False)
        tooltip_text = kwargs.get('tooltip', None)
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
        kind = kwargs.get('kind', 'str')
        default_value = kwargs.get('default', None)
        tooltip_text = kwargs.get('tooltip', None)
        minval = kwargs.get('mini', None)
        ic(kind)
        ic(default_value)
        ic(tooltip_text)
        ic(kwargs)
        base, layout = InputFactory.createBase(*args, **kwargs)
        field = QLineEdit(base)
        if kind == 'int' or kind == 'integer':
            data_handler = GeneralInput(data_type=int, **kwargs)
            validator = QIntValidator(field)
        elif kind == 'float':
            data_handler = GeneralInput(data_type=float, **kwargs)
            validator = QDoubleValidator(field)
        elif kind == 'str':
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
    

class ConverterDialog(QDialog):

    new_thread_objects = Signal(list)
    new_path = Signal(str)

    def __init__(self, *args, converter: IJob = 'Dummy', **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.handlers = {}
        self.converter_instance = None
        self.converter_constructor = converter
        self.default_path = '.'

        if converter == 'Dummy':
            settings = OrderedDict([('dummy int', ('int', {'default': 1.0, 'label': 'Time step (ps)'})),
                                    ('time_step', ('float', {'default': 1.0, 'label': 'Time step (ps)'})),
                                    ('fold', ('boolean', {'default': False, 'label': 'Fold coordinates in to box'})),
                                    # ('dcd_file', ('input_file', {'wildcard': 'DCD files (*.dcd)|*.dcd|All files|*', 'default': '../../../Data/Trajectories/CHARMM/2vb1.dcd'})),
                                    # ('output_file', ('single_output_file', {'format': 'hdf', 'root': 'pdb_file'}))
                                    ])
        else:
            converter_instance = converter()
            converter_instance.build_configuration()
            settings = converter_instance.settings
            self.converter_instance = converter_instance
        for key, value in settings.items():
            dtype = value[0]
            ddict = value[1]
            defaultvalue = ddict.get('default', 0.0)
            labeltext = ddict.get('label', "Mystery X the Unknown")
            base, data_handler = InputFactory.createInputField(parent = self, kind = dtype, **ddict)
            layout.addWidget(base)
            self.handlers[key] = data_handler
        
        buttonbase = QWidget(self)
        buttonlayout = QHBoxLayout(buttonbase)
        buttonbase.setLayout(buttonlayout)
        self.cancel_button = QPushButton("Cancel", buttonbase)
        self.execute_button = QPushButton("CONVERT!", buttonbase)
        self.execute_button.setStyleSheet("font-weight: bold")

        self.cancel_button.clicked.connect(self.cancel_dialog)
        self.execute_button.clicked.connect(self.execute_converter)

        buttonlayout.addWidget(self.cancel_button)
        buttonlayout.addWidget(self.execute_button)

        layout.addWidget(buttonbase)
    
    @Slot(dict)
    def parse_updated_params(self, new_params: dict):
        if 'path' in new_params.keys():
            self.default_path = new_params['path']
            self.new_path.emit(self.default_path)

    @Slot()
    def cancel_dialog(self):
        self.destroy()

    @Slot()
    def execute_converter(self):
        if self.converter_instance is None:
            ic("No converter instance attached to the Dialog")
            return False
        pardict = {}
        ic(f"handlers: {self.handlers}")
        for key, value in self.handlers.items():
            pardict[key] = value.returnValue()
        ic(f"Passing {pardict} to the converter instance {self.converter_instance}")
        self.converter_instance.setup(pardict)
        # when we are ready, we can consider running it
        self.converter_instance.run(pardict)
        # this would send the actual instance, which _may_ be wrong
        # self.new_thread_objects.emit([self.converter_instance, pardict])
        # self.new_thread_objects.emit([self.converter_constructor, pardict])





class InputDialog(QDialog):

    got_values = Signal(dict)

    def __init__(self, *args, fields: Iterable['InputVariable'] = None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields = fields #  we need to store it for later
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

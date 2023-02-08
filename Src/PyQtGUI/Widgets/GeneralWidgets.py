
from typing import Union, Iterable
from collections import OrderedDict
import copy

from icecream import ic

from qtpy.QtWidgets import QDialog, QPushButton, QFrame, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QSizePolicy, QMenu, QLineEdit, QTableView,\
                           QFormLayout, QHBoxLayout
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

    def __init__(self, *args, data_type = None, **kwargs):
        new_kwargs = copy.copy(kwargs)
        for kkey in InputFactory.reserved_keywords:
            if kkey in new_kwargs.keys():
                new_kwargs.pop(kkey)
        super().__init__(*args, **new_kwargs)

        self.data_type = data_type
        self.default_value = getattr(kwargs, 'default', None)
        self.current_value = self.default_value

    @Slot(str)
    @Slot(object)
    def updateValue(self, newone):
        try:
            converted = self.data_type(newone)
        except ValueError:
            converted = self.default_value
            ic(f"ValueError converting {newone} using {self.data_type}")
        except TypeError:
            converted = self.default_value
            ic(f"TypeError converting {newone} using {self.data_type}")
        self.current_value = converted

    def returnValue(self):
        self.final_value.emit(self.current_value)
        return self.current_value



class InputFactory():

    reserved_keywords = ['kind', 'default_value', 'label', 'tooltip']

    def createInputField(*args, **kwargs):
        kind = kwargs.get('kind', 'str')

        if kind == 'str':
            result = InputFactory.createSingle(*args, **kwargs)
        elif kind == 'int':
            result = InputFactory.createSingle(*args, **kwargs)
        elif kind == 'float':
            result = InputFactory.createSingle(*args, **kwargs)
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
        return [base, layout]

    def createSingle(*args, **kwargs):
        kind = kwargs.get('kind', 'str')
        default_value = kwargs.get('default_value', None)
        tooltip_text = kwargs.get('tooltip', None)
        ic(kind)
        ic(default_value)
        ic(tooltip_text)
        ic(kwargs)
        base, layout = InputFactory.createBase(*args, **kwargs)
        field = QLineEdit(base)
        if kind == 'int':
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
        field.textChanged.connect(data_handler.updateValue)
        field.setText(str(default_value))
        field.setToolTip(tooltip_text)
        layout.addWidget(field)
        return [base, data_handler]
    

class ConverterDialog(QDialog):


    def __init__(self, *args, converter: IJob = 'Dummy', **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.handlers = {}

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
        for key, value in settings.items():
            dtype = value[0]
            ddict = value[1]
            defaultvalue = ddict.get('default', 0.0)
            labeltext = ddict.get('label', "Mystery X the Unknown")
            base, data_handler = InputFactory.createInputField(kind = dtype, default_value = defaultvalue, label = labeltext)
            layout.addWidget(base)
            self.handlers[key] = data_handler






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

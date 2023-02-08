
from typing import Union, Iterable

from qtpy.QtWidgets import QDialog, QPushButton, QFrame, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QSizePolicy, QMenu, QLineEdit, QTableView,\
                           QFormLayout, QHBoxLayout
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel,\
                        QObject
from qtpy.QtGui import QFont, QEnterEvent, QStandardItem, QStandardItemModel,\
                    QIntValidator, QDoubleValidator, QValidator



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


class InputFactory():

    def createInputField(self, *args, kind = 'int', **kwargs):

        if kind == 'int':
            result = self.createInt(*args, **kwargs)
        
        return result
    
    def createBase(self, *args, **kwargs):
        """Some parts of the input will always be the same,
        so we handle them in one function that will be called
        before we get to the specific details

        Returns:
            [base, layout] pair of QWidget and associated layout
        """
        parent = getattr(kwargs, 'parent', None)
        label_text = getattr(kwargs, 'label', None)
        tooltip_text = getattr(kwargs, 'tooltip', None)
        base = QWidget(parent)
        layout = QHBoxLayout(base)
        base.setLayout(layout)
        label = QLabel(label_text)
        label.setToolTip(tooltip_text)
        layout.addWidget(label)
        return [base, layout]


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

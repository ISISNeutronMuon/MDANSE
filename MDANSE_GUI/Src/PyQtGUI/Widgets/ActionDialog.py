from typing import Union, Iterable
from collections import OrderedDict
import copy
import os

from icecream import ic
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
from MDANSE_GUI.PyQtGUI.Widgets.GeneralWidgets import InputFactory


class ActionDialog(QDialog):
    new_thread_objects = Signal(list)
    new_path = Signal(str)

    last_paths = {}

    def __init__(self, *args, converter: IJob = "Dummy", **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.handlers = {}
        self.converter_instance = None
        self.converter_constructor = converter
        self.default_path = "."
        try:
            cname = converter.name
        except:
            pass
        else:
            self.cname = cname
            self.last_paths[cname] = "."

        if converter == "Dummy":
            settings = OrderedDict(
                [
                    ("dummy int", ("int", {"default": 1.0, "label": "Time step (ps)"})),
                    (
                        "time_step",
                        ("float", {"default": 1.0, "label": "Time step (ps)"}),
                    ),
                    (
                        "fold",
                        (
                            "boolean",
                            {"default": False, "label": "Fold coordinates in to box"},
                        ),
                    ),
                    # ('dcd_file', ('input_file', {'wildcard': 'DCD files (*.dcd)|*.dcd|All files|*', 'default': '../../../Data/Trajectories/CHARMM/2vb1.dcd'})),
                    # ('output_file', ('single_output_file', {'format': 'hdf', 'root': 'pdb_file'}))
                ]
            )
        else:
            converter_instance = converter()
            converter_instance.build_configuration()
            settings = converter_instance.settings
            self.converter_instance = converter_instance
        for key, value in settings.items():
            dtype = value[0]
            ddict = value[1]
            defaultvalue = ddict.get("default", 0.0)
            labeltext = ddict.get("label", "Mystery X the Unknown")
            base, data_handler = InputFactory.createInputField(
                parent=self, kind=dtype, **ddict
            )
            layout.addWidget(base)
            self.handlers[key] = data_handler

        buttonbase = QWidget(self)
        buttonlayout = QHBoxLayout(buttonbase)
        buttonbase.setLayout(buttonlayout)
        self.cancel_button = QPushButton("Cancel", buttonbase)
        self.save_button = QPushButton("Save as script", buttonbase)
        self.execute_button = QPushButton("RUN!", buttonbase)
        self.execute_button.setStyleSheet("font-weight: bold")

        self.cancel_button.clicked.connect(self.cancel_dialog)
        self.save_button.clicked.connect(self.save_dialog)
        self.execute_button.clicked.connect(self.execute_converter)

        buttonlayout.addWidget(self.cancel_button)
        buttonlayout.addWidget(self.save_button)
        buttonlayout.addWidget(self.execute_button)

        layout.addWidget(buttonbase)

    @Slot(dict)
    def parse_updated_params(self, new_params: dict):
        if "path" in new_params.keys():
            self.default_path = new_params["path"]
            self.new_path.emit(self.default_path)

    @Slot()
    def cancel_dialog(self):
        self.destroy()

    @Slot()
    def save_dialog(self):
        try:
            cname = self.cname
        except:
            currentpath = "."
        else:
            currentpath = self.last_paths[cname]
        result, ftype = QFileDialog.getSaveFileName(
            self, "Save job as a Python script", currentpath, "Python script (*.py)"
        )
        if result is None:
            return None
        path, _ = os.path.split(result)
        try:
            cname = self.cname
        except:
            pass
        else:
            self.last_paths[cname] = path
        pardict = self.set_parameters()
        self.converter_instance.save(result, pardict)

    def set_parameters(self):
        if self.converter_instance is None:
            ic("No converter instance attached to the Dialog")
            return False
        pardict = {}
        ic(f"handlers: {self.handlers}")
        for key, value in self.handlers.items():
            pardict[key] = value.returnValue()
        ic(f"Passing {pardict} to the converter instance {self.converter_instance}")
        self.converter_instance.setup(pardict)
        return pardict

    @Slot()
    def execute_converter(self):
        pardict = self.set_parameters()
        # when we are ready, we can consider running it
        self.converter_instance.run(pardict)
        # this would send the actual instance, which _may_ be wrong
        # self.new_thread_objects.emit([self.converter_instance, pardict])
        # self.new_thread_objects.emit([self.converter_constructor, pardict])
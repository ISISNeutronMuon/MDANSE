
from typing import Union, Iterable
from collections import OrderedDict
import copy

from icecream import ic
from qtpy.QtWidgets import QDialog, QPushButton, QFileDialog, QGridLayout,\
                           QVBoxLayout, QWidget, QLabel, QApplication,\
                           QComboBox, QMenu, QLineEdit, QTableView,\
                           QFormLayout, QHBoxLayout, QCheckBox, \
                           QWizard, QWizardPage
from qtpy.QtCore import Signal, Slot, Qt, QPoint, QSize, QSortFilterProxyModel,\
                        QObject
from qtpy.QtGui import QFont, QEnterEvent, QStandardItem, QStandardItemModel,\
                    QIntValidator, QDoubleValidator, QValidator

from MDANSE.Framework.Jobs.IJob import IJob
# from MDANSE.Framework.Jobs.Converter import InteractiveConverter
from MDANSE.PyQtGUI.Widgets.GeneralWidgets import GeneralInput, InputFactory

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


class ConvertWizard(QWizard):

    def __init__(self, *args, converter: IJob = 'Dummy', **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle(str(converter) + " wizard")

        self.converter_instance = None
        self.converter_constructor = converter
        self.default_path = '.'

        converter_instance = InteractiveConverter.create(converter)()
        converter_instance.build_configuration()
        settings = converter_instance.settings
        self.converter_instance = converter_instance

        firstone = self.converter_instance.primaryInputs()
        firstpage = ConverterFirstPage(self, parameter_dict = firstone)
        self.addPage(firstpage)

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

class ConverterFirstPage(QWizardPage):

    new_thread_objects = Signal(list)
    new_path = Signal(str)

    def __init__(self, *args, parameter_dict : dict = {}, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.handlers = {}
        self.default_path = '.'

        if len(parameter_dict) < 1:
            settings = OrderedDict([('dummy int', ('int', {'default': 1.0, 'label': 'Time step (ps)'})),
                                    ('time_step', ('float', {'default': 1.0, 'label': 'Time step (ps)'})),
                                    ('fold', ('boolean', {'default': False, 'label': 'Fold coordinates in to box'})),
                                    # ('dcd_file', ('input_file', {'wildcard': 'DCD files (*.dcd)|*.dcd|All files|*', 'default': '../../../Data/Trajectories/CHARMM/2vb1.dcd'})),
                                    # ('output_file', ('single_output_file', {'format': 'hdf', 'root': 'pdb_file'}))
                                    ])
        else:
            settings = parameter_dict
        for key, value in settings.items():
            dtype = value[0]
            ddict = value[1]
            defaultvalue = ddict.get('default', 0.0)
            labeltext = ddict.get('label', "Mystery X the Unknown")
            base, data_handler = InputFactory.createInputField(parent = self, kind = dtype, **ddict)
            layout.addWidget(base)
            self.handlers[key] = data_handler
    
    @Slot(dict)
    def parse_updated_params(self, new_params: dict):
        if 'path' in new_params.keys():
            self.default_path = new_params['path']
            self.new_path.emit(self.default_path)

    @Slot()
    def cancel_dialog(self):
        self.destroy()
    
    def validatePage(self) -> bool:
        # here we could try to parse some stuff.
        return super().validatePage()





import sys

from qtpy.QtWidgets import QApplication, QMainWindow, QPushButton
from qtpy.QtCore import QSettings, QThread, Qt

from MDANSE.PyQtGUI.MainWindow import Main
from MDANSE.PyQtGUI.BackEnd import BackEnd
from MDANSE.PyQtGUI.Widgets.Generator import WidgetGenerator

from MDANSE.Framework.Jobs.Converter import InteractiveConverter

class DummyLauncher(QMainWindow):

    def __init__(self, *args, title = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.setWindowTitle(title)

        self.widgen = WidgetGenerator()

        # butt = QPushButton("Launch The Wizard!")
        # butt.clicked.connect(self.launchWizard)
        # butt.setText("Launch The Wizard!")

        docker, button = self.widgen.wrapWidget(cls = QPushButton, parent= self, dockable = True,
                                             name="Trajectories")
        # lay = self.layout()
        # lay.addWidget(butt)

        button.clicked.connect(self.launchWizard)
        button.setText("Launch The Wizard!")

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, docker)

    @Slot()
    def launchWizard(self):
        whizz = ConvertWizard(converter = 'ase')
        whizz.show()
        result = whizz.result()

def startGUI(some_args):
    app = QApplication(some_args)
    root = DummyLauncher(parent=None, title = "<b>dummy</b> window!")
    root.show()
    app.exec()

if __name__ == '__main__':
    startGUI(sys.argv)

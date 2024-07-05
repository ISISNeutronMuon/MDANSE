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
import logging
from collections import OrderedDict

import qtpy
from qtpy.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QWizard,
    QWizardPage,
    QProgressBar,
)
from qtpy.QtCore import Signal, Slot

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE_GUI.Widgets.GeneralWidgets import InputFactory

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


LOG = logging.getLogger("MDANSE")


class ConvertWizard(QWizard):
    def __init__(self, *args, converter: IJob = "Dummy", **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle(str(converter) + " wizard")

        self.converter_instance = None
        self.converter_constructor = converter
        self.default_path = "."

        converter_instance = InteractiveConverter.create(converter)()
        converter_instance.build_configuration()
        settings = converter_instance.settings
        self.converter_instance = converter_instance

        for page_dict in self.converter_instance:
            self.addPage(ConverterPage(page_dict))

        firstone = self.converter_instance.primaryInputs()
        middleone = self.converter_instance.secondaryInputs()
        lastone = self.converter_instance.finalInputs()
        firstpage = ConverterFirstPage(self, parameter_dict=firstone)
        progpage = ConverterProgressPage(self)
        secondpage = ConverterSecondPage(self, parameter_dict=middleone)
        thirdpage = ConverterThirdPage(self, parameter_dict=lastone)
        # will adding the pages at the end help avoid the race condition?
        self.addPage(firstpage)
        self.addPage(secondpage)
        self.addPage(progpage)
        self.addPage(thirdpage)

    @Slot()
    def execute_converter(self):
        if self.converter_instance is None:
            LOG.error("No converter instance attached to the Dialog")
            return False
        pardict = {}
        LOG.info(f"handlers: {self.handlers}")
        for key, value in self.handlers.items():
            pardict[key] = value.returnValue()
        LOG.info(f"Passing {pardict} to the converter instance {self.converter_instance}")
        self.converter_instance.setup(pardict)
        # when we are ready, we can consider running it
        self.converter_instance.run(pardict)
        # this would send the actual instance, which _may_ be wrong
        # self.new_thread_objects.emit([self.converter_instance, pardict])
        # self.new_thread_objects.emit([self.converter_constructor, pardict])

    def setInputFiles(self, input_filenames: list[str]):
        """This function is called by a wizard page. The wizard will pass the
        input parameters (i.e. file names) to the instance of the InteractiveConverter.
        This way the converter will be able to read information from the input
        files, and make it available in the next page of the wizard.

        Arguments
        ---------
            trajectory_filename (str) : name of the trajectory to be read.
            configuration_filename (str) : name of an optional configuration file.
        """
        self.converter_instance.setFilenames(...)

    # def closeEvent(self, event) -> None:
    #     event.accept()
    #     # return super().closeEvent(event)


class ConverterPage(QWizardPage):
    """The first page of the converter is where the user can specify
    the input files.
    """

    new_thread_objects = Signal(list)
    new_path = Signal(str)

    def __init__(self, *args, parameter_dict: dict = {}, **kwargs):
        super().__init__(*args, **kwargs)
        LOG.info(dir(self))
        # ic(dir(self.wizard()))
        self.setTitle("The Input Files")
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.handlers = {}
        self.default_path = "."

        if len(parameter_dict) < 1:
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
            settings = parameter_dict
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

    @Slot(dict)
    def parse_updated_params(self, new_params: dict):
        if "path" in new_params.keys():
            self.default_path = new_params["path"]
            self.new_path.emit(self.default_path)

    def initializePage(self) -> None:
        return super().initializePage()

    @Slot()
    def cancel_dialog(self):
        self.destroy()

    def validatePage(self) -> bool:
        # here we could try to parse some stuff.
        return super().validatePage()


class ConverterFirstPage(QWizardPage):
    """The first page of the converter is where the user can specify
    the input files.
    """

    new_thread_objects = Signal(list)
    new_path = Signal(str)

    def __init__(self, *args, parameter_dict: dict = {}, **kwargs):
        super().__init__(*args, **kwargs)
        LOG.info(dir(self))
        # ic(dir(self.wizard()))
        self.setTitle("The Input Files")
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.handlers = {}
        self.default_path = "."

        if len(parameter_dict) < 1:
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
            settings = parameter_dict
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

    @Slot(dict)
    def parse_updated_params(self, new_params: dict):
        if "path" in new_params.keys():
            self.default_path = new_params["path"]
            self.new_path.emit(self.default_path)

    def initializePage(self) -> None:
        return super().initializePage()

    @Slot()
    def cancel_dialog(self):
        self.destroy()

    def validatePage(self) -> bool:
        # here we could try to parse some stuff.
        return super().validatePage()


class ConverterProgressPage(QWizardPage):
    """The page with a progress bar will be shown whenever
    some inputs are processed. The typical use cases will be:
    1) preliminary reading of the input files,
    2) actual conversion of the trajectory.
    """

    new_thread_objects = Signal(list)
    new_path = Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTitle("Work in progress")
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        tag = QLabel("Your inputs are being processed!", self)
        self.progbar = QProgressBar(self)
        layout.addWidget(tag)
        layout.addWidget(self.progbar)

    def initializePage(self) -> None:
        return super().initializePage()

    @Slot()
    def cancel_dialog(self):
        self.destroy()

    def validatePage(self) -> bool:
        # here we could try to parse some stuff.
        return super().validatePage()


class ConverterSecondPage(QWizardPage):
    """The second page is the most complicated one: it will
    allow the user to modify some of the parameters after
    they have been read from the files.
    """

    new_thread_objects = Signal(list)
    new_path = Signal(str)

    def __init__(self, *args, parameter_dict: dict = {}, **kwargs):
        super().__init__(*args, **kwargs)
        # ic(dir(self))
        # ic(dir(self.wizard()))
        self.setTitle("Verify the information")

        self.parameter_dict = parameter_dict
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.handlers = {}
        self.default_path = "."
        parameter_dict = self.parameter_dict

        if len(parameter_dict) < 1:
            settings = OrderedDict(
                [
                    (
                        "first_frame",
                        ("int", {"default": 1.0, "label": "Number of the first frame"}),
                    ),
                    (
                        "last_frame",
                        ("int", {"default": 1.0, "label": "Number of the last frame"}),
                    ),
                    (
                        "frame_step",
                        (
                            "int",
                            {"default": 1.0, "label": "Step (take every N frames)"},
                        ),
                    ),
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
                ]
            )
        else:
            settings = parameter_dict
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

    def initializePage(self) -> None:
        return super().initializePage()

    @Slot()
    def cancel_dialog(self):
        self.destroy()

    def validatePage(self) -> bool:
        # here we could try to parse some stuff.
        return super().validatePage()


class ConverterThirdPage(QWizardPage):
    """This page will normally be used just to specify the name
    of the output file.
    """

    new_thread_objects = Signal(list)
    new_path = Signal(str)

    def __init__(self, *args, parameter_dict: dict = {}, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTitle("The Output File")

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.handlers = {}
        self.default_path = "."

        if len(parameter_dict) < 1:
            settings = OrderedDict(
                [("single_output_file", {"format": "MDTFormat", "root": "config_file"})]
            )
        else:
            settings = parameter_dict
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

    @Slot()
    def cancel_dialog(self):
        self.destroy()

    def validatePage(self) -> bool:
        # here we could try to parse some stuff.
        return super().validatePage()


import sys

from qtpy.QtWidgets import QApplication, QMainWindow, QPushButton
from qtpy.QtCore import Qt

from MDANSE_GUI.Widgets.Generator import WidgetGenerator


class DummyLauncher(QMainWindow):
    def __init__(self, *args, title=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle(title)

        self.widgen = WidgetGenerator()

        # butt = QPushButton("Launch The Wizard!")
        # butt.clicked.connect(self.launchWizard)
        # butt.setText("Launch The Wizard!")

        docker, button = self.widgen.wrapWidget(
            cls=QPushButton, parent=self, dockable=True, name="Trajectories"
        )
        # lay = self.layout()
        # lay.addWidget(butt)

        button.clicked.connect(self.launchWizard)
        button.setText("Launch The Wizard!")

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, docker)

    @Slot()
    def launchWizard(self):
        whizz = ConvertWizard(converter="ase")
        whizz.show()
        result = whizz.result()
        # whizz.accept()


def startGUI(some_args):
    LOG.info(qtpy.API)
    app = QApplication(some_args)
    root = DummyLauncher(parent=None, title="<b>dummy</b> window!")
    root.show()
    app.exec()


if __name__ == "__main__":
    startGUI(sys.argv)

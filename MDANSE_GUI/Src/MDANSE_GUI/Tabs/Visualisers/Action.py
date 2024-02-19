# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      MDANSE_GUI/Tabs/Visualisers/Action.py
# @brief     Base widget for the MDANSE GUI
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Research Software Group at ISIS (see AUTHORS)
#
# *************************************************************************
from typing import Optional
from qtpy.QtWidgets import (
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QScrollArea,
)
from qtpy.QtCore import Signal, Slot
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE_GUI.InputWidgets import *


widget_lookup = {  # these all come from MDANSE_GUI.InputWidgets
    "FloatConfigurator": FloatWidget,
    "BooleanConfigurator": BooleanWidget,
    "StringConfigurator": StringWidget,
    "IntegerConfigurator": IntegerWidget,
    "FramesConfigurator": FramesWidget,
    "RangeConfigurator": RangeWidget,
    "HDFTrajectoryConfigurator": HDFTrajectoryWidget,
    "InterpolationOrderConfigurator": InterpolationOrderWidget,
    "OutputFilesConfigurator": OutputFilesWidget,
    "InputFileConfigurator": InputFileWidget,
    "RunningModeConfigurator": RunningModeWidget,
    "WeightsConfigurator": ComboWidget,
    "GroupingLevelConfigurator": ComboWidget,
    "SingleChoiceConfigurator": ComboWidget,
    "QVectorsConfigurator": QVectorsWidget,
    "InputDirectoryConfigurator": InputDirectoryWidget,
    "OutputDirectoryConfigurator": OutputDirectoryWidget,
    "OutputTrajectoryConfigurator": OutputTrajectoryWidget,
    "ProjectionConfigurator": ProjectionWidget,
    "AtomSelectionConfigurator": AtomSelectionWidget,
    "AtomTransmutationConfigurator": AtomTransmutationWidget,
    "InstrumentResolutionConfigurator": InstrumentResolutionWidget,
}


class Action(QWidget):
    new_thread_objects = Signal(list)
    new_path = Signal(str)

    last_paths = {}

    def __init__(self, *args, **kwargs):
        self._default_path = None
        self._input_trajectory = None
        self._trajectory_configurator = None
        default_path = kwargs.pop("path", None)
        input_trajectory = kwargs.pop("trajectory", None)
        self.set_trajectory(default_path, input_trajectory)
        super().__init__(*args, **kwargs)

        buffer = QWidget(self)
        scroll_area = QScrollArea()
        scroll_area.setWidget(buffer)
        scroll_area.setWidgetResizable(True)
        self.layout = QVBoxLayout(buffer)
        base_layout = QVBoxLayout(self)
        buffer.setLayout(self.layout)
        base_layout.addWidget(scroll_area)
        self.setLayout(base_layout)
        self.handlers = {}
        self._widgets = []
        self._widgets_in_layout = []

    def set_trajectory(self, path: Optional[str], trajectory: Optional[str]) -> None:
        """Set the trajectory path and filename.

        Parameters
        ----------
        path : str or None
            The path of the trajectory
        trajectory : str or None
            The path and filename of the trajectory
        """
        self._default_path = path
        self._input_trajectory = trajectory
        path = None
        if self._input_trajectory is not None:
            path, filename = os.path.split(self._input_trajectory)
        if self._default_path is None:
            if path is None:
                self._default_path = "."
            else:
                self._default_path = path

    def clear_widgets(self) -> None:
        """Clear the widgets so that it leaves an empty layout"""
        for widget in self._widgets_in_layout:
            widget.setParent(None)
            self.layout.removeWidget(widget)
        self._widgets = []
        self._widgets_in_layout = []

    def set_widgets(self, job_name: str) -> None:
        """Sets all the widgets for the selected job.

        Parameters
        ----------
        job_name : str
            The job name.
        """
        self.clear_widgets()

        self._job_name = job_name
        self.last_paths[job_name] = "."
        try:
            job_instance = IJob.create(job_name)
        except ValueError as e:
            print(f"Failed to create IJob {job_name}")
            return
        job_instance.build_configuration()
        settings = job_instance.settings
        self._job_instance = job_instance
        print(f"Settings {settings}")
        print(f"Configuration {job_instance.configuration}")
        if "trajectory" in settings.keys():
            if self._input_trajectory is None:
                return
            key, value = "trajectory", settings["trajectory"]
            dtype = value[0]
            ddict = value[1]
            configurator = job_instance.configuration[key]
            configurator.configure(self._input_trajectory)
            if not "label" in ddict.keys():
                ddict["label"] = key
            ddict["configurator"] = configurator
            ddict["source_object"] = self._input_trajectory
            widget_class = widget_lookup[dtype]
            input_widget = widget_class(parent=self, **ddict)
            widget = input_widget._base
            self.layout.addWidget(widget)
            self._widgets_in_layout.append(widget)
            self._widgets.append(input_widget)
            self._trajectory_configurator = input_widget._configurator
            print("Set up input trajectory")
        for key, value in settings.items():
            if key == "trajectory":
                continue
            dtype = value[0]
            ddict = value[1]
            configurator = job_instance.configuration[key]
            if not "label" in ddict.keys():
                ddict["label"] = key
            ddict["configurator"] = configurator
            ddict["source_object"] = self._input_trajectory
            ddict["trajectory_configurator"] = self._trajectory_configurator
            if not dtype in widget_lookup.keys():
                ddict["tooltip"] = (
                    "This is not implemented in the MDANSE GUI at the moment, and it MUST BE!"
                )
                placeholder = BackupWidget(parent=self, **ddict)
                widget = placeholder._base
                self.layout.addWidget(widget)
                self._widgets_in_layout.append(widget)
                self._widgets.append(placeholder)
                print(f"Could not find the right widget for {key}")
            else:
                widget_class = widget_lookup[dtype]
                # expected = {key: ddict[key] for key in widget_class.__init__.__code__.co_varnames}
                input_widget = widget_class(parent=self, **ddict)
                widget = input_widget._base
                self.layout.addWidget(widget)
                self._widgets_in_layout.append(widget)
                self._widgets.append(input_widget)
                input_widget.valid_changed.connect(self.allow_execution)
                print(f"Set up the right widget for {key}")
            # self.handlers[key] = data_handler
            configured = False
            iterations = 0
            while not configured:
                configured = True
                for widget in self._widgets:
                    widget.value_from_configurator()
                    configured = configured and widget._configurator.is_configured()
                iterations += 1
                if iterations > 5:
                    break

        buttonbase = QWidget(self)
        buttonlayout = QHBoxLayout(buttonbase)
        buttonbase.setLayout(buttonlayout)
        self.save_button = QPushButton("Save as script", buttonbase)
        self.execute_button = QPushButton("RUN!", buttonbase)
        self.execute_button.setStyleSheet("font-weight: bold")

        self.save_button.clicked.connect(self.save_dialog)
        self.execute_button.clicked.connect(self.execute_converter)

        buttonlayout.addWidget(self.save_button)
        buttonlayout.addWidget(self.execute_button)
    
        self.layout.addWidget(buttonbase)
        self._widgets_in_layout.append(buttonbase)

    @Slot(dict)
    def parse_updated_params(self, new_params: dict):
        if "path" in new_params.keys():
            self.default_path = new_params["path"]
            self.new_path.emit(self.default_path)

    @Slot()
    def allow_execution(self):
        allow = True
        for widget in self._widgets:
            if not widget._configurator.valid:
                allow = False
        if allow:
            self.execute_button.setEnabled(True)
        else:
            self.execute_button.setEnabled(False)

    @Slot()
    def cancel_dialog(self):
        self.destroy()

    @Slot()
    def save_dialog(self):
        try:
            cname = self._job_name
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
            cname = self._job_name
        except:
            pass
        else:
            self.last_paths[cname] = path
        pardict = self.set_parameters(mock_labels=True)
        self._job_instance.save(result, pardict)

    def set_parameters(self, mock_labels=False):
        results = {}
        for widnum, key in enumerate(self._job_instance.settings.keys()):
            if mock_labels:
                results[key] = (self._widgets[widnum].get_widget_value(), "")
            else:
                results[key] = self._widgets[widnum].get_widget_value()
        return results

    @Slot()
    def execute_converter(self):
        pardict = self.set_parameters()
        print(pardict)
        # when we are ready, we can consider running it
        # self.converter_instance.run(pardict)
        # this would send the actual instance, which _may_ be wrong
        # self.new_thread_objects.emit([self.converter_instance, pardict])
        self.new_thread_objects.emit([self._job_name, pardict])

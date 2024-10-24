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
from typing import Optional
import traceback

import numpy as np
from qtpy.QtWidgets import (
    QPushButton,
    QFileDialog,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QCheckBox,
    QTextEdit,
)
from qtpy.QtCore import Signal, Slot

from MDANSE.MLogging import LOG
from MDANSE.Framework.Jobs.IJob import IJob

from MDANSE_GUI.InputWidgets import *
from MDANSE_GUI.Tabs.Visualisers.InstrumentInfo import SimpleInstrument


widget_lookup = {  # these all come from MDANSE_GUI.InputWidgets
    "FloatConfigurator": FloatWidget,
    "BooleanConfigurator": BooleanWidget,
    "StringConfigurator": StringWidget,
    "IntegerConfigurator": IntegerWidget,
    "CorrelationFramesConfigurator": CorrelationFramesWidget,
    "FramesConfigurator": FramesWidget,
    "RangeConfigurator": RangeWidget,
    "DistHistCutoffConfigurator": DistHistCutoffWidget,
    "VectorConfigurator": VectorWidget,
    "HDFInputFileConfigurator": InputFileWidget,
    "HDFTrajectoryConfigurator": HDFTrajectoryWidget,
    "DerivativeOrderConfigurator": DerivativeOrderWidget,
    "InterpolationOrderConfigurator": InterpolationOrderWidget,
    "OutputFilesConfigurator": OutputFilesWidget,
    "ASEFileConfigurator": InputFileWidget,
    "AseInputFileConfigurator": AseInputFileWidget,
    "ConfigFileConfigurator": InputFileWidget,
    "InputFileConfigurator": InputFileWidget,
    "MDFileConfigurator": InputFileWidget,
    "FieldFileConfigurator": InputFileWidget,
    "XDATCARFileConfigurator": InputFileWidget,
    "XTDFileConfigurator": InputFileWidget,
    "XYZFileConfigurator": InputFileWidget,
    "RunningModeConfigurator": RunningModeWidget,
    "WeightsConfigurator": ComboWidget,
    "MultipleChoicesConfigurator": MultipleCombosWidget,
    "MoleculeSelectionConfigurator": MoleculeWidget,
    "GroupingLevelConfigurator": ComboWidget,
    "SingleChoiceConfigurator": ComboWidget,
    "QVectorsConfigurator": QVectorsWidget,
    "InputDirectoryConfigurator": InputDirectoryWidget,
    "OutputDirectoryConfigurator": OutputDirectoryWidget,
    "OutputStructureConfigurator": OutputStructureWidget,
    "OutputTrajectoryConfigurator": OutputTrajectoryWidget,
    "ProjectionConfigurator": ProjectionWidget,
    "AtomSelectionConfigurator": AtomSelectionWidget,
    "AtomMappingConfigurator": AtomMappingWidget,
    "AtomTransmutationConfigurator": AtomTransmutationWidget,
    "InstrumentResolutionConfigurator": InstrumentResolutionWidget,
    "PartialChargeConfigurator": PartialChargeWidget,
    "UnitCellConfigurator": UnitCellWidget,
}


class Action(QWidget):
    new_thread_objects = Signal(list)
    run_and_load = Signal(list)
    new_path = Signal(str)

    last_paths = {}

    def __init__(self, *args, use_preview=False, **kwargs):
        self._default_path = None
        self._input_trajectory = None
        self._parent_tab = None
        self._trajectory_configurator = None
        self._settings = None
        self._use_preview = use_preview
        self._current_instrument = None
        default_path = kwargs.pop("path", None)
        input_trajectory = kwargs.pop("trajectory", None)
        self.set_trajectory(default_path, input_trajectory)
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout(self)
        self.handlers = {}
        self._widgets = []
        self._widgets_in_layout = []

    def set_settings(self, settings):
        self._settings = settings

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

    def set_instrument(self, instrument: SimpleInstrument) -> None:
        self._current_instrument = instrument

    def clear_panel(self) -> None:
        """Clear the widgets so that it leaves an empty layout"""
        for widget in self._widgets_in_layout:
            self.layout.removeWidget(widget)
            # fixes #448
            # even with the call to deleteLater sometimes the widget
            # windows can pop up and then disappear we need to hide
            # them first to make sure this doesn't happen
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        self._widgets = []
        self._widgets_in_layout = []
        self._preview_box = None

    def update_panel(self, job_name: str) -> None:
        """Sets all the widgets for the selected job.

        Parameters
        ----------
        job_name : str
            The job name.
        """
        self.clear_panel()

        self._job_name = job_name
        self.last_paths[job_name] = self._parent_tab.get_path(job_name)
        try:
            job_instance = IJob.create(job_name)
        except ValueError as e:
            LOG.debug(
                f"Failed to create IJob {job_name};\n"
                f"reason {e};\n"
                f"traceback {traceback.format_exc()}"
            )
            return
        job_instance.build_configuration()
        settings = job_instance.settings
        self._job_instance = job_instance
        LOG.info(f"Configuration {job_instance.configuration}")
        if "trajectory" in settings.keys():
            if self._input_trajectory is None:
                return
            key, value = "trajectory", settings["trajectory"]
            dtype = value[0]
            ddict = value[1]
            configurator = job_instance.configuration[key]
            if not "label" in ddict.keys():
                ddict["label"] = key
            ddict["configurator"] = configurator
            ddict["source_object"] = self._input_trajectory
            widget_class = widget_lookup[dtype]
            input_widget = widget_class(parent=self, **ddict)
            widget = input_widget._base
            self.layout.addWidget(widget, stretch=input_widget._relative_size)
            self._widgets_in_layout.append(widget)
            self._widgets.append(input_widget)
            self._trajectory_configurator = input_widget._configurator
            LOG.info("Set up input trajectory")
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
                self.layout.addWidget(widget, stretch=placeholder._relative_size)
                self._widgets_in_layout.append(widget)
                self._widgets.append(placeholder)
                LOG.warning(f"Could not find the right widget for {key}")
            else:
                widget_class = widget_lookup[dtype]
                # expected = {key: ddict[key] for key in widget_class.__init__.__code__.co_varnames}
                input_widget = widget_class(parent=self, **ddict)
                widget = input_widget._base
                self.layout.addWidget(widget, stretch=input_widget._relative_size)
                self._widgets_in_layout.append(widget)
                self._widgets.append(input_widget)
                input_widget.valid_changed.connect(self.allow_execution)
                if self._use_preview:
                    input_widget.value_updated.connect(self.show_output_prediction)
                LOG.info(f"Set up the right widget for {key}")
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

        if self._use_preview:
            self._preview_box = QTextEdit(self)
            self.layout.addWidget(self._preview_box)
            self._widgets_in_layout.append(self._preview_box)

        buttonbase = QWidget(self)
        buttonlayout = QHBoxLayout(buttonbase)
        buttonbase.setLayout(buttonlayout)
        self.save_button = QPushButton("Save as script", buttonbase)
        self.execute_button = QPushButton("RUN!", buttonbase)
        self.execute_button.setStyleSheet("font-weight: bold")
        self.post_execute_checkbox = QCheckBox("Auto-load results", buttonbase)
        try:
            default_check_status = (
                self._parent_tab._settings.group("Execution").get("auto-load") == "True"
            )
        except:
            LOG.debug(f"Converter tab could not load auto-load settings")
            default_check_status = False
        if default_check_status:
            self.post_execute_checkbox.setChecked(True)

        self.save_button.clicked.connect(self.save_dialog)
        self.execute_button.clicked.connect(self.execute_converter)

        buttonlayout.addWidget(self.save_button)
        buttonlayout.addWidget(self.execute_button)
        buttonlayout.addWidget(self.post_execute_checkbox)

        self.layout.addWidget(buttonbase)
        self._widgets_in_layout.append(buttonbase)
        self.apply_instrument()

    def apply_instrument(self):
        if self._current_instrument is not None:
            q_vector_tuple = self._current_instrument.create_q_vector_params()
            resolution_tuple = self._current_instrument.create_resolution_params()
            for widget in self._widgets:
                if isinstance(widget, InstrumentResolutionWidget):
                    if resolution_tuple is None:
                        continue
                    widget.change_function(resolution_tuple[0], resolution_tuple[1])
                if isinstance(widget, QVectorsWidget):
                    if q_vector_tuple is None:
                        continue
                    widget._selector.setCurrentText(q_vector_tuple[0])
                    widget._model.switch_qvector_type(
                        q_vector_tuple[0], q_vector_tuple[1]
                    )
        self.allow_execution()
        self.show_output_prediction()

    @Slot()
    def show_output_prediction(self):
        if self._use_preview:
            self.allow_execution()
            LOG.info("Show output prediction")
            pardict = self.set_parameters()
            self._job_instance.setup(pardict)
            axes = self._job_instance.preview_output_axis()
            LOG.info(f"Axes = {axes.keys()}")
            text = "<p><b>The results will cover the following range:</b></p>"
            for unit, old_array in axes.items():
                scale_factor, new_unit = self._parent_tab.conversion_factor(unit)
                array = np.array(old_array) * scale_factor
                if len(array) < 6:
                    text += f"<p>{array} ({new_unit})</p>"
                else:
                    text += f"<p>[{array[0]}, {array[1]}, {array[2]}, ..., {array[-1]}] ({new_unit})</p>"
            self._preview_box.setHtml(text)

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
        if self._job_name == "AverageStructure":
            self.post_execute_checkbox.setEnabled(False)
        else:
            self.post_execute_checkbox.setEnabled(True)

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
            currentpath = self._parent_tab.get_path(self._job_name + "_script")
        result, ftype = QFileDialog.getSaveFileName(
            self, "Save job as a Python script", currentpath, "Python script (*.py)"
        )
        if result == "":
            return None
        path, _ = os.path.split(result)
        try:
            cname = self._job_name
        except:
            pass
        else:
            self.last_paths[cname] = path
            self._parent_tab.set_path(self._job_name + "_script", path)
        pardict = self.set_parameters(labels=True)
        self._job_instance.save(result, pardict)

    def set_parameters(self, labels=False):
        results = {}
        for widnum, key in enumerate(self._job_instance.settings.keys()):
            if labels:
                label = self._job_instance.settings[key][1]["label"]
                results[key] = (self._widgets[widnum].get_widget_value(), label)
            else:
                results[key] = self._widgets[widnum].get_widget_value()
        return results

    @Slot()
    def execute_converter(self):
        pardict = self.set_parameters()
        LOG.info(pardict)
        self._parent_tab.set_path(self._job_name, self._default_path)
        # when we are ready, we can consider running it
        # self.converter_instance.run(pardict)
        # this would send the actual instance, which _may_ be wrong
        # self.new_thread_objects.emit([self.converter_instance, pardict])
        if (
            self.post_execute_checkbox.isChecked()
            and self._job_name != "AverageStructure"
        ):
            self.run_and_load.emit([self._job_name, pardict])
        else:
            self.new_thread_objects.emit([self._job_name, pardict])

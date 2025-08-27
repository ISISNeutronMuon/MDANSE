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

import traceback
from pathlib import Path

import numpy as np
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Framework.Configurators.HDFTrajectoryConfigurator import (
    HDFTrajectoryConfigurator,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.InputWidgets import (
    AseInputFileWidget,
    AtomMappingWidget,
    AtomSelectionWidget,
    AtomTransmutationWidget,
    BackupWidget,
    BooleanWidget,
    ComboWidget,
    CorrelationFramesWidget,
    DerivativeOrderWidget,
    DistHistCutoffWidget,
    FloatWidget,
    FramesWidget,
    HDFTrajectoryWidget,
    InputDirectoryWidget,
    InputFileWidget,
    InstrumentResolutionWidget,
    IntegerWidget,
    InterpolationOrderWidget,
    MDAnalysisCoordinateFileWidget,
    MDAnalysisMDTrajTimeStepWidget,
    MDAnalysisTopologyFileWidget,
    MDTrajTopologyFileWidget,
    MoleculeAndAxisWidget,
    MoleculeWidget,
    MultiInputFileWidget,
    MultipleCombosWidget,
    OptionalFloatWidget,
    OutputDirectoryWidget,
    OutputFilesWidget,
    OutputStructureWidget,
    OutputTrajectoryWidget,
    PartialChargeWidget,
    ProjectionWidget,
    QVectorsWidget,
    RangeWidget,
    RunningModeWidget,
    StringWidget,
    TrajectoryFilterWidget,
    UnitCellWidget,
    VectorWidget,
)
from MDANSE_GUI.Tabs.Visualisers.InstrumentInfo import SimpleInstrument
from MDANSE_GUI.Widgets.DelayedButton import DelayedButton

widget_lookup = {  # these all come from MDANSE_GUI.InputWidgets
    "FloatConfigurator": FloatWidget,
    "OptionalFloatConfigurator": OptionalFloatWidget,
    "BooleanConfigurator": BooleanWidget,
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
    "MDAnalysisCoordinateFileConfigurator": MDAnalysisCoordinateFileWidget,
    "InputFileConfigurator": InputFileWidget,
    "MDAnalysisTopologyFileConfigurator": MDAnalysisTopologyFileWidget,
    "MDFileConfigurator": InputFileWidget,
    "FieldFileConfigurator": InputFileWidget,
    "XDATCARFileConfigurator": InputFileWidget,
    "XTDFileConfigurator": InputFileWidget,
    "XYZFileConfigurator": InputFileWidget,
    "OptionalXYZFileConfigurator": InputFileWidget,
    "RunningModeConfigurator": RunningModeWidget,
    "WeightsConfigurator": ComboWidget,
    "MultipleChoicesConfigurator": MultipleCombosWidget,
    "MoleculeSelectionConfigurator": MoleculeWidget,
    "AxisSelectionConfigurator": MoleculeAndAxisWidget,
    "GroupingLevelConfigurator": ComboWidget,
    "SingleChoiceConfigurator": ComboWidget,
    "QVectorsConfigurator": QVectorsWidget,
    "OutputStructureConfigurator": OutputStructureWidget,
    "OutputTrajectoryConfigurator": OutputTrajectoryWidget,
    "ProjectionConfigurator": ProjectionWidget,
    "AtomSelectionConfigurator": AtomSelectionWidget,
    "AtomMappingConfigurator": AtomMappingWidget,
    "AtomTransmutationConfigurator": AtomTransmutationWidget,
    "InstrumentResolutionConfigurator": InstrumentResolutionWidget,
    "PartialChargeConfigurator": PartialChargeWidget,
    "TrajectoryFilterConfigurator": TrajectoryFilterWidget,
    "UnitCellConfigurator": UnitCellWidget,
    "MDAnalysisTimeStepConfigurator": MDAnalysisMDTrajTimeStepWidget,
    "MDTrajTimeStepConfigurator": MDAnalysisMDTrajTimeStepWidget,
    "MDTrajTrajectoryFileConfigurator": MultiInputFileWidget,
    "MDTrajTopologyFileConfigurator": MDTrajTopologyFileWidget,
}


class Action(QWidget):
    new_thread_objects = Signal(list)
    run_and_load = Signal(list)
    new_path = Signal(str)

    def __init__(self, *args, use_preview=False, **kwargs):
        self._default_path = None
        self._input_traj_path = None
        self._parent_tab = None
        self._trajectory_configurator = None
        self._trajectory_instance = None
        self._settings = None
        self._job_name = None
        self._job_instance = IJob()
        self._use_preview = use_preview
        self._current_instrument = None
        self._has_been_initialised = False
        self.execute_button = None
        self.post_execute_checkbox = None
        input_trajectory = kwargs.pop("trajectory", None)
        self.set_trajectory(input_trajectory)
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout(self)
        self.handlers = {}
        self._widgets = []
        self._widgets_in_layout = {}

    def set_settings(self, settings):
        self._settings = settings

    def set_trajectory(self, trajectory: Trajectory | None) -> None:
        """Set the trajectory path and filename.

        Parameters
        ----------
        trajectory : Trajectory
            An instance of the trajectory class
        """
        if trajectory is None:
            self._trajectory_configurator = None
            self._trajectory_instance = None
            self._input_traj_path = None
            self._has_been_initialised = False
            return
        new_path = trajectory.filename
        if new_path == self._input_traj_path:
            LOG.debug("Skipping set_trajectory, no change.")
            return
        self._job_instance = IJob()
        self._trajectory_instance = trajectory
        self._trajectory_configurator = HDFTrajectoryConfigurator(
            "Input Trajectory", instance=trajectory
        )
        self._trajectory_configurator.configure_from_instance()
        self._input_traj_path = new_path
        if self._input_traj_path is not None:
            self._default_path = Path(self._input_traj_path).parent
        else:
            self._default_path = Path().absolute()
        if self._job_name is not None:
            self._parent_tab.set_path(self._job_name, str(self._default_path))

    def set_instrument(self, instrument: SimpleInstrument) -> None:
        self._current_instrument = instrument

    def clear_panel(self) -> None:
        """Clear the widgets so that it leaves an empty layout"""
        for widget in self._widgets_in_layout.values():
            self.layout.removeWidget(widget)
            # fixes #448
            # even with the call to deleteLater sometimes the widget
            # windows can pop up and then disappear we need to hide
            # them first to make sure this doesn't happen
            widget.hide()
            widget.setParent(None)
            widget.deleteLater()
        self._widgets = []
        self._widgets_in_layout = {}
        self._preview_box = None

    def update_panel(self, job_name: str) -> None:
        """Sets all the widgets for the selected job.

        Parameters
        ----------
        job_name : str
            The job name.
        """
        LOG.debug(
            "Old job type %s, new job type %s",
            type(self._job_instance).__name__,
            job_name,
        )
        if type(self._job_instance).__name__ != job_name:
            self.clear_panel()
            self._has_been_initialised = False

            self._job_name = job_name
            if self._default_path is None or Path(self._default_path).samefile(Path()):
                self._default_path = str(Path(self._parent_tab.get_path(job_name)))
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
        else:
            job_instance = self._job_instance
            settings = self._job_instance.settings
        LOG.info(f"Configuration {job_instance.configuration}")
        LOG.debug(f"{self._input_traj_path} loaded as {self._trajectory_instance}")
        if "trajectory" in settings.keys():
            if self._input_traj_path is None:
                return
            key, value = "trajectory", settings["trajectory"]
            dtype = value[0]
            ddict = value[1]
            configurator = job_instance.configuration[key]
            if key not in self._widgets_in_layout:
                ddict.setdefault("label", key)
                ddict["configurator"] = configurator
                ddict["source_object"] = self._input_traj_path
                widget_class = widget_lookup[dtype]
                input_widget = widget_class(
                    parent=self, trajectory_instance=self._trajectory_instance, **ddict
                )
                widget = input_widget._base
                self.layout.addWidget(widget, stretch=input_widget._relative_size)
                self._widgets_in_layout[key] = widget
                self._widgets.append(input_widget)
                self._trajectory_configurator = input_widget._configurator
            LOG.info("Set up input trajectory")
        for key, value in settings.items():
            if key in self._widgets_in_layout:
                continue
            dtype = value[0]
            ddict = value[1]
            configurator = job_instance.configuration[key]
            ddict.setdefault("label", key)
            ddict["configurator"] = configurator
            ddict["source_object"] = self._input_traj_path
            ddict["trajectory_configurator"] = self._trajectory_configurator
            if dtype not in widget_lookup:
                ddict["tooltip"] = (
                    "This is not implemented in the MDANSE GUI at the moment, and it MUST BE!"
                )
                placeholder = BackupWidget(parent=self, **ddict)
                widget = placeholder._base
                self.layout.addWidget(widget, stretch=placeholder._relative_size)
                self._widgets_in_layout[key] = widget
                self._widgets.append(placeholder)
                LOG.warning(f"Could not find the right widget for {key}")
            else:
                widget_class = widget_lookup[dtype]
                # expected = {key: ddict[key] for key in widget_class.__init__.__code__.co_varnames}
                input_widget = widget_class(parent=self, **ddict)
                widget = input_widget._base
                self.layout.addWidget(widget, stretch=input_widget._relative_size)
                self._widgets_in_layout[key] = widget
                self._widgets.append(input_widget)
                input_widget.valid_changed.connect(self.allow_execution)
                has_preview = callable(
                    getattr(input_widget._configurator, "preview_output_axis", False)
                )
                if self._use_preview and has_preview:
                    input_widget.value_updated.connect(self.show_output_prediction)
                LOG.info(f"Set up the right widget for {key}")
            # self.handlers[key] = data_handler
        self._has_been_initialised = True
        self.check_inputs()

        if self._use_preview and "preview_box" not in self._widgets_in_layout:
            self._preview_box = QTextEdit(self)
            self.layout.addWidget(self._preview_box)
            self._widgets_in_layout["preview_box"] = self._preview_box

        if "button_base" not in self._widgets_in_layout:
            buttonbase = QWidget(self)
            buttonlayout = QHBoxLayout(buttonbase)
            buttonbase.setLayout(buttonlayout)
            self.save_button = QPushButton("Save as script", buttonbase)
            self.execute_button = DelayedButton("RUN!", buttonbase, delay=3000)
            self.execute_button.setStyleSheet("font-weight: bold")
            self.post_execute_checkbox = QCheckBox("Auto-load results", buttonbase)
            try:
                default_check_status = (
                    self._parent_tab._settings.group("Execution").get("auto-load")
                    == "True"
                )
            except Exception:
                LOG.debug("Converter tab could not load auto-load settings")
                default_check_status = False
            if default_check_status:
                self.post_execute_checkbox.setChecked(True)

            self.save_button.clicked.connect(self.save_dialog)
            self.execute_button.clicked.connect(self.execute_converter)
            self.execute_button.needs_updating.connect(self.allow_execution)

            buttonlayout.addWidget(self.save_button)
            buttonlayout.addWidget(self.execute_button)
            buttonlayout.addWidget(self.post_execute_checkbox)

            self.layout.addWidget(buttonbase)
            self._widgets_in_layout["button_base"] = buttonbase
        self.apply_instrument()
        self.allow_execution()

    def check_inputs(self) -> bool:
        configured = False
        iterations = 0
        while not configured:
            configured = True
            for widget in self._widgets:
                widget.value_from_configurator()
                configured = configured and widget._configurator.is_configured()
            iterations += 1
            if iterations > 3:
                break
        return configured

    @Slot()
    def test_file_outputs(self):
        if not self._has_been_initialised:
            return
        self.check_inputs()
        for widget in self._widgets:
            if isinstance(widget, (OutputFilesWidget, OutputTrajectoryWidget)):
                widget.updateValue()
        self.allow_execution()

    def apply_instrument(self):
        if self._current_instrument is not None:
            initial_configuration = self._trajectory_configurator[
                "instance"
            ].configuration()
            q_vector_tuple = self._current_instrument.create_q_vector_params(
                initial_configuration
            )
            resolution_tuple = self._current_instrument.create_resolution_params()
            for widget in self._widgets:
                has_preview = callable(
                    getattr(widget._configurator, "preview_output_axis", False)
                )
                if not has_preview:
                    continue
                # These widgets will emit a signal and call
                # show_output_prediction this means that this function
                # can be called multiple times. We need to block the
                # signals from these widgets to stop this from happening
                # show_output_prediction will be called at the end of
                # this function.
                widget.blockSignals(True)
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
                widget.blockSignals(False)
        self.allow_execution()
        self.show_output_prediction()

    @Slot()
    def show_output_prediction(self):
        if self._use_preview:
            self.allow_execution()
            LOG.info("Show output prediction")
            pardict = self.set_parameters()
            self._job_instance.setup(pardict, rebuild=False)
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

    @Slot()
    def allow_execution(self):
        allow = True
        has_warning = False
        for widget in self._widgets:
            if not widget._configurator.valid:
                allow = False
                widget.mark_error(widget._configurator.error_status, silent=True)
            has_warning = has_warning or widget.has_warning
        if self.execute_button is not None:
            self.execute_button.setEnabled(allow)
            if has_warning:
                self.execute_button.setStyleSheet(
                    "QWidget { background-color:rgb(220,210,30); font-weight: bold }"
                )
                self.execute_button.setToolTip(
                    "Warning(s) found in input widgets above."
                )
            else:
                self.execute_button.setStyleSheet("QWidget { }")
                self.execute_button.setToolTip(
                    "Launch the job using the current parameters."
                )
        if self.post_execute_checkbox is not None:
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
            _cname = self._job_name
        except Exception:
            currentpath = Path().absolute()
        else:
            currentpath = Path(self._parent_tab.get_path(self._job_name + "_script"))
        result, ftype = QFileDialog.getSaveFileName(
            self,
            "Save job as a Python script",
            str(currentpath),
            "Python script (*.py)",
        )
        if result == "":
            return None
        path = Path(result).parent
        try:
            _cname = self._job_name
        except Exception:
            pass
        else:
            self._parent_tab.set_path(self._job_name + "_script", str(path))
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
        self._parent_tab.set_path(self._job_name, str(self._default_path))
        self._parent_tab._session.save()
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
        self.check_inputs()
        for widget in self._widgets:
            widget.updateValue()
        self.allow_execution()

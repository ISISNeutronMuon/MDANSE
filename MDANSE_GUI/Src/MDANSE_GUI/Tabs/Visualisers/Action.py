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
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from qtpy.QtCore import QObject, Signal, Slot
from qtpy.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from MDANSE.Framework.Converters import Converter
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Parameters import (
    Array,
    ASEOutputFormat,
    AtomMapping,
    AtomSelection,
    AtomTransmutation,
    Boolean,
    CorrelationWindow,
    DynamicSingleChoice,
    Float,
    FrameSelect,
    GridStep,
    GroupingLevel,
    InstrumentResolution,
    Integer,
    InterpOrder,
    ManyPath,
    MDANSEResult,
    MDANSETrajectory,
    MolecularAxis,
    Molecule,
    OutputFile,
    OutputTrajectory,
    PartialCharge,
    PathParam,
    Projection,
    QVectors,
    Range,
    RangeCellCutoff,
    RunningMode,
    SingleChoice,
    Vector,
    Weights,
)
from MDANSE.Framework.Parameters.Parameters import ConfigError, Parameter
from MDANSE.IO.IOUtils import summarise_array
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets import (
    ArrayWidget,
    AtomMappingWidget,
    AtomSelectionWidget,
    AtomTransmutationWidget,
    BooleanWidget,
    ComboWidget,
    FloatWidget,
    FramesWidget,
    HDFTrajectoryWidget,
    InputFileWidget,
    InstrumentResolutionWidget,
    IntegerWidget,
    MoleculeAndAxisWidget,
    MoleculeWidget,
    MultiInputFileWidget,
    OutputFilesWidget,
    OutputStructureWidget,
    OutputTrajectoryWidget,
    PartialChargeWidget,
    ProjectionWidget,
    QVectorsWidget,
    RangeWidget,
    RunningModeWidget,
)
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.Utils import block_signals
from MDANSE_GUI.Widgets.DelayedButton import DelayedButton

if TYPE_CHECKING:
    from MDANSE.MolecularDynamics.Trajectory import Trajectory
    from MDANSE_GUI.Tabs.Visualisers.InstrumentInfo import SimpleInstrument

widget_lookup: defaultdict[type[Parameter], type[WidgetBase]] = defaultdict(
    lambda: WidgetBase,
)
widget_lookup.update(
    {
        Float: FloatWidget,
        GridStep: FloatWidget,
        Boolean: BooleanWidget,
        Integer: IntegerWidget,
        CorrelationWindow: IntegerWidget,
        InterpOrder: IntegerWidget,
        FrameSelect: FramesWidget,
        Range: RangeWidget,
        RangeCellCutoff: RangeWidget,
        AtomMapping: AtomMappingWidget,
        AtomSelection: AtomSelectionWidget,
        AtomTransmutation: AtomTransmutationWidget,
        SingleChoice: ComboWidget,
        DynamicSingleChoice: ComboWidget,
        Weights: ComboWidget,
        GroupingLevel: ComboWidget,
        InstrumentResolution: InstrumentResolutionWidget,
        ManyPath: MultiInputFileWidget,
        Molecule: MoleculeWidget,
        MolecularAxis: MoleculeAndAxisWidget,
        ASEOutputFormat: OutputStructureWidget,
        OutputTrajectory: OutputTrajectoryWidget,
        OutputFile: OutputFilesWidget,
        PartialCharge: PartialChargeWidget,
        PathParam: InputFileWidget,
        MDANSEResult: InputFileWidget,
        Projection: ProjectionWidget,
        QVectors: QVectorsWidget,
        RunningMode: RunningModeWidget,
        MDANSETrajectory: HDFTrajectoryWidget,
        Array: ArrayWidget,
        Vector: ArrayWidget,
    }
)

# String:              raise NotImplementedError()
# MultipleChoice:              raise NotImplementedError()
# DynamicMultiChoice:         #     raise NotImplementedError()
# Filter:         #     raise NotImplementedError()


class Action(QWidget):
    new_thread_objects = Signal(list)
    run_and_load = Signal(list)
    new_path = Signal(str)

    def __init__(
        self,
        *args,
        use_preview: bool = False,
        trajectory: Trajectory | None = None,
        **kwargs,
    ):
        self._default_path: Path | None = None
        self._input_traj_path: Path | None = None
        self._parent_tab: QObject | None = None
        self._trajectory_configurator = None
        self._trajectory_instance: Trajectory | None = None
        self._settings = None
        self._job_name: str | None = None
        self._job_instance: IJob = IJob()
        self._use_preview = use_preview
        self._current_instrument = None
        self._has_been_initialised = False
        self.execute_button = None
        self.post_execute_checkbox = None
        self.set_trajectory(trajectory)
        super().__init__(*args, **kwargs)

        self.layout = QVBoxLayout(self)
        self.handlers = {}
        self._widgets: list[WidgetBase] = []
        self._widgets_in_layout: dict[str, QWidget] = {}
        self._raw_widgets: dict[str, WidgetBase] = {}

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

        self._trajectory_instance = trajectory
        self._job_instance.trajectory = trajectory

        self._input_traj_path = new_path

        if self._input_traj_path is not None:
            self._default_path = Path(self._input_traj_path).parent
        else:
            self._default_path = Path.cwd()

        if self._job_name is not None:
            self._parent_tab.set_path(self._job_name, str(self._default_path))

        if self._has_been_initialised:
            for widget in (
                widget
                for widget in self._raw_widgets.values()
                if isinstance(widget, WidgetBase)
            ):
                widget.trajectory_changed()
            self.show_output_prediction()

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
            if self._default_path is None or (
                Path(self._default_path).exists()
                and Path(self._default_path).samefile(Path.cwd())
            ):
                self._default_path = str(Path(self._parent_tab.get_path(job_name)))

            try:
                self._job_instance = IJob.create(job_name)
                if self._trajectory_instance:
                    self._job_instance.trajectory = self._trajectory_instance
            except ValueError as e:
                LOG.error(
                    f"Failed to create IJob {job_name};\n"
                    f"reason {e};\n"
                    f"traceback {traceback.format_exc()}"
                )
                return

        if (
            not isinstance(self._job_instance, Converter)
            and self._input_traj_path is None
        ):
            return

        LOG.info("Configuration %s", self._job_instance)
        LOG.debug(f"{self._input_traj_path} loaded as {self._trajectory_instance}")

        for key, desc in self._job_instance.descriptors.items():
            if key in self._widgets_in_layout:
                continue

            widget_class = widget_lookup[type(desc)]
            LOG.info(f"Setting up {widget_class.__name__} for {key}")
            input_widget = widget_class(
                parent=self,
                label=key,
                configurable=self._job_instance,
                prop=key,
                parameter=desc,
            )
            widget = input_widget._base
            self.layout.addWidget(widget, stretch=input_widget._relative_size)
            self._widgets_in_layout[key] = widget
            self._raw_widgets[key] = input_widget
            self._widgets.append(input_widget)
            input_widget.value_changed.connect(self.allow_execution)

        self._has_been_initialised = True

        if self._use_preview and "preview_box" not in self._widgets_in_layout:
            box = QGroupBox("Preview of output axes")
            self._preview_box = QLabel(self)
            self._preview_box.setToolTip(
                "The current input parameters will result in the output "
                "being calculated at the following points."
            )
            QHBoxLayout(box).addWidget(self._preview_box)
            self.layout.addWidget(box)
            self._widgets_in_layout["preview_box"] = box

            for predictor in self._job_instance.PREDICTORS:
                self._raw_widgets[predictor].value_changed.connect(
                    self.show_output_prediction
                )

        if "button_base" not in self._widgets_in_layout:
            buttonbase = QWidget(self)
            buttonlayout = QHBoxLayout(buttonbase)
            buttonbase.setLayout(buttonlayout)
            self.save_button = QPushButton("Save as script", buttonbase)
            self.execute_button = DelayedButton("RUN!", buttonbase, delay=3000)
            font = self.execute_button.font()
            font.setBold(True)
            self.execute_button.setFont(font)
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
        return self._job_instance.check_status()

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
            initial_configuration = self._trajectory_instance
            q_vector_tuple = self._current_instrument.create_q_vector_params(
                initial_configuration
            )
            resolution_tuple = self._current_instrument.create_resolution_params()

            for widget in self._raw_widgets.values():
                has_preview = callable(
                    getattr(widget.parameter, "preview_output_axis", False)
                )

                if not has_preview:
                    continue
                # These widgets will emit a signal and call
                # show_output_prediction this means that this function
                # can be called multiple times. We need to block the
                # signals from these widgets to stop this from happening
                # show_output_prediction will be called at the end of
                # this function.
                with block_signals(widget):
                    if isinstance(widget, InstrumentResolutionWidget):
                        if resolution_tuple is None:
                            continue
                        widget.value = resolution_tuple

                    if isinstance(widget, QVectorsWidget):
                        if q_vector_tuple is None:
                            continue
                        widget.value = q_vector_tuple

        self.allow_execution()
        self.show_output_prediction()

    @Slot()
    def show_output_prediction(self):
        if self._use_preview:
            self.allow_execution()
            LOG.info("Show output prediction")

            try:
                axes = self._job_instance.preview_output_axis()
            except ConfigError:
                self._preview_box.setText(
                    "The following parameters are not correctly defined:\n - "
                    + "\n - ".join(self._job_instance.invalid)
                )
                return

            axes = self._job_instance.preview_output_axis()
            LOG.info(f"Axes = {[axis[0] for axis in axes if axis is not None]}")
            text = "<p><b>The results will cover the following range:</b></p>"
            for label, old_array, unit in axes:
                scale_factor, new_unit = self._parent_tab.conversion_factor(unit)
                array = np.array(old_array) * scale_factor
                text += f"<p>{label}: [{summarise_array(array, arr_fmt='5.3f')}] ({new_unit})</p>"
            self._preview_box.setText(text)

    @Slot()
    def allow_execution(self):
        allow = self._job_instance.check_status()
        has_warning = any(widget.has_warning for widget in self._widgets)

        if self.execute_button is not None:
            self.execute_button.setEnabled(allow)
            self.save_button.setEnabled(allow)
            if has_warning:
                self.execute_button.setStyleSheet(
                    "QWidget { background-color:rgb(220,210,30); font-weight: bold }"
                )
                self.execute_button.setToolTip(
                    "Warning(s) found in input widgets above."
                )
            else:
                self.execute_button.setStyleSheet("")
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
            currentpath = Path.cwd()
        else:
            currentpath = Path(self._parent_tab.get_path(self._job_name + "_script"))
        result, _ftype = QFileDialog.getSaveFileName(
            self,
            "Save job as a Python script",
            str(currentpath),
            "Python script (*.py)",
        )

        if not result:
            return None

        path = Path(result).parent

        try:
            _cname = self._job_name
        except Exception:
            pass
        else:
            self._parent_tab.set_path(self._job_name + "_script", str(path))

        self._job_instance.save(result)

    def set_parameters(self, labels=False):
        results = {}
        for widnum, key in enumerate(self._job_instance.settings.keys()):
            if labels:
                label = self._job_instance.settings[key][1]["label"]
                if tooltip := self._job_instance.settings[key][1].get("tooltip"):
                    label += f". {tooltip}"
                results[key] = (self._widgets[widnum].get_widget_value(), label)
            else:
                results[key] = self._widgets[widnum].get_widget_value()
        return results

    @Slot()
    def execute_converter(self):
        self._parent_tab.set_path(self._job_name, str(self._default_path))
        self._parent_tab._session.save()

        if (
            self.post_execute_checkbox.isChecked()
            and self._job_name != "AverageStructure"
        ):
            self.run_and_load.emit([self._job_name, self._job_instance.raw_values])
        else:
            self.new_thread_objects.emit(
                [self._job_name, self._job_instance.raw_values]
            )

        self.allow_execution()

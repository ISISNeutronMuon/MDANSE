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

import copy
from collections.abc import Sequence
from typing import Any, Callable

import matplotlib.pyplot as mpl
import numpy as np
import numpy.typing as npt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)
from qtpy.QtCore import QObject, Qt, QThread, Signal, Slot
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStackedLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from scipy import signal
from scipy.interpolate import interp1d

from MDANSE.Framework.Configurators.TrajectoryFilterConfigurator import (
    TrajectoryFilterConfigurator,
)
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.Jobs.PositionPowerSpectrum import PositionPowerSpectrum
from MDANSE.Mathematics.Signal import (
    DEFAULT_FILTER_CUTOFF,
    DEFAULT_N_STEPS,
    DEFAULT_TIME_STEP,
    FILTER_MAP,
    Filter,
    FrequencyDomain,
    filter_description_string,
)
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase

# Default maximum value for a float spinbox
DEFAULT_SPINBOX_MAX_FLOAT = 1000.0

# Default step size for a float spinbox
DEFAULT_SPINBOX_STEP_FLOAT = 0.1

# Decimal precision for a float spinbox
FLOAT_SPINBOX_DECIMALS = 8


class BackgroundThread(QThread):
    """Runs one MDANSE job and returns the requested datasets."""

    results = Signal(object)

    def __init__(
        self,
        parent,
        job_name: str,
        parameters: dict[str, str],
        result_keys: list[str],
    ):
        super().__init__(parent)
        self.job_name = job_name
        self.parameters = parameters
        self.res_keys = result_keys

    def run(self):
        """Run the job and emit datasets with labels in self.res_keys.

        This will be run automatically after the thread's .start() method
        has been called.
        """
        job = IJob.create(self.job_name)
        self.parameters["output_files"] = (
            "OUTPUT_FILENAME",
            ["FileInMemory"],
            "no logs",
        )
        job.run(self.parameters, status=True)
        output = job.results
        res_dict = {key: output[key][:] for key in self.res_keys}
        self.results.emit(res_dict)


class ConstrainedDoubleSpinBox(QDoubleSpinBox):
    """A spinbox that only allows values from a specific set.

    This custom QDoubleSpinBox allows for the application of a function
    to changed values in order to find an appropriate new value that
    satisfies the constraint.

    """

    def __init__(self, minimum: float, maximum: float, step: float, value: float):
        """
        Parameters
        ----------
        minimum: float
            Spinbox minimum value.
        maximum: float
            Spinbox maximum value.
        step: float
            Single step on spinbox.
        value: float
            Initial value.

        """
        super().__init__()

        self.setDecimals(FLOAT_SPINBOX_DECIMALS)

        self.setKeyboardTracking(False)

        self.setMinimum(minimum)
        self.setMaximum(maximum)
        self.setSingleStep(step)
        self.setValue(value)

    def reset_connections(self):
        """Reset all connections to custom slots."""
        for slot_func in (self.snap_to_value, self.search_by_function):
            for signal_func in (self.valueChanged, self.textChanged):
                try:
                    signal_func.disconnect(slot_func)
                except TypeError:
                    continue

    def set_search(self, constraint_func: Callable) -> None:
        """Set the search constraint function to be invoked when spinbox value or text changes.

        Parameters
        ----------
        constraint_func : Callable
            Lambda for imposing constraint on spinbox value.

        """
        self.reset_connections()
        self.constraint = constraint_func
        callback = self.search_by_function
        self.valueChanged.connect(callback)
        self.textChanged.connect(callback)

    def set_snap(self, snap_to: float) -> None:
        """Set the value to be snapped to modulo zero when spinbox value or text changes.

        Parameters
        ----------
        snap_to : float
            Value to snap to.

        """
        self.reset_connections()
        self.constraint = snap_to
        callback = self.snap_to_value
        self.valueChanged.connect(callback)
        self.textChanged.connect(callback)

    def setValue(self, val) -> None:
        """Store the input value and change the value in the spin box.

        Overrides setValue method of QDoubleSpinBox.
        Sets a record of the initial value of the spinbox, for determination
        of direction of change.
        Other methods of this class will change the value to the nearest one
        that is on the grid of allowed values.

        Parameters
        ----------
        val : float
            Value of the spinbox.

        """
        self.initial_value = val
        super().setValue(val)

    def snap_to_value(self, value: Any) -> None:
        """Change the value to the nearest allowed value.

        Apply the constraint by snapping up/down (depending on the change direction) to the nearest value
        modulo zero.

        Parameters
        ----------
        value : Any
            Value of the spinbox.

        """
        value = self.to_float(value)

        remainder = value % self.constraint
        if not self.constraint or np.isclose(remainder, 0):
            return

        # New value is the closest value evenly dividing the constraint
        new_value = np.round(value / self.constraint) * self.constraint
        self.setValue(np.round(new_value, FLOAT_SPINBOX_DECIMALS))

    def search_by_function(self, value: Any) -> None:
        """Apply the constraint formalised in the lambda.

        The spinbox will search in both directions until the lambda
        returns True on the current value.

        Parameters
        ----------
        value : Any
            Value of the spinbox.

        """
        value = self.to_float(value)

        if (
            not self.constraint
            or self.constraint(value)
            or (not hasattr(self, "initial_value"))
        ):
            return

        current = self.to_float(self.value())
        value_found = False
        if current < self.initial_value:
            for x in np.arange(value, self.minimum(), -self.singleStep()):
                if self.constraint(x):
                    value_found = True
                    break
        else:
            for x in np.arange(value, self.maximum(), self.singleStep()):
                if self.constraint(x):
                    value_found = True
                    break

        if not value_found:
            self.setValue(self.initial_value)
            return

        # Update with constrained value
        self.setValue(x)

    @staticmethod
    def to_float(value: Any) -> float:
        """Convert spinbox value to float if string.

        Parameters
        ----------
        value : Any
            Value of the spinbox.

        Returns
        -------
        float
            Value of the spinbox.

        """
        return float(value)


class FilterPreferencesGroup(QObject):
    """Interface for a filter preferences group.

    Provides a grid layout of settings for a given filter.

    """

    # Signal: emits a dictionary of preferences when settings have been updated
    _preferences_updated = Signal(dict)

    def __init__(self, render_func: Callable):
        """
        Parameters
        ----------
        render_func : Callable
            Filter designer function to call when preferences have been updated. The supplied function re-renders the
            filter designer graph.

        """
        super().__init__()

        # Dictionary mapping preferences to their values
        self.preferences = {}

        # Grid layout into which the input widgets are placed
        self.grid = QGridLayout()

        # Dictionary mapping setting name to input widget
        self.widgets = {}

        # Connection: when the preferences have been updated, re-render the filter designer
        self._preferences_updated.connect(render_func)

    def store_widget(self, name: str, widget: QWidget) -> None:
        """Store a widget in self.

        Parameters
        ----------
        name : str
            Name of the instance attribute to be stored, or key string.
        widget : QWidget
            Widget to be stored, or value corresponding to the key.

        Returns
        -------
        QWidget
            The stored widget.

        """
        self.widgets[name] = widget

    def add_combobox(
        self,
        key: str,
        items: tuple = (),
        tooltip: str = "",
        *,
        enabled: bool = True,
    ) -> QWidget:
        """Produce a combobox for a filter designer preference.

        Parameters
        ----------
        key : str
            Preference name.
        items : tuple
            Items representing the available preference settings.
        tooltip : str
            Tooltip to display when hovering over widget.
        enabled : enabled
            Preference is enabled by default.

        Returns
        -------
        QWidget
            Specified QComboBox.

        """
        widget = QComboBox()
        widget.addItems(items)
        widget.setCurrentText(items[0])
        widget.setEnabled(enabled)
        widget.setToolTip(tooltip)
        self.store_widget(key, widget)
        self.preferences.update({key: widget.currentText()})
        widget.currentTextChanged.connect(self.collect_inputs)
        return widget

    @Slot()
    def collect_inputs(self) -> None:
        """Slot: iterate over input widgets, collecting their values and update attributes."""
        for name, widget in self.widgets.items():
            value = self.visit(widget)
            self.preferences[name] = value

        self._preferences_updated.emit(self.preferences)

    def as_grid(self) -> QGridLayout:
        """Populate the preferences grid layout with the filter designer preference widgets.

        Parameters
        ----------
        grid : QGridLayout
            Grid layout to which preference widgets will be added

        """
        # Y-axis in amplitude or decibels
        self.grid.addWidget(QLabel("Response units"), 0, 0)
        response_cbox = self.add_combobox(
            "response_units",
            ("amplitude", "dB"),
            "View y-axis in amplitude or decibels",
        )
        self.grid.addWidget(response_cbox, 0, 1)

        # X-axis in angular frequency or energy (meV)
        self.grid.addWidget(QLabel("X-axis units"), 1, 0)
        xaxis_cbox = self.add_combobox(
            "xaxis_units",
            ("frequency", "meV"),
            "View x-axis as frequency or energy (meV)",
        )
        self.grid.addWidget(xaxis_cbox, 1, 1)

        # Display filter transfer function in terms of analogue or digital filter coefficients
        self.grid.addWidget(QLabel("Filter coefficients"), 2, 0)
        coeff_type_cbox = self.add_combobox(
            "coeff_type",
            ("analog", "digital"),
            "View filter transfer function in terms of analogue (S-domain/continuous time) or digital (Z-domain/discrete time) coefficients",
        )
        self.grid.addWidget(coeff_type_cbox, 2, 1)

        # Display trajectory position power spectral attentuation for comparison
        self.pps_label = QLabel("Show trajectory attenuation")
        self.grid.addWidget(self.pps_label, 3, 0)
        attenuation_checkbox = QCheckBox()
        self.pps_checkbox = attenuation_checkbox
        self.widgets.update({"show_attenuation": attenuation_checkbox})
        attenuation_checkbox.setEnabled(True)
        attenuation_checkbox.stateChanged.connect(self.collect_inputs)
        attenuation_checkbox.setToolTip(
            "Display trajectory power spectrum for comparison",
        )
        self.grid.addWidget(attenuation_checkbox, 3, 1)

        return self.grid

    @Slot(bool)
    def enable_pps(self, enable: bool):
        """Allow or block another calculation of PositionPowerSpectrum.

        The checkbox will not be possible to uncheck while the calculation
        is running, and the label text will inform the user that the
        calculation is in progres..
        """
        self.pps_checkbox.setEnabled(enable)
        message = "Show trajectory attenuation" if enable else "Calculating PPS..."
        self.pps_label.setText(message)

    @staticmethod
    def visit(widget: QWidget) -> Any:
        """Get widget value by QWidget instance.

        Parameters
        ----------
        widget : QWidget
            Widget whose value we want to get.

        Returns
        -------
        Any
            Widget value.

        """
        if isinstance(widget, QComboBox):
            return widget.currentText()

        if isinstance(widget, QCheckBox):
            return widget.isChecked()


class FilterSettingGroup(QObject):
    """Interface for a filter settings group.

    Provides a grid layout of settings for a given filter.

    """

    # Signal: emits a dictionary of attributes when settings have been updated
    _settings_updated = Signal(dict)

    # Signal: emitted when a setting has changed
    _setting_changed = Signal()

    def __init__(
        self,
        parent_attributes: dict,
        schema: dict,
        render_func: Callable,
        flags: set = set(),
    ):
        """
        Parameters
        ----------
        parent_attributes : dict
            Dictionary of attributes belonging to the parent filter designer widget.
        schema : dict
            Dictionary representing the schema for the filter-specific settings.
        render_func : Callable
            Filter designer function to call when preferences have been updated. The supplied function re-renders the
            filter designer graph with the updated attributes.
        flags : set
            Set of flags associated with the current filter that can be used to invoke certain rules about settings.

        """
        super().__init__()

        # Flags
        self.flags = flags

        # Set frequency units
        if Filter.Flags.DIGITAL_ONLY in self.flags:
            self.units = Filter.FrequencyUnits.CYCLIC
        else:
            self.units = Filter.FrequencyUnits.ANGULAR

        # Filter designer settings
        self.parent_attributes = parent_attributes

        # Dictionary of group specific settings
        self.attributes = {}

        # Dictionary mapping setting name to input widget
        self.widgets = {}

        # Grid layout into which the input widgets are placed
        self.grid = QGridLayout()

        # Schema for the filter settings
        self.schema = schema
        self.load_from_schema()

        freq_key = [key for key in self.schema if key.endswith("_freq")]
        initial_value = 1 / (
            self.parent_attributes["time_step_ps"] * self.parent_attributes["n_steps"]
        )
        if self.units is Filter.FrequencyUnits.ANGULAR:
            initial_value *= Filter._cyclic_to_angular
        self.attributes.update({freq_key.pop(): initial_value})

        # Indices for populating the settings grid layout
        self.indices = list(self.generate_grid_indices(len(self.schema.items())))

        # Connection: when a setting is changed, collect inputs
        self._setting_changed.connect(self.collect_inputs)

        # Connection: when the settings have been updated, re-render the filter designer
        self._settings_updated.connect(render_func)

    def load_from_schema(self) -> None:
        """Load the attributes from the filter setting schema."""
        for name, setting_dict in self.schema.items():
            self.attributes[name] = setting_dict["value"]

    def store_widget(self, name: str, widget: QWidget) -> None:
        """Store a widget in self.

        Parameters
        ----------
        name : str
            Name of the instance attribute to be stored, or key string.
        widget : QWidget
            Widget to be stored, or value corresponding to the key.

        Returns
        -------
        QWidget
            Stored widget

        """
        self.widgets.update({name: widget})

    def retrieve_widget(self, name: str) -> QWidget | None:
        """Retrieve a widget from self.

        Parameters
        ----------
        name : str
            Name of the filter type to which the attribute belongs.
        attribute : str
            Filter attribute as a string.

        Returns
        -------
        QWidget
            Stored widget.

        """
        return self.widgets.get(name)

    @staticmethod
    def visit(widget: QWidget) -> Any:
        """Get widget value by QWidget instance.

        Parameters
        ----------
        widget : QWidget
            Widget whose value we want to get.

        Returns
        -------
        Any
            The widget value.

        """
        if isinstance(widget, QSpinBox):
            return widget.value()

        if isinstance(widget, QDoubleSpinBox):
            return np.round(widget.value(), FLOAT_SPINBOX_DECIMALS)

        if isinstance(widget, QComboBox):
            return widget.currentText()

        if isinstance(widget, QCheckBox):
            return widget.isChecked()

    @Slot()
    def collect_inputs(self) -> None:
        """Slot: iterate over input widgets, collecting their values and update preferences."""
        for name, widget in self.widgets.items():
            if widget and name in self.attributes:
                self.attributes[name] = self.visit(widget)

        self._settings_updated.emit(self.attributes)

    def as_grid(self) -> QGridLayout:
        """Create the filter settings grid layout.

        Parameters
        ----------
        filter : Filter
            Selected filter class (one of [Butterworth, ChebyshevTypeI, ChebyshevTypeII, Elliptical, Bessel, Notch, Peak, Comb]).

        Returns
        -------
        QWidget
            Grid layout for filter settings.

        """
        if not self.indices:
            self.indices = list(self.generate_grid_indices(len(self.schema.items())))

        items = self.schema.items()
        for key, value in items:
            grid_pos = self.indices.pop(0)
            label = QLabel(key.replace("_", " ").capitalize())
            self.grid.addWidget(label, grid_pos[0][0], grid_pos[0][1])
            setting_widget = self.setting_to_widget(setting_key=key, val_group=value)
            # Store widget in object
            self.store_widget(key, setting_widget)
            self.grid.addWidget(setting_widget, grid_pos[1][0], grid_pos[1][1])

        return self.grid

    def setting_to_widget(self, setting_key: str, val_group: dict) -> QWidget:
        """Convert the setting dictionary to the corresponding setting widget and sets up connections.

        Parameters
        ----------
        setting_key : str
            Name of the edited setting.
        val_group : dict
            Dictionary containing the default value ("value" field) for the setting
            and the range of accepted values ("values" field) if applicable.

        Returns
        -------
        QWidget
            Setting widget with tooltip.

        """
        widget = None
        setting = val_group["value"]
        setting_group = val_group.get("values")
        tooltip = val_group.get("description", "")
        if isinstance(setting, int) and not setting_group:
            widget = QSpinBox()
            widget.setValue(setting)
            widget.setMinimum(0)
            widget.setSingleStep(1)
            signal = widget.valueChanged

        if isinstance(setting, float):
            if setting_key in {"cutoff_freq", "fundamental_freq"}:
                # Filter frequency spinbox with constrained values
                n_steps = self.parent_attributes.get("n_steps", DEFAULT_N_STEPS)
                time_step = self.parent_attributes.get(
                    "time_step_ps", DEFAULT_TIME_STEP
                )

                bin_width = np.round(
                    Filter.frequency_resolution(n_steps, time_step, units=self.units),
                    FLOAT_SPINBOX_DECIMALS,
                )

                vmax = np.round(
                    Filter.nyquist(time_step, units=self.units) - bin_width,
                    FLOAT_SPINBOX_DECIMALS,
                )

                # Configure constrained spinbox based on filter type
                if Filter.Flags.FUNDAMENTAL_EVENLY_DIVIDES_FS in self.flags:
                    widget = ConstrainedDoubleSpinBox(
                        minimum=bin_width,
                        maximum=vmax,
                        step=bin_width,
                        value=bin_width,
                    )
                    widget.set_search(
                        constraint_func=lambda x: ((1 / time_step) % x) == 0
                    )
                else:
                    widget = ConstrainedDoubleSpinBox(
                        minimum=bin_width,
                        maximum=vmax,
                        step=bin_width,
                        value=bin_width,
                    )
                    widget.set_snap(snap_to=bin_width)
            else:
                # Other data spinbox
                widget = QDoubleSpinBox()
                widget.setMinimum(0)
                widget.setMaximum(DEFAULT_SPINBOX_MAX_FLOAT)
                widget.setSingleStep(DEFAULT_SPINBOX_STEP_FLOAT)
                widget.setValue(setting)

            widget.setDecimals(FLOAT_SPINBOX_DECIMALS)
            signal = widget.valueChanged

        if isinstance(setting, bool):
            widget = QCheckBox()
            widget.setChecked(False)
            signal = widget.stateChanged

        if isinstance(setting, str) and setting_group:
            widget = QComboBox()
            for i in setting_group:
                widget.addItem(i)
            widget.setCurrentText(setting)
            signal = widget.currentTextChanged

        signal.connect(self.notify)
        widget.setToolTip(tooltip)
        return widget

    def notify(self) -> None:
        """Emit the signal on setting changed."""
        self._setting_changed.emit()

    @staticmethod
    def generate_grid_indices(n: int):
        """Generate indices for widgets positions on a grid.

        Returns a generator for a pair of position tuples representing the indices settings grid.
        The first element of the tuple is the position of the settings widget label, and the second element is the widget itself.

        Parameters
        ----------
        n : int
            Number of rows in the grid layout.

        """
        for i in range(n):
            yield ((i, 0), (i, 1))


class BoundedFilterSettingsGroup(FilterSettingGroup):
    """Interface for a filter settings group, where the filter cutoff frequency is bounded.

    Provides a grid layout of settings for a given filter.

    Attributes
    ----------
    _unbounded_filters : Set[string]
        Settings corresponding to the frequency bounds 'off' state.
        When these settings are used, the filter frequency is unbounded.
    _bounded_filters : Set[string]
        Settings corresponding to the frequency bounds 'on' state.
        When these settings are used, the filter frequency is bounded.

    """

    # Bounds behaviour corresponding to attenuation settings
    _unbounded_filters = {"lowpass", "highpass"}
    _bounded_filters = {"bandpass", "bandstop"}

    # Signal: emitted when frequency bounds are enabled
    _frequency_bounded = Signal(bool)

    def __init__(
        self,
        parent_attributes: dict,
        schema: dict,
        render_func: Callable,
        flags: set = set(),
    ):
        """
        Parameters
        ----------
        parent_attributes : dict
            Dictionary of attributes belonging to the parent filter designer widget.
        schema : dict
            Dictionary representing the schema for the filter-specific settings.
        render_func : Callable
            Filter designer function to call when preferences have been updated. The supplied function re-renders the
            filter designer graph with the updated attributes.
        flags : Set[Filter.Flags]
            Set of flags associated with the current filter that can be used to invoke certain rules about settings.

        """
        super().__init__(parent_attributes, schema, render_func, flags)

        # Generate an extra index for the frequency bound widget in the grid layout
        last_index = self.indices[-1]
        self.indices.append(((last_index[0][0] + 1, 0), (last_index[1][0] + 1, 1)))

        # Connection: when the attenuation type requires/doesn't require frequency bounds, toggle the bounds widget on/off
        self._frequency_bounded.connect(self.toggle_bound_frequencies)

    def get_frequency_bounds(self) -> list:
        """Create a list representing the upper and lower bounds of the filter critical frequencies.

        Returns
        -------
        list :
            List of length 2 containing the critical frequency bounds.

        """
        values = [
            self.retrieve_widget("cutoff_freq").value(),
            self.retrieve_widget("bound_freq").value(),
        ]
        return sorted(values)

    def toggle_bound_frequencies(self, on: bool = True) -> None:
        """Toggle the pair of critical frequency inputs on/off.

        Parameters
        ----------
        on : bool
            If true, both inputs for upper and lower frequency bounds are enabled, else only one input is enabled.

        """
        bounds = self.retrieve_widget("bound_freq")
        if bounds:
            bounds.setEnabled(on)

    def notify(self, value: Any) -> None:
        """Emit the signal on setting changed."""
        if value in (self._bounded_filters | self._unbounded_filters):
            self._frequency_bounded.emit(value in self._bounded_filters)

        # Ensure that cutoff frequency and bound frequency cannot have the same value
        if self.retrieve_widget("bound_freq").isEnabled():
            self.separate_bounds()

        super().notify()

    def separate_bounds(self):
        """Separate the cutoff and bound frequency spinbox values by a single step."""
        cutoff = self.retrieve_widget("cutoff_freq")
        bound = self.retrieve_widget("bound_freq")

        if cutoff.value() == bound.value():
            # Values are the same - we must keep the values separated by a single step

            # Ensure that the new bound value not greater than the maximum
            if (bound.value() + bound.singleStep()) > bound.maximum():
                cutoff.setValue(cutoff.value() - cutoff.singleStep())
                return

            # Ensure that the new bound value not less than the minimum
            if (bound.value() - bound.singleStep()) < bound.minimum():
                cutoff.setValue(cutoff.value() + cutoff.singleStep())
                return

            cutoff.setValue(cutoff.value() - cutoff.singleStep())

    @Slot()
    def collect_inputs(self) -> None:
        """Slot: iterate over input widgets, collecting their values and update attributes."""
        for name, widget in self.widgets.items():
            if widget and name in self.attributes:
                value = self.visit(widget)
                self.attributes[name] = value

                # Check if attribute invokes change in how frequencies are passed to filter (single cutoff value or array of critical frequencies)
                if value in {"bandpass", "bandstop"}:
                    self.toggle_bound_frequencies()
                    self.attributes["cutoff_freq"] = self.get_frequency_bounds()
                elif value in {"lowpass", "highpass"}:
                    self.toggle_bound_frequencies(False)
                    self.attributes["cutoff_freq"] = self.retrieve_widget(
                        "cutoff_freq"
                    ).value()
                elif (
                    self.retrieve_widget("attenuation_type").currentText()
                    in self._bounded_filters
                ):
                    self.attributes["cutoff_freq"] = self.get_frequency_bounds()

        self._settings_updated.emit(self.attributes)

    def as_grid(self) -> QGridLayout:
        """Populate the preferences grid layout with the filter designer preference widgets.

        Parameters
        ----------
        grid : QGridLayout
            Grid layout to which preference widgets will be added.

        """
        grid = super().as_grid()
        grid_pos = self.indices.pop()

        cutoff = self.retrieve_widget("cutoff_freq")
        step = cutoff.singleStep()
        widget = ConstrainedDoubleSpinBox(
            minimum=cutoff.minimum(),
            maximum=cutoff.maximum(),
            step=step,
            value=cutoff.value() + step,
        )
        widget.setDecimals(FLOAT_SPINBOX_DECIMALS)
        widget.set_snap(snap_to=step)
        widget.setEnabled(False)
        widget.valueChanged.connect(self.notify)
        self.store_widget("bound_freq", widget)
        grid.addWidget(widget, grid_pos[1][0] + 1, grid_pos[1][1])

        return grid


class FilterDesigner(QDialog):
    """Graphical interface for the trajectory filter.

    Generates a JSON string that specifies the designed filter.

    Attributes
    ----------
    _helper_title : str
        Title of the helper dialog window.
    _canvas_dimensions : dict
        Dimensions of the filter graph canvas.
    _trajectory_power_spectrum :  Sequence[npt.NDArray[float]] | None
        Trajectory power spectrum as a tuple containing the x-axis values (frequency domain) and the y-axis values (magnitudes).

    """

    _helper_title = "Filter designer"
    _canvas_dimensions = {"width": 700, "height": 500}
    _trajectory_power_spectrum = None

    def __init__(
        self,
        field: QLineEdit,
        configurator: TrajectoryFilterConfigurator,
        parent,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)
        self.field = field
        self.configurator = configurator

        self.graph_ready = False

        self.setting_stack_layout = QStackedLayout()
        self.preferences = {}
        self.settings_group = {}
        self.preferences_group = None

        self.pps_thread = None
        self.pps_last_params = {}
        self.pps_last_result = []

        self.layouts = QHBoxLayout()

        self.set_filter(self.configurator._default_filter.__name__)
        self.create_designer()
        self.preferences_group.pps_checkbox.checkStateChanged.connect(self.update_pps)

    def find_configuration(self) -> dict[str, str]:
        """Find the configuration of the main filter job.

        Returns
        -------
        dict[str, str]
            All configuration parameters of TrajectoryFilter

        """
        config = self.configurator.configurable._configuration
        return {
            k: v._original_input
            for k, v in config.items()
            if k in PositionPowerSpectrum.settings
        }

    def current_filter_units(self) -> Filter.FrequencyUnits:
        """Find the frequency unit enum based on the current filter.

        Returns
        -------
        FrequencyUnits
            Enum current filter frequency units.

        """
        current_index = self.setting_stack_layout.currentIndex()
        settings_group = tuple(self.settings_group.values())[current_index]
        return settings_group.units

    def set_filter(self, filter_type: str) -> None:
        """Set up a new filter settings dictionary.

        Parameters
        ----------
        filter_type : str
            Name of the filter class.

        """
        self.settings = {
            "filter": filter_type,
            "attributes": {
                # Number of simulation steps
                "n_steps": self.configurator.configurable.settings["trajectory"][1][
                    "configurator"
                ]["length"],
                # Simulation time step in picoseconds
                "time_step_ps": self.configurator.configurable.settings["trajectory"][
                    1
                ]["configurator"]["md_time_step"],
            },
        }

    def create_designer(self) -> None:
        """Create filter designer elements."""
        graph_layout = QVBoxLayout()
        settings_layout = QVBoxLayout()

        # Create the filter designer frequency-domain graph UI component
        self.create_graph_layout(graph_layout)

        # Create the filter designer settings UI component
        self.create_settings_layout(settings_layout)

        self.layouts = QHBoxLayout()
        self.layouts.addLayout(graph_layout)
        self.layouts.addLayout(settings_layout)
        self.setLayout(self.layouts)

    def update_filter(self, filter_type: str) -> None:
        """Re-renders the filter designer on filter type selection.

        Parameters
        ----------
        filter_type : str
            Name of the filter class.

        """
        self.set_filter(filter_type)

        # Set current index for settings stack layout
        index = list(FILTER_MAP.keys()).index(filter_type)
        self.setting_stack_layout.setCurrentIndex(index)

        settings_group = tuple(self.settings_group.values())[index]

        # Re-render filter graph
        settings_group._setting_changed.emit()

    def edit_preferences(self, preferences: dict) -> None:
        """Re-renders the filter according to display preferences.

        Parameters
        ----------
        preferences: dict
            A dictionary of filter settings.

        """
        self.preferences.update(preferences)

        self.render_canvas_assets()

    def resample_and_normalise(self, values, to_len):
        """Resample the input signal values to a given length, with normalisation of output signal.

        Parameters
        ----------
        values : np.ndarray
            Values of the signal.
        to_len : int
            New length of the signal after resampling.

        Returns
        -------
        np.ndarray
            Resampled and normalised signal.

        """
        return signal.resample(values, to_len) / values.max()

    @Slot(object)
    def accept_results(self, res_dict: dict[str, npt.NDArray[float]]):
        """Store the results of the calculation inf a background thread.

        Parameters
        ----------
        res_dict: dict[str, npt.NDArray[float]]
            A dictionary of {dataset_name: dataset_array} pairs.

        """
        self._trajectory_power_spectrum = list(res_dict.values())
        self.pps_thread = None
        self.render_canvas_assets()

    @Slot()
    def unblock_checkbox(self):
        """Make the checkbox clickable after the calculation thread has finshed."""
        self.preferences_group.enable_pps(True)

    def update_pps(self):
        """Run another PositionPowerSpectrum calculation.

        It will only start a new calculation if the calculation is not running already,
        there are no results so far, or the input parameters have changed.
        """
        if (
            self.pps_thread is not None
            or not self.preferences_group.pps_checkbox.isChecked()
        ):
            return
        new_params = self.find_configuration()
        if self.pps_last_params and all(
            self.pps_last_params[k] == new_params[k] for k in new_params
        ):
            return
        self.pps_last_params.update(new_params)
        self.pps_thread = BackgroundThread(
            None,
            "PositionPowerSpectrum",
            new_params,
            ["pps/axes/romega", "pps/total"],
        )
        self.pps_thread.results.connect(self.accept_results)
        self.pps_thread.finished.connect(self.unblock_checkbox)
        self.preferences_group.enable_pps(False)
        self.pps_thread.start()

    def set_trajectory_power_spectrum(
        self,
        tr_filter: Filter,
    ) -> Sequence[npt.NDArray[float]]:
        """Put curves on the same scale for the plot.

        Generate an appropriately resampled power spectrum for the input trajectory,
        as well as the multiplicative attenuation effect of the designed filter.

        Parameters
        ----------
        tr_filter : Filter
            Filter class for the designed filter.

        Returns
        -------
        raw_power_spectrum_freqs : npt.NDArray[float]
            Frequency axis of the original PPS result.
        power_spectrum : npt.NDArray[float]
            Trajectory power spectrum.
        attenuated_power_spectrum : npt.NDArray[float]
            Attenuated power spectrum due to the designed filter response.

        """
        response = tr_filter.freq_response

        # Trajectory power spectrum data
        raw_power_spectrum = copy.deepcopy(self._trajectory_power_spectrum)
        raw_power_spectrum_freqs, raw_power_spectrum_values = raw_power_spectrum

        # Resample trajectory power spectrum energies (x-axis) and convert to frequency domain
        power_spectrum_freqs = np.linspace(
            raw_power_spectrum_freqs.min(),
            raw_power_spectrum_freqs.max(),
            len(response.frequencies),
        )

        # Set custom frequency range on filter object
        tr_filter.custom_freq_range = power_spectrum_freqs
        tr_filter.freq_response = (tr_filter.coeffs, Filter.FrequencyRangeMethod.CUSTOM)

        # Resample and normalise trajectory power spectrum (y-axis)
        ps = raw_power_spectrum_values / np.max(raw_power_spectrum_values)

        attenuation = interp1d(
            tr_filter.freq_response.frequencies,
            tr_filter.freq_response.magnitudes,
            fill_value=0.0,
            bounds_error=False,
        )
        # Compute power spectral attenuation due to filter (multiplicative)
        attenuated_ps = ps * attenuation(raw_power_spectrum_freqs)

        return (raw_power_spectrum_freqs, ps, attenuated_ps)

    def create_settings_layout(self, widget_area: QVBoxLayout) -> None:
        """Create the filter settings vertical layout.

        Parameters
        ----------
        widget_area : QVBoxLayout
            Vertical box layout containing the filter type combobox, settings grid, and push buttons.

        """
        # Add filter type combobox
        type_cbox = QComboBox()
        for filter_name in FILTER_MAP:
            type_cbox.addItem(filter_name)

        type_label = QLabel("Filter type")
        type_cbox.setCurrentText(self.settings["filter"])

        type_cbox.currentTextChanged.connect(self.update_filter)

        filter_type_layout = QHBoxLayout()
        filter_type_layout.addWidget(type_label)
        filter_type_layout.addWidget(type_cbox)

        widget_area.addLayout(filter_type_layout)

        # Add each of the filter settings grid layout to the stack
        settings_groupbox = QGroupBox("Settings")
        settings_groupbox.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )

        for name, filter_class in FILTER_MAP.items():
            template = (
                FilterSettingGroup
                if Filter.Flags.DIGITAL_ONLY in filter_class.flags
                else BoundedFilterSettingsGroup
            )
            group_obj = template(
                parent_attributes=copy.deepcopy(self.settings["attributes"]),
                schema=filter_class.default_settings,
                render_func=self.render_canvas_assets,
                flags=filter_class.flags,
            )
            self.settings_group[name] = group_obj
            widget = QWidget()
            layout = self.settings_group[name].as_grid()
            widget.setLayout(layout)
            self.setting_stack_layout.addWidget(widget)

        # Set current index for settings stack layout
        index = list(FILTER_MAP).index(self.settings["filter"])
        self.setting_stack_layout.setCurrentIndex(index)

        settings_groupbox.setLayout(self.setting_stack_layout)
        widget_area.addWidget(settings_groupbox)

        # Add the filter designer preferences stack layout
        preferences_groupbox = QGroupBox("Preferences")
        preferences_groupbox.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )

        self.preferences_group = FilterPreferencesGroup(
            render_func=self.edit_preferences,
        )
        preferences_groupbox.setLayout(self.preferences_group.as_grid())

        widget_area.addWidget(preferences_groupbox)

        # Get default preferences
        self.preferences.update(
            {
                name: FilterPreferencesGroup.visit(widget)
                for name, widget in self.preferences_group.widgets.items()
            },
        )

        self.graph_ready = True

        # Render graph
        index = self.setting_stack_layout.currentIndex()
        tuple(self.settings_group.values())[index]._setting_changed.emit()

        # Add buttons
        buttons_layout = QHBoxLayout()
        for button in self.create_buttons():
            buttons_layout.addWidget(button)

        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget_area.addLayout(buttons_layout)

    def render_graph(
        self,
        freqs: FrequencyDomain = TrajectoryFilterConfigurator._default_filter.freq_response,
        db_response: bool = False,
        energies: bool = False,
        trajectory_power_spectrum: Sequence[npt.NDArray[float]] | None = None,
    ) -> None:
        """Render the graph of the designed filter frequency response.

        Parameters
        ----------
        freqs : FrequencyDomain
            Named tuple containing the magnitudes and frequencies of the filter frequency response.
        db_response : bool
            Display response (y-axis) in decibels, else magnitude.
        energies : bool
            Display response domain (x-axis) in meV, else frequency in terahertz.
        trajectory_power_spectrum : Sequence[npt.NDArray[float]]
            Tuple containing trajectory power spectrum and attenuation due to filter.

        """
        self._figure.clear()

        x, y = freqs.frequencies, freqs.magnitudes
        x_max = x.max()

        axes = self._figure.add_axes([0.1, 0.1, 0.8, 0.8])
        axes.plot(
            x,
            20 * np.log10(abs(y)) if db_response else y,
            label="Filter response",
        )

        # Conditionally display trajectory power spectral attenuation
        if trajectory_power_spectrum:
            psx, ps, attenuated_ps = trajectory_power_spectrum
            axes.plot(
                psx,
                20 * np.log10(abs(ps)) if db_response else ps,
                label="Trajectory response",
                color="grey",
            )
            axes.plot(
                psx,
                20 * np.log10(abs(attenuated_ps)) if db_response else attenuated_ps,
                label="Attenuation",
                color="black",
            )

        # Conditionally convert frequencies to energies (meV)
        if energies:
            energy_ticks = np.floor(
                Filter.freq_to_energy(axes.get_xticks(), self.current_filter_units()),
            ).astype(int)
            axes.set_xticks(axes.get_xticks(), labels=energy_ticks)

        axes.set_xlim(0.0, x_max)

        frequency_units = self.current_filter_units().value
        axes.set_xlabel(
            "Energy (meV)" if energies else f"Frequency ({frequency_units})",
        )
        axes.set_ylabel("Magnitude (dB)" if db_response else "Amplitude")

        axes.legend(loc="best")
        axes.grid(True)

        self._figure.canvas.draw()

    def render_graph_text(
        self,
        polynomial: str,
        cutoff: float,
        sample_freq: float,
    ) -> None:
        """Render the text containing the filter transfer function polynomial, cutoff energy, and simulation sample frequency.

        Parameters
        ----------
        polynomial : str
            String representation of the filter transfer function as a polynomial (in the variable S for an analogue filter).
        cutoff : float
            Cutoff frequency of the designed filter.
        sample_freq : float
            Sample frequency of the molecular dynamics simulation in THz (terahertz).

        """
        self._figure_info.clear()

        unit = polynomial["unit"]
        numerator = polynomial["numerator"]
        denominator = polynomial["denominator"]

        if (
            self.settings["filter"] not in {"Notch", "Peak", "Comb"}
            and self.settings["attributes"].get("order", 1) < 6
        ):
            self._figure_info.append(f"           {numerator}")
            self._figure_info.append(f"H({unit})=    {'-' * len(denominator)}")
            self._figure_info.append(f"           {denominator}")
        else:
            self._figure_info.append(
                "Number of filter coefficients exceeds available display area",
            )
            self._figure_info.append(" ")
            self._figure_info.append(" ")

        self._figure_info.append(
            f"Cutoff energy: {np.round(Filter.freq_to_energy(cutoff, self.current_filter_units()), FLOAT_SPINBOX_DECIMALS)} meV, Sample frequency: {sample_freq} THz",
        )

    def render_canvas_assets(self, attributes: dict | None = None) -> None:
        """Render all elements of the filter designer graphing area, including data text.

        Parameters
        ----------
        attributes: dict | None
            Filter attributes dictionary.

        """
        if not self.graph_ready:
            return

        if attributes:
            self.settings["attributes"].update(attributes)

        # Set preferences
        analog_filter = self.preferences["coeff_type"] == "analog"
        db_response = self.preferences["response_units"] == "dB"
        energies = self.preferences["xaxis_units"] == "meV"
        show_attenuation = self.preferences.get("show_attenuation", False)

        # Preview instantiation of the selected filter
        filter_class = FILTER_MAP[self.settings["filter"]]
        filter_preview = filter_class(**self.settings["attributes"])

        # Check if we are displaying trajectory power spectral attenuation alongside filter response
        ps, attenuated_ps = None, None
        if (
            show_attenuation
            and self.pps_thread is None
            and self._trajectory_power_spectrum is not None
        ):
            ps_axis, ps, attenuated_ps = self.set_trajectory_power_spectrum(
                filter_preview,
            )

        numerator, denominator = (
            filter_preview.to_digital_coeffs()
            if not analog_filter
            else filter_preview.coeffs
        )

        # Render the filter graph and text
        self.render_graph(
            filter_preview.freq_response,
            db_response=db_response,
            energies=energies,
            trajectory_power_spectrum=(ps_axis, ps, attenuated_ps)
            if ps is not None and attenuated_ps is not None
            else None,
        )
        self.render_graph_text(
            filter_class.rational_polynomial_string(
                numerator,
                denominator,
                analog=analog_filter,
            ),
            self.settings["attributes"].get(
                "cutoff_freq",
                self.settings["attributes"].get(
                    "fundamental_freq",
                    DEFAULT_FILTER_CUTOFF,
                ),
            ),
            filter_preview.sample_freq,
        )

    def create_graph_canvas(self, fig_width=10.0, fig_height=10.0, dpi=100) -> QWidget:
        """Create the canvas for the graphing area of the filter designer.

        Parameters
        ----------
        fig_width: float
            The figure width.
        fig_height: float
            The figure height.
        dpi: int
            Figure dpi.

        Returns
        -------
        QWidget
            Canvas for the filter designer graph.

        """
        canvas = QWidget(self)
        layout = QVBoxLayout(canvas)
        figure = mpl.figure(figsize=[fig_width, fig_height], dpi=dpi, frameon=True)
        figAgg = FigureCanvasQTAgg(figure)
        figAgg.setParent(canvas)
        toolbar = NavigationToolbar2QTAgg(figAgg, canvas)
        toolbar.update()
        figAgg.setMinimumSize(*self._canvas_dimensions.values())
        figAgg.setFixedSize(*self._canvas_dimensions.values())
        figAgg.updateGeometry()
        layout.addWidget(figAgg)
        layout.addWidget(toolbar)
        self._figure_info = QTextEdit()
        self._figure_info.setFontPointSize(8)
        self._figure_info.setReadOnly(True)
        layout.addWidget(self._figure_info)
        self._figure = figure
        self._toolbar = toolbar
        return canvas

    def create_graph_layout(self, widget_area: QVBoxLayout) -> None:
        """Create the canvas for the graphing area of the filter designer.

        Parameters
        ----------
        widget_area: QVBoxLayout
            The layout within the filter designer into which the filter graph will be positioned.

        """
        canvas = self.create_graph_canvas()
        widget_area.addWidget(canvas)
        self.render_canvas_assets()

    def combine_attributes(self, tr_filter: Filter, attributes: dict) -> dict:
        """Update the filter attributes with missing attributes, using default values.

        Parameters
        ----------
        tr_filter : Filter
            The filter class for the designed filter.
        attributes: dict
            Dictionary of filter attributes.

        Returns
        -------
        dict
            Combined attributes.

        """
        for key, val in tr_filter.default_settings.items():
            attributes.setdefault(key, val["value"])
        return attributes

    def apply(self) -> None:
        """Pass the filter parameters to the main widget."""
        self.configurator.configure(self.settings)

        filter_class = FILTER_MAP[self.settings["filter"]]

        # update widget field text to reflect filter designer
        field = filter_description_string(
            filter_class,
            self.combine_attributes(filter_class, self.settings["attributes"]),
        )
        self.field.setText(field)
        self.close()

    def create_buttons(self) -> list[QPushButton]:
        """Create button widgets needed by the filter interface.

        Returns
        -------
        list[QPushButton]
            List of push buttons to add to the last layout from
            create_layouts.

        """
        apply = QPushButton("Use Setting")
        close = QPushButton("Close")

        apply.setAutoDefault(False)
        apply.setDefault(False)
        close.setAutoDefault(False)
        close.setDefault(False)

        apply.clicked.connect(self.apply)
        close.clicked.connect(self.close)
        return [apply, close]


class TrajectoryFilterWidget(WidgetBase):
    """Trajectory filter designer widget."""

    _push_button_text = "Filter designer"
    _default_value = TrajectoryFilterConfigurator.get_default()
    _tooltip_text = "Design a trajectory filter. The input is a JSON string, and filter setting can be edited using the filter designer."

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._value = self._default_value
        self._field = QLineEdit(self._default_value, self._base)
        self._field.setPlaceholderText(self._default_value)
        self._field.setMaxLength(2147483647)  # set to the largest possible
        self._field.textChanged.connect(self.updateValue)
        self.filter_designer = self.create_helper()
        helper_button = QPushButton(self._push_button_text, self._base)
        helper_button.clicked.connect(self.helper_dialog)
        self._layout.addWidget(self._field)
        self._layout.addWidget(helper_button)
        self.update_labels()
        self.updateValue()
        self._field.setToolTip(self._tooltip_text)

    def create_helper(self) -> FilterDesigner:
        """
        Returns
        -------
        FilterDesigner
            Create and return the filter designer QDialog.

        """
        return FilterDesigner(self._field, self._configurator, self._base)

    @Slot()
    def helper_dialog(self) -> None:
        """Open the helper dialog."""
        if self.filter_designer.isVisible():
            self.filter_designer.close()
        else:
            self.filter_designer.update_pps()
            self.filter_designer.show()

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON selector setting.

        """
        selection_string = self._field.text()
        self._empty = not selection_string
        return selection_string if selection_string else self._default_value

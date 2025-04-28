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
import copy
from typing import Tuple, Any, Callable

import numpy as np
from scipy import signal
from qtpy.QtCore import Qt, Slot, Signal, QObject
from qtpy.QtWidgets import (
    QLineEdit,
    QPushButton,
    QDialog,
    QComboBox,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSpinBox,
    QStackedLayout,
    QDoubleSpinBox,
    QTextEdit,
    QWidget,
)
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE.Framework.Configurators.TrajectoryFilterConfigurator import (
    TrajectoryFilterConfigurator,
)
from MDANSE.Mathematics.Signal import (
    Filter,
    filter_description_string,
    FILTER_MAP,
    DEFAULT_FILTER_CUTOFF,
    DEFAULT_N_STEPS,
    DEFAULT_TIME_STEP,
    power_spectrum,
)
import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import (
    NavigationToolbar2QT as NavigationToolbar2QTAgg,
)


class ConstrainedDoubleSpinBox(QDoubleSpinBox):
    """Custom QDoubleSpinBox allowing for the application of a function
    to changed values in order to find an appropriate new value that satisfies the constraint.

    """

    def __init__(self, constraint_func: Callable = None):
        """
        Parameters
        ----------
        constraint_func : Callable
            Lambda for imposing constraint on spinbox value.
        """
        super().__init__()
        self.constraint_func = constraint_func
        self.valueChanged.connect(self.apply_constraint)

    def setValue(self, val) -> None:
        """Overrides setValue method of QDoubleSpinBox.
        Sets a record of the initial value of the spinbox, for determination of direction of change.

        Parameters
        ----------
        val : float
            The value of the spinbox.
        """
        self.initial_value = val
        super().setValue(val)

    def apply_constraint(self, value: Any) -> None:
        """Apply the constraint formalised in the lambda

        Parameters
        ----------
        value : Any
            The value of the spinbox.
        """
        if not self.constraint_func or self.constraint_func(value):
            return

        value_found = False
        if self.value() < self.initial_value:
            for x in np.arange(value, self.minimum(), -self.singleStep()):
                if self.constraint_func(x):
                    value_found = True
                    break
        else:
            for x in np.arange(value, self.maximum(), self.singleStep()):
                if self.constraint_func(x):
                    value_found = True
                    break

        if not value_found:
            return

        # Update with constrained value
        self.setValue(x)


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
            Filter designer function to call when preferences have been updated.
            Function re-renders the filter designer graph.
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
        """Stores a widget in self

        Parameters
        ----------
        name : str
            The name of the instance attribute to be stored, or key string.
        widget : QWidget
            The wadget to be stored, or value corresponding to the key.

        Returns
        -------
        QWidget:
            The stored widget
        """
        self.widgets.update({name: widget})

    def add_combobox(
        self, key: str, items: tuple = tuple(), tooltip: str = "", enabled: bool = True
    ) -> QWidget:
        """Produce a combobox for a filter designer preference

        Parameters
        --------
        on : bool
            If true, both inputs for upper and lower frequency bounds are enabled, else only one input is enabled

        Returns
        -------
        key : str
            The preference name
        items : tuple
            Items representing the available preference settings
        enabled : enabled
            Preference is enabled by default
        """
        widget = QComboBox()
        for i in items:
            widget.addItem(i)
        widget.setCurrentText(items[0])
        widget.setEnabled(enabled)
        widget.setToolTip(tooltip)
        self.store_widget(key, widget)
        self.preferences.update({key: widget.currentText()})
        widget.currentTextChanged.connect(self.collect_inputs)
        return widget

    @Slot()
    def collect_inputs(self) -> None:
        """Slot: iterate over input widgets, collecting their values and update attributes"""
        for name, widget in self.widgets.items():
            value = self.visit(widget)
            self.preferences[name] = value

        self._preferences_updated.emit(self.preferences)

    def as_grid(self) -> QGridLayout:
        """Populate the preferences grid layout with the filter designer preference widgets

        Parameters
        ---------
        grid : QGridLayout
            The grid layout to which preference widgets will be added
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
            ("rad/ps", "meV"),
            "View x-axis as angular frequency (rad/ps) or energy (meV)",
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
        self.grid.addWidget(QLabel("Show trajectory attenuation"), 3, 0)
        attenuation_checkbox = QCheckBox()
        self.widgets.update({"show_attenuation": attenuation_checkbox})
        attenuation_checkbox.setEnabled(True)
        attenuation_checkbox.stateChanged.connect(self.collect_inputs)
        attenuation_checkbox.setToolTip(
            "Display trajectory power spectrum for comparison"
        )
        self.grid.addWidget(attenuation_checkbox, 3, 1)

        return self.grid

    @staticmethod
    def visit(widget: QWidget) -> Any:
        """Get widget value by QWidget instance

        Parameters
        ----------
        widget : QWidget
            The wadget whose value we want to get.

        Returns
        -------
        Any:
            The widget value
        """
        if isinstance(widget, QComboBox):
            return widget.currentText()

        if isinstance(widget, QCheckBox):
            return widget.isChecked()


class FilterSettingGroup(QObject):
    """Interface for a filter settings group.
    provides a grid layout of settings for a given filter.

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
            Filter designer function to call when attributes have been updated.
            Function re-renders the filter designer graph with updated attributes.
        flags : set
            The set of flags associated with the current filter that can be used to invoke certain rules about settings.
        """
        super().__init__()

        # Flags
        self.flags = flags

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

        # Indices for populating the settings grid layout
        self.indices = list(self.generate_grid_indices(len(self.schema.items())))

        # Connection: when a setting is changed, collect inputs
        self._setting_changed.connect(self.collect_inputs)

        # Connection: when the settings have been updated, re-render the filter designer
        self._settings_updated.connect(render_func)

    def load_from_schema(self) -> None:
        """Load the attributes from the filter setting schema"""
        for name, setting_dict in self.schema.items():
            self.attributes[name] = setting_dict["value"]

    def store_widget(self, name: str, widget: QWidget) -> None:
        """Stores a widget in self

        Parameters
        ----------
        name : str
            The name of the instance attribute to be stored, or key string.
        widget : QWidget
            The wadget to be stored, or value corresponding to the key.

        Returns
        -------
        QWidget:
            The stored widget
        """
        self.widgets.update({name: widget})

    def retrieve_widget(self, name: str) -> QWidget | None:
        """Retrieves a widget from self

        Parameters
        ----------
        name : str
            The name of the filter type to which the attribute belongs.
        attribute : str
            Filter attribute as a string.

        Returns
        -------
        QWidget:
            The stored widget
        """
        return self.widgets.get(name)

    @staticmethod
    def visit(widget: QWidget) -> Any:
        """Get widget value by QWidget instance

        Parameters
        ----------
        widget : QWidget
            The wadget whose value we want to get.

        Returns
        -------
        Any:
            The widget value
        """
        if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
            return widget.value()

        if isinstance(widget, QComboBox):
            return widget.currentText()

        if isinstance(widget, QCheckBox):
            return widget.isChecked()

    @Slot()
    def collect_inputs(self) -> None:
        """Slot: iterate over input widgets, collecting their values and update preferences"""
        for name, widget in self.widgets.items():
            if widget and (name in self.attributes.keys()):
                self.attributes[name] = self.visit(widget)

        self._settings_updated.emit(self.attributes)

    def as_grid(self) -> QGridLayout:
        """Creates the filter settings grid layout.

        Parameters
        ----------
        filter : Filter
            Selected filter class (one of [Butterworth, ChebyshevTypeI, ChebyshevTypeII, Elliptical, Bessel, Notch, Peak, Comb])

        Returns
        ----------
        QWidget

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
        """Converts the setting dictionary to the corresponding setting widget and sets up connections.

        Parameters
        ----------
        setting_key : str
            The name of the edited setting.
        val_group : dict
            A dictionary containing the default value ("value" field) for the setting
            and the range of accepted values ("values" field) if applicable.

        Returns
        -------
        QWidget:
            Setting widget with tooltip
        """
        widget = None
        setting = val_group["value"]
        setting_group = val_group.get("values", None)
        tooltip = val_group.get("description", "")
        if isinstance(setting, int) and not setting_group:
            widget = QSpinBox()
            widget.setValue(setting)
            widget.setMinimum(0)
            widget.setSingleStep(1)
            signal = widget.valueChanged

        if isinstance(setting, float):
            n_steps = self.parent_attributes.get("n_steps", DEFAULT_N_STEPS)
            time_step = self.parent_attributes.get("time_step_ps", DEFAULT_TIME_STEP)
            fs = time_step ** (-1)
            if (
                Filter.Flags.FUNDAMENTAL_EVENLY_DIVIDES_FS in self.flags
                and setting_key == "fundamental_freq"
            ):
                widget = ConstrainedDoubleSpinBox(lambda x: (fs % x) == 0)
            else:
                widget = QDoubleSpinBox()
            step = 1 / (n_steps * time_step)
            widget.setDecimals(3)
            widget.setValue(setting)
            widget.setMaximum(1000)
            widget.setMinimum(step)
            widget.setSingleStep(step)
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

        if setting_key == "cutoff_freq":
            widget.setValue(DEFAULT_FILTER_CUTOFF)
        signal.connect(self.notify)
        widget.setToolTip(tooltip)
        return widget

    def notify(self) -> None:
        """Emit the signal on setting changed"""
        self._setting_changed.emit()

    @staticmethod
    def generate_grid_indices(n: int):
        """Returns a generator for a pair of position tuples representing the indices settings grid.
        The first element of the tuple is the position of the settings widget label, and the second element is the widget itself.

        Parameters
        ----------
        n : int
            The number of rows in the grid layout
        """
        for i in range(n):
            yield ((i, 0), (i, 1))


class BoundedFilterSettingsGroup(FilterSettingGroup):
    """Interface for a filter settings group, where the filter cutoff frequency is bounded.
    provides a grid layout of settings for a given filter.

    Attributes
    ----------
    _bounds_off : Set[string]
        The settings corresponding to the frequency bounds 'off' state.
        When these settings are used, the filter frequency is unbounded.
    _bounds_on : Set[string]
        The settings corresponding to the frequency bounds 'on' state.
        When these settings are used, the filter frequency is bounded.
    """

    # Bounds behaviour corresponding to attenuation settings
    _bounds_off = {"lowpass", "highpass"}
    _bounds_on = {"bandpass", "bandstop"}

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
            Filter designer function to call when attributes have been updated.
            Function re-renders the filter designer graph with updated attributes.
        flags : set
            The set of flags associated with the current filter that can be used to invoke certain rules about settings.
        """
        super().__init__(parent_attributes, schema, render_func, flags)

        # Generate an extra index for the frequency bound widget in the grid layout
        last_index = self.indices[-1]
        self.indices.append(((last_index[0][0] + 1, 0), (last_index[1][0] + 1, 1)))

        # Connection: when the attenuation type requires/doesn't require frequency bounds, toggle the bounds widget on/off
        self._frequency_bounded.connect(self.toggle_bound_frequencies)

    def get_frequency_bounds(self) -> list:
        """Create a list representing the upper and lower bounds of the filter critical frequencies

        Returns
        -------
        list :
            List of length 2 containing the critical frequency bounds.
        """
        return np.array(
            sorted(
                [
                    self.retrieve_widget("cutoff_freq").value(),
                    self.retrieve_widget("bound_freq").value(),
                ]
            )
        ).tolist()

    def toggle_bound_frequencies(self, on: bool = True) -> None:
        """Toggle the pair of critical frequency inputs on/off.

        Parameters
        --------
        on : bool
            If true, both inputs for upper and lower frequency bounds are enabled, else only one input is enabled
        """
        bounds = self.retrieve_widget("bound_freq")
        if bounds and on:
            bounds.setEnabled(True)
            return
        bounds.setEnabled(False)

    def notify(self, value: Any) -> None:
        """Emit the signal on setting changed"""
        if value in (self._bounds_on | self._bounds_off):
            self._frequency_bounded.emit(value in self._bounds_on)
        super().notify()

    @Slot()
    def collect_inputs(self) -> None:
        """Slot: iterate over input widgets, collecting their values and update attributes"""
        for name, widget in self.widgets.items():
            if widget and (name in self.attributes.keys()):
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
                    in self._bounds_on
                ):
                    self.attributes["cutoff_freq"] = self.get_frequency_bounds()

        self._settings_updated.emit(self.attributes)

    def as_grid(self) -> QGridLayout:
        """Populate the preferences grid layout with the filter designer preference widgets

        Parameters
        ---------
        grid : QGridLayout
            The grid layout to which preference widgets will be added
        """
        grid = super().as_grid()
        grid_pos = self.indices.pop()

        widget = QDoubleSpinBox()
        step = self.retrieve_widget("cutoff_freq").singleStep()
        widget.setDecimals(3)
        widget.setMaximum(self.retrieve_widget("cutoff_freq").maximum())
        widget.setMinimum(step)
        widget.setSingleStep(step)
        widget.setValue(DEFAULT_FILTER_CUTOFF * 0.5)
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
        The title of the helper dialog window.
    _canvas_dimensions : dict
        Dimensions of the filter graph canvas.
    _trajectory_power_spectrum :  tuple[ndarray, ndarray] | None
        Trajectory power spectrum as a tuple containing the x-axis values (frequency domain) and the y-axis values (magnitudes)
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

        self.setting_stack_layout = QStackedLayout()
        self.preferences = {}
        self.settings_group = {}
        self.preferences_group = None

        self.layouts = QHBoxLayout()

        self.set_filter(self.configurator._default_filter.__name__)
        self.create_designer()

    def find_configuration_property(self, key) -> Any:
        """Find a configurator value from a key string

        Parameters
        -------
        key: str
            Configuration key to get.

        Returns
        -------
        Any
            Configuration value.
        """
        config = self.configurator._configurable._configuration
        return config.get(key)

    def set_filter(self, filter_type: str) -> None:
        """Set up a new filter settings dictionary.

        Parameters
        ----------
        filter_type : str
            The name of the filter class.
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

        # Create the filter designer settings UI component
        self.create_settings_layout(settings_layout)

        # Create the filter designer frequency-domain graph UI component
        self.create_graph_layout(graph_layout)

        self.layouts = QHBoxLayout()
        self.layouts.addLayout(graph_layout)
        self.layouts.addLayout(settings_layout)
        self.setLayout(self.layouts)

    def update_filter(self, filter_type: str) -> None:
        """Re-renders the filter designer on filter type selection.

        Parameters
        ----------
        filter_type : str
            The name of the filter class.
        """
        self.set_filter(filter_type)

        # Set current index for settings stack layout
        index = list(FILTER_MAP.keys()).index(filter_type)
        self.setting_stack_layout.setCurrentIndex(index)

        # Check figure attribute exists before attempting to render
        if hasattr(self, "_figure"):
            self.render_canvas_assets()

    def edit_preferences(self, preferences: dict) -> None:
        """Re-renders the filter according to display preferences.

        Parameters
        ----------
        key : str
            The name of the edited preference.
        value : any
            The value of the edited preference.
        """
        self.preferences.update(preferences)

        # Load trajectory attenuation
        if self.preferences["show_attenuation"] and not self._trajectory_power_spectrum:
            self._trajectory_power_spectrum = power_spectrum(
                self.find_configuration_property("trajectory"),
                self.find_configuration_property("frames"),
                self.find_configuration_property("projection"),
                self.find_configuration_property("atom_selection"),
                self.find_configuration_property("weights"),
                self.find_configuration_property("instrument_resolution"),
            )

        self.render_canvas_assets()

    def resample_and_normalise(self, values, to_len):
        """Resample the input signal values to a given length, with normalisation of output signal

        Parameters
        ----------
        values : np.ndarray
            The values of the signal
        to_len : int
            The new length of the signal after resampling

        Returns
        -------
        np.ndarray
            Resampled and normalised signal
        """
        return signal.resample(values, to_len) * (values.max() ** (-1))

    def set_trajectory_power_spectrum(
        self, filter: Filter
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate an appropriately resampled power spectrum for the input trajectory,
        as well as the multiplicative attenuation effect of the designed filter.

        Parameters
        ----------
        filter : Filter
            The Filter class for the designed filter

        Returns
        -------
        Tuple[np.ndarray, np.ndarray]
            Trajectory power spectrum and the attenuated power spectrum due to the designed filter response
        """
        response = filter.freq_response

        # Trajectory power spectrum data
        raw_power_spectrum = copy.deepcopy(self._trajectory_power_spectrum)
        raw_power_spectrum_energies, raw_power_spectrum_values = raw_power_spectrum

        # Resample trajectory power spectrum energies (x-axis) and convert to frequency domain
        power_spectrum_energies = np.linspace(
            raw_power_spectrum_energies.min(),
            raw_power_spectrum_energies.max(),
            len(response.frequencies),
        )
        power_spectrum_freqs = Filter.energy_to_freq(
            power_spectrum_energies, Filter.FrequencyUnits.ANGULAR
        )

        # Set custom frequency range on filter object
        filter._custom_freq_range = power_spectrum_freqs
        filter.freq_response = (filter._coeffs, Filter.FrequencyRangeMethod.CUSTOM)

        # Resample and normalise trajectory power spectrum (y-axis)
        ps = self.resample_and_normalise(
            values=raw_power_spectrum_values, to_len=len(response.frequencies)
        )

        # Compute power spectral attenuation due to filter (multiplicative)
        attenuated_ps = ps * filter.freq_response.magnitudes

        return (ps, attenuated_ps)

    def create_settings_layout(self, widget_area: QVBoxLayout) -> None:
        """Creates the filter settings vertical layout.

        Parameters
        ----------
        widget_area : QVBoxLayout
            The vertical box layout containing the filter type combobox, settings grid, and push buttons.
        """
        # Add filter type combobox
        type_cbox = QComboBox()
        for filter_name in FILTER_MAP.keys():
            type_cbox.addItem(filter_name)

        type_label = QLabel("Filter type")
        type_cbox.setCurrentText(self.settings["filter"])

        type_cbox.currentTextChanged.connect(self.update_filter)

        filter_type_layout = QHBoxLayout()
        filter_type_layout.addWidget(type_label)
        filter_type_layout.addWidget(type_cbox)

        widget_area.addLayout(filter_type_layout)

        # Add each of the filter settings grid layout to the stack
        settings_groupbox = QGroupBox("Settings", None)
        settings_groupbox.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
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
            self.settings_group.update({name: group_obj})
            widget = QWidget()
            layout = self.settings_group[name].as_grid()
            widget.setLayout(layout)
            self.setting_stack_layout.addWidget(widget)

        # Set current index for settings stack layout
        index = list(FILTER_MAP.keys()).index(self.settings["filter"])
        self.setting_stack_layout.setCurrentIndex(index)

        settings_groupbox.setLayout(self.setting_stack_layout)
        widget_area.addWidget(settings_groupbox)

        # Add the filter designer preferences stack layout
        preferences_groupbox = QGroupBox("Preferences", None)
        preferences_groupbox.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )

        self.preferences_group = FilterPreferencesGroup(
            render_func=self.edit_preferences
        )
        preferences_groupbox.setLayout(self.preferences_group.as_grid())

        widget_area.addWidget(preferences_groupbox)

        # Get default preferences
        self.preferences.update(
            {
                name: FilterPreferencesGroup.visit(widget)
                for name, widget in self.preferences_group.widgets.items()
            }
        )

        # Add buttons
        buttons_layout = QHBoxLayout()
        for button in self.create_buttons():
            buttons_layout.addWidget(button)

        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget_area.addLayout(buttons_layout)

    def render_graph(
        self,
        freqs: Filter.FrequencyDomain = TrajectoryFilterConfigurator._default_filter.freq_response,
        db_response: bool = False,
        energies: bool = False,
        trajectory_power_spectrum: Tuple[np.ndarray, np.ndarray] = None,
    ) -> None:
        """Renders the graph of the designed filter frequency response.

        Parameters
        ----------
        freqs : Filter.FrequencyDomain
            Named tuple containing the magnitudes and frequencies of the filter frequency response.
        db_response : bool
            Display response (y-axis) in decibels, else magnitude
        energies : bool
            Display response domain (x-axis) in meV, else frequency in terahertz
        trajectory_power_spectrum : Tuple[np.ndarray, np.ndarray]
            Tuple containing trajectory power spectrum and attenuation due to filter
        """
        self._figure.clear()

        x = freqs.frequencies
        x_max = x.max()

        axes = self._figure.add_axes([0.1, 0.1, 0.8, 0.8])
        axes.plot(
            x,
            20 * np.log10(abs(freqs.magnitudes)) if db_response else freqs.magnitudes,
            label="Filter response",
        )

        # Conditionally display trajectory power spectral attenuation
        if trajectory_power_spectrum:
            ps, attenuated_ps = trajectory_power_spectrum
            axes.plot(
                x,
                20 * np.log10(abs(ps)) if db_response else ps,
                label="Trajectory response",
                color="grey",
            )
            axes.plot(
                x,
                20 * np.log10(abs(attenuated_ps)) if db_response else attenuated_ps,
                label="Attenuation",
                color="black",
            )

        # Conditionally convert frequencies (rad/ps) to energies (meV)
        if energies:
            energy_ticks = np.int32(
                np.floor(
                    Filter.freq_to_energy(
                        axes.get_xticks(), Filter.FrequencyUnits.ANGULAR
                    )
                )
            )
            axes.set_xticks(axes.get_xticks(), labels=energy_ticks)

        axes.set_xlim(0.0, x_max)

        axes.set_xlabel("Energy (meV)" if energies else "Frequency (rad/ps)")
        axes.set_ylabel("Magnitude (dB)" if db_response else "Amplitude")

        axes.legend(loc="best")
        axes.grid(True)

        self._figure.canvas.draw()

    def render_graph_text(
        self, polynomial: str, cutoff: float, sample_freq: float
    ) -> None:
        """Renders the text containing the filter transfer function polynomial, cutoff energy, and simulation sample frequency.

        Parameters
        ----------
        polynomial : str
            String representation of the filter transfer function as a polynomial (in the variable S for an analogue filter).
        cutoff : float
            Cutoff frequency of the designed filter in rad/ps
        sample_freq : float
            Sample frequency of the molecular dynamics simulation in THz (terahertz)
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
                "Number of filter coefficients exceeds available display area"
            )
            self._figure_info.append(" ")
            self._figure_info.append(" ")

        self._figure_info.append(
            f"Cutoff energy: {np.round(Filter.freq_to_energy(cutoff, Filter.FrequencyUnits.ANGULAR), 3)} meV, Sample frequency: {sample_freq} THz"
        )

    def render_canvas_assets(self, attributes: dict = None) -> None:
        """Render all elements of the filter designer graphing area, including data text"""
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
        if show_attenuation:
            ps, attenuated_ps = self.set_trajectory_power_spectrum(filter_preview)

        numerator, denominator = (
            filter_preview.to_digital_coeffs()
            if not analog_filter
            else filter_preview._coeffs
        )

        # Render the filter graph and text
        self.render_graph(
            filter_preview.freq_response,
            db_response=db_response,
            energies=energies,
            trajectory_power_spectrum=(ps, attenuated_ps) if show_attenuation else None,
        )
        self.render_graph_text(
            filter_class.rational_polynomial_string(
                numerator, denominator, analog=analog_filter
            ),
            self.settings["attributes"].get("cutoff_freq", DEFAULT_FILTER_CUTOFF),
            filter_preview._sample_freq,
        )

    def create_graph_canvas(self, fig_width=10.0, fig_height=10.0, dpi=100) -> QWidget:
        """Create the canvas for the graphing area of the filter designer

        Parameters
        ----------
        fig_width: float
            The figure width
        fig_height: float
            The figure height
        dpi: int
            Figure dpi

        Returns
        -------
        QWidget
            Canvas for the filter designer graph
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
        """Create the canvas for the graphing area of the filter designer

        Parameters
        ----------
        widget_area: QVBoxLayout
            The layout within the filter designer into which the filter graph will be positioned
        """
        canvas = self.create_graph_canvas()
        widget_area.addWidget(canvas)
        self.render_canvas_assets()

    def combine_attributes(self, filter: Filter, attributes: dict) -> dict:
        """Update the filter attributes with missing attributes, using default values

        Parameters
        ----------
        filter : Filter
            The filter class for the designed filter
        attributes: dict
            Dictionary of filter attributes

        Returns
        -------
        dict
            Combined attributes
        """
        defaults = filter.default_settings
        missing = set(attributes) ^ set(defaults)
        attributes.update(
            {
                key: filter.default_settings[key]["value"]
                for key in missing
                if key in defaults
            }
        )
        return attributes

    def apply(self) -> None:
        """Set the field of the TrajectoryFilterWidget to the currently
        chosen setting in this widget.
        """
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
        """
        Returns
        -------
        list[QPushButton]
            List of push buttons to add to the last layout from
            create_layouts.
        """
        apply = QPushButton("Use Setting")
        close = QPushButton("Close")
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
        """Opens the helper dialog."""
        if self.filter_designer.isVisible():
            self.filter_designer.close()
        else:
            self.filter_designer.show()

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON selector setting.
        """
        selection_string = self._field.text()
        if len(selection_string) < 1:
            self._empty = True
            return self._default_value
        else:
            self._empty = False
        return selection_string

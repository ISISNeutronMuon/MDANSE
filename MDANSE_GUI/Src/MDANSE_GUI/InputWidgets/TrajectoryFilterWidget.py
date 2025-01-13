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
from typing import Tuple, Any

import numpy as np
from scipy import signal
from qtpy.QtCore import Qt, Slot, QTimer, QCoreApplication
from qtpy.QtWidgets import (
    QLineEdit,
    QPushButton,
    QDialog,
    QComboBox,
    QCheckBox,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QTextEdit,
    QWidget,
    QMessageBox
)
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE.Framework.Configurators.TrajectoryFilterConfigurator import TrajectoryFilterConfigurator
from MDANSE.Mathematics.Signal import Filter, filter_map, DEFAULT_FILTER_CUTOFF, power_spectrum
import matplotlib.pyplot as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

class FilterDesigner(QDialog):
    """Graphical interface for the trajectory filter.
    Generates a JSON string that specifies the designed filter.

    Attributes
    ----------
    _helper_title : str
        The title of the helper dialog window.
    _canvas_dimensions: dict
        Dimensions of the filter graph canvas.
    _settings_grid_layout: QGridLayout
        Grid layout for the filter settings.
    """

    _helper_title = "Filter designer"
    _canvas_dimensions = {
        "width": 600,
        "height": 500
    }
    _setting_grid_layout = QGridLayout()
    _preferences_grid_layout = QGridLayout()
    _preferences = dict()
    _trajectory_power_spectrum = None

    def __init__(self, field: QLineEdit, configurator: TrajectoryFilterConfigurator, parent, *args, **kwargs):
        """
        Parameters
        ----------
        field : QLineEdit
            The QLineEdit field that will need to be updated when
            applying the setting.
        """

        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)
        self._field = field
        self._configurator = configurator

        self.layouts = QHBoxLayout()

        self.set_filter(self._configurator.filter.__name__)
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
        config = self._configurator._configurable._configuration
        return config.get(key, None)

    def set_filter(self, filter_type: str) -> None:
        """Set up a new filter settings dictionary.

        Parameters
        ----------
        filter_type : str
            The name of the filter class.
        """
        self._settings = {
            "filter": filter_type,
            "attributes": {
                # Number of simulation steps
                "n_steps": self._configurator.configurable.settings["trajectory"][1]["configurator"]["length"],
                # Simulation time step in picoseconds
                "time_step_ps": self._configurator.configurable.settings["trajectory"][1]["configurator"]["md_time_step"]
            }
        }

    def clear_settings_grid(self, grid: QGridLayout) -> None:
        """Clear all widgets contained in the settings grid layout.

        """
        for i in reversed(range(grid.count())):
            widget = grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def create_designer(self) -> None:
        """Create filter designer elements.

        """
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
        self.clear_settings_grid(self._setting_grid_layout)
        self.set_filter(filter_type)
        self.make_settings_grid(
            filter_map[self._settings["filter"]],
            self._setting_grid_layout
        )

        # Check figure attribute exists before attempting to render
        if hasattr(self, "_figure"):
            self.render_canvas_assets()

    def get_frequency_bounds(self) -> list:
        """Create a list representing the upper and lower bounds of the filter critical frequencies

        Returns
        -------
        list :
            List of length 2 containing the critical frequency bounds.
        """
        return np.array(
            sorted(
                [self.cutoff_freq_widget.value(),
                 self.bound_freq_widget.value()]
            )
        ).tolist()

    def edit_current_filter(self, key: str, value: any) -> None:
        """Re-renders the filter graph preview and updates the current filter settings when a setting is edited.

        Parameters
        ----------
        key : str
            The name of the edited setting.
        value : any
            The value of the edited setting.
        """
        # Update attribute
        self._settings["attributes"].update({key: value})

        # Check if attribute invokes change in how frequencies are passed to filter (single cutoff value or array of critical frequencies)
        if value in {"bandpass", "bandstop"}:
            self.toggle_bound_frequencies()
            self._settings["attributes"]["cutoff_freq"] = self.get_frequency_bounds()
        elif value in {"lowpass", "highpass"}:
            self.toggle_bound_frequencies(False)
            self._settings["attributes"]["cutoff_freq"] = self.cutoff_freq_widget.value()
        elif self.attenuation_type_widget.currentText() in {"bandpass", "bandstop"}:
            self._settings["attributes"]["cutoff_freq"] = self.get_frequency_bounds()

        # Re-render filter graph
        self.render_canvas_assets()

    def edit_preferences(self, key: str, value: any) -> None:
        """Re-renders the filter according to display preferences.

        Parameters
        ----------
        key : str
            The name of the edited preference.
        value : any
            The value of the edited preference.
        """
        self._preferences.update({key: value})

        # Load trajectory attenuation
        if key == "show_attenuation" and not self._trajectory_power_spectrum:
            self._trajectory_power_spectrum = power_spectrum(
                self.find_configuration_property("trajectory"),
                self.find_configuration_property("frames"),
                self.find_configuration_property("projection"),
                self.find_configuration_property("atom_selection"),
                self.find_configuration_property("weights"),
                self.find_configuration_property("instrument_resolution")
            )

        self.render_canvas_assets()

    def set_trajectory_power_spectrum(self, filter: Filter) -> Tuple[np.ndarray, np.ndarray]:
        """Generate an appropriately resampled power spectrum for the input trajectory,
        as well as the multiplicative attenuation effect of the designed filter.

        Parameters:
        ----------
        filter: Filter
            The Filter class for the designed filter

        Returns:
        -------
        Tuple[np.ndarray, np.ndarray]
            Trajectory power spectrum and the attenuated power spectrum due to the designed filter response
        """
        response = filter.freq_response

        # Lambda to resample and normalise input values
        values = lambda a, new_len: signal.resample(a, new_len) * (a.max() ** (-1))

        # Trajectory power spectrum data
        raw_power_spectrum = copy.deepcopy(self._trajectory_power_spectrum)
        raw_power_spectrum_energies, raw_power_spectrum_values = raw_power_spectrum

        # Resample trajectory power spectrum energies (x-axis) and convert to frequency domain
        power_spectrum_energies = np.linspace(raw_power_spectrum_energies.min(), raw_power_spectrum_energies.max(), len(response.frequencies))
        power_spectrum_freqs = Filter.energy_to_freq(power_spectrum_energies)

        # Set custom frequency range on filter object
        filter.custom_freq_range = power_spectrum_freqs
        filter.freq_response = (filter.coeffs, Filter.FrequencyRangeMethod.Custom)

        # Resample and normalise trajectory power spectrum (y-axis)
        ps = values(raw_power_spectrum_values, len(response.frequencies))

        # Compute power spectral attenuation due to filter (multiplicative)
        attenuated_ps = ps * filter.freq_response.magnitudes

        return (ps, attenuated_ps)

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
            widget = QDoubleSpinBox()
            step = 1.0
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
        signal.connect(lambda val: self.edit_current_filter(setting_key, val))
        widget.setToolTip(tooltip)
        return widget

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

    def make_settings_grid(self, filter: Filter, grid: QGridLayout) -> None:
        """Creates the filter settings grid layout.

        Parameters
        ----------
        filter : Filter
            Selected filter class (one of [Butterworth, ChebyshevTypeI, ChebyshevTypeII, Elliptical, Bessel, Notch, Peak, Comb])
        """
        filter.set_defaults()
        setting_items = filter.default_settings.items()

        # Add filter settings to grid layout
        indices = list(
            self.generate_grid_indices(len(setting_items))
        )

        try:
            item_count = 0
            for key, value in setting_items:
                grid_pos = indices.pop(0)
                label = QLabel(key.replace('_', ' ').capitalize())
                grid.addWidget(label, grid_pos[0][0], grid_pos[0][1])
                setting_widget = self.setting_to_widget(setting_key=key, val_group=value)
                # Store widget in object
                self.__dict__.update({f'{key}_label': label})
                self.__dict__.update({f'{key}_widget': setting_widget})
                grid.addWidget(setting_widget, grid_pos[1][0], grid_pos[1][1])
                item_count += 1

            # For non-IIR filters, add frequency bound spinbox in case designed filter is bandpass/stop
            if filter.__name__ not in {'Notch', 'Peaks', 'Comb'}:
                self.bound_freq_widget = QDoubleSpinBox()
                step = 1.0
                widget = self.bound_freq_widget
                widget.setMaximum(1000)
                widget.setMinimum(step)
                widget.setSingleStep(step)
                widget.setValue(DEFAULT_FILTER_CUTOFF*0.5)
                widget.setEnabled(False)
                widget.valueChanged.connect(lambda val: self.edit_current_filter('cutoff_freq', val))
                grid.addWidget(self.bound_freq_widget, grid_pos[1][0]+1, grid_pos[1][1])
                item_count += 1

        except RuntimeError:
            # C++ object wrapping grid layout may have been deleted - recreate grid layout and try again
            self._setting_grid_layout = QGridLayout()
            self.update_filter(filter.__name__)

    def toggle_bound_frequencies(self, on: bool=True):
        """Toggle the pair of critical frequency inputs on/off.

        Parameters
        --------
        on : bool
            If true, both inputs for upper and lower frequency bounds are enabled, else only one input is enabled
        """
        if on:
            self.bound_freq_widget.setEnabled(True)
            return
        self.bound_freq_widget.setEnabled(False)

    def add_preference_combobox(self, key: str, items: tuple=tuple(), enabled: bool=True) -> QWidget:
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
        self._preferences.update({key: widget.currentText()})
        return widget

    def make_preferences_grid(self, grid: QGridLayout) -> None:
        """Populate the preferences grid layout with the filter designer preference widgets

        Parameters
        ---------
        grid : QGridLayout
            The grid layout to which preference widgets will be added
        """
        try:
            # Y-axis in amplitude or decibels
            grid.addWidget(QLabel("Response units"), 0, 0)
            key_0 = "response_units"
            widget_0 = self.add_preference_combobox(key_0, ("amplitude", "dB"))
            widget_0.currentTextChanged.connect(lambda val: self.edit_preferences(key_0, val))
            grid.addWidget(widget_0, 0, 1)

            # X-axis in angular frequency or energy (meV)
            grid.addWidget(QLabel("X-axis units"), 1, 0)
            key_1 = "xaxis_units"
            widget_1 = self.add_preference_combobox(key_1, ("pHz", "meV"))
            widget_1.currentTextChanged.connect(lambda val: self.edit_preferences(key_1, val))
            grid.addWidget(widget_1, 1, 1)

            # Display filter transfer function in terms of analogue or digital filter coefficients
            grid.addWidget(QLabel("Filter coefficients"), 2, 0)
            key_2 = "coeff_type"
            widget_2 = self.add_preference_combobox(key_2, ("analog", "digital"))
            widget_2.currentTextChanged.connect(lambda val: self.edit_preferences(key_2, val))
            grid.addWidget(widget_2, 2, 1)

            # Display trajectory position power spectral attentuation for comparison
            grid.addWidget(QLabel("Show trajectory attenuation"), 3, 0)
            key_4 = "show_attenuation"
            attenuation_checkbox = QCheckBox()
            self._preferences.update({key_4: attenuation_checkbox.isChecked()})
            attenuation_checkbox.stateChanged.connect(lambda val: self.edit_preferences(key_4, val))
            grid.addWidget(attenuation_checkbox, 3, 1)
            attenuation_checkbox.setEnabled(True)

        except RuntimeError:
            # C++ object wrapping grid layout may have been deleted - recreate grid layout and try again
            self._preferences_grid_layout = QGridLayout()
            self.make_preferences_grid(self._preferences_grid_layout)


    def create_settings_layout(self, widget_area: QVBoxLayout) -> None:
        """Creates the filter settings vertical layout.

        Parameters
        ----------
        widget_area : QVBoxLayout
            The vertical box layout containing the filter type combobox, settings grid, and push buttons.
        """
        # Add filter type combobox
        type_cbox = QComboBox()
        for filter_name in filter_map.keys():
            type_cbox.addItem(filter_name)

        type_label = QLabel("Filter type")
        type_cbox.setCurrentText(self._settings["filter"])

        type_cbox.currentTextChanged.connect(lambda filter_type: self.update_filter(filter_type))

        filter_type_layout = QHBoxLayout()
        filter_type_layout.addWidget(type_label)
        filter_type_layout.addWidget(type_cbox)

        widget_area.addLayout(filter_type_layout)

        # Add the filter settings grid layout
        filter_class = filter_map[self._settings["filter"]]
        self.make_settings_grid(filter_class, self._setting_grid_layout)

        widget_area.addLayout(self._setting_grid_layout)

        # Add the filter designer preferences grid layout
        self.make_preferences_grid(self._preferences_grid_layout)
        widget_area.addLayout(self._preferences_grid_layout)

        # Add buttons
        buttons_layout = QHBoxLayout()
        for button in self.create_buttons():
            buttons_layout.addWidget(button)

        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget_area.addLayout(buttons_layout)

    def render_graph(self,
                     freqs: Filter.FrequencyDomain=TrajectoryFilterConfigurator._filter.freq_response,
                     db_response: bool=False,
                     energies: bool=False,
                     trajectory_power_spectrum: Tuple[np.ndarray, np.ndarray]=None
        ) -> None:
        """Renders the graph of the designed filter frequency response.

        Parameters
        ----------
        freqs : Filter.FrequencyDomain
            Named tuple containing the magnitudes and frequencies of the filter frequency response.
        db_response : bool
            Display response (y-axis) in decibels, else magnitude
        energies : bool
            Display response domain (x-axis) in meV, else frequency in picohertz
        trajectory_power_spectrum : Tuple[np.ndarray, np.ndarray]
            Tuple containing trajectory power spectrum and attenuation due to filter
        """
        self._figure.clear()

        x = freqs.frequencies
        x_max = x.max()

        axes = self._figure.add_axes([0.1, 0.1, 0.8, 0.8])
        axes.plot(x, 20 * np.log10(abs(freqs.magnitudes)) if db_response else freqs.magnitudes, label="Filter response")

        # Conditionally display trajectory power spectral attenuation
        if trajectory_power_spectrum:
            ps, attenuated_ps = trajectory_power_spectrum
            axes.plot(x, 20 * np.log10(abs(ps)) if db_response else ps, label="Trajectory response", color="grey")
            axes.plot(x, 20 * np.log10(abs(attenuated_ps)) if db_response else attenuated_ps, label="Attenuation", color="black")

        # Conditionally convert frequencies (pHz) to energies (meV)
        if energies:
            energy_ticks = np.int32(np.floor(Filter.freq_to_energy(axes.get_xticks())))
            axes.set_xticks(axes.get_xticks(), labels=energy_ticks)

        axes.set_xlim(0.0, x_max)

        axes.set_xlabel("Energy (meV)" if energies else "Frequency (pHz)")
        axes.set_ylabel("Magnitude (dB)" if db_response else "Amplitude")

        axes.legend(loc="best")
        axes.grid(True)

        self._figure.canvas.draw()

    def render_graph_text(self, polynomial: str, cutoff: float, sample_freq: float) -> None:
        """Renders the text containing the filter transfer function polynomial, cutoff energy, and simulation sample frequency.

        Parameters
        ----------
        polynomial : str
            String representation of the filter transfer function as a polynomial (in the variable S for an analogue filter).
        polynomial : float
            Sample frequency of the molecular dynamics simulation in pHz (picohertz)
        """
        self._figure_info.clear()

        unit = polynomial["unit"]
        numerator = polynomial["numerator"]
        denominator = polynomial["denominator"]

        if self._settings["filter"] not in {"Notch", "Peaks", "Comb"} and self._settings["attributes"].get("order", 1) < 6:
            self._figure_info.append(f"           {numerator}")
            self._figure_info.append(f"H({unit})=    {'-'*len(denominator)}")
            self._figure_info.append(f"           {denominator}")
        else:
            self._figure_info.append(f"Number of filter coefficients exceeds available display area")
            self._figure_info.append(f" ")
            self._figure_info.append(f" ")

        self._figure_info.append(f"Cutoff energy: {np.round(Filter.freq_to_energy(cutoff), 1)} meV, Sample frequency: {sample_freq} pHz")

    def render_canvas_assets(self) -> None:
        """Render all elements of the filter designer graphing area, including data text

        """
        # Set preferences
        analog_filter = self._preferences["coeff_type"] == "analog"
        db_response = self._preferences["response_units"] == "dB"
        energies = self._preferences["xaxis_units"] == "meV"
        show_attenuation = self._preferences.get("show_attenuation", False)

        # Preview instantiation of the selected filter
        filter_class = filter_map[self._settings["filter"]]
        filter_preview = filter_class(**self._settings["attributes"])

        # Check if we are displaying trajectory power spectral attenuation alongside filter response
        if show_attenuation:
            ps, attenuated_ps = self.set_trajectory_power_spectrum(filter_preview)

        numerator, denominator = filter_preview.to_digital_coeffs() if not analog_filter else filter_preview.coeffs

        # Render the filter graph and text
        self.render_graph(filter_preview.freq_response, db_response=db_response, energies=energies, trajectory_power_spectrum=(ps, attenuated_ps) if show_attenuation else None)#, show_attenuation=show_attenuation)
        self.render_graph_text(
            filter_class.rational_polynomial_string(numerator, denominator, analog=analog_filter),
            self._settings["attributes"].get("cutoff_freq", DEFAULT_FILTER_CUTOFF),
            filter_preview.sample_freq
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
        figAgg.setMinimumSize(*self._canvas_dimensions.values())
        figAgg.setFixedSize(*self._canvas_dimensions.values())
        figAgg.updateGeometry()
        layout.addWidget(figAgg)
        self._figure_info = QTextEdit()
        self._figure_info.setFontPointSize(8)
        self._figure_info.setReadOnly(True)
        layout.addWidget(self._figure_info)
        self._figure = figure
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

    @staticmethod
    def combine_attributes(filter: Filter, attributes: dict) -> dict:
        """Update the filter attributes with missing attributes, using default values

        Parameters
        ----------
        filter: Filter
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
            {key: filter.default_settings[key]['value'] for key in missing if key in defaults.keys()}
        )
        return attributes

    def apply(self) -> None:
        """Set the field of the TrajectoryFilterWidget to the currently
        chosen setting in this widget.
        """
        self._configurator.configure(self._settings)

        filter_class = filter_map[self._settings['filter']]

        # update widget field text to reflect filter designer
        field = self._configurator.filter_description_string(
            filter_class,
            self.combine_attributes(filter_class, self._settings["attributes"])
        )
        self._field.setText(field)
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

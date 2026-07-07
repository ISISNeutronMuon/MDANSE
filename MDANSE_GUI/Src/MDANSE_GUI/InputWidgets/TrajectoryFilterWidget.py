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
import json
from collections.abc import Callable, Iterable, Iterator, Sequence
from enum import auto
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Generic,
    NamedTuple,
    SupportsFloat,
    TypedDict,
    TypeVar,
    overload,
)

import h5py
import matplotlib.pyplot as mpl
import numpy as np
import numpy.typing as npt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from more_itertools import first_true, nth, numeric_range
from qtpy.QtCore import QObject, Qt, QThread, Signal, Slot
from qtpy.QtGui import QColor, QDoubleValidator, QIntValidator
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
from MDANSE.IO.IOUtils import UCEnum, standardise_name
from MDANSE.Mathematics.Signal import (
    DEFAULT_FILTER_CUTOFF,
    DEFAULT_N_STEPS,
    DEFAULT_TIME_STEP,
    FILTER_MAP,
    Filter,
    FrequencyDomain,
    RationalPolynomial,
    filter_default_attributes,
    filter_description_string,
)
from MDANSE.MLogging import LOG
from MDANSE_GUI.InputWidgets.WidgetBase import WidgetBase
from MDANSE_GUI.PlotUtils import MDANSEMatPlotLibNavBar
from MDANSE_GUI.Utils import block_signals
from MDANSE_GUI.Widgets.StepValidator import ConstrainedSnapSpinBox

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from MDANSE.Framework.Configurators.HDFInputFileConfigurator import (
        HDFInputFileConfigurator,
    )
    from MDANSE.util_types import FloatArray

# Default maximum value for a float spinbox
DEFAULT_SPINBOX_MAX_FLOAT: Final[float] = 1000.0

# Default step size for a float spinbox
DEFAULT_SPINBOX_STEP_FLOAT: Final[float] = 0.1

# Decimal precision for a float spinbox
FLOAT_SPINBOX_DECIMALS: Final[int] = 8

T = TypeVar("T")

if TYPE_CHECKING:  # 3.10 doesn't support generic Namedtuple

    class Param(NamedTuple, Generic[T]):
        name: str
        value: T | Iterable[T]
        tooltip: str
        initial: T | None = None
        connect: Callable | None = None
        internal_name: str | None = None
        extra_args: dict[str, Any] | None = None

        @property
        def args(self):
            if self.extra_args is None:
                return {}
            return self.extra_args.copy()

    class Field(NamedTuple, Generic[T]):
        label: QLabel
        widget: T

else:

    class Param(NamedTuple):
        name: str
        value: Any | Iterable[Any]
        tooltip: str
        initial: Any | None = None
        connect: Callable | None = None
        internal_name: str | None = None
        extra_args: dict[str, Any] | None = None

        @property
        def args(self):
            if self.extra_args is None:
                return {}
            return self.extra_args.copy()

    class Field(NamedTuple):
        label: QLabel
        widget: Any


class FilterDesSettings(TypedDict):
    filter: str
    parameters: dict[str, Any]
    preferences: dict[str, Any]
    attenuation: dict[str, Any]
    attributes: dict[str, Any]


@overload
def build_widget(parent, param: Param[str | float]) -> Field[QLineEdit]: ...
@overload
def build_widget(parent, param: Param[int]) -> Field[QSpinBox]: ...
@overload
def build_widget(parent, param: Param[bool]) -> Field[QCheckBox]: ...
@overload
def build_widget(parent, param: Param[Iterable[str]]) -> Field[QComboBox]: ...
def build_widget(parent: QWidget | None, param: Param) -> Field:
    label = QLabel(param.name, parent=parent)

    match param.value:
        case bool():
            cls = QCheckBox
        case int():
            cls = QSpinBox
        case float():
            cls = ConstrainedSnapSpinBox
        case str():
            cls = QLineEdit
        case Iterable():
            cls = QComboBox
        case _:
            raise TypeError(
                f"Cannot determine widget type from {type(param.value).__name__}"
            )

    field = cls(parent=parent, **param.args)

    if isinstance(field, QComboBox):
        field.addItems(param.value)

    set_val(field, param.initial if param.initial is not None else param.value)
    label.setToolTip(param.tooltip)
    field.setToolTip(param.tooltip)

    if param.connect:
        get_changed_signal(field).connect(param.connect)

    return Field(label, field)


def get_val(widget: QWidget) -> Any:  # noqa: PLR0911
    """Get standard value from a widget.

    Parameters
    ----------
    widget : QWidget
        Widget to get value from.

    Returns
    -------
    Any
        Widget's value as appropriate type.
    """
    match widget:
        case QComboBox():
            return widget.currentText()
        case QCheckBox():
            return widget.isChecked()
        case QSpinBox():
            return widget.value()
        case QDoubleSpinBox():
            return round(widget.value(), FLOAT_SPINBOX_DECIMALS)
        case QLineEdit() if widget.text().isdigit():
            return int(widget.text())
        case QLineEdit() if all(x.isdigit() for x in widget.text().split(".", 1)):
            return float(widget.text())
        case QLineEdit():
            return widget.text()
        case WidgetBase():
            return widget.get_widget_value()


def set_val(widget: QWidget, value):
    match widget:
        case QComboBox():
            return widget.setCurrentText(str(value))
        case QCheckBox():
            return widget.setChecked(bool(value))
        case QSpinBox():
            return widget.setValue(int(value))
        case QDoubleSpinBox():
            return widget.setValue(float(value))
        case QLineEdit():
            return widget.setText(str(value))


def get_changed_signal(widget: QWidget) -> Signal:
    match widget:
        case QComboBox():
            return widget.currentTextChanged
        case QCheckBox():
            return widget.stateChanged
        case QSpinBox() | QDoubleSpinBox():
            return widget.valueChanged
        case QLineEdit():
            return widget.textChanged


def build_grid(
    *params: Param, grid_width: int = 2, connect: Callable | None = None
) -> tuple[QGridLayout, dict[str, Field]]:
    """Build a grid layout from Params."""
    grid = QGridLayout()
    fields = {}

    for i, param in enumerate(params):
        x, y = divmod(i, grid_width)
        if connect:
            param = param._replace(connect=connect)  # noqa: PLW2901
        field = build_widget(None, param)
        grid.addWidget(field.label, x, 2 * y)
        grid.addWidget(field.widget, x, 2 * y + 1)
        name = param.internal_name or param.name
        fields[name] = field

    return grid, fields


def _build_filter_settings_block(
    obj, *, grid_width: int, connect: Callable | None = None
):
    def _custom_validators(obj, filter_name: str, params: dict[str, Param]):
        current_filter = FILTER_MAP[filter_name]
        flags = current_filter.flags
        units = (
            Filter.FrequencyUnits.CYCLIC
            if Filter.Flags.DIGITAL_ONLY in flags
            else Filter.FrequencyUnits.ANGULAR
        )
        bin_width = round(
            Filter.frequency_resolution(obj.n_steps, obj.time_step, units=units),
            FLOAT_SPINBOX_DECIMALS,
        )
        vmax = round(
            Filter.nyquist(obj.time_step, units=units) - bin_width,
            FLOAT_SPINBOX_DECIMALS,
        )

        for name in ("cutoff_freq", "fundamental_freq"):
            if param := params.get(name):
                if Filter.Flags.FUNDAMENTAL_EVENLY_DIVIDES_FS in flags:

                    def valid_func(x):
                        return ((1 / obj.time_step) % x) == 0
                else:
                    valid_func = None

                init = 1 / obj.time_step * obj.n_steps
                if units is Filter.FrequencyUnits.ANGULAR:
                    init *= Filter._cyclic_to_angular

                params[name] = param._replace(
                    initial=init,
                    extra_args={
                        "step": bin_width,
                        "constraint": valid_func,
                        "minmax": (bin_width, vmax),
                        "decimal": FLOAT_SPINBOX_DECIMALS,
                        "suffix": f" {units.value}",
                    },
                )

        if param := params.get("bound_freq"):
            init = 1 / obj.time_step * obj.n_steps
            if units is Filter.FrequencyUnits.ANGULAR:
                init *= Filter._cyclic_to_angular

            params["bound_freq"] = param._replace(
                extra_args={
                    "step": bin_width,
                    "minmax": (bin_width, vmax),
                    "decimal": FLOAT_SPINBOX_DECIMALS,
                    "suffix": f" {units.value}",
                },
            )

    settings_box = QGroupBox("Settings", obj._base)
    obj._settings_layout = QStackedLayout()
    settings_box.setLayout(obj._settings_layout)
    obj.parameter_fields: dict[str, dict[str, Field]] = {}

    for filter_name, current_filter in FILTER_MAP.items():
        params: dict[str, Param] = {}

        for name, props in current_filter.default_settings.items():
            tooltip = props.get("description", "")
            match props:
                case {"value": False | True as value}:
                    initial = None
                case {"values": value, "value": selection}:
                    initial = selection
                case {"value": value}:
                    initial = None
                case _:
                    raise KeyError(
                        f"Bad dict in {type(current_filter).__name__}.default_settings"
                    )

            params[name] = Param(
                standardise_name(name),
                value,
                tooltip,
                initial,
                internal_name=name,
            )

        if "attenuation_type" in current_filter.default_settings:
            params["bound_freq"] = Param(
                "Bound frequency",
                current_filter.default_settings["cutoff_freq"]["value"],
                tooltip,
                initial=current_filter.default_settings["cutoff_freq"]["value"],
                internal_name="bound_freq",
            )

        _custom_validators(obj, filter_name, params)

        widget = QWidget()
        layout, obj.parameter_fields[filter_name] = build_grid(
            *params.values(),
            grid_width=grid_width,
            connect=connect,
        )

        widget.setLayout(layout)

        obj._settings_layout.addWidget(widget)

    obj._settings_layout.setCurrentIndex(0)
    return settings_box


def read_pps_from_file(
    filename: str | Path,
) -> tuple[FloatArray, FloatArray] | tuple[None, None]:
    """Reads a trajectory position power spectrum from an .mda filename,
    returning the power spectrum as a dataset consisting of the energies (meV)
    and the corresponding spectrum.

    Parameters
    ----------
    filename: str | Path
        Name of the external .mda filename containing the position power spectrum

    Returns
    -------
    tuple[FloatArray, FloatArray] | tuple[None, None]
        Energy axis and corresponding trajectory power spectrum

    """
    try:
        with h5py.File(filename) as source:
            energy_axis = source["pps/axes/romega"][:]
            data_array = source["/pps/isotropic/total"][:]
    except KeyError:
        LOG.error("PPS data could not be found in file %s", filename)
    except Exception:
        LOG.error(
            "Path %s could not be opened for reading a Position Power Spectrum",
            filename,
        )
    else:
        return energy_axis, data_array
    return None, None


def gaussian(x: FloatArray, mu: float, sigma: float) -> float:
    """Returns a centered Gaussian, paramterised by values mu and sigma, over
    a given input domain x.

    Parameters
    ----------
    x : FloatArray
        Domain values (x-axis) over which the Gaussian function will be computed
    mu : float
        Parameter mu of the Gaussian
    sigma : float
        Parameter sigma of the Gaussian

    """
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (2 * np.pi)


def double_gaussian(x: FloatArray, mu: float, sigma: float) -> float:
    """Returns a double Gaussian, paramterised by values mu and sigma, over
    a given input domain x.

    The Gaussian curves are centered symmetrically one quarter of the length
    of x, either side of the midpoint.

    Parameters
    ----------
    x : FloatArray
        Domain values (x-axis) over which the Gaussian function will be computed
    mu : float
        Parameter mu of the Gaussian
    sigma : float
        Parameter sigma of the Gaussian

    """
    return gaussian(x, 0.5 * mu, sigma) + gaussian(x, 1.5 * mu, sigma)


class AttenuationFunction(UCEnum):
    GAUSSIAN = auto()
    DOUBLE_GAUSSIAN = auto()
    EXTERNAL_FILE = auto()


class FilterDesigner(QDialog):
    """Graphical interface for the trajectory filter.

    Generates a JSON string that specifies the designed filter.

    Attributes
    ----------
    _helper_title : str
        Title of the helper dialog window.
    _canvas_dimensions : dict
        Dimensions of the filter graph canvas.
    _trajectory_power_spectrum :  Sequence[FloatArray] | None
        Trajectory power spectrum as a tuple containing the x-axis values (frequency domain) and the y-axis values (magnitudes).

    """

    _helper_title = "Filter designer"
    _canvas_dimensions = {"width": 700, "height": 500}

    def __init__(
        self,
        parent_widget: TrajectoryFilterWidget,
        configurator: TrajectoryFilterConfigurator,
        parent,
        *args,
        **kwargs,
    ):
        super().__init__(parent, *args, **kwargs)
        self.setWindowTitle(self._helper_title)
        self.parent_widget = parent_widget
        self.configurator = configurator

        self.parent_widget._pps_file_widget.value_changed.connect(
            self.render_canvas_assets
        )
        self.parent_widget._type_combo.currentTextChanged.connect(self.update_filter)
        self.graph_ready = False

        self.layouts = QHBoxLayout()
        self.create_designer()

        self.update_filter(self.parent_widget._type_combo.currentText())

    def create_settings_layout(self, widget_area: QVBoxLayout) -> None:
        """Create the filter settings vertical layout.

        Parameters
        ----------
        widget_area : QVBoxLayout
            Vertical box layout containing the filter type combobox, settings grid, and push buttons.

        """
        # Add filter type combobox
        self.type_cbox = QComboBox()
        self.type_cbox.addItems(FILTER_MAP)
        self.type_cbox.setCurrentText(self.configurator._default_filter.__name__)
        self.type_cbox.currentTextChanged.connect(self.update_filter)

        type_label = QLabel("Filter type")

        filter_type_layout = QHBoxLayout()
        filter_type_layout.addWidget(type_label)
        filter_type_layout.addWidget(self.type_cbox)

        widget_area.addLayout(filter_type_layout)

        self.parameter_fields: dict[str, dict[str, Field]]
        self._settings_layout: QStackedLayout
        self.settings_box = self._build_filter_settings_block()

        # Set current index for settings stack layout
        index = list(FILTER_MAP).index(self.type_cbox.currentText())
        self._settings_layout.setCurrentIndex(index)

        widget_area.addWidget(self.settings_box)

        # Add the filter designer preferences stack layout

        preferences_groupbox = self._build_preferences_group()
        widget_area.addWidget(preferences_groupbox)

        # Add the filter designer attenuation stack layout

        attenuation_groupbox = self._build_attenuation_panel()
        widget_area.addWidget(attenuation_groupbox)

        # Set filter designer graph ready
        self.graph_ready = True

        # Render graph
        self.render_canvas_assets()

        # Add buttons
        buttons_layout = QHBoxLayout()
        for button in self.create_buttons():
            buttons_layout.addWidget(button)

        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        widget_area.addLayout(buttons_layout)

    def _build_filter_settings_block(self) -> QGroupBox:
        return _build_filter_settings_block(
            self, grid_width=1, connect=self.render_canvas_assets
        )

    @property
    def _base(self) -> QDialog:
        return self

    @property
    def time_step(self) -> float:
        return self.parent_widget.time_step

    @property
    def n_steps(self) -> int:
        return self.parent_widget.n_steps

    def _build_attenuation_panel(self):
        # Attenuation form
        attenuation_groupbox = QGroupBox("Attenuation")
        attenuation_groupbox.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )

        attenuation = Param(
            "Form",
            ("Gaussian", "Double Gaussian", "External file"),
            "Select form of attenuated function, either an analytic functional form or a spectrum from an existing .mda file",
            internal_name="form",
        )
        show = Param(
            "Show",
            False,
            "Display trajectory power spectrum for comparison",
            internal_name="show",
        )
        self.attenuation_grid, self.attenuation_fields = build_grid(
            attenuation, show, grid_width=1, connect=self.render_canvas_assets
        )

        attenuation_groupbox.setLayout(self.attenuation_grid)

        return attenuation_groupbox

    def _build_preferences_group(self):
        preferences_groupbox = QGroupBox("Preferences")
        preferences_groupbox.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )

        self.preferences_grid, self.preferences_fields = build_grid(
            Param(
                "Response units",
                ("amplitude", "dB"),
                "View y-axis in amplitude or decibels",
                internal_name="response_units",
            ),
            Param(
                "X-axis units",
                ("frequency", "meV"),
                "View x-axis as frequency or energy (meV)",
                internal_name="xaxis_units",
            ),
            Param(
                "Filter coefficients",
                ("analog", "digital"),
                "View filter transfer function in terms of analogue (S-domain/continuous time) or digital (Z-domain/discrete time) coefficients",
                internal_name="filter_coefficients",
            ),
            connect=self.render_canvas_assets,
            grid_width=1,
        )
        preferences_groupbox.setLayout(self.preferences_grid)

        return preferences_groupbox

    def find_configuration(self) -> dict[str, str]:
        """Find the configuration of the main filter job.

        Returns
        -------
        dict[str, str]
            All configuration parameters of TrajectoryFilter

        """
        return {
            k: v._original_input
            for k, v in self.configurator.configurable._configuration.items()
            if k in PositionPowerSpectrum.settings
        }

    @property
    def current_filter(self) -> type[Filter]:
        return FILTER_MAP[self.type_cbox.currentText()]

    def current_filter_units(self) -> Filter.FrequencyUnits:
        """Find the frequency unit enum based on the current filter.

        Returns
        -------
        FrequencyUnits
            Enum current filter frequency units.

        """
        return (
            Filter.FrequencyUnits.CYCLIC
            if Filter.Flags.DIGITAL_ONLY in self.current_filter.flags
            else Filter.FrequencyUnits.ANGULAR
        )

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
        # Set current index for settings stack layout
        set_val(self.type_cbox, filter_type)
        index = list(FILTER_MAP).index(filter_type)
        self._settings_layout.setCurrentIndex(index)

        # Re-render filter graph
        self.render_canvas_assets()

    @property
    def settings(self) -> FilterDesSettings:
        filter = get_val(self.type_cbox)
        return {
            "filter": filter,
            "parameters": {
                name: get_val(field.widget)
                for name, field in self.parameter_fields[filter].items()
            },
            "attenuation": {
                name: get_val(field.widget)
                for name, field in self.attenuation_fields.items()
            },
            "preferences": {
                name: get_val(field.widget)
                for name, field in self.preferences_fields.items()
            },
            "attributes": {
                # Number of simulation steps
                "n_steps": self.n_steps,
                # Simulation time step in picoseconds
                "time_step_ps": self.time_step,
            },
        }

    def resample_and_normalise(self, values: FloatArray, to_len: int):
        """Resample the input signal values to a given length, with normalisation of output signal.

        Parameters
        ----------
        values : FloatArray
            Values of the signal.
        to_len : int
            New length of the signal after resampling.

        Returns
        -------
        FloatArray
            Resampled and normalised signal.

        """
        return signal.resample(values, to_len) / values.max()

    def get_attenuation_function(
        self, tr_filter: Filter, source: str
    ) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
        """Put curves on the same scale for the plot.

        Generate an attenuation function to display alongside the filter frequency response,
        returning the frequency values of the attenuation function, as well as its magnitudes
        and magnitudes after attenuation.

        Parameters
        ----------
        tr_filter : Filter
            Filter class for the designed filter.
        source : str
            String name of the attenuation function to display.

        Returns
        -------
        raw_power_spectrum_freqs : FloatArray
            Frequency axis of the original PPS result.
        power_spectrum : FloatArray
            Trajectory power spectrum.
        attenuated_power_spectrum : FloatArray
            Attenuated power spectrum due to the designed filter response.
        normalised_response : FloatArray
            Normalised response.
        """
        freqs = tr_filter.freq_response.frequencies

        match AttenuationFunction(source):
            case AttenuationFunction.GAUSSIAN:
                values = gaussian(freqs, freqs.max() / 2, freqs.max() / 4)
            case AttenuationFunction.DOUBLE_GAUSSIAN:
                values = double_gaussian(freqs, freqs.max() / 2, freqs.max() / 8)
            case AttenuationFunction.EXTERNAL_FILE:
                (
                    raw_freqs,
                    power_spectrum,
                    attenuated_power_spectrum,
                    normalised_response,
                ) = self.get_attenuation_power_spectrum(
                    tr_filter, get_val(self.parent_widget._pps_file_widget)
                )
                return (
                    raw_freqs,
                    power_spectrum,
                    attenuated_power_spectrum,
                    normalised_response,
                )
            case _:
                raise ValueError("Unknown attenuation functional form")

        normalised = values / np.max(values)

        return (
            freqs,
            normalised,
            freqs,
            normalised * tr_filter.freq_response.magnitudes,
        )

    def get_attenuation_power_spectrum(
        self,
        tr_filter: Filter,
        pps_filename: str,
    ) -> tuple[FloatArray, FloatArray, FloatArray, FloatArray]:
        """Put curves on the same scale for the plot.

        Generate an appropriately resampled power spectrum for the input trajectory,
        as well as the multiplicative attenuation effect of the designed filter.

        Parameters
        ----------
        tr_filter : Filter
            Filter class for the designed filter.
        pps_filename : str | None
            File name from which the reference spectrum will be loaded, optional.

        Returns
        -------
        raw_power_spectrum_freqs : FloatArray
            Frequency axis of the original PPS result.
        power_spectrum : FloatArray
            Trajectory power spectrum.
        attenuated_power_spectrum : FloatArray
            Attenuated power spectrum due to the designed filter response.
        normalised_response : FloatArray
            Normalised response.
        """
        freqs, _ = tr_filter.freq_response

        file_freqs, file_values = read_pps_from_file(pps_filename)

        file_freqs = freqs if file_freqs is None else file_freqs / (2 * np.pi)

        if file_values is None:
            file_values = np.ones_like(freqs)

        # Resample trajectory power spectrum energies (x-axis) and convert to frequency domain, setting
        # custom frequency range on filter object

        overlap_mask = (file_freqs >= freqs.min()) & (file_freqs <= freqs.max())
        att_freqs = file_freqs[overlap_mask]

        # Normalise trajectory power spectrum (y-axis)
        normalised = file_values / np.max(file_values)

        attenuation = interp1d(
            tr_filter.freq_response.frequencies,
            tr_filter.freq_response.magnitudes,
            fill_value=0.0,
            bounds_error=False,
        )

        return (
            file_freqs,
            normalised,
            att_freqs,
            normalised[overlap_mask] * abs(attenuation(att_freqs)) ** 4,
        )

    @staticmethod
    def to_dB(
        x: float | FloatArray,
    ) -> np.floating | FloatArray:
        """Value on decibel (dB) scale.

        Parameters
        ----------
        x : float or ~FloatArray
            Value to convert.

        Returns
        -------
        float-like or ~FloatArray
            Value as dB.

        Examples
        --------
        >>> self.to_dB(100)
        np.float64(40.0)
        >>> conv(-10)
        np.float64(20.0)
        """
        return 20 * np.log10(abs(x))

    @staticmethod
    def raw(x: T) -> T:
        """NOP for standard values.

        Parameters
        ----------
        x : float or ~FloatArray
            Value to convert.

        Returns
        -------
        float or ~FloatArray
            Original value.
        """
        return x

    def render_graph(
        self,
        freqs: FrequencyDomain,
        *,
        db_response: bool = False,
        energies: bool = False,
        trajectory_power_spectrum: Sequence[FloatArray] | None = None,
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
        trajectory_power_spectrum : Sequence[FloatArray]
            Tuple containing trajectory power spectrum and attenuation due to filter.

        """
        self._figure.clear()

        conv = self.to_dB if db_response else self.raw

        axes = self._figure.add_axes(rect=(0.1, 0.1, 0.8, 0.8))
        axes.plot(
            freqs.frequencies,
            conv(abs(freqs.magnitudes) ** 4),
            label="Filter response",
        )

        # Conditionally display trajectory power spectral attenuation
        if trajectory_power_spectrum:
            psx, ps, apsx, attenuated_ps = trajectory_power_spectrum
            axes.plot(
                psx,
                conv(ps),
                label="Trajectory response",
                color="grey",
            )
            axes.plot(
                apsx,
                20 * np.log10(attenuated_ps) if db_response else attenuated_ps,
                label="Attenuation",
                color="black",
            )

        # Conditionally convert frequencies to energies (meV)
        if energies:
            energy_ticks = np.floor(
                Filter.freq_to_energy(axes.get_xticks(), self.current_filter_units()),
            ).astype(int)
            axes.set_xticks(axes.get_xticks(), labels=energy_ticks)

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
        polynomial: RationalPolynomial,
        cutoff: float,
        sample_freq: float,
    ) -> None:
        """Render the text containing the filter transfer function polynomial, cutoff energy, and simulation sample frequency.

        Parameters
        ----------
        polynomial : RationalPolynomial
            Representation of the filter transfer function as a polynomial.
        cutoff : float
            Cutoff frequency of the designed filter.
        sample_freq : float
            Sample frequency of the molecular dynamics simulation in THz (terahertz).
        """
        self._figure_info.clear()

        if (
            self.settings["filter"] not in {"Notch", "Peak", "Comb"}
            and self.settings["attributes"].get("order", 1) < 6
        ):
            self._figure_info.append(f"           {polynomial.numerator}")
            self._figure_info.append(
                f"H({polynomial.unit})=    {'-' * len(polynomial.denominator)}"
            )
            self._figure_info.append(f"           {polynomial.denominator}")
        else:
            self._figure_info.append(
                "Number of filter coefficients exceeds available display area",
            )
            self._figure_info.append(" ")
            self._figure_info.append(" ")

        self._figure_info.append(
            f"Cutoff energy: {np.round(Filter.freq_to_energy(cutoff, self.current_filter_units()), FLOAT_SPINBOX_DECIMALS)} meV, Sample frequency: {sample_freq} THz",
        )

    def render_canvas_assets(self, attributes: dict[str, Any] | None = None) -> None:
        """Render all elements of the filter designer graphing area, including data text.

        Parameters
        ----------
        attributes: dict | None
            Filter attributes dictionary.

        """
        if not self.graph_ready:
            return

        settings = self.settings

        filter = settings["filter"]
        parameters = settings["parameters"]
        preferences = settings["preferences"]
        attenuation = settings["attenuation"]

        self.synchronise_freqs(filter, parameters)

        if isinstance(attributes, dict):
            attributes = settings["attributes"] | attributes
        else:
            attributes = settings["attributes"]

        # Set preferences
        analog_filter = preferences["filter_coefficients"] == "analog"
        db_response = preferences["response_units"] == "dB"
        energies = preferences["xaxis_units"] == "meV"

        # Set attenuation
        source = attenuation.get("form", "Gaussian")
        show_attenuation = attenuation.get("show", False)

        # Preview instantiation of the selected filter
        filter_class = FILTER_MAP[filter]
        try:
            filter_preview = filter_class(**parameters, **attributes)
        except Exception as exc:
            self.mark_error(str(exc))
            LOG.error("%s", exc)
            return
        self.clear_error()

        # Get comparative attenuation from either an external trajectory PPS, or from an analytical functional form
        ps, attenuated_ps = None, None

        if show_attenuation:
            ps_axis, ps, attenuated_ps_axis, attenuated_ps = (
                self.get_attenuation_function(filter_preview, source)
            )

        # Get filter coefficients
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
            trajectory_power_spectrum=(ps_axis, ps, attenuated_ps_axis, attenuated_ps)
            if ps is not None and attenuated_ps is not None
            else None,
        )
        self.render_graph_text(
            filter_class.rational_polynomial(
                numerator,
                denominator,
                analog=analog_filter,
            ),
            attributes.get(
                "cutoff_freq",
                attributes.get("fundamental_freq", DEFAULT_FILTER_CUTOFF),
            ),
            filter_preview.sample_freq,
        )

    def synchronise_freqs(self, filter: str, parameters: dict[str, Any]) -> None:
        if "attenuation_type" not in parameters:
            return

        bound_freq_widget: ConstrainedSnapSpinBox = self.parameter_fields[filter][
            "bound_freq"
        ].widget
        cutoff_freq_widget: ConstrainedSnapSpinBox = self.parameter_fields[filter][
            "cutoff_freq"
        ].widget
        bound_freq_widget.setMinimum(
            get_val(cutoff_freq_widget) + cutoff_freq_widget.singleStep()
        )

        if parameters["attenuation_type"] in {"highpass", "lowpass"}:
            bound_freq_widget.setEnabled(False)
        else:
            bound_freq_widget.setEnabled(True)
            parameters["cutoff_freq"] = (
                get_val(cutoff_freq_widget),
                get_val(bound_freq_widget),
            )

    def create_graph_canvas(
        self,
        fig_width: float = 10.0,
        fig_height: float = 10.0,
        dpi: int = 100,
    ) -> QWidget:
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
        toolbar = MDANSEMatPlotLibNavBar(figAgg, canvas)
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

    def mark_error(self, error_text: str, *, silent: bool = False):
        """Highlight an erroneous entry and display given error_text.

        Parameters
        ----------
        error_text : str
            Message displayed on hover-over.
        silent : bool
            If True, update the widget's error without sending signals

        """
        font = self.settings_box.font()
        font.setBold(True)
        self.settings_box.setStyleSheet("QGroupBox {background-color: rgb(180,20,180)}")
        self.settings_box.setFont(font)
        self.settings_box.setToolTip(error_text)

    def clear_error(self):
        """Remove error highlighting."""

        font = self.settings_box.font()
        font.setBold(False)
        self.settings_box.setStyleSheet("")
        self.settings_box.setFont(font)
        self.settings_box.setToolTip("")

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

    def apply(self) -> None:
        """Pass the filter parameters to the main widget."""
        self.parent_widget.set_widget_values(
            filter=self.settings["filter"], **self.settings["parameters"]
        )
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

        apply.setAutoDefault(False)
        apply.setDefault(False)

        apply.clicked.connect(self.apply)
        return [apply]

    def closeEvent(self, a0):
        self.apply()
        return super().closeEvent(a0)


class TrajectoryFilterWidget(WidgetBase):
    """Trajectory filter designer widget."""

    _push_button_text = "Filter designer"
    _default_value = TrajectoryFilterConfigurator.get_default()
    _tooltip_text = "Design a trajectory filter. The input is a JSON string, and filter setting can be edited using the filter designer."

    def __init__(self, *args, configurator: TrajectoryFilterConfigurator, **kwargs):
        kwargs["layout_type"] = "QGridLayout"
        super().__init__(*args, configurator=configurator, **kwargs)

        self._type_label = QLabel("Filter type", self._base)
        self._type_combo = QComboBox(parent=self._base)
        self._type_combo.addItems(FILTER_MAP.keys())
        self._type_combo.currentTextChanged.connect(self.filter_changed)

        self._pps_file_widget = self.get_dep("pps_input_file")
        self._frames_widget = self.get_dep("frames")

        self.parameter_fields: dict[str, dict[str, Field]]
        self._settings_layout: QStackedLayout
        self._settings_box = self._build_filter_settings_block()
        self.filter_designer = None
        helper_button = QPushButton(self._push_button_text, self._base)
        helper_button.clicked.connect(self.helper_dialog)

        self._layout.addWidget(self._type_label, 0, 0)
        self._layout.addWidget(self._type_combo, 0, 1)
        self._layout.addWidget(helper_button, 0, 2)
        self._layout.addWidget(self._settings_box, 1, 0, 1, 3)

        self.synchronise_freqs()
        self.update_labels()
        self.updateValue()

    @property
    def time_step(self) -> float:
        return self._frames_widget._configurator["time_step"]

    @property
    def n_steps(self) -> int:
        return self._frames_widget._configurator["number"]

    def _build_filter_settings_block(self) -> QGroupBox:
        box = _build_filter_settings_block(
            self, grid_width=3, connect=self.synchronise_freqs
        )
        for filter_settings in self.parameter_fields.values():
            for _, widget in filter_settings.values():
                get_changed_signal(widget).connect(self.updateValue)
        return box

    @property
    def current_filter_name(self) -> str:
        return self._type_combo.currentText()

    @property
    def filter_index(self) -> int:
        return list(FILTER_MAP).index(self.current_filter_name)

    @property
    def current_fields(self) -> dict[str, Field]:
        return self.parameter_fields[self.current_filter_name]

    @property
    def current_filter(self) -> type[Filter]:
        return FILTER_MAP[self._type_combo.currentText()]

    @current_filter.setter
    def current_filter(self, value: str):
        self._type_combo.setCurrentText(value)

    @property
    def settings(self) -> dict[str, Any]:
        return {
            "filter": get_val(self._type_combo),
            "attributes": self.attributes,
        }

    @property
    def attributes(self) -> dict[str, Any]:
        return {
            name: get_val(field) for name, (_, field) in self.current_fields.items()
        }

    def synchronise_freqs(self) -> None:
        if "attenuation_type" not in self.attributes:
            return

        bound_freq_widget: ConstrainedSnapSpinBox = self.current_fields[
            "bound_freq"
        ].widget
        cutoff_freq_widget: ConstrainedSnapSpinBox = self.current_fields[
            "cutoff_freq"
        ].widget
        bound_freq_widget.setMinimum(
            get_val(cutoff_freq_widget) + cutoff_freq_widget.singleStep()
        )
        if self.attributes["attenuation_type"] in {"highpass", "lowpass"}:
            bound_freq_widget.setEnabled(False)
        else:
            bound_freq_widget.setEnabled(True)
            self.attributes["cutoff_freq"] = (
                get_val(cutoff_freq_widget),
                get_val(bound_freq_widget),
            )

    def filter_changed(self, new_filter: str):
        self.update_filter_entries({"filter": new_filter})

    def update_filter_entries(self, parameters: dict[str, Any] | None = None):
        if parameters is None:
            parameters = {}

        if new_filter := parameters.pop("filter", None):
            with block_signals(self):
                self.current_filter = new_filter

        self._settings_layout.setCurrentIndex(self.filter_index)
        self.synchronise_freqs()
        self.updateValue()

    def create_helper(self) -> FilterDesigner:
        """
        Returns
        -------
        FilterDesigner
            Create and return the filter designer QDialog.

        """
        return FilterDesigner(self, self._configurator, self._base)

    @Slot()
    def helper_dialog(self) -> None:
        """Open the helper dialog."""
        if self.filter_designer is None:
            self.filter_designer = self.create_helper()

            if self._pps_file_widget:
                self._pps_file_widget.value_changed.connect(
                    self.filter_designer.render_canvas_assets
                )

        if self.filter_designer.isVisible():
            self.filter_designer.close()
        else:
            self.filter_designer.show()

    def set_from_configurator(self):
        data = self._configurator.configurable["value"]
        if isinstance(data, str):
            data = json.loads(data)
        self.update_filter_entries(data)

    def set_widget_values(self, **value) -> None:
        if "filter" in value:
            set_val(self._type_combo, value["filter"])
        for key in self.current_fields.keys() & value.keys():
            set_val(self.current_fields[key].widget, value[key])

    def get_widget_value(self) -> str:
        """
        Returns
        -------
        str
            The JSON selector setting.

        """
        settings = self.settings
        if "attenuation_type" not in settings["attributes"]:
            pass
        elif settings["attributes"]["attenuation_type"] not in {"bandpass", "bandstop"}:
            settings["attributes"].pop("bound_freq")
        else:
            settings["attributes"]["cutoff_freq"] = (
                settings["attributes"]["cutoff_freq"],
                settings["attributes"].pop("bound_freq"),
            )

        return json.dumps(settings)

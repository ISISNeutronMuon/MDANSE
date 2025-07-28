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
import enum
from typing import TYPE_CHECKING, Any

import numpy as np

from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class NormOperations(enum.Enum):
    """Enum for selecting mathematical operations when calculating norms."""

    AVERAGE = enum.auto()
    SUM = enum.auto()
    NOT_IMPLEMENTED = enum.auto()


def str_to_enum(operation: str) -> NormOperations:
    """Get the right enum from the input text string.

    Parameters
    ----------
    operation : str
        name of the mathematical operation as string.

    Returns
    -------
    NormOperations
        enum value of the operation.

    """
    if operation == "average":
        return NormOperations.AVERAGE
    if operation == "sum":
        return NormOperations.SUM
    return NormOperations.NOT_IMPLEMENTED


def enum_to_str(operation: NormOperations) -> str:
    """Convert the enum to a text string for the GUI.

    Parameters
    ----------
    operation : NormOperations
        Enum of the mathematical operation

    Returns
    -------
    str
        name of the operation as string

    """
    if operation == NormOperations.AVERAGE:
        return "average"
    if NormOperations.SUM:
        return "sum"
    return "not implemented"


NORMALISATION_DEFAULTS = {
    "apply": False,
    "min_index": 0,
    "max_index": 1,
    "operation": NormOperations.AVERAGE,
}


class Plotter(metaclass=SubclassFactory):
    """Parent class to all classes used for displaying data."""

    def __init__(self) -> None:
        """Create defaults common to all plotters."""
        self._figure = None
        self._axes = []
        self._initial_values = [0.0, 0.0]
        self._slider_values = [0.0, 0.0]
        self._number_of_sliders = 2
        self._value_reset_needed = True
        self._toolbar = None
        self._slider_reference = None
        self.curve_length_limit = 10
        self._normalisation_values = copy.copy(NORMALISATION_DEFAULTS)
        self._normalisation_errors = []

    def request_slider_values(self):
        """Manually read values from sliders, if they are present."""
        if self._slider_reference is None:
            return
        self._slider_reference.collect_values()

    def clear(self, figure: Figure = None):
        """Clear the figure, usually before plotting again.

        Parameters
        ----------
        figure : Figure, optional
            Figure to be cleared. If None, clear the internally stored figure.
            By default None

        """
        target = self._figure if figure is None else figure
        if target is None:
            return
        target.clear()

    def slider_labels(self) -> list[str]:
        """Get text to be shown next to sliders."""
        return ["Slider 1", "Slider 2"]

    def slider_limits(self) -> list[str]:
        """Get default limit values for sliders."""
        return self._number_of_sliders * [[-1.0, 1.0, 0.01]]

    def sliders_coupled(self) -> bool:
        """Check if the slider values depend on each other."""
        return False

    def get_figure(self, figure: Figure = None):
        """Get the reference to the current figure, if present."""
        target = self._figure if figure is None else figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return None
        target.clear()
        return target

    def apply_settings(self, plotting_context: PlottingContext):
        """Check that the plotting context can be used."""
        if plotting_context.set_axes() is None:
            LOG.debug("Axis check failed.")
            return

    def enable_slider(self, *, allow_slider: bool = True):
        """Enable or disable sliders.

        Parameters
        ----------
        allow_slider : bool, optional
            It True, sliders will become active, by default True

        """
        self._slider_reference.setEnabled(allow_slider)
        self._slider_reference.blockSignals(not allow_slider)

    def handle_slider(self, new_value: list[float]):
        """Respond to new slider values."""
        self._slider_values = new_value

    def normalise_curve(
        self, xdata: np.ndarray, ydata: np.ndarray
    ) -> tuple[np.ndarray]:
        """Scale a 1D curve according to the current normalisation parameters.

        Parameters
        ----------
        xdata : np.ndarray
            1D array of x values of the curve
        ydata : np.ndarray
            1D array of y values of the curve

        Returns
        -------
        tuple[np.ndarray]
            xdata and ydata with scaling applied

        """
        apply = self._normalisation_values["apply"]
        operation = self._normalisation_values["operation"]
        if not apply or operation == NormOperations.NOT_IMPLEMENTED:
            return xdata, ydata
        min_index = self._normalisation_values["min_index"]
        max_index = self._normalisation_values["max_index"]
        ref_values = ydata[min_index:max_index]
        if len(ref_values) < 1:
            self._normalisation_errors.append(
                "No points within the specified index range"
            )
            return xdata, ydata
        if operation == NormOperations.AVERAGE:
            scale_factor = np.mean(ref_values)
        elif operation == NormOperations.SUM:
            scale_factor = np.sum(ref_values)
        if np.isclose(scale_factor, 0.0):
            self._normalisation_errors.append(
                "Normalisation factor is 0 and will not be applied."
            )
            return xdata, ydata
        return xdata, ydata / scale_factor

    def normalise_array(self, data_array: np.ndarray) -> np.ndarray:
        """Normalise a 2D array according to the current normalisation parameters.

        Parameters
        ----------
        data_array : np.ndarray
            2D array of data for plotting

        Returns
        -------
        np.ndarray
            the data_array with new relative intensities between rows

        """
        apply = self._normalisation_values["apply"]
        operation = self._normalisation_values["operation"]
        if not apply or operation == NormOperations.NOT_IMPLEMENTED:
            return data_array
        min_index = self._normalisation_values["min_index"]
        max_index = self._normalisation_values["max_index"]
        ref_column = data_array[:, min_index:max_index]
        if ref_column.shape[1] < 1:
            return data_array
        if operation == NormOperations.AVERAGE:
            scale_column = np.mean(ref_column, axis=1)
        elif operation == NormOperations.SUM:
            scale_column = np.sum(ref_column, axis=1)
        if np.any(np.isclose(scale_column, 0.0)):
            self._normalisation_errors.append(
                "Normalisation factor is 0 for some rows of the 2D array."
            )
            return data_array
        return data_array / scale_column.reshape((len(scale_column), 1))

    def change_normalisation(self, new_value: dict[str, Any]):
        """Respond to new normalisation values."""
        self._normalisation_errors = []
        self._normalisation_values = new_value

    def plot(
        self,
        plotting_context: PlottingContext,
        figure: Figure = None,
        update_only=False,
        toolbar=None,
    ):
        """Plot the selected data in the figure.

        Parameters
        ----------
        plotting_context : PlottingContext
            Data model storing the data to be plotted
        figure : Figure, optional
            Matplotlib figure instance for plotting, by default None
        update_only : bool, optional
            If true, try to re-use zoom settings, by default False
        toolbar : _type_, optional
            GUI instance of the matplotlib toolbar, by default None

        """
        LOG.info(f"normalisation errors {self._normalisation_errors}, setting to []")
        self._normalisation_errors = []
        target = self.get_figure(figure)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        axes = target.add_subplot(111)
        self._axes = [axes]
        self.apply_settings(plotting_context)

    def plot_blank(self, *, draw_cross: bool = True):
        """Inform the user that no data could be plotted.

        Parameters
        ----------
        draw_cross : bool, optional
            If True, plot two intersecting lines to indicate visually that plotting was not possible, by default True
        """
        figure = self.get_figure()
        axes = figure.add_subplot(111)
        if draw_cross:
            axes.axline([0, 0], [1, 1], color="k", linestyle="-")
            axes.axline([0, 1], [1, 0], color="k", linestyle="-")
        axes.set_title("The data sets you selected could not be plotted.")
        axes.set_xlabel(
            "If you expected a plot, please check the settings you changed last."
        )
        figure.canvas.draw()

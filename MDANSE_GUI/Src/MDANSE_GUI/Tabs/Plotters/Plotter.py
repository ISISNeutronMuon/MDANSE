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
from typing import TYPE_CHECKING

from MDANSE.Core.SubclassFactory import SubclassFactory
from MDANSE.MLogging import LOG

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Plotter(metaclass=SubclassFactory):
    """Parent class to all classes used for displaying data."""

    def __init__(self) -> None:
        self._figure = None
        self._axes = []
        self._initial_values = [0.0, 0.0]
        self._slider_values = [0.0, 0.0]
        self._number_of_sliders = 2
        self._value_reset_needed = True
        self._toolbar = None
        self._slider_reference = None

    def request_slider_values(self):
        """Manually read values from sliders, if they are present."""
        if self._slider_reference is None:
            return
        self._slider_reference.collect_values()

    def clear(self, figure: "Figure" = None):
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

    def get_figure(self, figure: "Figure" = None):
        """Get the reference to the current figure, if present."""
        target = self._figure if figure is None else figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return None
        target.clear()
        return target

    def apply_settings(self, plotting_context: "PlottingContext"):
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

    def plot(
        self,
        plotting_context: "PlottingContext",
        figure: "Figure" = None,
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
        target = self.get_figure(figure)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        axes = target.add_subplot(111)
        self._axes = [axes]
        self.apply_settings(plotting_context)

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
from typing import TYPE_CHECKING, List

import numpy as np

from MDANSE.Framework.Units import measure
from MDANSE.MLogging import LOG

from MDANSE_GUI.Tabs.Plotters.Plotter import Plotter

if TYPE_CHECKING:
    from qtpy.QtWidgets import QTextBrowser
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext


class Text(Plotter):

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._current_colours = []
        self._active_curves = []
        self._backup_curves = []
        self._backup_limits = []
        self._curve_limit_per_dataset = 12
        self.height_max, self.length_max = 0.0, 0.0

    def clear(self, figure: "QTextBrowser" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()

    def get_figure(self, figure: "QTextBrowser" = None):
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        return target

    def plot(
        self,
        plotting_context: "PlottingContext",
        figure: "QTextBrowser" = None,
        colours=None,
        update_only=False,
        toolbar=None,
    ):
        target = self.get_figure(figure)
        if target is None:
            return
        if toolbar is not None:
            self._toolbar = toolbar
        self._figure = target
        xaxis_unit = None
        self._active_curves = []
        self._backup_curves = []
        self.apply_settings(plotting_context, colours)
        self.height_max, self.length_max = 0.0, 0.0
        if plotting_context.set_axes() is None:
            LOG.error("Axis check failed.")
            return
        if len(plotting_context.datasets()) == 0:
            target.clear()
        new_header = "# MDANSE Data \n"
        new_text = ""
        top_line = []
        left_column = [""]
        all_fields = []
        for name, databundle in plotting_context.datasets().items():
            dataset, _, _, _, _ = databundle
            best_unit, best_axis = dataset.longest_axis()
            other_axes = {}
            xaxis_unit = plotting_context.get_conversion_factor(best_unit)
            try:
                conversion_factor = measure(1.0, best_unit, equivalent=True).toval(
                    xaxis_unit
                )
            except:
                continue
            else:
                if dataset._n_dim == 1:
                    temp = np.vstack(
                        [dataset._axes[best_axis] * conversion_factor, dataset._data]
                    ).T
                elif dataset._n_dim == 2:
                    shape = list(dataset._data.shape)
                    for name, axis in dataset._axes.items():
                        if name == best_axis:
                            continue
                        axis_unit = dataset._axes_units[name]
                        new_axis_unit = plotting_context.get_conversion_factor(
                            axis_unit
                        )
                        conv_factor = measure(1.0, axis_unit, equivalent=True).toval(
                            new_axis_unit
                        )
                        other_axes[name] = axis * conv_factor
                    for key, value in other_axes.items():
                        if len(value) in shape:
                            otheraxis = other_axes[key]
                            break
                    temp = np.hstack(
                        [dataset._axes[best_axis] * conversion_factor, dataset._data]
                    )
                    temp = np.vstack([np.concatenate([[0.0], otheraxis]), temp])
                else:
                    return
                text_data = "\n".join(
                    [" ".join([str(x) for x in line]) for line in temp]
                )
                new_text = "\n".join([new_header, text_data])
        target.setText(new_text)

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
    from MDANSE_GUI.Tabs.Models.PlottingContext import PlottingContext, SingleDataset


class DatasetFormatter:

    def __init__(self):
        self._plotting_context = None
        self._new_header = "# MDANSE Data \n"
        self._new_text = []
        top_line = []
        left_column = [""]
        all_fields = []

    def take_new_input(self, pc: "PlottingContext"):
        self._plotting_context = pc
        self._new_text = []
        if self._plotting_context is None:
            return ["No data selected"]
        for name, databundle in self._plotting_context.datasets().items():
            dataset, _, _, _, _ = databundle
            if dataset._n_dim == 1:
                self._new_text.append(self.process_1D_data(dataset))
            elif dataset._n_dim == 2:
                self._new_text.append(self.process_2D_data(dataset, name))
            else:
                self._new_text.append(self.process_ND_data(dataset, name))
        return self._new_text

    def make_dataset_header(self, dataset: "SingleDataset"):
        lines = []
        lines.append(f"# Dataset name: {dataset._name}")
        lines.append(f"# from file {dataset._filename}")
        lines.append(
            f"# Contains axes: "
            + ", ".join([str(axis) for axis in dataset.available_x_axes()])
        )
        lines.append(f"# data unit is {dataset._data_unit}")
        return lines

    def process_1D_data(self, dataset: "SingleDataset"):
        header_lines = self.make_dataset_header(dataset)
        best_unit, best_axis = dataset.longest_axis()
        xaxis_unit = self._plotting_context.get_conversion_factor(best_unit)
        try:
            conversion_factor = measure(1.0, best_unit, equivalent=True).toval(
                xaxis_unit
            )
        except:
            return f"Could not convert {best_unit} to {xaxis_unit}."
        else:
            header_lines.append(f"# units of x axis here: {xaxis_unit}")
            header_lines.append(
                f"# col1:{best_axis}:{xaxis_unit} col2:data:{dataset._data_unit}"
            )
            temp = np.vstack(
                [dataset._axes[best_axis] * conversion_factor, dataset._data]
            ).T
            text_data = "\n".join([" ".join([str(x) for x in line]) for line in temp])
            new_header = "\n".join(header_lines)
            return new_header + "\n" + text_data

    def process_2D_data(self, dataset: "SingleDataset", name: str):
        header_lines = self.make_dataset_header(dataset)
        temp = []
        if len(temp) > 0:
            text_data = "\n".join([" ".join([str(x) for x in line]) for line in temp])
        else:
            text_data = ""
        new_header = "\n".join(header_lines)
        return new_header + "\n" + text_data

    def process_ND_data(self, dataset: "SingleDataset", name: str):
        header_lines = self.make_dataset_header(dataset)
        temp = []
        if len(temp) > 0:
            text_data = "\n".join([" ".join([str(x) for x in line]) for line in temp])
        else:
            text_data = ""
        new_header = "\n".join(header_lines)
        return new_header + "\n" + text_data


class Text(Plotter):

    def __init__(self) -> None:
        super().__init__()
        self._figure = None
        self._current_colours = []
        self._active_curves = []
        self._backup_curves = []
        self._backup_limits = []
        self._formatter = DatasetFormatter()
        self._curve_limit_per_dataset = 12
        self.height_max, self.length_max = 0.0, 0.0

    def clear(self, figure: "QTextBrowser" = None):
        LOG.debug("Text.clear stared")
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            return
        target.clear()
        LOG.debug("Text.clear finished")

    def get_figure(self, figure: "QTextBrowser" = None):
        LOG.debug("Text.get_figure stared")
        if figure is None:
            target = self._figure
        else:
            target = figure
        if target is None:
            LOG.error(f"PlottingContext can't plot to {target}")
            return
        target.clear()
        LOG.debug("Text.get_figure finished")
        return target

    def apply_settings(self, plotting_context: "PlottingContext", colours=None):
        LOG.debug("Text.apply_settings stared")
        if colours is not None:
            self._current_colours = colours
        if plotting_context.set_axes() is None:
            LOG.error("Axis check failed.")
            return

    def plot(
        self,
        plotting_context: "PlottingContext",
        figure: "QTextBrowser" = None,
        colours=None,
        update_only=False,
        toolbar=None,
    ):
        """In the Text plotter, the plot method displays the data as text.
        Many arguments are included just for compatibility with the plotter.

        Parameters
        ----------
        plotting_context : PlottingContext
            Data model containing the data sets to be shown
        figure : QTextBrowser, optional
            Target widget, an instance of QTextBrowser
        colours : _type_, optional
            colours of datasets, ignored here
        update_only : bool, optional
            ignored
        toolbar : _type_, optional
            ignored
        """
        LOG.debug("Text.plot stared")
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
            return
        self._formatter.take_new_input(plotting_context)
        target.setText("\n".join(self._formatter._new_text))

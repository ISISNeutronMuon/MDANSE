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

import numpy as np

from qtpy import QtCore, QtGui

from matplotlib.markers import MarkerStyle

from MDANSE.Framework.Units import measure, UnitError


class Plot1DModelError(Exception):
    pass


class Plot1DModel(QtCore.QAbstractListModel):
    line_styles = ["-", "--", "-.", ":", "None"]

    legend_locations = [
        "best",
        "upper right",
        "upper left",
        "lower left",
        "lower right",
        "right",
        "center left",
        "center right",
        "lower center",
        "upper center",
        "center",
    ]

    markers = list(
        [marker for marker in MarkerStyle.markers.keys() if isinstance(marker, str)]
    )

    scales = ["linear", "symlog", "ln", "log 10", "log 2"]

    model_updated = QtCore.Signal()

    LineRole = QtCore.Qt.ItemDataRole.UserRole

    YDataRole = QtCore.Qt.ItemDataRole.UserRole + 1

    LineStyleRole = QtCore.Qt.ItemDataRole.UserRole + 2

    LineWidthRole = QtCore.Qt.ItemDataRole.UserRole + 3

    LineColorRole = QtCore.Qt.ItemDataRole.UserRole + 4

    MarkerStyleRole = QtCore.Qt.ItemDataRole.UserRole + 5

    def __init__(self, figure, x_data_info=None, parent=None):
        """Constructor.

        Args:
            figure (matplotlib.pyplot.figure): the figure that will display slices of the ND model
            x_data_info (dict): the information about the X axis
            parent: the parent of the model
        """
        super(Plot1DModel, self).__init__(parent)

        self._figure = figure

        self._selected_line = None

        self._show_legend = True
        self._legend_location = "best"
        self._legend_frameon = True
        self._legend_shadow = True
        self._legend_fancybox = False

        self._show_grid = False
        self._grid_line_style = "-"
        self._grid_width = 1.0
        self._grid_color = (0, 0, 0)

        self._line_splitter_maximum_offset = 0.0
        self._line_splitter_factor = 0.0

        if x_data_info is not None:
            self.reset(x_data_info)

    def add_line(self, y_data_info):
        """Add a new line to the model.

        Args:
            y_data_info (dict): the information about the Y of the line
        """
        y_variable = y_data_info["variable"]
        line_names = [line[0] for line in self._lines]
        if y_variable in line_names:
            return

        axis = y_data_info["axis"].split("|")
        if len(axis) != 1:
            raise Plot1DModelError("Can not add line: incompatible number of X axis")
        else:
            if axis[0] != self._x_data_info["variable"]:
                raise Plot1DModelError("Can not add line: incompatible X axis")

        y_data = y_data_info["data"]

        if y_data.ndim != 1:
            raise Plot1DModelError("Invalid dimension for Y data")

        # Case of the first line added: the Y unit are stored as the internal unit
        y_unit = y_data_info["units"]
        if not self._y_initial_unit:
            self._y_initial_unit = y_unit
            self._y_current_unit = self._y_initial_unit
            y_conversion_factor = 1.0
        else:
            # The unit of the line to add must be compatible with the internal one
            try:
                m = measure(1.0, self._y_initial_unit, equivalent=True)
                y_conversion_factor = m.toval(y_unit)
            except UnitError:
                raise Plot1DModelError("Can not add line: incompatible Y unit")

        if not self._y_axis_label:
            self._y_axis_label = y_variable
            self.set_y_axis_label(self._y_axis_label)

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
        line = self._figure.axes[0].plot(
            self._x_data_info["data"] * self._x_conversion_factor,
            y_data * y_conversion_factor,
            picker=3,
        )[0]
        self._lines.append([y_variable, line, y_data])
        self.endInsertRows()

        self.update_legend()
        self.adjust_axes()

    def adjust_axes(self):
        """Adjust the axes of the figure such that they match the global min/max values of the X and Y axis respectively."""
        x_min = self.get_x_axis_min_value()
        x_max = self.get_x_axis_max_value()
        self._figure.axes[0].set_xlim([x_min, x_max])

        y_min = self.get_y_axis_min_value()
        y_max = self.get_y_axis_max_value()
        self._figure.axes[0].set_ylim([y_min, y_max])

        self._figure.canvas.draw()

        return (x_min, x_max, y_min, y_max)

    def clear(self):
        """Clear the figure."""
        self._x_axis_label = ""
        self._y_axis_label = ""
        self._y_initial_unit = None
        self._y_current_unit = None
        self._lines.clear()
        self._figure.axes[0].clear()
        self._figure.canvas.draw()
        self.layoutChanged.emit()

    def data(self, index, role):
        """Return the data for a given index and role.

        Args:
            index (qtpy..QtCore.QModelIndex): the index
            role (int): the role

        Returns:
            any: the data
        """
        row = index.row()
        name, line, y_data = self._lines[row]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            return name

        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
            matplotlib_color = line.get_color()
            try:
                color = QtGui.QColor(matplotlib_color)
            except TypeError:
                r, g, b = matplotlib_color
                color = QtGui.QColor(int(r * 255), int(g * 255), int(b * 255))
            return color

        elif role == Plot1DModel.LineRole:
            return line

        elif role == Plot1DModel.YDataRole:
            return y_data

        else:
            return QtCore.QVariant()

    def flags(self, index):
        """Returns the flags of a given index.

        Args:
            index (qtpy.QtCore.QModelIndex): the index

        Returns:
            int: the flag
        """
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsEditable
        )

    def get_figure_title(self):
        """Returns the figure title.

        Returns:
            str: the figure title
        """
        suptitle = self._figure._suptitle
        return suptitle.get_text() if suptitle is not None else ""

    def get_grid_color(self):
        """Return the grid color. The color is expressed as 3-tuple in matlotlib convention ([0,1])

        Returns:
            3-tuple of float: the grid color
        """
        return self._grid_color

    def get_grid_line_style(self):
        """Return the grid style.

        Returns:
            str: the grid style
        """
        return self._grid_line_style

    def get_grid_width(self):
        """Returns the grid width.

        Returns:
            float: the grid width
        """
        return self._grid_width

    def get_legend_fancybox(self):
        """Returns whether or not the legend fancybox should be showed.

        Returns:
            bool: whether or not the legend fancybox should be showed
        """
        return self._legend_fancybox

    def get_legend_frameon(self):
        """Returns whether or not the legend frame should be showed.

        Returns:
            bool: whether or not the legend frame should be showed
        """
        return self._legend_frameon

    def get_legend_location(self):
        """Returns the legend location.

        Returns:
            str: the legend location
        """
        return self._legend_location

    def get_legend_shadow(self):
        """Returns whether or not the legend shadow should be showed.

        Returns:
            bool: whether or not the legend shadow should be showed
        """
        return self._legend_shadow

    def get_line_splitter_factor(self):
        """Returns the line splitter factor.

        Returns:
            float: the line splitter factor
        """
        return self._line_splitter_factor

    def get_line_splitter_maximum_offset(self):
        """Returns the line splitter maximum offset.

        Returns:
            float: the line splitter maximum offset
        """
        return self._line_splitter_maximum_offset

    def get_line_full_names(self):
        """Returns the names of the lines.

        Returns:
            list of str: the names of the lines
        """
        return [f"{line[0]} ({self._y_current_unit})" for line in self._lines]

    def get_line_names(self):
        """Returns the line names.

        Returns:
            list of str: the line names
        """
        return [line[0] for line in self._lines]

    def get_plot_title(self):
        """Returns the plot title.

        Returns:
            str: the plot title
        """
        return self._figure.axes[0].get_title()

    def get_selected_line_index(self):
        """Returns the selected line index. None if no line is selected.

        Returns:
            int or None: the selected line index.
        """
        if self._selected_line is None:
            return None

        lines = [line[1] for line in self._lines]
        for i, line in enumerate(lines):
            if line == self._selected_line:
                return i
        else:
            return None

    def get_show_grid(self):
        """Returns whether or not the grid should be showed.

        Returns:
            bool: whether or not the grid should be showed
        """
        return self._show_grid

    def get_show_legend(self):
        """Returns whether or not the legend should be showed.

        Returns:
            bool: whether or not the legend should be showed
        """
        return self._show_legend

    def get_x_axis_current_unit(self):
        """Returns the X axis current unit.

        Returns:
            str: the X axis current unit
        """
        return self._x_current_unit

    def get_x_axis_data(self):
        """Returns the X axis data converted to the current X axis unit.

        Returns:
            1D-array: the current X axis data
        """
        return self._x_data_info["data"] * self._x_conversion_factor

    def get_x_axis_label(self):
        """Returns the X axis label.

        Returns:
            str: the X axis label
        """
        return f"{self._x_axis_label} ({self._x_current_unit})"

    def get_x_axis_max_value(self):
        """Returns the global maximum of the X data of all lines.

        Returns:
            float: the global maximum
        """
        lines = [line[1] for line in self._lines]
        try:
            max_value = max([line.get_xdata().max() for line in lines])
        except ValueError:
            max_value = 0.0
        finally:
            return max_value

    def get_x_axis_min_value(self):
        """Returns the global minimum of the X data of all lines.

        Returns:
            float: the global minimum
        """
        lines = [line[1] for line in self._lines]
        try:
            min_value = min([line.get_xdata().min() for line in lines])
        except ValueError:
            min_value = 0.0
        finally:
            return min_value

    def get_x_axis_scale(self):
        """Returns the X axis scale.

        Returns:
            str: the X axis scale
        """
        return self._x_scale

    def get_x_axis_variable(self):
        """Returns the X axis underlying variable name.

        Returns:
            str: the X axis variable name
        """
        return self._x_data_info["variable"]

    def get_y_axis_current_unit(self):
        """Returns the Y axis current unit.

        Returns:
            str: the Y axis current unit
        """
        return self._y_current_unit

    def get_y_axis_data(self):
        """Returns the Y axis data for all lines converted to the current Y axis unit.

        Returns:
            list of 1D-array: all the Y axis data
        """
        return [line[1].get_ydata() for line in self._lines]

    def get_y_axis_label(self):
        """Returns the label of the Y axis.

        Returns:
            str: the label of the Y axis
        """
        return self._y_axis_label

    def get_y_axis_max_value(self):
        """Returns the global maximum of the Y data of all lines.

        Returns:
            float: the global maximum
        """
        lines = [line[1] for line in self._lines]
        try:
            max_value = max([line.get_ydata().max() for line in lines])
        except ValueError:
            max_value = 0.0
        finally:
            return max_value

    def get_y_axis_min_value(self):
        """Returns the global minimum of the Y data of all lines.

        Returns:
            float: the global minimum
        """
        lines = [line[1] for line in self._lines]
        try:
            min_value = min([line.get_ydata().min() for line in lines])
        except ValueError:
            min_value = 0.0
        finally:
            return min_value

    def get_y_axis_scale(self):
        """Returns the Y axis scale.

        Returns:
            str: the Y axis scale
        """
        return self._y_scale

    def removeRow(self, row, parent=None):
        """Remove a row from the model.

        Args:
            row (int): the index of the row to be removed
            parent (PyQt5.QtCore.QModelIndex): the parent

        Returns:
            bool: True if the removal was successful
        """
        if row < 0 or row >= self.rowCount():
            return

        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        self._lines[row][1].remove()
        del self._lines[row]
        self.endRemoveRows()

        if not self._lines:
            self._figure.axes[0].set_prop_cycle(None)
        else:
            self.adjust_axes()

        self.update_legend()

        self.model_updated.emit()

        return True

    def reset(self, x_data_info):
        """Reset the model with new X axis info.

        Args:
            x_data_info (dict): the X axis information
        """
        x_data = x_data_info["data"]
        if x_data.ndim != 1:
            raise Plot1DModelError("Invalid dimension for X data")

        self._x_data_info = x_data_info

        self._x_axis_label = self._x_data_info["variable"]

        self._x_current_unit = self._x_data_info["units"]

        self._x_conversion_factor = 1.0

        self._y_axis_label = ""

        self._y_initial_unit = None
        self._y_current_unit = None

        self._x_scale = "linear"
        self._y_scale = "linear"

        self.reset_axes()

        self.set_x_axis_label(self._x_axis_label)

    def reset_axes(self):
        """Reset the the axes."""
        self.unselect_line()
        self._figure.axes[0].clear()
        self._lines = []
        self._figure.canvas.draw()

    def rowCount(self, parent=QtCore.QModelIndex()):
        """Return the number of numors stored in the model.

        Args:
            parent (PyQt5.QtCore.QObject): the parent object

        Returns:
            int: the numner of numors stored in the model
        """
        return len(self._lines)

    def setData(self, index, value, role):
        """Set the data of the model.

        Args:
            index (qtpy.QtCore.QModelIndex): the index
            value (any): the value
            role (int): the role
        """
        if not index.isValid():
            return

        row = index.row()
        if role == QtCore.Qt.ItemDataRole.EditRole:
            self._lines[row][0] = value
            self.update_legend()
            self.model_updated.emit()
            return True
        elif role == Plot1DModel.LineStyleRole:
            line = self._lines[row][1]
            if value not in Plot1DModel.line_styles:
                raise Plot1DModelError("Invalid line style")
            line.set_linestyle(value)
            self.update_legend()
            return True
        elif role == Plot1DModel.LineWidthRole:
            line = self._lines[row][1]
            line.set_linewidth(value)
            self.update_legend()
            return True
        elif role == Plot1DModel.LineColorRole:
            line = self._lines[row][1]
            line.set_color(value)
            self.update_legend()
            return True
        elif role == Plot1DModel.MarkerStyleRole:
            line = self._lines[row][1]
            if value not in Plot1DModel.markers:
                raise Plot1DModelError("Invalid marker")
            line.set_marker(value)
            self.update_legend()
            return True
        return False

    def select_line(self, line):
        """Select a line of the figure.

        Args:
            line (matplotlib.lines.Line2D): the line to select
        """
        lines = [line[1] for line in self._lines]
        if line not in lines:
            return

        # If there was a previously selected line, set back its alpha value to 1.0
        if self._selected_line is not None:
            self._selected_line.set_alpha(1.0)

        self._selected_line = line
        self._selected_line.set_alpha(0.4)
        self._figure.canvas.draw()

    def set_figure_title(self, title):
        """Set the figure title.

        Args:
            title (str): the new title
        """
        self._figure.suptitle(title)
        self._figure.canvas.draw()

    def set_grid_color(self, color):
        """Set the grid color. The color must be set in the matplotlib RGB convention i.e. a 3-tuple of floats between 0 and 1.

        Args:
            color (3-tuple of float): the grid color
        """
        self._grid_color = color
        self.update_grid()

    def set_grid_line_style(self, style):
        """Set the grid style.

        Args:
            style (str): the grid style
        """
        if style not in Plot1DModel.line_styles:
            raise Plot1DModelError("Invalid style")
        self._grid_line_style = style
        self.update_grid()

    def set_grid_width(self, width):
        """Set the grid width.

        Args:
            width (float): the grid width
        """
        self._grid_width = width
        self.update_grid()

    def set_legend_fancybox(self, state):
        """Set whether or not the legend fancybox should be showed.

        Args:
            state (bool): whether or not the legend fancybox should be showed
        """
        self._legend_fancybox = state
        self.update_legend()

    def set_legend_frameon(self, state):
        """Set whether or not the legend frame should be showed.

        Args:
            state (bool): whether or not the legend frame should be showed
        """
        self._legend_frameon = state
        self.update_legend()

    def set_legend_location(self, location):
        """Set the legend location.

        Args:
            location (str): the legend location
        """
        if location not in Plot1DModel.legend_locations:
            raise Plot1DModelError("Invalid location")
        self._legend_location = location
        self.update_legend()

    def set_legend_shadow(self, state):
        """Set whether or not the legend shadow should be showed.

        Args:
            state (bool): whether or not the legend shadow should be showed
        """
        self._legend_shadow = state
        self.update_legend()

    def set_line_splitter_factor(self, factor):
        """Set the line splitter factor.

        Args:
            factor (float): the line splitter factor
        """
        self._line_splitter_factor = factor
        self.split_lines()

    def set_line_splitter_maximum_offset(self, offset):
        """Set the line splitter maximum offset.

        Args:
            factor (float): the line splitter maximum offset
        """
        self._line_splitter_maximum_offset = offset
        self.split_lines()

    def set_plot_title(self, title):
        """Set the plot title.

        Args:
            title (str): the new title
        """
        self._figure.axes[0].set_title(title)
        self._figure.canvas.draw()

    def set_show_grid(self, state):
        """Set whether or not the grid should be showed.

        Args:
            state (bool): whether or not the grid should be showed
        """
        self._show_grid = state
        self.update_grid()

    def set_show_legend(self, state):
        """Set whether or not the legend should be showed.

        Args:
            state (bool): whether or not the legend should be showed
        """
        self._show_legend = state
        self.update_legend()

    def set_x_axis_label(self, label):
        """Set the X axis label.

        Args:
            label (str): the X axis label
        """
        self._x_axis_label = label
        self._figure.axes[0].set_xlabel(f"{label} ({self._x_current_unit})")
        self._figure.canvas.draw()
        self.model_updated.emit()

    def set_x_axis_range(self, x_min, x_max):
        """Set the X axis range.

        Args:
            x_min (float): the minimum value
            x_max (float): the maximum value
        """
        if x_min >= x_max:
            raise Plot1DModelError("Invalid min/max values")

        self._figure.axes[0].set_xlim([x_min, x_max])
        self._figure.canvas.draw()

    def set_x_axis_scale(self, scale):
        """Set the X axis scale.

        Args:
            scale (str): the X axis scale
        """
        if scale not in Plot1DModel.scales:
            raise Plot1DModelError("Invalid X axis scale")

        self._x_scale = scale
        if scale == "linear":
            self._figure.axes[0].set_xscale("linear")
        elif scale == "symlog":
            self._figure.axes[0].set_xscale("symlog")
        elif scale == "ln":
            self._figure.axes[0].set_xscale("log", base=np.exp(1))
        elif scale == "log 10":
            self._figure.axes[0].set_xscale("log", base=10)
        elif scale == "log 2":
            self._figure.axes[0].set_xscale("log", base=2)
        self._figure.canvas.draw()

    def set_x_axis_unit(self, x_unit):
        """Set the X axis current unit.

        Args:
            x_unit (str): the X axis unit
        """
        try:
            m = measure(1.0, self._x_data_info["units"], equivalent=True)
            self._x_conversion_factor = m.toval(x_unit)
        except UnitError:
            raise Plot1DModelError(
                f"Units {self._x_data_info['units']} and {x_unit} are incompatible"
            )
        else:
            self._x_current_unit = x_unit
            for _, line, _ in self._lines:
                line.set_xdata(self._x_data_info["data"] * self._x_conversion_factor)
            self.set_x_axis_label(self._x_axis_label)
            self.adjust_axes()
            self.model_updated.emit()

    def set_y_axis_label(self, label):
        """Set the Y axis label.

        Args:
            label (str): the Y axis label
        """
        self._y_axis_label = label
        self._figure.axes[0].set_ylabel(f"{label} ({self._y_current_unit})")
        self._figure.canvas.draw()

    def set_y_axis_range(self, y_min, y_max):
        """Set the Y axis range.

        Args:
            y_min (float): the minimum value
            y_max (float): the maximum value
        """
        if y_min >= y_max:
            raise Plot1DModelError("Invalid min/max values")
        self._figure.axes[0].set_ylim([y_min, y_max])
        self._figure.canvas.draw()

    def set_y_axis_scale(self, scale):
        """Set the Y axis scale.

        Args:
            scale (str): the Y axis scale
        """
        if scale not in Plot1DModel.scales:
            raise Plot1DModelError("Invalid Y axis scale")
        self._y_scale = scale
        if scale == "linear":
            self._figure.axes[0].set_yscale("linear")
        elif scale == "symlog":
            self._figure.axes[0].set_yscale("symlog")
        elif scale == "ln":
            self._figure.axes[0].set_yscale("log", base=np.exp(1))
        elif scale == "log 10":
            self._figure.axes[0].set_yscale("log", base=10)
        elif scale == "log 2":
            self._figure.axes[0].set_yscale("log", base=2)
        self.adjust_axes()

    def set_y_axis_unit(self, y_unit):
        """Set the Y axis current unit.

        Args:
            y_unit (str): the Y axis unit
        """
        try:
            m = measure(1.0, self._y_initial_unit, equivalent=True)
            conversion_factor = m.toval(y_unit)
        except UnitError:
            raise Plot1DModelError(
                f"Units {self._y_initial_unit} and {y_unit} are incompatible"
            )
        else:
            self._y_current_unit = y_unit
            for i, (_, line, y_data) in enumerate(self._lines):
                offset = (
                    i * self._line_splitter_maximum_offset * self._line_splitter_factor
                )
                line.set_ydata(y_data * conversion_factor + offset)
            self.set_y_axis_label(self._y_axis_label)
            self.adjust_axes()
            self.model_updated.emit()

    def split_lines(self):
        """Split the lines according the current offset."""
        if not self._lines:
            return

        m = measure(1.0, self._y_initial_unit, equivalent=True)
        conversion_factor = m.toval(self._y_current_unit)

        for i, (_, line, y_data) in enumerate(self._lines):
            offset = i * self._line_splitter_maximum_offset * self._line_splitter_factor
            line.set_ydata(y_data * conversion_factor + offset)

        self.adjust_axes()
        self.model_updated.emit()

    def unselect_line(self):
        """Unselect the selected line if any."""
        if self._selected_line is not None:
            self._selected_line.set_alpha(1.0)
            self._selected_line = None
            self._figure.canvas.draw()

    def update_grid(self):
        """Update the grid."""
        if not self._show_grid:
            self._figure.axes[0].grid(False)
        else:
            self._figure.axes[0].grid(
                True,
                linestyle=self._grid_line_style,
                linewidth=self._grid_width,
                color=self._grid_color,
            )
        self._figure.canvas.draw()

    def update_legend(self):
        """Update the legend."""
        axes = self._figure.axes[0]
        if not self._lines:
            axes.get_legend().remove()
            self._figure.canvas.draw()
            return

        if not self._show_legend:
            axes.get_legend().remove()
            self._figure.canvas.draw()
            return

        line_names = [line[0] for line in self._lines]

        axes.legend(
            line_names,
            loc=self._legend_location,
            frameon=self._legend_frameon,
            shadow=self._legend_shadow,
            fancybox=self._legend_fancybox,
        )

        self._figure.canvas.draw()

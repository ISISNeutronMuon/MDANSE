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
from matplotlib.colors import LogNorm, Normalize, SymLogNorm
from matplotlib import pyplot
from qtpy import QtCore

from MDANSE.Framework.Units import measure, UnitError
from MDANSE.MLogging import LOG

from MDANSE_GUI.Plotter.utils.numeric import smart_round


class Plot2DModelError(Exception):
    pass


class Plot2DModel(QtCore.QObject):
    x_variable_updated = QtCore.pyqtSignal(str)

    y_variable_updated = QtCore.pyqtSignal(str)

    z_variable_updated = QtCore.pyqtSignal(str)

    aspects = ["auto", "equal"]

    cmaps = sorted(pyplot.colormaps(), key=lambda v: v.lower())

    interpolations = [
        "none",
        "nearest",
        "bilinear",
        "bicubic",
        "spline16",
        "spline36",
        "hanning",
        "hamming",
        "hermite",
        "kaiser",
        "quadric",
        "catrom",
        "gaussian",
        "bessel",
        "mitchell",
        "sinc",
        "lanczos",
    ]

    normalizers = ["none", "linear", "log", "symlog"]

    def __init__(self, figure, x_data_info, y_data_info, z_data_info, *args, **kwargs):
        super(Plot2DModel, self).__init__(*args, **kwargs)

        self._figure = figure

        self._interpolation = "nearest"

        self._add_colorbar = True

        self._aspect = "auto"

        self._cmap = "viridis"

        self._colorbar = None

        self._norm = "none"

        self._slicer = None

        self.set_data(x_data_info, y_data_info, z_data_info)

    def _plot(self):
        """ """
        self._image = self._figure.axes[0].imshow(
            self._z_data.T,
            interpolation=self._interpolation,
            origin="lower",
            cmap=self._cmap,
        )

        extent = self.get_extent()
        self._image.set_extent(extent)

        self.set_aspect(self._aspect)
        self.set_x_axis_label(self._x_variable)
        self.set_y_axis_label(self._y_variable)
        self.set_norm(self._norm)
        self.toggle_colorbar(self._add_colorbar)

    def export_data(self, filename):
        """ """

    #     header = []
    #     header.append(f"# {self._x_variable} ({self._x_current_unit})")
    #     for name in line_names:
    #         header.append(f"# {name} ({self._y_unit})")
    #     header = "\n".join(header)
    #     packed_data = self.pack_data()
    #     with open(filename, 'w') as f:
    #         f.write(header)
    #         f.write("\n")
    #         np.savetxt(f,packed_data, fmt='%12.4e', delimiter="  ")
    #         f.close()

    def get_aspect(self):
        """ """
        return self._aspect

    def get_cmap(self):
        """ """
        return self._cmap

    def get_extent(self):
        """ """
        xmin = self._x_data[0] * self._x_conversion_factor
        xmax = self._x_data[-1] * self._x_conversion_factor
        ymin = self._y_data[0] * self._y_conversion_factor
        ymax = self._y_data[-1] * self._y_conversion_factor
        return [xmin, xmax, ymin, ymax]

    def get_figure_title(self):
        suptitle = self._figure._suptitle
        return suptitle.get_text() if suptitle is not None else ""

    def get_interpolation(self):
        """ """
        return self._interpolation

    def get_norm(self):
        """ """
        return self._norm

    def get_plot_title(self):
        """ """
        return self._figure.axes[0].get_title()

    def get_x_current_unit(self):
        """ """
        return self._x_current_unit

    def get_x_data(self):
        """ """
        return self._x_data * self._x_conversion_factor

    def get_x_slice_info(self, index):
        """ """
        x_data = self._x_data * self._x_conversion_factor
        x_value = smart_round(x_data[index], sigfigs=3, output="std")

        y_data = self._y_data * self._y_conversion_factor

        z_data = self._z_data * self._z_conversion_factor
        x_slice = z_data[index, :]

        y_variable = f"{self._z_variable} ({self._x_variable}={x_value})"

        x_data_info = {
            "variable": self._y_variable,
            "data": y_data,
            "units": self._y_current_unit,
            "axis": "index",
        }
        y_data_info = {
            "variable": y_variable,
            "data": x_slice,
            "units": self._z_current_unit,
            "axis": self._y_variable,
        }

        return (x_data_info, y_data_info)

    def get_x_variable(self):
        """ """
        return self._x_variable

    def get_y_current_unit(self):
        """ """
        return self._y_current_unit

    def get_y_data(self):
        """ """
        return self._y_data * self._y_conversion_factor

    def get_y_slice_info(self, index):
        """ """
        y_data = self._y_data * self._y_conversion_factor
        y_value = smart_round(y_data[index], sigfigs=3, output="std")

        x_data = self._x_data * self._x_conversion_factor

        z_data = self._z_data * self._z_conversion_factor
        y_slice = z_data[:, index]

        y_variable = f"{self._z_variable} ({self._y_variable}={y_value})"

        x_data_info = {
            "variable": self._x_variable,
            "data": x_data,
            "units": self._x_current_unit,
            "axis": "index",
        }
        y_data_info = {
            "variable": y_variable,
            "data": y_slice,
            "units": self._z_current_unit,
            "axis": self._x_variable,
        }

        return (x_data_info, y_data_info)

    def get_y_variable(self):
        """ """
        return self._y_variable

    def get_z_current_unit(self):
        """ """
        return self._z_current_unit

    def get_z_variable(self):
        """ """
        return self._z_variable

    def add_colorbar(self):
        """ """
        return self._add_colorbar

    def set_aspect(self, aspect):
        """ """
        self._aspect = aspect
        self._figure.axes[0].set_aspect(self._aspect)
        self._figure.canvas.draw()

    def set_cmap(self, cmap):
        """ """
        self._cmap = cmap
        self._image.set_cmap(cmap)
        self._figure.canvas.draw()

    def set_data(self, x_data_info, y_data_info, z_data_info):
        """ """
        self._x_data = x_data_info["data"]

        self._x_variable = x_data_info["variable"]

        self._x_initial_unit = x_data_info["units"]
        self._x_current_unit = self._x_initial_unit

        self._x_conversion_factor = 1.0

        self._y_data = y_data_info["data"]

        self._y_variable = y_data_info["variable"]

        self._y_initial_unit = y_data_info["units"]
        self._y_current_unit = self._y_initial_unit

        self._y_conversion_factor = 1.0

        self._z_data = z_data_info["data"]

        self._z_variable = z_data_info["variable"]

        self._z_initial_unit = z_data_info["units"]
        self._z_current_unit = self._z_initial_unit

        self._z_conversion_factor = 1.0

        self._plot()

    def set_figure_title(self, title):
        """ """
        self._figure.suptitle(title)
        self._figure.canvas.draw()

    def set_interpolation(self, interpolation):
        """ """
        self._interpolation = interpolation
        self._image.set_interpolation(interpolation)
        self._figure.canvas.draw()

    def set_norm(self, norm):
        """ """
        if norm not in self.normalizers:
            return

        data = self._image.get_array()
        if norm == "log" and data.min() <= 0.0:
            LOG.error(f"Data contains negative value, {['main', 'popup']}, {'error'}")
            return

        if norm == "none":
            normalizer = Normalize(vmin=data.min(), vmax=data.max())
        elif norm == "linear":
            normalizer = Normalize(vmin=0.0, vmax=1)
        elif norm == "log":
            normalizer = LogNorm(vmin=data.min(), vmax=data.max())
        else:
            normalizer = SymLogNorm(
                vmin=data.min(), vmax=data.max(), linthresh=0.3, linscale=0.3
            )
        self._image.set_norm(normalizer)
        self._norm = norm
        self.toggle_colorbar(self._add_colorbar)

    def set_plot_title(self, title):
        """ """
        self._figure.axes[0].set_title(title)
        self._figure.canvas.draw()

    def set_slicer(self, row, column):
        """ """
        if self._slicer is not None:
            hline, vline = self._slicer
            hline.remove()
            vline.remove()

        x_data = self._x_data * self._x_conversion_factor
        vline = self._figure.axes[0].axvline(x=x_data[row], linewidth=3)

        y_data = self._y_data * self._y_conversion_factor
        hline = self._figure.axes[0].axhline(y=y_data[column], linewidth=3)

        self._slicer = (hline, vline)

        self._figure.canvas.draw()

    def set_x_axis_label(self, label):
        """ """
        self._x_variable = label
        self._figure.axes[0].set_xlabel(f"{label} ({self._x_current_unit})")
        self._figure.canvas.draw()
        self.x_variable_updated.emit(self._x_variable)

    def set_x_unit(self, x_unit):
        """ """
        try:
            m = measure(1.0, self._x_initial_unit, equivalent=True)
            self._x_conversion_factor = m.toval(x_unit)
        except UnitError:
            raise Plot2DModelError(
                f"Units {self._x_initial_unit} and {x_unit} are incompatible"
            )
        else:
            self._x_current_unit = x_unit
            extent = self.get_extent()
            self._image.set_extent(extent)
            self.set_x_axis_label(self._x_variable)

    def set_y_axis_label(self, label):
        """ """
        self._y_variable = label
        self._figure.axes[0].set_ylabel(f"{label} ({self._y_current_unit})")
        self._figure.canvas.draw()
        self.y_variable_updated.emit(self._y_variable)

    def set_y_unit(self, y_unit):
        """ """
        try:
            m = measure(1.0, self._y_initial_unit, equivalent=True)
            self._y_conversion_factor = m.toval(y_unit)
        except UnitError:
            raise Plot2DModelError(
                f"Units {self._y_initial_unit} and {y_unit} are incompatible"
            )
        else:
            self._y_current_unit = y_unit
            extent = self.get_extent()
            self._image.set_extent(extent)
            self.set_y_axis_label(self._y_variable)

    def set_z_axis_label(self, label):
        """ """
        self._z_variable = label
        if self._colorbar is not None:
            self._colorbar.ax.get_yaxis().labelpad = 15
            self._colorbar.ax.set_ylabel(
                f"{label} ({self._z_current_unit})", rotation=270
            )
            self._figure.canvas.draw()
        self.z_variable_updated.emit(self._z_variable)

    def set_z_unit(self, z_unit):
        """ """
        try:
            m = measure(1.0, self._z_initial_unit, equivalent=True)
            self._z_conversion_factor = m.toval(z_unit)
        except UnitError:
            raise Plot2DModelError(
                f"Units {self._z_initial_unit} and {z_unit} are incompatible"
            )
        else:
            self._z_current_unit = z_unit
            scaled_data = self._z_data * self._z_conversion_factor
            self._image.set_data(scaled_data)
            self._image.set_clim(vmin=scaled_data.min(), vmax=scaled_data.max())
            self.set_z_axis_label(self._z_variable)
            self.toggle_colorbar(self._add_colorbar)

    def unset_slicer(self):
        """ """
        if self._slicer is not None:
            hline, vline = self._slicer
            hline.remove()
            vline.remove()
            self._slicer = None
            self._figure.canvas.draw()

    def toggle_colorbar(self, state):
        """ """
        self._add_colorbar = state

        if self._colorbar is not None:
            self._colorbar.remove()
            self._colorbar = None

        if self._add_colorbar:
            self._colorbar = self._figure.colorbar(self._image)
            self.set_z_axis_label(self._z_variable)

        self._figure.canvas.draw()

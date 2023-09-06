import numpy as np

from qtpy import QtCore

from matplotlib import pyplot
from matplotlib.colors import LogNorm, Normalize, SymLogNorm
from matplotlib.patches import Rectangle

from MDANSE.Framework.Units import measure, UnitError

from MDANSE_GUI.PyQtGUI.pygenplot.utils.numeric import smart_round


class PlotNDModelError(Exception):
    pass


class PlotNDModel(QtCore.QObject):
    model_updated = QtCore.Signal()

    x_variable_updated = QtCore.Signal(str)

    y_variable_updated = QtCore.Signal(str)

    z_variable_updated = QtCore.Signal(str)

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

    def __init__(self, figure, axis_info, data_info, *args, **kwargs):
        """Constructor.

        Args:
            figure (matplotlib.pyplot.figure): the figure that will display slices of the ND model
            axis_info (list): the list of axis. Each element of the list stores the basic information about the axis through a dictionary
            data_info (dict): the information about the ND data
        """
        super(PlotNDModel, self).__init__(*args, **kwargs)

        self._figure = figure

        self._interpolation = "nearest"

        self._show_colorbar = True

        self._aspect = "auto"

        self._cmap = "viridis"

        self._colorbar = None

        self._norm = "none"

        self._x_slicer = None

        self._y_slicer = None

        self._x_integration_box = None

        self._y_integration_box = None

        self._transpose = False

        self._axis_info = axis_info

        if len(self._axis_info) != data_info["dimension"]:
            raise PlotNDModelError("Axis inconsistent with the data")

        try:
            self._axis_current_units = [axis["units"] for axis in self._axis_info]
        except KeyError:
            raise PlotNDModelError("No units defined in axis")

        try:
            _ = [
                measure(1.0, unit, equivalent=True) for unit in self._axis_current_units
            ]
        except UnitError as e:
            raise PlotNDModelError(str(e))

        self._axis_conversion_factors = [1.0] * len(self._axis_info)

        self._data_info = data_info
        try:
            self._data_current_unit = self._data_info["units"]
        except KeyError:
            raise PlotNDModelError("No units defined in data")

        try:
            _ = measure(1.0, self._data_current_unit, equivalent=True)
        except UnitError as e:
            raise PlotNDModelError(str(e))

        self._data_conversion_factor = 1.0

        slices = tuple(
            [slice(None), slice(None)] + [slice(0, 1, 1)] * (len(self._axis_info) - 2)
        )

        summed_dimensions = [False] * len(self._axis_info)

        self.update_model(list(zip(slices, summed_dimensions)), self._transpose)

    def _plot(self):
        """Plot a slice of the ND data."""
        slices = tuple([sli for sli, _ in self._slices])
        summed_dimensions_indexes = tuple(
            [
                i
                for i, (_, summed_dimension) in enumerate(self._slices)
                if summed_dimension
            ]
        )
        try:
            data = np.sum(
                self._data_info["data"][slices], axis=summed_dimensions_indexes
            )
        except IndexError:
            raise PlotNDModelError("Invalid slices indices")

        data = np.squeeze(data)
        if data.ndim != 2:
            raise PlotNDModelError("Ill-formed data")

        if self._transpose:
            data = data.T

        self._image = self._figure.axes[0].imshow(
            data.T, interpolation=self._interpolation, origin="lower", cmap=self._cmap
        )

        extent = self.get_extent()
        self._image.set_extent(extent)

        self.set_aspect(self._aspect)
        self.set_x_axis_label(self._axis_info[self._x_index]["variable"])
        self.set_y_axis_label(self._axis_info[self._y_index]["variable"])
        self.set_norm(self._norm)
        self.update_colorbar()

    def _set_slices(self, slices):
        """Set a slice of the ND data.

        Args:
            slices (list): a list of 2-list where the first element is a slice of the ND array and the second element is a boolean specifying whether or not the array should be summed along the corresponding dimension
        """
        if len(slices) != self._data_info["dimension"]:
            raise PlotNDModelError("Invalid slices dimension")

        for sli, summed_dimensions in slices:
            if (sli == slice(None)) and summed_dimensions:
                raise PlotNDModelError(
                    "A summed dimension can not be one of the selected dimension to plot"
                )

        try:
            self._x_index, self._y_index = [
                i for i, s in enumerate(slices) if s[0] == slice(None)
            ]
        except (TypeError, ValueError):
            raise PlotNDModelError("Invalid number of selected dimensions")

        if self._transpose:
            self._x_index, self._y_index = self._y_index, self._x_index

        self._slices = slices

    def get_aspect(self):
        """Returns the aspect of the image.

        Returns:
            str: the aspect of the image
        """
        return self._aspect

    def get_axis_conversion_factors(self):
        """Returns the axis conversion factors.

        Returns:
            list of float: the axis conversion factors
        """
        return self._axis_conversion_factors

    def get_axis_current_units(self):
        """Returns the axis current units.

        Returns:
            list of str: the axis current units
        """
        return self._axis_current_units

    def get_axis_current_data(self):
        """Returns the axis data converted to the current unit.

        Returns:
            list of 1D-arrays: the axis current data
        """
        return [
            axis_info["data"] * conversion_factor
            for axis_info, conversion_factor in zip(
                self._axis_info, self._axis_conversion_factors
            )
        ]

    def get_axis_variables(self):
        """Returns the axis names.

        Returns:
            list of str: the axis names
        """
        return [axis_info["variable"] for axis_info in self._axis_info]

    def get_cmap(self):
        """Returns the current color map.

        Returns:
            str: the color map
        """
        return self._cmap

    def get_data(self):
        """Return the image data.

        Returns:
            2D-array: the image data
        """
        return self._image.get_array()

    def get_data_current_unit(self):
        """Returns the current unit of the ND data.

        Returns:
            str: the current unit of the ND data
        """
        return self._data_current_unit

    def get_data_shape(self):
        """Returns the shape of the ND data.

        Returns:
            tuple: the shape of the ND data
        """
        return self._data_info["shape"]

    def get_data_range(self):
        """Returns the range of the image.

        Returns:
            2-tuple of float: the range of the image
        """
        z_data = self._image.get_array()
        return (z_data.min(), z_data.max())

    def get_data_variable(self):
        """Returns the name of the ND data.

        Returns:
            str: the name of the ND data
        """
        return self._data_info["variable"]

    def get_extent(self):
        """Returns the extent of the image.

        Returns:
            4-tuple of float: the extent of the image
        """
        xmin = (
            self._axis_info[self._x_index]["data"][0]
            * self._axis_conversion_factors[self._x_index]
        )
        xmax = (
            self._axis_info[self._x_index]["data"][-1]
            * self._axis_conversion_factors[self._x_index]
        )
        ymin = (
            self._axis_info[self._y_index]["data"][0]
            * self._axis_conversion_factors[self._y_index]
        )
        ymax = (
            self._axis_info[self._y_index]["data"][-1]
            * self._axis_conversion_factors[self._y_index]
        )
        return [xmin, xmax, ymin, ymax]

    def get_figure_title(self):
        """Returns the figure title.

        Returns:
            str: the figure title
        """
        suptitle = self._figure._suptitle
        return suptitle.get_text() if suptitle is not None else ""

    def get_interpolation(self):
        """Returns the interpolation of the image.

        Returns:
            str: the interpolation of the image
        """
        return self._interpolation

    def get_n_dimensions(self):
        """Returns the number of dimensions of the ND data.

        Returns:
            int: the number of dimensions of the image
        """
        return self._data_info["dimension"]

    def get_norm(self):
        """Returns the norm used for normalizing the image.

        Returns:
            str: the norm
        """
        return self._norm

    def get_plot_title(self):
        """Returns the plot title.

        Returns:
            str: the plot title
        """
        return self._figure.axes[0].get_title()

    def get_show_colorbar(self):
        """Returns whether or not the color bar is showed.

        Returns:
            bool: True if the colorbar is showed, False otherwise
        """
        return self._show_colorbar

    def get_summed_dimensions(self):
        """Returns whether or not a dimension of the ND data should be summed.

        Returns:
            list of bool: the list specifying for each dimension whether it should be summed or not
        """
        return [summed_dimension for (_, summed_dimension) in self._slices]

    def get_transpose(self):
        """Returns whether or not the image should be transposed.

        Returns:
            bool: True if the image should be transposed, False otherwise
        """
        return self._transpose

    def get_x_axis_current_info(self):
        """Returns the information about the current X axis.

        Returns:
            dict: the information
        """
        info = {}
        info["variable"] = self._axis_info[self._x_index]["variable"]
        info["units"] = self._axis_current_units[self._x_index]
        info["data"] = (
            self._axis_info[self._x_index]["data"]
            * self._axis_conversion_factors[self._x_index]
        )
        return info

    def get_x_axis_current_unit(self):
        """Returns the X axis current unit.

        Returns:
            str: the X axis current unit
        """
        return self._axis_current_units[self._x_index]

    def get_x_axis_data(self):
        """Returns the X axis data converted to X axis unit.

        Returns:
            1D-array: the current X axis data
        """
        return (
            self._axis_info[self._x_index]["data"]
            * self._axis_conversion_factors[self._x_index]
        )

    def get_x_index(self):
        """Return the index of the current X axis.

        Returns:
            int: the index of the current X axis
        """
        return self._x_index

    def get_x_slice_info(self, index, sli):
        """Returns the information about a slice through X axis.

        Returns:
            2-tuple of dict: the X and Y informations about the slice
        """
        x_data = (
            self._axis_info[self._x_index]["data"]
            * self._axis_conversion_factors[self._x_index]
        )
        x_value = smart_round(x_data[index], sigfigs=3, output="std")

        y_data = (
            self._axis_info[self._y_index]["data"]
            * self._axis_conversion_factors[self._y_index]
        )

        z_data = self._image.get_array()
        try:
            if sli is not None:
                x_slice = np.sum(z_data[:, sli], axis=1)
                y_variable = f"{self._data_info['variable']} ([{sli.start},{sli.stop-1}]-integrated)"
            else:
                x_slice = z_data[:, index]
                y_variable = f"{self._data_info['variable']} ({self._axis_info[self._x_index]['variable']}={x_value})"
        except IndexError:
            raise PlotNDModelError("Invalid X slice")

        x_data_info = {
            "variable": self._axis_info[self._y_index]["variable"],
            "data": y_data,
            "units": self._axis_current_units[self._y_index],
            "axis": "index",
        }

        y_data_info = {
            "variable": y_variable,
            "data": x_slice,
            "units": self._data_current_unit,
            "axis": self._axis_info[self._y_index]["variable"],
        }

        return (x_data_info, y_data_info)

    def get_x_axis_variable(self):
        """Returns the X axis name.

        Returns:
            str: the X axis name
        """
        return self._axis_info[self._x_index]["variable"]

    def get_y_axis_current_info(self):
        """Returns the information about the current Y axis.

        Returns:
            dict: the information
        """
        info = {}
        info["variable"] = self._axis_info[self._y_index]["variable"]
        info["units"] = self._axis_current_units[self._y_index]
        info["data"] = (
            self._axis_info[self._y_index]["data"]
            * self._axis_conversion_factors[self._y_index]
        )
        return info

    def get_y_axis_current_unit(self):
        """Returns the Y axis current unit.

        Returns:
            str: the Y axis current unit
        """
        return self._axis_current_units[self._y_index]

    def get_y_axis_data(self):
        """Returns the Y axis data converted to Y axis unit.

        Returns:
            1D-array: the current Y axis data
        """
        return (
            self._axis_info[self._y_index]["data"]
            * self._axis_conversion_factors[self._y_index]
        )

    def get_y_index(self):
        """Return the index of the current Y axis.

        Returns:
            int: the index of the current Y axis
        """
        return self._y_index

    def get_y_slice_info(self, index, sli):
        """Returns the information about a slice through Y axis.

        Returns:
            2-tuple of dict: the X and Y informations about the slice
        """
        y_data = (
            self._axis_info[self._y_index]["data"]
            * self._axis_conversion_factors[self._y_index]
        )
        y_value = smart_round(y_data[index], sigfigs=3, output="std")

        x_data = (
            self._axis_info[self._x_index]["data"]
            * self._axis_conversion_factors[self._x_index]
        )

        z_data = self._image.get_array()
        try:
            if sli is not None:
                y_slice = np.sum(z_data[sli, :], axis=0)
                y_variable = f"{self._data_info['variable']} ([{sli.start},{sli.stop-1}]-integrated)"
            else:
                y_slice = z_data[index, :]
                y_variable = f"{self._data_info['variable']} ({self._axis_info[self._y_index]['variable']}={y_value})"
        except IndexError:
            raise PlotNDModelError("Invalid Y slice")

        x_data_info = {
            "variable": self._axis_info[self._x_index]["variable"],
            "data": x_data,
            "units": self._axis_current_units[self._x_index],
            "axis": "index",
        }

        y_data_info = {
            "variable": y_variable,
            "data": y_slice,
            "units": self._data_current_unit,
            "axis": self._axis_info[self._x_index]["variable"],
        }

        return (x_data_info, y_data_info)

    def get_y_axis_variable(self):
        """Returns the Y axis name.

        Returns:
            str: the Y axis name
        """
        return self._axis_info[self._y_index]["variable"]

    def reset_x_axis(self, min_x, max_x, unit):
        """Reset the X axis from min to max values expressed in provided unit.

        Args:
            min_x (float): the minimum value
            max_x (float): the maximum value
            unit (str): the unit
        """
        if min_x >= max_x:
            raise PlotNDModelError("Invalid min/max values")

        unit = unit.strip()
        if not unit:
            raise PlotNDModelError("No unit provided")

        try:
            _ = measure(1.0, unit, equivalent=True)
        except UnitError as e:
            raise PlotNDModelError(str(e))

        x_data = np.linspace(
            min_x, max_x, self._axis_info[self._x_index]["data"].size, True
        )

        self._axis_info[self._x_index]["data"] = x_data
        self._axis_info[self._x_index]["units"] = unit
        self._axis_current_units[self._x_index] = unit
        self._axis_conversion_factors[self._x_index] = 1.0

        extent = self.get_extent()
        self._image.set_extent(extent)

        self.set_x_axis_label(self._axis_info[self._x_index]["variable"])

        self._figure.canvas.draw()

        self.model_updated.emit()

    def reset_y_axis(self, min_y, max_y, unit):
        """Reset the Y axis from min to max values expressed in provided unit.

        Args:
            min_y (float): the minimum value
            max_y (float): the maximum value
            unit (str): the unit
        """
        if min_y >= max_y:
            raise PlotNDModelError("Invalid min/max values")

        unit = unit.strip()
        if not unit:
            raise PlotNDModelError("No unit provided")

        try:
            _ = measure(1.0, unit, equivalent=True)
        except UnitError as e:
            raise PlotNDModelError(str(e))

        y_data = np.linspace(
            min_y, max_y, self._axis_info[self._y_index]["data"].size, True
        )

        self._axis_info[self._y_index]["data"] = y_data
        self._axis_info[self._y_index]["units"] = unit
        self._axis_current_units[self._y_index] = unit
        self._axis_conversion_factors[self._y_index] = 1.0

        extent = self.get_extent()
        self._image.set_extent(extent)

        self.set_y_axis_label(self._axis_info[self._y_index]["variable"])

        self._figure.canvas.draw()

        self.model_updated.emit()

    def set_aspect(self, aspect):
        """Set the aspect of the image.

        Args:
            aspect (str): the aspect of the image
        """
        if aspect not in PlotNDModel.aspects:
            raise PlotNDModelError("Unknown aspect")

        self._aspect = aspect
        self._figure.axes[0].set_aspect(self._aspect)
        self._figure.canvas.draw()

    def set_cmap(self, cmap):
        """Set the colormap of the image.

        Args:
            cmap (str): the colormap of the image
        """
        if cmap not in PlotNDModel.cmaps:
            raise PlotNDModelError("Unknown color map")
        self._cmap = cmap
        self._image.set_cmap(cmap)
        self._figure.canvas.draw()

    def set_data_current_unit(self, z_unit):
        """Set the ND data unit.

        Args:
            z_unit (str): the ND data unit
        """
        try:
            initial_unit = self._data_info["units"]
            m = measure(1.0, initial_unit, equivalent=True)
            self._data_conversion_factor = m.toval(z_unit)
        except UnitError:
            raise PlotNDModelError(
                f"Units {initial_unit} and {z_unit} are incompatible"
            )
        else:
            self._data_current_unit = z_unit

            slices = tuple([sli for sli, _ in self._slices])
            summed_dimensions_indexes = tuple(
                [
                    i
                    for i, (_, summed_dimension) in enumerate(self._slices)
                    if summed_dimension
                ]
            )
            try:
                data = np.sum(
                    self._data_info["data"][slices], axis=summed_dimensions_indexes
                )
            except IndexError:
                raise PlotNDModelError("Invalid slices indices")

            data = np.squeeze(data)
            if data.ndim != 2:
                raise PlotNDModelError("Ill-formed data")

            if self._transpose:
                scaled_data = scaled_data.T

            scaled_data = data * self._data_conversion_factor
            self._image.set_data(scaled_data.T)
            self._image.set_clim(vmin=scaled_data.min(), vmax=scaled_data.max())
            self.set_data_label(self._data_info["variable"])
            self.update_colorbar()
            self.model_updated.emit()

    def set_data_label(self, label):
        """Set the ND data label.

        Args:
            label (str): the new label
        """
        self._data_info["variable"] = label
        self.update_colorbar()
        self._figure.canvas.draw()
        self.z_variable_updated.emit(self._data_info["variable"])

    def set_data_range(self, min_z, max_z):
        """Set the ND data range.

        Args:
            min_z (float): the minimum value
            max_z (float): the maximum value
        """
        if min_z >= max_z:
            raise PlotNDModelError("Invalid min/max values")

        self._image.set_clim(vmin=min_z, vmax=max_z)
        self._figure.canvas.draw()

    def set_figure_title(self, title):
        """Set the title of the figure.

        Args:
            title (str): the new title
        """
        self._figure.suptitle(title)
        self._figure.canvas.draw()

    def set_interpolation(self, interpolation):
        """Set the interpolation of the image.

        Args:
            interpolation (str): the interpolation
        """
        if interpolation not in PlotNDModel.interpolations:
            raise PlotNDModelError("Unknown interpolation")
        self._interpolation = interpolation
        self._image.set_interpolation(interpolation)
        self._figure.canvas.draw()

    def set_norm(self, norm):
        """Set the norm of the image.

        Args:
            norm (str): the norm
        """
        if norm not in PlotNDModel.normalizers:
            raise PlotNDModelError("Unknwon norm")

        data = self._image.get_array()
        if norm == "log" and data.min() <= 0.0:
            print("Data contains negative value", ["main", "popup"], "error")
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
        self.update_colorbar()

    def set_plot_title(self, title):
        """Set the title of the plot.

        Args:
            title (str): the new title
        """
        self._figure.axes[0].set_title(title)
        self._figure.canvas.draw()

    def set_show_colorbar(self, show_colorbar):
        """Set whether or not the colorbar should be showed.

        Args:
            show_colorbar (bool): True if the colorbar should be showed, False otherwise
        """
        self._show_colorbar = show_colorbar
        self.update_colorbar()

    def set_x_axis_label(self, label):
        """Set the X axis label.

        Args:
            label (str): the new label
        """
        self._axis_info[self._x_index]["variable"] = label
        self._figure.axes[0].set_xlabel(
            f"{label} ({self._axis_current_units[self._x_index]})"
        )
        self._figure.canvas.draw()
        self.x_variable_updated.emit(self._axis_info[self._x_index]["variable"])

    def set_x_axis_unit(self, x_unit):
        """Set the X axis unit.

        Args:
            unit (str): the X axis unit
        """
        try:
            initial_unit = self._axis_info[self._x_index]["units"]
            m = measure(1.0, initial_unit, equivalent=True)
            self._axis_conversion_factors[self._x_index] = m.toval(x_unit)
        except UnitError:
            raise PlotNDModelError(
                f"Units {initial_unit} and {x_unit} are incompatible"
            )
        else:
            self._axis_current_units[self._x_index] = x_unit
            extent = self.get_extent()
            self._image.set_extent(extent)
            self.set_x_axis_label(self._axis_info[self._x_index]["variable"])
            self.model_updated.emit()

    def set_x_integration_box(self, min_x, max_x):
        """Draw the X integration box.

        Args:
            min_x (int): the index of the minimum X
            max_x (int): the index of the maximum X
        """
        if self._x_integration_box is not None:
            self._x_integration_box.remove()

        origin = (min_x, 0)
        width = max_x - min_x
        height = self._axis_info[self._y_index]["shape"][0]
        x_integration_box = Rectangle(
            origin,
            width,
            height,
            facecolor=(1, 0, 0, 0.5),
            edgecolor=(0, 0, 0, 1),
            fill=True,
            linewidth=2,
        )
        self._x_integration_box = self._figure.axes[0].add_patch(x_integration_box)
        self._figure.canvas.draw()

    def set_x_slicer(self, row):
        """Draw the slicer line for X axis slice.

        Args:
            row (int) the index of the X axis slicer
        """
        if self._x_slicer is not None:
            self._x_slicer.remove()

        x_data = (
            self._axis_info[self._x_index]["data"]
            * self._axis_conversion_factors[self._x_index]
        )
        try:
            self._x_slicer = self._figure.axes[0].axvline(
                x=x_data[row], color=(1, 0, 0), linewidth=3
            )
        except IndexError:
            raise PlotNDModelError("Invalid X axis index")

        extent = self.get_extent()
        self._image.set_extent(extent)

        self._figure.canvas.draw()

    def set_y_axis_label(self, label):
        """Set the Y axis label.

        Args:
            label (str): the new label
        """
        self._axis_info[self._y_index]["variable"] = label
        self._figure.axes[0].set_ylabel(
            f"{label} ({self._axis_current_units[self._y_index]})"
        )
        self._figure.canvas.draw()
        self.y_variable_updated.emit(self._axis_info[self._y_index]["variable"])

    def set_y_integration_box(self, min_y, max_y):
        """Draw the Y integration box.

        Args:
            min_y (int): the index of the minimum Y
            max_y (int): the index of the maximum Y
        """
        if self._y_integration_box is not None:
            self._y_integration_box.remove()

        origin = (0, min_y)
        width = self._axis_info[self._x_index]["shape"][0]
        height = max_y - min_y
        y_integration_box = Rectangle(
            origin,
            width,
            height,
            facecolor=(0, 1, 0, 0.5),
            edgecolor=(0, 0, 0, 1),
            fill=True,
            linewidth=2,
        )
        self._y_integration_box = self._figure.axes[0].add_patch(y_integration_box)
        self._figure.canvas.draw()

    def set_y_slicer(self, column):
        """Draw the slicer line for Y axis slice.

        Args:
            column (int) the index of the Y axis slicer
        """
        if self._y_slicer is not None:
            self._y_slicer.remove()

        y_data = (
            self._axis_info[self._y_index]["data"]
            * self._axis_conversion_factors[self._y_index]
        )
        try:
            self._y_slicer = self._figure.axes[0].axhline(
                y=y_data[column], color=(0, 1, 0), linewidth=3
            )
        except IndexError:
            raise PlotNDModelError("Invalid Y axis index")

        extent = self.get_extent()
        self._image.set_extent(extent)

        self._figure.canvas.draw()

    def set_y_axis_unit(self, y_unit):
        """Set the Y axis unit.

        Args:
            unit (str): the Y axis unit
        """
        try:
            initial_unit = self._axis_info[self._y_index]["units"]
            m = measure(1.0, initial_unit, equivalent=True)
            self._axis_conversion_factors[self._y_index] = m.toval(y_unit)
        except UnitError:
            raise PlotNDModelError(
                f"Units {initial_unit} and {y_unit} are incompatible"
            )
        else:
            self._axis_current_units[self._y_index] = y_unit
            extent = self.get_extent()
            self._image.set_extent(extent)
            self.set_y_axis_label(self._axis_info[self._y_index]["variable"])
            self.model_updated.emit()

    def unset_x_integration_box(self):
        """Unset the integration box."""
        if self._x_integration_box is not None:
            self._x_integration_box.remove()
            self._x_integration_box = None
            self._figure.canvas.draw()

    def unset_x_slicer(self):
        """Unset the X axis slice line."""
        if self._x_slicer is not None:
            self._x_slicer.remove()
            self._x_slicer = None
            self._figure.canvas.draw()

    def unset_y_integration_box(self):
        """Unset the integration box."""
        if self._y_integration_box is not None:
            self._y_integration_box.remove()
            self._y_integration_box = None
            self._figure.canvas.draw()

    def unset_y_slicer(self):
        """Unset the X axis slice line."""
        if self._y_slicer is not None:
            self._y_slicer.remove()
            self._y_slicer = None
            self._figure.canvas.draw()

    def update_colorbar(self):
        """Update the colorbar."""
        if self._colorbar is not None:
            self._colorbar.remove()
            self._colorbar = None

        if self._show_colorbar:
            self._colorbar = self._figure.colorbar(self._image)
            self._colorbar.ax.get_yaxis().labelpad = 15
            self._colorbar.ax.set_ylabel(
                f"{self._data_info['variable']} ({self._data_current_unit})",
                rotation=270,
            )

        self._figure.canvas.draw()

    def update_model(self, slices, transpose):
        """Update the model. This will produce a new image of the ND data for given slices and/or summed dimensions.

        Args:
            slices (list of 2-list): the information about selected dimensions, slices and/or summed dimensions.
            Nested list of 2-list where the first element is a slice of the ND data and the second element a boolean
            indicating whether or not the data should be summed along the corresponding dimension.
            transpose (bool): True if the data should be transposed, False otherwise
        """
        self._transpose = transpose

        self._set_slices(slices)

        self._plot()

        self.model_updated.emit()

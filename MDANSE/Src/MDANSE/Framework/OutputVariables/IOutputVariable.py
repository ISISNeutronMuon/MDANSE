#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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

import collections
from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

import numpy as np
import numpy.typing as npt

from MDANSE.Core.RegisterFactory import RegisterFactory
from MDANSE.Framework.Formats.IFormat import IFormat
from MDANSE.IO.IOUtils import UCDict

if TYPE_CHECKING:
    from collections.abc import Sequence


class OutputVariableError(Exception):
    pass


class OutputData(collections.OrderedDict):
    def add(self, dataName, dataType, data, **kwargs):
        self[dataName] = IOutputVariable.create(dataType, data, dataName, **kwargs)

    def write(self, basename, formats, header=None, inputs=None):
        for fmt in formats:
            temp_format = IFormat.create(fmt)
            self.data_object = temp_format.write(basename, self, header, inputs)


class IOutputVariable(np.ndarray, RegisterFactory):
    """
    Defines a MDANSE output variable.

    A MDANSE output variable is defined as s subclass of Numpy array that stores additional attributes.
    Those extra attributes will be contain information necessary for the the MDANSE plotter.
    """

    registry: ClassVar[UCDict[str, type[IOutputVariable]]] = UCDict()

    def __new__(
        cls,
        value: tuple[int, ...] | npt.ArrayLike,
        varname: str,
        axis: str | Sequence[str] | None = None,
        units: str = "unitless",
        *,
        main_result: bool = False,
        partial_result: bool = False,
        dtype: type = np.float64,
    ):
        """Instantiate a new MDANSE output variable.

        Parameters
        ----------
        value : Union[Tuple[int, ...], npt.ArrayLike]
            If value is tuple create empty array with those dimensions.

            If value is ArrayLike interpret as array data.
        varname : str
            Variable name for reference.
        axis : Union[str, Sequence[str], None]
            List of axis labels. If str split on ``|``.
        units : str
            Units of main data.
        main_result : bool
            Whether the data are the main result of a calculation.
        partial_result : bool
            Whether the data are a complete calculation.

        Raises
        ------
        OutputVariableError
            If dimensions of provided data do not align with those of object.
        """
        if isinstance(value, np.ndarray):
            value = np.array(value, dtype=value.dtype)
        elif isinstance(value, tuple):
            value = np.zeros(value, dtype=dtype)
        else:
            value = np.array(list(value), dtype=dtype)

        if isinstance(axis, str):
            axis = axis.split("|")
        elif axis is None:
            axis = ["index"] * value.ndim

        if value.ndim != cls._nDimensions:
            raise OutputVariableError(
                f"Invalid number of dimensions ({value.ndim}) for an output variable ({varname}) of type {cls.__name__!r}"
            )

        if len(axis) != cls._nDimensions:
            raise OutputVariableError(
                f"Invalid number of dimensions ({len(axis)}) for an axis label ({', '.join(axis)}) of type {cls.__name__!r}"
            )

        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        obj = np.asarray(value).view(cls)

        # The name of the output variable.
        obj.varname = varname

        obj.units = units

        obj.axis = "|".join(axis)

        obj.scaling_factor = 1.0

        data_tags = []
        if main_result:
            data_tags.append("main")
        if partial_result:
            data_tags.append("partial")

        obj.tags = ",".join(data_tags)

        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return

        self.varname = getattr(obj, "varname", None)

        self.axis = getattr(obj, "axis", ())

        self.units = getattr(obj, "units", "unitless")

    def info(self):
        return f"""\
# variable name: {self.varname}
# \ttype: {self.__class__.__name__}
# \taxis: {self.axis!s}
# \tunits: {self.units}"""

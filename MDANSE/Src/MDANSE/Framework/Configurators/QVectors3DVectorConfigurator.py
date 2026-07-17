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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from .VectorConfigurator import VectorConfigurator


@IConfigurator.register("QVectors3DVectorConfigurator")
class QVectors3DVectorConfigurator(VectorConfigurator):
    """Inputs a vector given as 3 floating point numbers or a string to
    specify that this vector will be a cross production of two others."""

    _default = [1.0, 0.0, 0.0]

    def __init__(
        self,
        name: str,
        other_vec_1: str,
        other_vec_2: str,
        valueType: type = int,
        normalize: bool = False,
        notNull: bool = False,
        dimension: int = 3,
        mini: int | float | None = None,
        maxi: int | float | None = None,
        **kwargs,
    ):
        """
        Initializes the configurator.

        Parameters
        ----------
        name : str
            The name of the configurator as it will appear in the configuration.
        other_vec_1 : str
            The name of one of the other vector that this vector could
            be a cross product of.
        other_vec_2 : str
            The name of one of the other vector that this vector could
            be a cross product of.
        valueType : type
            The numeric type for the vector, `int` or `float`.
        normalize : bool
            if True the vector will be normalized.
        notNull : bool
            If True, the vector must be non-null.
        dimension : int
            The dimension of the vector.
        mini : int or float or None
            The minimum value of the vectors values.
        maxi : int or float or None
            The maximum value of the vectors values.
        """
        super().__init__(
            name, valueType, normalize, notNull, dimension, mini, maxi, **kwargs
        )

        self.other_vec_1 = other_vec_1
        self.other_vec_2 = other_vec_2
        self.other_vecs = {other_vec_1, other_vec_2}

    def configure(self, value: list | tuple | str):  # noqa: PLR0911
        """
        Configure a vector.

        Parameters
        ----------
        value : list or tuple
            The vector components.
        """
        if isinstance(value, list | tuple):
            self["cross_product"] = False
            super().configure(value)
            return

        if not isinstance(value, str):
            self.error_status = "Invalid input type should be list, tuple, or str."
            return

        if not self.update_needed(value):
            return

        self._original_input = value

        cross_str = value.split(" ")

        if len(cross_str) != 3:
            self.error_status = (
                "Q vector basis option not valid should be something like 'q1 x q2'."
            )
            return

        q1, x, q2 = cross_str
        if q1 not in self.other_vecs or q2 not in self.other_vecs:
            self.error_status = (
                f"Q vectors should be either {self.other_vec_1} or {self.other_vec_2}"
            )
            return

        if q1 == q2:
            self.error_status = (
                "Q vector basis should not be a cross product of the same basis vector."
            )
            return

        if x not in {"x", "X"}:
            self.error_status = f"Unrecognised operation: {x}"
            return

        self["vector"] = None
        self["cross_product"] = True
        self["value"] = value

        self.error_status = "OK"

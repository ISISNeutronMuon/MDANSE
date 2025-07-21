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
from typing import Literal

import numpy as np
import numpy.typing as npt

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Mathematics.LinearAlgebra import Vector


class VectorList(IConfigurator):
    """
    This configurator allows a user to input many vectors.

    Parameters
    ----------
    name : str
        The name of the configurator as it will appear in the configuration.
    valueType : Literal[float, int]
        The numeric type for the vectors.
    normalize : bool
        Whether the vectors will be normalized.
    notNull : bool
        Whether zero-length vectors are allowed.
    dimension : int
        Number of dimensions in each vector.
    """

    _default = [[1.0, 0.0, 0.0]]

    def __init__(
        self,
        name: str,
        valueType: type[int] | type[float] = float,
        normalize: bool = False,
        notNull: bool = False,
        dimension: int = 3,
        wildcard: str | None = None,
        **kwargs,
    ):
        IConfigurator.__init__(self, name, **kwargs)

        self._valueType = valueType
        self._normalize = normalize
        self._notNull = notNull
        self._dimension = dimension

        if wildcard is not None:
            self._wildcard = wildcard


    def configure(self, value: npt.ArrayLike) -> None:
        """Configure a vector.

        Parameters
        ----------
        value : ArrayLike
            The vector components.
        """
        self._original_input = value

        if not isinstance(value, npt.ArrayLike):
            self.error_status = "Invalid input type"
            return

        try:
            vector = np.array(value, dtype=self._valueType)
        except Exception:
            self.error_status = "Invalid vector."
            return

        if self._normalize:
            vector = np.linalg.vector_norm(axis=1)

        if self._notNull and any(np.allclose(vec, 0.0) for vec in vector):
            self.error_status = "A vector is null"
            return

        self["vector"] = vector
        self["value"] = vector

        self.error_status = "OK"

    @property
    def wildcard(self) -> str:
        """
        Returns the wildcard used to filter the input file.

        Returns
        -------
        str
            the wildcard used to filter the input file.
        """

        return self._wildcard

    @property
    def valueType(self) -> type[float] | type[int]:
        """Values type of the vector.

        Returns
        -------
        type
            The values type of the range.
        """

        return self._valueType

    @property
    def normalize(self) -> bool:
        """Whether or not the configured vector will be normalized.

        Returns
        -------
        bool
            Whether the vector will be normalized.
        """

        return self._normalize

    @property
    def notNull(self) -> bool:
        """Whether or not a null vector is accepted.

        Returns
        -------
        bool
            True if a null vector is not accepted, False otherwise.
        """

        return self._notNull

    @property
    def dimension(self) -> int:
        """Get the dimension of the vector.

        Returns
        -------
        int
            the dimension of the vector.
        """

        return self._dimension

    def get_information(self) -> str:
        """Returns string information about this configurator.

        Returns
        -------
        str
            the information about this configurator.
        """
        if "value" not in self:
            return "Not configured yet\n"

        return f"Value: {self['value']!r}\n"

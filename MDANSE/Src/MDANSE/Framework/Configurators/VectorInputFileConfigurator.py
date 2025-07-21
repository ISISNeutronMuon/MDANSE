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
from pathlib import Path
from typing import Union
import numpy as np

from MDANSE.Framework.Configurators.InputFileConfigurator import InputFileConfigurator


class VectorInputFileConfigurator(InputFileConfigurator):
    """
    This configurator allows to input a list of vectors from a file.
    """

    def __init__(
        self,
        name: str,
        wildcard: str = "All files (*)",
        **kwargs,
    ):
        """Configure a list of vectors.

        Parameters
        ----------
        name : str
            Name of variable.
        wildcard : str
            Files to match.
        """

        # The base class constructor.
        super().__init__(name, **kwargs)

        self._wildcard = wildcard

    def configure(self, value: Union[Path, str]):
        """Configure vector list file.

        Parameters
        ----------
        value : Union[Path, str]
            File to open.
        """
        self._original_input = value

        super().configure(value)

        if not self._valid:
            return

        try:
            self["vectors"] = np.loadtxt(self["value"], dtype=float)
        except Exception:
            self.error_status = f"Numpy could not load file {self['value']!r}"
            return

        self.error_status = "OK"


    @property
    def wildcard(self):
        """
        Returns the wildcard used to filter the input file.

        :return: the wildcard used to filter the input file.
        :rtype: str
        """

        return self._wildcard

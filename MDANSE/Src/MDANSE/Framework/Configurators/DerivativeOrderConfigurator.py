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
from typing import Optional

from MDANSE.Framework.Configurators.IntegerConfigurator import IntegerConfigurator


class DerivativeOrderConfigurator(IntegerConfigurator):
    """Configurator used when numerical derivatives are required."""

    _default = 3

    def __init__(self, name: str, **kwargs) -> None:
        """
        Parameters
        ----------
        name : str
            The name of the configurator as it will appear in the
            configuration.
        """
        IntegerConfigurator.__init__(self, name, **kwargs)

    def configure(self, value: Optional[int]) -> None:
        """Configure the input derivative order.

        Parameters
        ----------
        value : int or None
            The numerical derivative order to use.
        """
        self._original_input = value
        if value is None:
            value = self._default

        IntegerConfigurator.configure(self, value)

        if value <= 0 or value > 5:
            self.error_status = (
                f"Use an derivative order less than or equal to zero or "
                f"greater than 5 is not implemented."
            )
            return

        self.error_status = "OK"

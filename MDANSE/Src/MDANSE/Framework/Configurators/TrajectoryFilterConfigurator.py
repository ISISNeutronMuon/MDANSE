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

import json

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Mathematics.Signal import (
    DEFAULT_FILTER,
    filter_default_attributes,
    filter_description_string,
)


class TrajectoryFilterConfigurator(IConfigurator):
    """Defines the filter that will be applied to atom positions.

    The filters are provided by the scipy.signal library.

    Attributes
    ----------
    _default : str
        The defaults selection setting.

    """

    _default_filter = DEFAULT_FILTER

    _settings = filter_default_attributes()

    @classmethod
    def get_default(cls) -> str:
        """Return the default filter string.

        Returns
        -------
        str
            A string representation of the default filter settings dictionary

        """
        return cls._default

    _default = filter_description_string()

    def configure(self, value: str):
        """Configure an input value.

        Parameters
        ----------
        value : str
            The selection setting in a json readable format.

        """
        if not self.update_needed(value):
            return

        self._settings = value

        try:
            dict_value = json.loads(value)

            if not {"filter", "attributes"} <= dict_value.keys():
                self.error_status = f"The dictionary \n{dict_value}\n does not contain the expected keys"

        except (TypeError, ValueError):
            self.error_status = f"Value \n{value}\n in {self} is not of correct format (expected JSON string)"

        self.error_status = "OK"
        self["value"] = self._settings

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

from MDANSE.Framework.AtomMapping import check_mapping_valid, fill_remaining_labels
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class AtomMappingConfigurator(IConfigurator):
    """The atom mapping configurator for trajectory converters.

    It allows the user to verify and potentially change the way
    atom types from an MD trajectory will be converted to the
    chemical elements used by MDANSE.

    Attributes
    ----------
    _default : dict
        The default atom map setting JSON string.

    """

    _default = "{}"

    def configure(self, value) -> None:
        """
        Parameters
        ----------
        value : str
            The atom map setting JSON string.
        """
        if not self.update_needed(value):
            return

        if value is None:
            value = self._default
        self._original_input = value

        if not isinstance(value, str):
            self.error_status = "Invalid input value."
            return

        try:
            value = json.loads(value)
        except json.decoder.JSONDecodeError:
            self.error_status = "Unable to load JSON string."
            return

        file_configurator = self.configurable[self.dependencies["input_file"]]
        if not file_configurator.valid:
            self.error_status = "Input file not selected or valid."
            return

        labels = file_configurator.labels
        try:
            fill_remaining_labels(value, labels)
        except AttributeError:
            self.error_status = "Unable to map all atoms."
            return

        if not check_mapping_valid(value, labels):
            self.error_status = "Atom mapping is not valid."
            return

        self.error_status = "OK"
        self["value"] = value

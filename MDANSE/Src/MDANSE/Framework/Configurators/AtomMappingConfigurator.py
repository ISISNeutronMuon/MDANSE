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
import json

from MDANSE.Framework.AtomMapping import fill_remaining_labels, check_mapping_valid
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class AtomMappingConfigurator(IConfigurator):
    """The atom mapping configurator.

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

        file_configurator = self._configurable[self._dependencies["input_file"]]
        if not file_configurator._valid:
            self.error_status = "Input file not selected."
            return

        labels = file_configurator.get_atom_labels()
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

    def get_information(self) -> str:
        """Returns some information on the atom mapping configurator.

        Returns
        -------
        str
            The atom map JSON string.
        """
        if "value" not in self:
            return "Not configured yet\n"

        return str(self["value"]) + "\n"

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

from collections import Counter, defaultdict
from json import JSONDecodeError

from MDANSE.Framework.AtomSelector.selector import ReusableSelection
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


class AtomSelectionConfigurator(IConfigurator):
    """Selects atoms in trajectory based on the input string.

    This configurator allows the selection of a specific set of
    atoms on which the analysis will be performed. The defaults setting
    selects all atoms.

    Attributes
    ----------
    _default : str
        The defaults selection setting.

    """

    _default = "{}"

    def configure(self, value: str) -> None:
        """Configure an input value.

        Parameters
        ----------
        value : str
            The selection setting in a json readable format.

        """
        if not self.update_needed(value):
            return

        self._original_input = value

        trajConfig = self.configurable[self.dependencies["trajectory"]]
        self.selector = ReusableSelection()

        if value is None:
            value = self._default

        if not isinstance(value, str):
            self.error_status = "Invalid input value."
            return

        try:
            self.selector.load_from_json(value)
        except JSONDecodeError:
            self.error_status = "Invalid JSON string."
            return

        self["value"] = value

        self.selector.load_from_json(value)
        indices = self.selector.select_in_trajectory(trajConfig["instance"])

        self["flatten_indices"] = sorted(indices)
        self["selection_length"] = len(self["flatten_indices"])
        if self["selection_length"] == 0:
            self.error_status = "The atom selection is empty."
            return
        self.error_status = "OK"

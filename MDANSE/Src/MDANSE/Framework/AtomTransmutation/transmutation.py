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
from typing import Union

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Framework.AtomSelector import Selector


class AtomTransmuter:
    """The atom transmuter setting generator. Updates an atom
    transmutation setting with applications of the apply_transmutation
    method with a selection setting and symbol."""

    def __init__(self, system: ChemicalSystem) -> None:
        """
        Parameters
        ----------
        system : ChemicalSystem
            The chemical system object.
        """
        self.selector = Selector(system)
        self._original_map = {}
        for at in system.atom_list:
            self._original_map[at.index] = at.symbol
        self._new_map = {}

    def apply_transmutation(
        self, selection_dict: dict[str, Union[bool, dict]], symbol: str
    ) -> None:
        """With the selection dictionary update the transmutation map.

        Parameters
        ----------
        selection_dict: dict[str, Union[bool, dict]]
            The selection setting to get the indexes to map the inputted
            symbol.
        symbol: str
            The element to map the selected atoms to.
        """
        if symbol not in ATOMS_DATABASE:
            raise ValueError(f"{symbol} not found in the atom database.")

        self.selector.update_settings(selection_dict, reset_first=True)
        for idx in self.selector.get_idxs():
            self._new_map[idx] = symbol

    def get_setting(self) -> dict[int, str]:
        """
        Returns
        -------
        dict[int, str]
            The minimal transmutation setting.
        """
        minimal_map = {}
        for k, v in self._original_map.items():
            if k not in self._new_map:
                continue
            if self._new_map[k] != v:
                minimal_map[k] = self._new_map[k]
        return minimal_map

    def get_json_setting(self) -> str:
        """
        Returns
        -------
        str
            A json string of the minimal transmutation setting.
        """
        return json.dumps(self.get_setting())

    def reset_setting(self) -> None:
        """Resets the transmutation setting."""
        self._new_map = {}

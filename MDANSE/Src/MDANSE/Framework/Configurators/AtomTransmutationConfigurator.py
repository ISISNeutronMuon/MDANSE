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

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
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
        """With the selection dictionary update selector and then
        update the transmutation map.

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


class AtomTransmutationConfigurator(IConfigurator):
    """This configurator allows to define a set of atoms to be
    transmuted to a given chemical element.

    For some analysis it can be necessary to change the nature of the
    chemical element of a given part of the system to have results
    closer to experience. A good example is to change some hydrogen
    atoms to deuterium in order to fit with experiments where
    deuteration experiments have been performed for improving the
    contrast and having a better access to the dynamics of a specific
    part of the molecular system.

    Attributes
    ----------
    _default : str
        The defaults transmutation setting.
    """

    _default = "{}"

    def configure(self, value: str):
        """Configure an input value.

        Parameters
        ----------
        value : str
            The transmutation setting in a json readable format.
        """

        self["value"] = value
        self._original_input = value

        # if the input value is None, do not perform any transmutation
        if value is None or value == "":
            return

        if not isinstance(value, str):
            self.error_status = "Invalid input value."
            return

        try:
            value = json.loads(value)
        except json.decoder.JSONDecodeError:
            self.error_status = "Unable to load JSON string."
            return

        traj_config = self._configurable[self._dependencies["trajectory"]]
        system = traj_config["instance"].chemical_system
        idxs = [at.index for at in system.atom_list]

        self._nTransmutatedAtoms = 0
        for idx, element in value.items():

            try:
                idx = int(idx)
            except ValueError:
                self.error_status = "Key of transmutation map should be castable to int"
                return

            if idx not in idxs:
                self.error_status = "Inputted setting not valid - atom index not found in the current system."
                return

            if element not in ATOMS_DATABASE:
                self.error_status = (
                    f"the element {element} is not registered in the database"
                )
                return

            self.transmutate(idx, element)

        atomSelConfigurator = self._configurable[self._dependencies["atom_selection"]]
        atomSelConfigurator["unique_names"] = sorted(set(atomSelConfigurator["names"]))
        atomSelConfigurator["masses"] = [
            [ATOMS_DATABASE.get_atom_property(n, "atomic_weight")]
            for n in atomSelConfigurator["names"]
        ]
        self.error_status = "OK"

    def transmutate(self, idx: int, element: str) -> None:
        """Transmute the atom index to the chosen element.

        Parameters
        ----------
        idx : int
            The index of the atom to transmute.
        element : str
            The element to transmute the atom to.
        """
        atomSelConfigurator = self._configurable[self._dependencies["atom_selection"]]

        try:
            idxInSelection = atomSelConfigurator["flatten_indexes"].index(idx)
        except ValueError:
            pass
        else:
            atomSelConfigurator["names"][idxInSelection] = element
            atomSelConfigurator["elements"][idxInSelection] = [element]
            self._nTransmutatedAtoms += 1

    def get_information(self) -> str:
        """
        Returns
        -------
        str
            Some information on the atoms selected for being transmuted.
        """
        if "value" not in self:
            return "Not configured yet"

        if self["value"] is None:
            return "No atoms selected for transmutation\n"

        return "Number of transmuted atoms:%d\n" % self._nTransmutatedAtoms

    def get_transmuter(self) -> AtomTransmuter:
        """
        Returns
        -------
        AtomTransmuter
            The atom transmuter object initialised with the trajectories
            chemical system.
        """
        traj_config = self._configurable[self._dependencies["trajectory"]]
        transmuter = AtomTransmuter(traj_config["instance"].chemical_system)
        return transmuter

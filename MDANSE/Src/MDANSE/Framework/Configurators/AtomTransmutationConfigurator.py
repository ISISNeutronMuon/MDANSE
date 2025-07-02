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
from MDANSE.Framework.AtomSelector.selector import ReusableSelection
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class AtomTransmuter:
    """The atom transmuter setting generator. Updates an atom
    transmutation setting with applications of the apply_transmutation
    method with a selection setting and symbol."""

    def __init__(self, trajectory: Trajectory) -> None:
        """
        Parameters
        ----------
        system : ChemicalSystem
            The chemical system object.
        """
        self.selector = ReusableSelection()
        self._original_map = {}
        for number, element in enumerate(trajectory.chemical_system.atom_list):
            self._original_map[number] = element
        self._new_map = {}
        self._current_trajectory = trajectory

    def apply_transmutation(self, selection_string: str, symbol: str) -> None:
        """With the selection dictionary update selector and then
        update the transmutation map.

        Parameters
        ----------
        selection_string: str
            the JSON string of the selection operation to use.
        symbol: str
            The element to map the selected atoms to.
        """
        if symbol not in ATOMS_DATABASE:
            raise ValueError(f"{symbol} not found in the atom database.")

        self.selector.load_from_json(selection_string)
        indices = self.selector.select_in_trajectory(self._current_trajectory)
        self._new_map.update(dict.fromkeys(indices, symbol))

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
        self.selector.reset()


class AtomTransmutationConfigurator(IConfigurator):
    """Assigns different chemical elements to selected atoms.

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

        traj_config = self.configurable[self.dependencies["trajectory"]]
        system = traj_config["instance"].chemical_system
        idxs = system._atom_indices

        self._nTransmutedAtoms = 0

        try:
            value = {int(idx): element for idx, element in value.items()}
        except ValueError:
            self.error_status = "Key of transmutation map should be castable to int"
            return

        for idx, element in value.items():
            if idx not in idxs:
                self.error_status = "Inputted setting not valid - atom index not found in the current system."
                return

            if (element not in traj_config["instance"].atoms_in_database) and (
                element not in ATOMS_DATABASE.atoms
            ):
                self.error_status = (
                    f"the element {element} is not registered in the database"
                )
                return

            self.transmute(idx, element)

        atomSelConfigurator = self.configurable[self.dependencies["atom_selection"]]
        atomSelConfigurator["unique_names"] = sorted(set(atomSelConfigurator["names"]))
        self.error_status = "OK"

    def transmute(self, idx: int, element: str) -> None:
        """Transmute the atom index to the chosen element.

        Parameters
        ----------
        idx : int
            The index of the atom to transmute.
        element : str
            The element to transmute the atom to.
        """
        atomSelConfigurator = self.configurable[self.dependencies["atom_selection"]]

        try:
            idxInSelection = atomSelConfigurator["flatten_indices"].index(idx)
        except ValueError:
            pass
        else:
            if (
                "grouping_level" in self.dependencies
                and "atom"
                != self.configurable[self.dependencies["grouping_level"]]["level"]
            ):
                group_config = self.configurable[self.dependencies["grouping_level"]]
                prev_element = atomSelConfigurator["elements"][idxInSelection][0]
                group_name = atomSelConfigurator["names"][idxInSelection][
                    : -(len(prev_element) + 1)
                ]
                atomSelConfigurator["names"][idxInSelection] = (
                    group_name + "_" + element
                )
                group_config["group_elements"][group_name].remove(prev_element)
                group_config["group_elements"][group_name].append(element)
            else:
                atomSelConfigurator["names"][idxInSelection] = element
            atomSelConfigurator["elements"][idxInSelection] = [element]
            traj_config = self.configurable[self.dependencies["trajectory"]]
            atomSelConfigurator["masses"][idxInSelection] = [
                traj_config["instance"].get_atom_property(element, "atomic_weight")
            ]
            self._nTransmutedAtoms += 1

    def get_transmuter(self) -> AtomTransmuter:
        """
        Returns
        -------
        AtomTransmuter
            The atom transmuter object initialised with the trajectories
            chemical system.
        """
        traj_config = self.configurable[self.dependencies["trajectory"]]
        transmuter = AtomTransmuter(traj_config["instance"])
        return transmuter

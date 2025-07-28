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
from typing import Union

import numpy as np

from MDANSE.Framework.AtomSelector.selector import ReusableSelection
from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.MolecularDynamics.Trajectory import Trajectory


class PartialChargeMapper:
    """The partial charge mapper. Updates an atom partial charge map
    with applications of the update_charges method with a selection
    setting and partial charge."""

    def __init__(self, trajectory: Trajectory) -> None:
        """
        Parameters
        ----------
        system : ChemicalSystem
            The chemical system object.
        """
        system = trajectory.chemical_system
        self._traj_charges = trajectory.charges(0)[:]
        self._current_trajectory = trajectory
        self._original_map = {}
        for at_num, at in enumerate(system.atom_list):
            try:
                self._original_map[at_num] = self._traj_charges[at_num]
            except Exception:
                self._original_map[at_num] = 0.0
        self._new_map = {}

    def update_charges(self, selection_string: str, charge: float) -> None:
        """With the selection dictionary update the selector and then
        update the partial charge map.

        Parameters
        ----------
        selection_dict: dict[str, Union[bool, dict]]
            The selection setting to get the indices to map the input
            partial charge.
        charge: float
            The partial charge to map the selected atoms to.
        """
        selector = ReusableSelection()
        selector.load_from_json(selection_string)
        indices = selector.select_in_trajectory(self._current_trajectory)
        for idx in indices:
            self._new_map[idx] = charge

    def get_full_setting(self) -> dict[int, float]:
        """
        Returns
        -------
        dict[int, float]
            The full partial charge setting.
        """
        full_map = {}
        for k, v in self._original_map.items():
            if k not in self._new_map:
                full_map[k] = v
            else:
                full_map[k] = self._new_map[k]
        return full_map

    def get_setting(self) -> dict[int, float]:
        """
        Returns
        -------
        dict[int, float]
            The minimal partial charge setting.
        """
        minimal_map = {}
        for k, v in self._original_map.items():
            if k not in self._new_map:
                continue
            if self._new_map[k] != v:
                minimal_map[k] = self._new_map[k]
        return minimal_map

    def get_grouped_setting(self) -> dict[tuple[int], float]:
        """Return a dict of groups of indices with the same charge.

        Returns
        -------
        dict[tuple[int], float]
            The minimal partial charge setting.
        """
        groups = {}
        new_charges = self._traj_charges.copy()
        for k, v in self._new_map.items():
            new_charges[k] = v
        valid_indices = np.where(
            np.logical_not(np.isclose(new_charges - self._traj_charges, 0.0))
        )
        unique_charges = np.unique(new_charges[valid_indices])
        for charge in unique_charges:
            charge_indices = set(np.where(np.isclose(new_charges, charge))[0])
            key = charge_indices.intersection(valid_indices[0])
            groups[charge] = [int(x) for x in key]
        return groups

    def get_json_setting(self) -> str:
        """
        Returns
        -------
        str
            A json string of the minimal partial charge setting.
        """
        return json.dumps(self.get_grouped_setting())

    def reset_setting(self) -> None:
        """Resets the partial charge setting."""
        self._new_map = {}


class PartialChargeConfigurator(IConfigurator):
    """Assigns partial charges to atoms."""

    _default = "{}"

    def configure(self, value):
        """
        Parameters
        ----------
        value
            The partial charge setting in the json format.
        """
        if not self.update_needed(value):
            return

        self["charges"] = {}

        if value is None or value == "":
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

        processed_values = {}
        for k, v in value.items():
            if isinstance(v, list):
                try:
                    charge = float(k)
                except (TypeError, ValueError):
                    self.error_status = f"Wrong charge {k} in the charge dictionary"
                    return
                else:
                    for index in v:
                        processed_values[index] = charge
                continue
            try:
                index = int(k)
                charge = float(v)
            except (TypeError, ValueError):
                self.error_status = (
                    f"Index/charge pair {k}/{v} is not a valid int/float pair."
                )
                return
            else:
                processed_values[index] = charge

        traj_config = self.configurable[self.dependencies["trajectory"]]
        system = traj_config["instance"].chemical_system
        traj_indices = system._atom_indices
        charge_indices = set(processed_values.keys())

        for index in charge_indices.intersection(traj_indices):
            self["charges"][index] = processed_values[index]

        if not charge_indices.issubset(traj_indices):
            self.warning_status = (
                "At least one atom index not found in the current system."
            )
            return

        self.error_status = "OK"
        self.warning_status = ""

    def get_charge_mapper(self) -> PartialChargeMapper:
        """
        Returns
        -------
        PartialChargeMapper
            The partial charge mapper object initialised with the
            trajectories chemical system.
        """
        traj_config = self.configurable[self.dependencies["trajectory"]]
        mapper = PartialChargeMapper(traj_config["instance"])
        return mapper

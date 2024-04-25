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
from typing import Union
import json

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator
from MDANSE.Framework.AtomSelector import Selector
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


class PartialChargeMapper:
    """The partial charge mapper. Updates an atom partial charge map
    with applications of the update_charges method with a selection
    setting and partial charge."""

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
            self._original_map[at.index] = 0.0
        self._new_map = {}

    def update_charges(
        self, selection_dict: dict[str, Union[bool, dict]], charge: float
    ) -> None:
        """With the selection dictionary update the selector and then
        update the partial charge map.

        Parameters
        ----------
        selection_dict: dict[str, Union[bool, dict]]
            The selection setting to get the indexes to map the inputted
            partial charge.
        charge: float
            The partial charge to map the selected atoms to.
        """
        self.selector.update_settings(selection_dict, reset_first=True)
        for idx in self.selector.get_idxs():
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

    def get_json_setting(self) -> str:
        """
        Returns
        -------
        str
            A json string of the minimal partial charge setting.
        """
        return json.dumps(self.get_setting())

    def reset_setting(self) -> None:
        """Resets the partial charge setting."""
        self._new_map = {}


class PartialChargeConfigurator(IConfigurator):
    """This configurator allows to input partial charges."""

    _default = "{}"

    def configure(self, value):
        """
        Parameters
        ----------
        value
            The partial charge setting in the json format.
        """
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

        for k in value.keys():
            try:
                int(k)
            except ValueError:
                self.error_status = (
                    "Setting not valid - keys should be castable to an int."
                )
                return

        traj_config = self._configurable[self._dependencies["trajectory"]]
        system = traj_config["instance"].chemical_system
        idxs = [at.index for at in system.atom_list]

        if any([int(i) not in idxs for i in value.keys()]):
            self.error_status = "Inputted setting not valid - atom index not found in the current system."
            return

        for idx in idxs:
            if str(idx) in value:
                self["charges"][idx] = value[str(idx)]
            else:
                self["charges"][idx] = 0.0

        self.error_status = "OK"

    def get_information(self):
        """Returns some basic information about the partial charges.

        Returns
        -------
        str
            The information about the partial charges.
        """

        info = f"Charge map setting {self['charges']}\n"
        return info

    def get_charge_mapper(self) -> PartialChargeMapper:
        """
        Returns
        -------
        PartialChargeMapper
            The partial charge mapper object initialised with the
            trajectories chemical system.
        """
        traj_config = self._configurable[self._dependencies["trajectory"]]
        mapper = PartialChargeMapper(traj_config["instance"].chemical_system)
        return mapper

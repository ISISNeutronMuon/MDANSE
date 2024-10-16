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
import copy
from typing import Union
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Framework.AtomSelector.all_selector import select_all
from MDANSE.Framework.AtomSelector.atom_selectors import *
from MDANSE.Framework.AtomSelector.group_selectors import *
from MDANSE.Framework.AtomSelector.molecule_selectors import *


class Selector:
    """Used to get the indexes of a subset of atoms of a chemical system.

    Attributes
    ----------
    _default : dict[str, bool | dict]
        The default settings.
    _funcs : dict[str, Callable]
        A dictionary of the functions.
    _kwarg_keys : dict[str, str]
        A dictionary of the function arg keys.
    """

    _default = {
        "all": True,
        "dummy": False,
        "hs_on_heteroatom": False,
        "primary_amine": False,
        "hydroxy": False,
        "methyl": False,
        "phosphate": False,
        "sulphate": False,
        "thiol": False,
        "water": False,
        # e.g. {"S": True}
        "hs_on_element": {},
        "element": {},
        "name": {},
        "fullname": {},
        # e.g. {1: True}
        "index": {},
    }

    _funcs = {
        "all": select_all,
        "dummy": select_dummy,
        "hs_on_heteroatom": select_hs_on_heteroatom,
        "primary_amine": select_primary_amine,
        "hydroxy": select_hydroxy,
        "methyl": select_methly,
        "phosphate": select_phosphate,
        "sulphate": select_sulphate,
        "thiol": select_thiol,
        "water": select_water,
        "hs_on_element": select_hs_on_element,
        "element": select_element,
        "name": select_atom_name,
        "fullname": select_atom_fullname,
        "index": select_index,
    }

    _kwarg_keys = {
        "hs_on_element": "symbol",
        "element": "symbol",
        "name": "name",
        "fullname": "fullname",
        "index": "index",
    }

    def __init__(self, system: ChemicalSystem) -> None:
        """
        Parameters
        ----------
        system: ChemicalSystem
            The chemical system to apply the selection to.
        """
        self.system = system
        self.all_idxs = set([at.index for at in system.atom_list])
        self.settings = copy.deepcopy(self._default)

        symbols = set([at.symbol for at in system.atom_list])
        # all possible values for the system
        self._kwarg_vals = {
            "element": symbols,
            "hs_on_element": set(
                [
                    symbol
                    for symbol in symbols
                    if select_hs_on_element(system, symbol, check_exists=True)
                ]
            ),
            "name": set([at.name for at in system.atom_list]),
            "fullname": set([at.full_name for at in system.atom_list]),
            "index": self.all_idxs,
        }

        # figure out if a match exists for the selector function
        self.match_exists = self.full_settings
        for k0, v0 in self.match_exists.items():
            if isinstance(v0, dict):
                for k1 in v0.keys():
                    self.match_exists[k0][k1] = True
            else:
                self.match_exists[k0] = self._funcs[k0](self.system, check_exists=True)

    def reset_settings(self) -> None:
        """Resets the settings back to the defaults."""
        self.settings = copy.deepcopy(self._default)

    def update_settings(
        self, settings: dict[str, Union[bool, dict]], reset_first: bool = False
    ) -> None:
        """Updates the selection settings.

        Parameters
        ----------
        settings : dict[str, bool | dict]
            The selection settings.
        reset_first : bool, optional
            Resets the settings to the default before loading.

        Raises
        ------
        ValueError
            Raises a ValueError if the inputted settings are not valid.
        """
        if not self.check_valid_setting(settings):
            raise ValueError(
                f"Settings are not valid for the given chemical system - {settings}."
            )

        if reset_first:
            self.reset_settings()

        for k0, v0 in settings.items():
            if isinstance(self.settings[k0], dict):
                for k1, v1 in v0.items():
                    self.settings[k0][k1] = v1
            else:
                self.settings[k0] = v0

    def get_idxs(self) -> set[int]:
        """The atom indexes after applying the selection to the system.

        Returns
        -------
        set[int]
            The atoms indexes.
        """
        idxs = set([])

        for k, v in self.settings.items():

            if isinstance(v, dict):
                args = [{self._kwarg_keys[k]: i} for i in v.keys()]
                switches = v.values()
            else:
                args = [{}]
                switches = [v]

            for arg, switch in zip(args, switches):
                if not switch:
                    continue

                idxs.update(self._funcs[k](self.system, **arg))

        return idxs

    def update_with_idxs(self, idxs: set[int]) -> None:
        """Using the inputted idxs change the selection setting so
        that it would return the same idxs with get_idxs. It will
        switch off the setting if idxs is not a superset of the
        selection for that setting.

        Parameters
        ----------
        idxs : set[int]
            With the indexes of the atom selection.
        """
        new_settings = copy.deepcopy(self.settings)
        added = set([])
        prev_selected = set([])
        for k, v in self.settings.items():

            if isinstance(v, dict):
                args = [{self._kwarg_keys[k]: i} for i in v.keys()]
                switches = v.values()
            else:
                args = [{}]
                switches = [v]

            for arg, switch in zip(args, switches):
                if not switch:
                    continue

                selection = self._funcs[k](self.system, **arg)
                if idxs.issuperset(selection):
                    added.update(selection)
                    continue

                prev_selected.update(selection)
                if isinstance(v, dict):
                    new_settings[k][arg[self._kwarg_keys[k]]] = False
                else:
                    new_settings[k] = False

        for idx in idxs - added:
            new_settings["index"][idx] = True
        for idx in prev_selected - idxs:
            new_settings["index"][idx] = False

        self.settings = new_settings

    def settings_to_json(self) -> str:
        """Return the minimal json string required to achieve the same
        settings with the settings_from_json method.

        Returns
        -------
        str
            A JSON string.
        """
        minimal_dict = {}
        for k0, v0 in self.settings.items():
            if isinstance(v0, bool) and (k0 == "all" or k0 != "all" and v0):
                minimal_dict[k0] = v0
            elif isinstance(v0, dict):
                sub_list = []
                for k1, v1 in v0.items():
                    if v1:
                        sub_list.append(k1)
                if sub_list:
                    minimal_dict[k0] = sub_list
        return json.dumps(minimal_dict)

    def json_to_settings(self, json_string: str) -> dict[str, Union[bool, dict]]:
        """Loads the json string and converts to a settings.

        Parameters
        ----------
        json_string : str
            The JSON string of settings.

        Returns
        -------
        dict[str, Union[bool, dict]]
            The selection settings.
        """
        json_setting = json.loads(json_string)
        settings = {}
        for k0, v0 in json_setting.items():
            if isinstance(v0, bool):
                settings[k0] = v0
            elif isinstance(v0, list):
                sub_dict = {}
                for k1 in v0:
                    sub_dict[k1] = True
                if sub_dict:
                    settings[k0] = sub_dict
        return settings

    def load_from_json(self, json_string: str) -> None:
        """Load the selection settings from a JSON string.

        Parameters
        ----------
        json_string : str
            The JSON string of settings.
        """
        self.update_settings(self.json_to_settings(json_string), reset_first=True)

    def check_valid_setting(self, settings: dict[str, Union[bool, dict]]) -> bool:
        """Checks that the input settings are valid.

        Parameters
        ----------
        settings : dict[str, bool | dict]
            The selection settings.

        Returns
        -------
        bool
            True if settings are valid.
        """
        setting_keys = self._default.keys()
        dict_setting_keys = self._kwarg_keys.keys()
        for k0, v0 in settings.items():

            if k0 not in setting_keys:
                return False

            if k0 not in dict_setting_keys:
                if not isinstance(v0, bool):
                    return False

            if k0 in dict_setting_keys:
                if not isinstance(v0, dict):
                    return False
                for k1, v1 in v0.items():
                    if k1 not in self._kwarg_vals[k0]:
                        return False
                    if not isinstance(v1, bool):
                        return False

        return True

    def check_valid_json_settings(self, json_string: str) -> bool:
        """Checks that the input JSON setting string is valid.

        Parameters
        ----------
        json_string : str
            The JSON string of settings.

        Returns
        -------
        bool
            True if settings are valid.
        """
        try:
            settings = self.json_to_settings(json_string)
        except ValueError:
            return False
        return self.check_valid_setting(settings)

    @property
    def full_settings(self) -> dict[str, Union[bool, dict]]:
        """
        Returns
        -------
        dict[str, Union[bool, dict]]
            The full settings for the initialised chemical system.
        """
        settings = copy.deepcopy(self.settings)
        for k, vs in self._kwarg_vals.items():
            for v in sorted(vs):
                if v not in settings[k]:
                    settings[k][v] = False
        return settings

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
        # True inverts the selection
        "invert": False,
        # True selects atoms
        "all": True,
        "hs_on_heteroatom": False,
        "primary_amine": False,
        "hydroxy": False,
        "methly": False,
        "phosphate": False,
        "sulphate": False,
        "thiol": False,
        "water": False,
        # e.g. {"S": True}
        "elements": {},
        "hs_on_elements": {},
        # e.g. {"1": True} or {1: True}
        "indexes": {},
    }

    _funcs = {
        "all": select_all,
        "hs_on_heteroatom": select_hs_on_heteroatom,
        "primary_amine": select_primary_amine,
        "hydroxy": select_hydroxy,
        "methly": select_methly,
        "phosphate": select_phosphate,
        "sulphate": select_sulphate,
        "thiol": select_thiol,
        "water": select_water,
        "elements": select_elements,
        "hs_on_elements": select_hs_on_elements,
        "indexes": select_index,
    }

    _kwarg_keys = {
        "elements": "symbols",
        "hs_on_elements": "symbols",
        "indexes": "index",
    }

    def __init__(self, system: ChemicalSystem) -> None:
        """
        Parameters
        ----------
        system: ChemicalSystem
            The chemical system to apply the selection to.
        """
        self.system = system
        self.all_idxs = select_all(system)
        self.settings = copy.deepcopy(self._default)

        symbols = set(["*"] + [at.symbol for at in system.atom_list])
        self._kwarg_vals = {
            "elements": symbols,
            "hs_on_elements": symbols,
            # we allow index keys to be str or int, this is mostly
            # done since json keys are str
            "indexes": self.all_idxs | set([str(i) for i in self.all_idxs]),
        }

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
            raise ValueError("Settings are not valid for the given chemical system.")

        if reset_first:
            self.reset_settings()

        for k1, v1 in settings.items():
            if isinstance(self.settings[k1], dict):
                for k2, v2 in v1.items():
                    self.settings[k1][k2] = v2
            else:
                self.settings[k1] = v1

    def get_idxs(self) -> set[int]:
        """The atom indexes after applying the selection to the system.

        Returns
        -------
        set[int]
            The atoms indexes.
        """
        idxs = set([])

        for k, v in self.settings.items():
            if k == "invert":
                continue

            if isinstance(v, dict):
                args = [{self._kwarg_keys[k]: i} for i in v.keys()]
                switches = v.values()
            else:
                args = [{}]
                switches = [v]

            for args, switch in zip(args, switches):
                if not switch:
                    continue

                idxs = idxs | self._funcs[k](self.system, **args)

        if self.settings["invert"]:
            return self.all_idxs - idxs
        else:
            return idxs

    def settings_to_json(self) -> str:
        """Return the minimal json string required to achieve the same
        settings with the settings_from_json method.

        Returns
        -------
        str
            A json string.
        """
        minimal_dict = {}
        for k0, v0 in self.settings.items():
            if isinstance(v0, bool) and (k0 == "all" and not v0 or k0 != "all" and v0):
                minimal_dict[k0] = v0
            elif isinstance(v0, dict):
                sub_dict = {}
                for k1, v1 in v0.items():
                    if v1:
                        sub_dict[k1] = v1
                if sub_dict:
                    minimal_dict[k0] = sub_dict
        return json.dumps(minimal_dict)

    def update_from_json(self, json_string: str, reset_first: bool = False) -> None:
        """Update the selection settings from a json string.

        Parameters
        ----------
        json_string : str
            The json string of settings.
        reset_first : bool, optional
            Resets the settings to the default before loading.
        """
        self.update_settings(json.loads(json_string), reset_first)

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
            if k0 not in dict_setting_keys and not isinstance(v0, bool):
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
        """Checks that the input json setting string is valid.

        Parameters
        ----------
        json_string : str
            The json string of settings.

        Returns
        -------
        bool
            True if settings are valid.
        """
        try:
            settings = json.loads(json_string)
        except ValueError:
            return False

        return self.check_valid_setting(settings)

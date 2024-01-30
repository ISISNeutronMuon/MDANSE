import json
import copy
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Framework.Selectors.all_selector import select_all
from MDANSE.Framework.Selectors.atom_selectors import *
from MDANSE.Framework.Selectors.group_selectors import *
from MDANSE.Framework.Selectors.molecule_selectors import *


class FilterSelection:
    """Used to get the indexes of a subset of atoms of a chemical system.

    Attributes
    ----------
    _default : dict[str, bool | dict]
        The default settings.
    _funcs : dict[str, Callable]
        A dictionary of the filter functions.
    _kwarg_keys : dict[str, str]
        A dictionary of the filter function arg keys.
    """

    _default = {
        # True deselects atoms
        "all": False,
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
        "index": {},
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
        "index": select_index,
    }

    _kwarg_keys = {
        "elements": "symbols",
        "hs_on_elements": "symbols",
        "index": "index",
    }

    def __init__(self, system: ChemicalSystem) -> None:
        """
        Parameters
        ----------
        system: ChemicalSystem
            The chemical system to apply the filter to.
        """
        self.system = system
        self.all_idxs = select_all(system)
        self.settings = copy.deepcopy(self._default)

    def reset_settings(self) -> None:
        """Resets the settings back to the defaults."""
        self.settings = copy.deepcopy(self._default)

    def update_settings(
        self, settings: dict[str, bool | dict], reset_first: bool = False
    ) -> None:
        """Updates the filter selection settings.

        Parameters
        ----------
        settings : dict[str, bool | dict]
            The filter selection settings.
        reset_first : bool, optional
            Resets the settings to the default before loading.
        """
        if reset_first:
            self.reset_settings()

        for k1, v1 in settings.items():
            if isinstance(self.settings[k1], dict):
                for k2, v2 in v1.items():
                    self.settings[k1][k2] = v2
            else:
                self.settings[k1] = v1

    def get_idxs(self) -> set[int]:
        """The atom indexes after applying the filters to the system.

        Returns
        -------
        set[int]
            The atoms indexes.
        """
        idxs = self.all_idxs

        for k, v in self.settings.items():
            if isinstance(v, dict):
                args = [{self._kwarg_keys[k]: i} for i in v.keys()]
                switches = v.values()
            else:
                args = [{}]
                switches = [v]

            for args, switch in zip(args, switches):
                if not switch:
                    continue

                idxs = idxs - self._funcs[k](self.system, **args)

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
            if isinstance(v0, bool) and v0:
                minimal_dict[k0] = v0
            elif isinstance(v0, dict):
                sub_dict = {}
                for k1, v1 in v0.items():
                    if v1:
                        sub_dict[k1] = v1
                if sub_dict:
                    minimal_dict[k0] = sub_dict
        return json.dumps(minimal_dict)

    def settings_from_json(self, json_string: str, reset_first: bool = False) -> None:
        """Load the filter selection setting from a json string.

        Parameters
        ----------
        json_string : str
            The json string of settings.
        reset_first : bool, optional
            Resets the settings to the default before loading.
        """
        self.update_settings(json.loads(json_string), reset_first)

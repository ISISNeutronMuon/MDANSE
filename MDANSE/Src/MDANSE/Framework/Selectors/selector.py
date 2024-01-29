import json
import copy
from typing import Literal
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Framework.Selectors.all_selector import select_all
from MDANSE.Framework.Selectors.atom_selectors import *
from MDANSE.Framework.Selectors.group_selectors import *
from MDANSE.Framework.Selectors.molecule_selectors import *


class Selector:

    # should not be changed
    _default = {
        # -1 remove atoms, +1 selects atoms, 0 skip
        "switch": {
            "all": 1,
            "elements": 0,
            "hs_on_heteroatom": 0,
            "hs_on_elements": 0,
            "primary_amine": 0,
            "hydroxy": 0,
            "methly": 0,
            "phosphate": 0,
            "sulphate": 0,
            "thiol": 0,
            "water": 0
        },
        "args": {
            "all": {},
            "elements": {"symbols": []},
            "hs_on_heteroatom": {},
            "hs_on_elements": {"symbols": []},
            "primary_amine": {},
            "hydroxy": {},
            "methly": {},
            "phosphate": {},
            "sulphate": {},
            "thiol": {},
            "water": {},
        }
    }

    def __init__(self, system: ChemicalSystem):
        self.system = system

        self._idxs = {
            "all": None,
            "elements": None,
            "hs_on_heteroatom": None,
            "hs_on_elements": None,
            "primary_amine": None,
            "hydroxy": None,
            "methly": None,
            "phosphate": None,
            "sulphate": None,
            "thiol": None,
            "water": None,
        }

        self._funcs = {
            "all": select_all,
            "elements": select_elements,
            "hs_on_heteroatom": select_hs_on_heteroatom,
            "hs_on_elements": select_hs_on_elements,
            "primary_amine": select_primary_amine,
            "hydroxy": select_hydroxy,
            "methly": select_methly,
            "phosphate": select_phosphate,
            "sulphate": select_sulphate,
            "thiol": select_thiol,
            "water": select_water
        }

        self.settings = copy.deepcopy(self._default)

    def reset_settings(self):
        self.settings = copy.deepcopy(self._default)

    def update_settings(self, settings: dict[Literal["switch", "args"], dict], reset_first=False) -> None:
        if reset_first:
            self.reset_settings()

        for k_0, v_0 in settings.items():
            for k_1, v_1 in v_0.items():
                if k_0 == "switch":
                    self.settings[k_0][k_1] = v_1
                elif k_0 == "args":
                    for k_2, v_2 in v_1.items():
                        self.settings[k_0][k_1][k_2] = v_2

    def get_selection(self) -> set[int]:
        idxs = set()

        for selection, switch in self.settings["switch"].items():

            if switch == 0:
                continue

            if self._idxs[selection] is None:
                kwargs = self.settings["args"][selection]
                self._idxs[selection] \
                    = self._funcs[selection](self.system, **kwargs)

            if switch == -1:
                idxs = idxs - self._idxs[selection]
            elif switch == 1:
                idxs = idxs | self._idxs[selection]

        return idxs

    def settings_to_json(self):
        return json.dumps(self.settings)

    def settings_from_json(self, json_string, reset_first=False):
        self.update_settings(json.loads(json_string), reset_first)

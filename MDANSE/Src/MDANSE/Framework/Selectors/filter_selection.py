from typing import Literal
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from .all_selector import select_all
from .atom_selectors import *
from .group_selectors import *
from .molecule_selectors import *


class FilterSelection:

    def __init__(self, system: ChemicalSystem):
        self.system = system
        self.all_idxs = select_all(system)

        self._idxs = {
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

        self.settings = {
            "switch": {
                "elements": False,
                "hs_on_heteroatom": False,
                "hs_on_elements": False,
                "primary_amine": False,
                "hydroxy": False,
                "methly": False,
                "phosphate": False,
                "sulphate": False,
                "thiol": False,
                "water": False
            },
            "args": {
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

    def load_settings(self, settings: dict[Literal["switch", "args"], dict]) -> None:
        for k_0, v_0 in settings.items():
            for k_1, v_1 in v_0.items():
                if k_0 == "switch":
                    self.settings[k_0][k_1] = v_1
                elif k_0 == "args":
                    for k_2, v_2 in v_1.items():
                        self.settings[k_0][k_1][k_2] = v_2

    def apply_filter(self) -> set[int]:
        idxs = self.all_idxs

        for selection, switch in self.settings["switch"].items():

            if switch is False:
                continue

            if self._idxs[selection] is None:
                kwargs = self.settings["args"][selection]
                self._idxs[selection] \
                    = self._funcs[selection](self.system, **kwargs)

            idxs = idxs - self._idxs[selection]

        return idxs

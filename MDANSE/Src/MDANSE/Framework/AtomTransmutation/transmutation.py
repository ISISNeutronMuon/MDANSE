from typing import Union
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Framework.AtomSelector import Selector


class AtomTransmuter:

    def __init__(self, system: ChemicalSystem) -> None:
        self.selector = Selector(system)
        self._original_map = {}
        for at in system.atom_list:
            self._original_map[at.index] = at.symbol
        self._new_map = {}

    def update_setting(self, selection_dict: dict[str, Union[bool, dict]], symbol: str) -> None:
        self.selector.update_settings(selection_dict, reset_first=True)
        for idx in self.selector.get_idxs():
            self._new_map[idx] = symbol

    def get_map(self) -> dict[int, str]:
        minimal_map = {}
        for k, v in self._new_map.items():
            if self._original_map[k] != v:
                minimal_map[k] = v
        return minimal_map

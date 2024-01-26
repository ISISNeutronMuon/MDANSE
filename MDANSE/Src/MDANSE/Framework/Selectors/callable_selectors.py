from typing import Callable
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem, Atom


def select_with_fullname(system: ChemicalSystem, names: list[str]):
    return select_with_callable(system, names, lambda x: x.full_name.strip())


def select_with_name(system: ChemicalSystem, names: list[str]):
    return select_with_callable(system, names, lambda x: x.name.strip())


def select_with_callable(
        system: ChemicalSystem, values: list[str], callable: Callable[[Atom], str]
) -> set[int]:

    idxs = set()
    for at in system.atom_list:
        result = callable(at)
        if result in values:
            idxs.add(at.index)

    return idxs

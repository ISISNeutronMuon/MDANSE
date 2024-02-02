from typing import Union
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Chemistry import ATOMS_DATABASE


__all__ = [
    "select_element",
    "select_hs_on_element",
    "select_hs_on_heteroatom",
    "select_index",
]


def select_element(system: ChemicalSystem, symbol: str) -> set[int]:
    """Selects all atoms for the input element.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    symbol : str
        Symbol of the element.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    if "*" == symbol:
        return set([at.index for at in system.atom_list])
    return system.get_substructure_matches(
        f"[#{ATOMS_DATABASE[symbol]['atomic_number']}]")


def select_hs_on_element(
    system: ChemicalSystem, symbol: Union[list[str], str]
) -> set[int]:
    """Selects all H atoms bonded to the input element.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    symbol : list[str] or str
        Symbol of the element that the H atoms are bonded to.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    num = ATOMS_DATABASE[symbol]["atomic_number"]
    xh_matches = system.get_substructure_matches(f"[#{num}]~[H]")
    x_matches = system.get_substructure_matches(f"[#{num}]")
    return xh_matches - x_matches


def select_hs_on_heteroatom(system: ChemicalSystem) -> set[int]:
    """Selects all H atoms bonded to any atom except carbon and
    hydrogen.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    xh_matches = system.get_substructure_matches("[!#6&!#1]~[H]")
    x_matches = system.get_substructure_matches("[!#6&!#1]")
    return xh_matches - x_matches


def select_index(system: ChemicalSystem, index: Union[int, str]) -> set[int]:
    """Selects atom with index - just returns the set with the
    index in it.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    index : int or str
        The index to select.

    Returns
    -------
    set[int]
        The index in a set.
    """
    return {int(index)}

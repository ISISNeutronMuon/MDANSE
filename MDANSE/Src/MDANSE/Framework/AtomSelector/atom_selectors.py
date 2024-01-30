from typing import Union
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Chemistry import ATOMS_DATABASE


__all__ = [
    "select_elements",
    "select_hs_on_elements",
    "select_hs_on_heteroatom",
    "select_index",
]


def select_elements(system: ChemicalSystem, symbols: Union[list[str], str]) -> set[int]:
    """Selects all atoms for the input elements.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    symbols : list[str]
        A symbol or list of symbols of the elements.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    patterns = []
    symbols = set(symbols if isinstance(symbols, list) else [symbols])
    if "*" in symbols:
        return set([at.index for at in system.atom_list])
    for symbol in symbols:
        patterns.append(f"[#{ATOMS_DATABASE[symbol]['atomic_number']}]")
    return system.get_substructure_matches(patterns)


def select_hs_on_elements(
    system: ChemicalSystem, symbols: Union[list[str], str]
) -> set[int]:
    """Selects all H atoms bonded to the input elements.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    symbols : list[str] or str
        A symbols or list of symbols of the elements that the H atoms are
        bonded to.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    matches = set()
    symbols = set(symbols if isinstance(symbols, list) else [symbols])
    for symbol in symbols:
        num = ATOMS_DATABASE[symbol]["atomic_number"]
        xh_matches = system.get_substructure_matches([f"[#{num}]~[H]"])
        x_matches = system.get_substructure_matches([f"[#{num}]"])
        matches.update(xh_matches - x_matches)
    return matches


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
    xh_matches = system.get_substructure_matches(["[!#6&!#1]~[H]"])
    x_matches = system.get_substructure_matches(["[!#6&!#1]"])
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

from typing import Union
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


__all__ = [
    "select_water",
]


def select_water(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects the O and H atoms of all water molecules.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    check_exists : bool, optional
        Check if a match exists.

    Returns
    -------
    Union[set[int], bool]
        The atom indices of the matched atoms or a bool if checking match.
    """
    pattern = "[#8X2;H2](~[H])~[H]"
    if check_exists:
        return system.has_substructure_match(pattern)
    else:
        return system.get_substructure_matches(pattern)

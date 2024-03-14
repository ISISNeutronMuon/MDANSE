from typing import Union
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


def select_all(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects all atoms in the chemical system except for the dummy
    atoms.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    check_exists : bool, optional
        Check if a match exists.

    Returns
    -------
    Union[set[int], bool]
        All atom indices except for dummy atoms or a bool if checking
        match.
    """
    if check_exists:
        return True
    else:
        return set([at.index for at in system.atom_list if at.element != "dummy"])

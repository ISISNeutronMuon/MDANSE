from typing import Union
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


__all__ = [
    "select_primary_amine",
    "select_hydroxy",
    "select_methly",
    "select_phosphate",
    "select_sulphate",
    "select_thiol",
]


def select_primary_amine(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects the N and H atoms of all primary amines.

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
    pattern = "[#7X3;H2;!$([#7][#6X3][!#6]);!$([#7][#6X2][!#6])](~[H])~[H]"
    if check_exists:
        return system.has_substructure_match(pattern)
    else:
        return system.get_substructure_matches(pattern)


def select_hydroxy(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects the O and H atoms of all hydroxy groups including water.

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
    # including -OH on water
    pattern = "[#8;H1,H2]~[H]"
    if check_exists:
        return system.has_substructure_match(pattern)
    else:
        return system.get_substructure_matches(pattern)


def select_methly(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects the C and H atoms of all methyl groups.

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
    pattern = "[#6;H3](~[H])(~[H])~[H]"
    if check_exists:
        return system.has_substructure_match(pattern)
    else:
        return system.get_substructure_matches(pattern)


def select_phosphate(system: ChemicalSystem, check_exists: bool = False) -> Union[set[int], bool]:
    """Selects the P and O atoms of all phosphate groups.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    check_exists : bool, optional
        Check if a match exists.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms or a bool if checking match.
    """
    pattern = "[#15X4](~[#8])(~[#8])(~[#8])~[#8]"
    if check_exists:
        return system.has_substructure_match(pattern)
    else:
        return system.get_substructure_matches(pattern)


def select_sulphate(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects the S and O atoms of all sulphate groups.

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
    pattern = "[#16X4](~[#8])(~[#8])(~[#8])~[#8]"
    if check_exists:
        return system.has_substructure_match(pattern)
    else:
        return system.get_substructure_matches(pattern)


def select_thiol(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects the S and H atoms of all thiol groups.

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
    pattern = "[#16X2;H1]~[H]"
    if check_exists:
        return system.has_substructure_match(pattern)
    else:
        return system.get_substructure_matches(pattern)

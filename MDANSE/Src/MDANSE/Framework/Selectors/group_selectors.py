from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


def select_primary_amine(system: ChemicalSystem) -> set[int]:
    """Selects the N and H atoms of all primary amines.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    patterns = ["[#7X3;H2;!$([#7][#6X3][!#6]);!$([#7][#6X2][!#6])](~[H])~[H]"]
    return system.get_substructure_matches(patterns)


def select_hydroxy(system: ChemicalSystem) -> set[int]:
    """Selects the O and H atoms of all hydroxy groups including water.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    # including -OH on water
    return system.get_substructure_matches(["[#8;H1,H2]~[H]"])


def select_methly(system: ChemicalSystem) -> set[int]:
    """Selects the C and H atoms of all methyl groups.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    return system.get_substructure_matches(["[#6;H3](~[H])(~[H])~[H]"])


def select_phosphate(system: ChemicalSystem) -> set[int]:
    """Selects the P and O atoms of all phosphate groups.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    return system.get_substructure_matches(["[#15X4](~[#8])(~[#8])(~[#8])~[#8]"])


def select_sulphate(system: ChemicalSystem) -> set[int]:
    """Selects the S and O atoms of all sulphate groups.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    return system.get_substructure_matches(["[#16X4](~[#8])(~[#8])(~[#8])~[#8]"])


def select_thiol(system: ChemicalSystem) -> set[int]:
    """Selects the S and H atoms of all thiol groups.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    return system.get_substructure_matches(["[#16X2H]~[H]"])

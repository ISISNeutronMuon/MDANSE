from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Chemistry import ATOMS_DATABASE


def select_all(system: ChemicalSystem) -> set[int]:
    """Selects all atoms with smarts.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    return system.get_substructure_matches(["[*]"])


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


def select_element(system: ChemicalSystem, symbol: str) -> set[int]:
    """Selects all atoms for the input element.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    symbol : str
        The symbol of the element.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    return select_elements(system, [symbol])


def select_elements(system: ChemicalSystem, symbols: list[str]) -> set[int]:
    """Selects all atoms for the input elements.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    symbols : list[str]
        A list of element symbols.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    patterns = []
    for symbol in symbols:
        if symbol == "*":
            patterns.append(f"[*]")
        else:
            patterns.append(f"[#{ATOMS_DATABASE[symbol]['atomic_number']}]")
    return system.get_substructure_matches(patterns)


def select_hs_on_element(system: ChemicalSystem, symbol: str) -> set[int]:
    """Selects all H atoms bonded to the input element.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    symbol : str
        The symbol of the element that the H atoms are bonded to.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    return select_hs_on_elements(system, [symbol])


def select_hs_on_elements(system: ChemicalSystem, symbols: list[str]) -> set[int]:
    """Selects all H atoms bonded to the input elements.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    symbols : list[str]
        A list of symbols of the elements that the H atoms are
        bonded to.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    matches = set()
    for symbol in symbols:
        num = ATOMS_DATABASE[symbol]["atomic_number"]
        xh_matches = system.get_substructure_matches([f"[#{num};H1,H2,H3,H4]~[H]"])
        x_matches = system.get_substructure_matches([f"[#{num};H1,H2,H3,H4]"])
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
    xh_matches = system.get_substructure_matches(["[!#6&!#1;H1,H2,H3,H4]~[H]"])
    x_matches = system.get_substructure_matches(["[!#6&!#1;H1,H2,H3,H4]"])
    return xh_matches - x_matches


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

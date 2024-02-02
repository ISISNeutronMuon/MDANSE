from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


__all__ = [
    "select_water",
]


def select_water(system: ChemicalSystem) -> set[int]:
    """Selects the O and H atoms of all water molecules.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        The atom indices of the matched atoms.
    """
    pattern = "[#8X2;H2](~[H])~[H]"
    return system.get_substructure_matches(pattern)

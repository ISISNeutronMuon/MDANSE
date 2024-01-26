from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


def select_all(system: ChemicalSystem) -> set[int]:
    """Selects all atoms in the chemical system.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.

    Returns
    -------
    set[int]
        All atom indices.
    """
    idxs = set()
    for at in system.atom_list:
        idxs.add(at.index)
    return idxs

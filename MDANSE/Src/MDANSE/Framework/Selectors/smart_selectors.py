from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


def select_all(system: ChemicalSystem):
    patterns = ["[*]"]
    return system.get_substructure_matches(patterns)


def select_primary_amine(system: ChemicalSystem):
    patterns = ["[NX3;H2;!$(NC=[!#6]);!$(NC#[!#6])]([H])[H]"]
    return system.get_substructure_matches(patterns)


def select_element(system: ChemicalSystem, symbol: str):
    patterns = [f"[{symbol}]"]
    return system.get_substructure_matches(patterns)


def select_elements(system: ChemicalSystem, symbols: list[str]):
    patterns = [f"[{symbol}]" for symbol in symbols]
    return system.get_substructure_matches(patterns)


def select_hs_on_carbon(system: ChemicalSystem):
    # smarts doesn't play well when matching hydrogen atoms lets take
    # the differences between two different well-behaved matches
    ch_matches = system.get_substructure_matches(["[#6;H1,H2,H3,H4][H]"])
    c_matches = system.get_substructure_matches(["[#6;H1,H2,H3,H4]"])
    return ch_matches - c_matches


def select_thiol(system: ChemicalSystem):
    pattern = ["[#16X2H][H]"]
    return system.get_substructure_matches(pattern)


def select_with_smarts(system: ChemicalSystem, smarts: str):
    return system.get_substructure_matches([smarts])

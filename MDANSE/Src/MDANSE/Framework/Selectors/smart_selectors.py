from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem
from MDANSE.Chemistry import ATOMS_DATABASE


def select_all(system: ChemicalSystem):
    return system.get_substructure_matches(["[*]"])


def select_primary_amine(system: ChemicalSystem):
    patterns = ["[#7X3;H2;!$([#7][#6X3][!#6]);!$([#7][#6X2][!#6])](~[H])~[H]"]
    return system.get_substructure_matches(patterns)


def select_element(system: ChemicalSystem, symbol: str):
    return select_elements(system, [symbol])


def select_elements(system: ChemicalSystem, symbols: list[str]):
    patterns = []
    for symbol in symbols:
        if symbol == "*":
            patterns.append(f"[*]")
        else:
            patterns.append(f"[#{ATOMS_DATABASE[symbol]['atomic_number']}]")
    return system.get_substructure_matches(patterns)


def select_hs_on_element(system: ChemicalSystem, symbol: str):
    return select_hs_on_elements(system, [symbol])


def select_hs_on_elements(system: ChemicalSystem, symbols: list[str]):
    matches = set()
    for symbol in symbols:
        num = ATOMS_DATABASE[symbol]["atomic_number"]
        xh_matches = system.get_substructure_matches([f"[#{num};H1,H2,H3,H4]~[H]"])
        x_matches = system.get_substructure_matches([f"[#{num};H1,H2,H3,H4]"])
        matches.update(xh_matches - x_matches)
    return matches


def select_hs_on_heteroatom(system: ChemicalSystem):
    xh_matches = system.get_substructure_matches(["[!#6;H1,H2,H3,H4]~[H]"])
    x_matches = system.get_substructure_matches(["[!#6,!#1;H1,H2,H3,H4]"])
    return xh_matches - x_matches


def select_hydroxy(system: ChemicalSystem):
    # including -OH on water
    return system.get_substructure_matches(["[#8;H1,H2]~[H]"])


def select_methly(system: ChemicalSystem):
    return system.get_substructure_matches(["[#6;H3](~[H])(~[H])~[H]"])


def select_phosphate(system: ChemicalSystem):
    return system.get_substructure_matches(["[#15X4](~[#8])(~[#8])(~[#8])~[#8]"])


def select_sulphate(system: ChemicalSystem):
    return system.get_substructure_matches(["[#16X4](~[#8])(~[#8])(~[#8])~[#8]"])


def select_thiol(system: ChemicalSystem):
    return system.get_substructure_matches(["[#16X2H]~[H]"])


def select_with_smarts(system: ChemicalSystem, smarts: str):
    return system.get_substructure_matches([smarts])

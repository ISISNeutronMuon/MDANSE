import os
import pytest
from MDANSE.IO.PDBReader import PDBReader
from MDANSE.Framework.AtomTransmutation.transmutation import AtomTransmuter



pbd_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data", "2vb1.pdb"
)


@pytest.fixture(scope="module")
def protein_chemical_system():
    reader = PDBReader(pbd_2vb1)
    protein_chemical_system = reader.build_chemical_system()
    return protein_chemical_system


def test_atom_transmutation_returns_empty_dictionary_when_no_transmutations_are_made(protein_chemical_system):
    atm_transmuter = AtomTransmuter(protein_chemical_system)
    mapping = atm_transmuter.get_map()
    assert mapping == {}


def test_atom_transmutation_return_dict_with_transmutations_with_s_element_transmutation(protein_chemical_system):
    atm_transmuter = AtomTransmuter(protein_chemical_system)
    atm_transmuter.update_setting({"all": False, "element": {"S": True}}, "C")
    mapping = atm_transmuter.get_map()
    assert mapping == {
        98: "C",
        175: "C",
        468: "C",
        990: "C",
        1160: "C",
        1217: "C",
        1404: "C",
        1557: "C",
        1731: "C",
        1913: "C"
    }


def test_atom_transmutation_return_dict_with_transmutations_with_s_element_transmutation_and_index_98_transmutation_0(protein_chemical_system):
    atm_transmuter = AtomTransmuter(protein_chemical_system)
    atm_transmuter.update_setting({"all": False, "element": {"S": True}}, "C")
    atm_transmuter.update_setting({"all": False, "index": {98: True}}, "N")
    mapping = atm_transmuter.get_map()
    assert mapping == {
        98: "N",
        175: "C",
        468: "C",
        990: "C",
        1160: "C",
        1217: "C",
        1404: "C",
        1557: "C",
        1731: "C",
        1913: "C"
    }


def test_atom_transmutation_return_dict_with_transmutations_with_s_element_transmutation_and_index_98_transmutation_1(protein_chemical_system):
    atm_transmuter = AtomTransmuter(protein_chemical_system)
    atm_transmuter.update_setting({"all": False, "element": {"S": True}}, "C")
    atm_transmuter.update_setting({"all": False, "index": {98: True}}, "S")
    mapping = atm_transmuter.get_map()
    assert mapping == {
        175: "C",
        468: "C",
        990: "C",
        1160: "C",
        1217: "C",
        1404: "C",
        1557: "C",
        1731: "C",
        1913: "C"
    }


def test_atom_transmutation_return_dict_with_transmutations_with_s_element_transmutation_and_index_98_transmutation_2(protein_chemical_system):
    atm_transmuter = AtomTransmuter(protein_chemical_system)
    atm_transmuter.update_setting({"all": False, "element": {"S": True}}, "C")
    atm_transmuter.update_setting({"all": False, "index": {98: True, 99: True}}, "S")
    mapping = atm_transmuter.get_map()
    assert mapping == {
        99: "S",
        175: "C",
        468: "C",
        990: "C",
        1160: "C",
        1217: "C",
        1404: "C",
        1557: "C",
        1731: "C",
        1913: "C"
    }
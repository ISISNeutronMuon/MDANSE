import os
import pytest
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Configurators.AtomTransmutationConfigurator import AtomTransmuter


traj_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Converted", "2vb1.mdt"
)


@pytest.fixture(scope="module")
def protein_trajectory():
    protein_trajectory = HDFTrajectoryInputData(traj_2vb1)
    return protein_trajectory.trajectory


def test_atom_transmutation_returns_empty_dictionary_when_no_transmutations_are_made(
    protein_trajectory,
):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    mapping = atm_transmuter.get_setting()
    assert mapping == {}


def test_atom_transmutation_return_dict_with_transmutations_with_incorrect_element_raises_exception(
    protein_trajectory,
):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    with pytest.raises(ValueError):
        atm_transmuter.apply_transmutation(
            {"all": False, "element": {"S": True}}, "CCC"
        )


def test_atom_transmutation_return_dict_with_transmutations_with_s_element_transmutation(
    protein_trajectory,
):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    atm_transmuter.apply_transmutation({"all": False, "element": {"S": True}}, "C")
    mapping = atm_transmuter.get_setting()
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
        1913: "C",
    }


def test_atom_transmutation_return_dict_with_transmutations_with_s_element_transmutation_and_index_98_transmutation_0(
    protein_trajectory,
):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    atm_transmuter.apply_transmutation({"all": False, "element": {"S": True}}, "C")
    atm_transmuter.apply_transmutation({"all": False, "index": {98: True}}, "N")
    mapping = atm_transmuter.get_setting()
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
        1913: "C",
    }


def test_atom_transmutation_return_dict_with_transmutations_with_s_element_transmutation_and_index_98_transmutation_1(
    protein_trajectory,
):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    atm_transmuter.apply_transmutation({"all": False, "element": {"S": True}}, "C")
    atm_transmuter.apply_transmutation({"all": False, "index": {98: True}}, "S")
    mapping = atm_transmuter.get_setting()
    assert mapping == {
        175: "C",
        468: "C",
        990: "C",
        1160: "C",
        1217: "C",
        1404: "C",
        1557: "C",
        1731: "C",
        1913: "C",
    }


def test_atom_transmutation_return_dict_with_transmutations_with_s_element_transmutation_and_index_98_transmutation_2(
    protein_trajectory,
):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    atm_transmuter.apply_transmutation({"all": False, "element": {"S": True}}, "C")
    atm_transmuter.apply_transmutation(
        {"all": False, "index": {98: True, 99: True}}, "S"
    )
    mapping = atm_transmuter.get_setting()
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
        1913: "C",
    }


def test_atom_transmutation_return_empty_dict_after_reset(protein_trajectory):
    atm_transmuter = AtomTransmuter(protein_trajectory)
    atm_transmuter.apply_transmutation({"all": False, "element": {"S": True}}, "C")
    atm_transmuter.apply_transmutation(
        {"all": False, "index": {98: True, 99: True}}, "S"
    )
    atm_transmuter.reset_setting()
    mapping = atm_transmuter.get_setting()
    assert mapping == {}

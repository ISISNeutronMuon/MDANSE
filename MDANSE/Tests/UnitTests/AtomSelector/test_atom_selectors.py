import os
import pytest
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.AtomSelector.atom_selectors import (
    select_element,
    select_hs_on_heteroatom,
    select_hs_on_element,
    select_dummy,
)


traj_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Converted", "2vb1.mdt"
)


@pytest.fixture(scope="module")
def protein_trajectory():
    protein_trajectory = HDFTrajectoryInputData(traj_2vb1)
    return protein_trajectory.trajectory


def test_select_element_returns_true_as_match_exist(
    protein_trajectory,
):
    exists = select_element(protein_trajectory, "S", check_exists=True)
    assert exists


def test_select_element_returns_false_as_match_does_not_exist(
    protein_trajectory,
):
    exists = select_element(protein_trajectory, "Si", check_exists=True)
    assert not exists


def test_select_element_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_element(protein_trajectory, "S")
    assert len(selection) == 10


def test_select_hs_on_carbon_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_hs_on_element(protein_trajectory, "C")
    assert len(selection) == 696


def test_select_hs_on_nitrogen_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_hs_on_element(protein_trajectory, "N")
    assert len(selection) == 243


def test_select_hs_on_oxygen_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_hs_on_element(protein_trajectory, "O")
    assert len(selection) == 19184


def test_select_hs_on_sulfur_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_hs_on_element(protein_trajectory, "S")
    assert len(selection) == 0


def test_select_hs_on_silicon_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_hs_on_element(protein_trajectory, "Si")
    assert len(selection) == 0


def test_select_hs_on_heteroatom_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_hs_on_heteroatom(protein_trajectory)
    assert len(selection) == 19427


def test_select_dummy_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_dummy(protein_trajectory)
    assert len(selection) == 0

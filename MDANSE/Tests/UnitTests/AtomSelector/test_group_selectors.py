import os
import pytest
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.AtomSelector.group_selectors import (
    select_primary_amine,
    select_hydroxy,
    select_methyl,
    select_phosphate,
    select_sulphate,
    select_thiol,
)


traj_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Converted", "2vb1.mdt"
)
traj_1gip = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Converted", "1gip.mdt"
)


@pytest.fixture(scope="module")
def protein_trajectory():
    protein_trajectory = HDFTrajectoryInputData(traj_2vb1)
    return protein_trajectory.trajectory


@pytest.fixture(scope="module")
def nucleic_acid_chemical_system():
    protein_trajectory = HDFTrajectoryInputData(traj_1gip)
    return protein_trajectory.trajectory


def test_select_primary_amine_returns_true_as_match_exists(
    protein_trajectory,
):
    exists = select_primary_amine(protein_trajectory, check_exists=True)
    assert exists


def test_select_sulphate_returns_false_as_match_does_not_exist(
    nucleic_acid_chemical_system,
):
    exists = select_sulphate(nucleic_acid_chemical_system, check_exists=True)
    assert not exists


def test_select_primary_amine_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_primary_amine(protein_trajectory)
    assert len(selection) == 117


def test_select_hydroxy_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_hydroxy(protein_trajectory)
    assert len(selection) == 28786


def test_select_methyl_returns_correct_number_of_atom_matches(protein_trajectory):
    selection = select_methyl(protein_trajectory)
    assert len(selection) == 244


def test_select_phosphate_returns_correct_number_of_atom_matches(
    nucleic_acid_chemical_system,
):
    selection = select_phosphate(nucleic_acid_chemical_system)
    assert len(selection) == 110


def test_select_sulphate_returns_correct_number_of_atom_matches(
    nucleic_acid_chemical_system,
):
    selection = select_sulphate(nucleic_acid_chemical_system)
    assert len(selection) == 0


def test_select_thiol_returns_correct_number_of_atoms_matches(protein_trajectory):
    selection = select_thiol(protein_trajectory)
    assert len(selection) == 0

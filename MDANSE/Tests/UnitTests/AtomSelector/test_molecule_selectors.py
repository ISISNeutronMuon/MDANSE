import os
import pytest
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.AtomSelector.molecule_selectors import select_water


traj_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Converted", "2vb1.mdt"
)


@pytest.fixture(scope="module")
def protein_trajectory():
    protein_trajectory = HDFTrajectoryInputData(traj_2vb1)
    return protein_trajectory.trajectory


def test_select_water_returns_true_as_match_exists(
    protein_trajectory,
):
    exists = select_water(protein_trajectory, check_exists=True)
    assert exists


def test_select_water_returns_correct_number_of_atom_matches(
    protein_trajectory,
):
    selection = select_water(protein_trajectory)
    assert len(selection) == 28746

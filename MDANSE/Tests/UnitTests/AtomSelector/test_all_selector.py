import os
import pytest
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.AtomSelector.all_selector import select_all


traj_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Converted", "2vb1.mdt"
)


@pytest.fixture(scope="module")
def protein_trajectory():
    protein_trajectory = HDFTrajectoryInputData(traj_2vb1)
    return protein_trajectory.trajectory


def test_select_all_returns_correct_number_of_atoms_matches(protein_trajectory):
    selection = select_all(protein_trajectory)
    assert len(selection) == 30714

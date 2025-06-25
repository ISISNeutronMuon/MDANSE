import pytest
from test_helpers.paths import CONV_DIR

from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.MolecularDynamics.Trajectory import Trajectory

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"


@pytest.fixture(scope="module")
def trajectory():
    trajectory = Trajectory(short_traj)
    yield trajectory


@pytest.mark.parametrize("output_unit", ["Angstrom", "Bohr", "nm", "pm"])
@pytest.mark.parametrize("output_format", ["vasp", "xyz", "turbomole", "abinit-in"])
def test_avg_structure(tmp_path, trajectory, output_unit, output_format):
    temp_name = tmp_path / "output"
    parameters = {
        "frames": (0, 10, 1),
        "output_units": output_unit,
        "fold": True,
        "output_files": (temp_name, output_format, "INFO"),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
    }
    temp = IJob.create("AverageStructure")
    temp.run(parameters, status=True)

    assert temp_name.is_file()

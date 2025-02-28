import tempfile
import os
from os import path
import pytest

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.paths import CONV_DIR

short_traj = CONV_DIR / "short_trajectory_after_changes.mdt"

@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


@pytest.mark.parametrize("qvector_generator", IQVectors.indirect_subclasses())
def test_disf(tmp_path, trajectory, qvector_generator):
    temp_name = tmp_path / "output"
    out_file = temp_name.with_suffix(".mda")
    log_file = temp_name.with_suffix(".log")

    parameters = {
        "atom_selection": None,
        "atom_transmutation": None,
        "frames": (0, 10, 1, 5),
        "instrument_resolution": ("Ideal", {}),
        "output_files": (temp_name, ("MDAFormat",), "INFO"),
        "running_mode": ("single-core",),
        "trajectory": short_traj,
        "weights": "b_incoherent2",
    }

    instance = IQVectors.create(qvector_generator, trajectory._data.configuration())
    qvector_defaults = {
        name: value[1]["default"] for name, value in instance.settings.items()
    }

    print(qvector_generator)
    print(qvector_defaults)

    if len(qvector_defaults) < 1:
        return

    parameters["q_vectors"] = (qvector_generator, qvector_defaults)

    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)

    assert out_file.is_file()
    assert log_file.is_file()

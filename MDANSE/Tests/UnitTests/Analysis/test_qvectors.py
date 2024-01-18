import sys
import tempfile
import os
from os import path
import pytest
from icecream import ic
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)
ic.disable()
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "..", "Data",
    "short_trajectory_after_changes.mdt")


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


def test_disf(trajectory):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("MDAFormat",))
    parameters["running_mode"] = ("monoprocessor",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent2"
    for qvector_generator in IQVectors.subclasses():
        instance = IQVectors.create(qvector_generator, trajectory.chemical_system)
        qvector_defaults = {
            name: value[1]["default"] for name, value in instance.settings.items()
        }
        if len(qvector_defaults) < 1:
            continue
        print(qvector_generator)
        print(qvector_defaults)
        parameters["q_vectors"] = (qvector_generator, qvector_defaults)
        disf = IJob.create("DynamicIncoherentStructureFactor")
        disf.run(parameters, status=True)
        assert path.exists(temp_name + ".mda")
        assert path.isfile(temp_name + ".mda")
        os.remove(temp_name + ".mda")

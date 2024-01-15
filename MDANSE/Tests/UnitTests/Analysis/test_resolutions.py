import sys
import tempfile
import os
from os import path
import pytest
from icecream import ic
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)
from MDANSE.Framework.Jobs.IJob import IJob
from ..Data.data import mol_traj as short_traj

sys.setrecursionlimit(100000)
ic.disable()

_, just_filename = path.split(short_traj)

# now we have the following variables related to the trajectory:
# 1. short_traj (str) - full path to the trajectory
# 2. just_filename (str) - filename of the trajectory
# 3. trajectory (pytest.fixture) - returns an instance of HDFTrajectoryInputData


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


def test_disf(trajectory):
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["q_vectors"] = (
        "SphericalLatticeQVectors",
        {"seed": 0, "shells": (5.0, 36, 10.0), "n_vectors": 10, "width": 9.0}
    )
    parameters["running_mode"] = ("monoprocessor",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent2"
    for resolution_generator in IInstrumentResolution.subclasses():
        temp_name = tempfile.mktemp()
        parameters["output_files"] = (temp_name, ("HDFFormat",))
        instance = IInstrumentResolution.create(resolution_generator)
        resolution_defaults = {
            name: value[1]["default"] for name, value in instance.settings.items()
        }
        print(resolution_generator)
        print(resolution_defaults)
        parameters["instrument_resolution"] = (
            resolution_generator,
            resolution_defaults,
        )
        disf = IJob.create("DynamicIncoherentStructureFactor")
        disf.run(parameters, status=True)
        assert path.exists(temp_name + ".h5")
        assert path.isfile(temp_name + ".h5")
        os.remove(temp_name + ".h5")

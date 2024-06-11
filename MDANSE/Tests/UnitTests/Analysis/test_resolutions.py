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


sys.setrecursionlimit(100000)
ic.disable()
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "short_trajectory_after_changes.mdt",
)


@pytest.fixture(scope="module")
def trajectory():
    trajectory = HDFTrajectoryInputData(short_traj)
    yield trajectory


def test_disf(trajectory):
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["q_vectors"] = (
        "SphericalLatticeQVectors",
        {"seed": 0, "shells": (5.0, 36, 10.0), "n_vectors": 10, "width": 9.0},
    )
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent2"
    for resolution_generator in IInstrumentResolution.subclasses():
        temp_name = tempfile.mktemp()
        parameters["output_files"] = (temp_name, ("MDAFormat",))
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
        assert path.exists(temp_name + ".mda")
        assert path.isfile(temp_name + ".mda")
        os.remove(temp_name + ".mda")


list_of_resolutions = IInstrumentResolution.subclasses()


@pytest.mark.parametrize("resolution_generator", list_of_resolutions)
def test_dos_text(trajectory, resolution_generator):
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["q_vectors"] = (
        "SphericalLatticeQVectors",
        {"seed": 0, "shells": (5.0, 36, 10.0), "n_vectors": 10, "width": 9.0},
    )
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent2"
    temp_name = tempfile.mktemp()
    parameters["output_files"] = (temp_name, ("TextFormat",))
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
    disf = IJob.create("DensityOfStates")
    disf.run(parameters, status=True)
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")

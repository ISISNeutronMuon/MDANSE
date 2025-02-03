import tempfile
import os
from os import path

import h5py
import numpy as np
import pytest

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import (
    IInstrumentResolution,
)
from MDANSE.Framework.Jobs.IJob import IJob


short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Converted",
    "short_trajectory_after_changes.mdt",
)
result_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Results",
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
        parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
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
        assert path.exists(temp_name + ".log")
        assert path.isfile(temp_name + ".log")
        os.remove(temp_name + ".log")


list_of_resolutions = IInstrumentResolution.subclasses()


@pytest.mark.parametrize("resolution_generator", list_of_resolutions)
def test_dos(trajectory, resolution_generator):
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1, 5)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent2"
    temp_name = tempfile.mktemp()
    parameters["output_files"] = (temp_name, ("MDAFormat", "TextFormat"), "INFO")
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
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    result_file = os.path.join(
        result_dir, f"dos_{resolution_generator}.mda")

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        np.testing.assert_array_almost_equal(actual["/dos_Cu"], desired["/dos_Cu"])
        np.testing.assert_array_almost_equal(actual["/dos_S"], desired["/dos_S"])
        np.testing.assert_array_almost_equal(actual["/dos_Sb"], desired["/dos_Sb"])
        np.testing.assert_array_almost_equal(actual["/dos_total"], desired["/dos_total"])
        np.testing.assert_array_almost_equal(actual["/vacf_Cu"], desired["/vacf_Cu"])
        np.testing.assert_array_almost_equal(actual["/vacf_S"], desired["/vacf_S"])
        np.testing.assert_array_almost_equal(actual["/vacf_Sb"], desired["/vacf_Sb"])
        np.testing.assert_array_almost_equal(actual["/vacf_total"], desired["/vacf_total"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + "_text.tar")
    assert path.isfile(temp_name + "_text.tar")
    os.remove(temp_name + "_text.tar")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")

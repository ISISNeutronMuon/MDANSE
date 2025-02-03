import tempfile
import os
from os import path

import numpy as np
import h5py
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

# Mean Square Displacements can accept many parameters, most of them optional
# settings['trajectory']=('hdf_trajectory',{})
# settings['frames']=('frames', {"dependencies":{'trajectory':'trajectory'}})
# settings['projection']=('projection', {"label":"project coordinates"})
# settings['atom_selection']=('atom_selection',{"dependencies":{'trajectory':'trajectory'}})
# settings['grouping_level']=('grouping_level',{"dependencies":{'trajectory':'trajectory','atom_selection':'atom_selection', 'atom_transmutation':'atom_transmutation'}})
# settings['atom_transmutation']=('atom_transmutation',{"dependencies":{'trajectory':'trajectory', 'atom_selection':'atom_selection'}})
# settings['weights']=('weights',{"dependencies":{"atom_selection":"atom_selection"}})
# settings['output_files']=('output_files', {"formats":["hdf","netcdf","ascii","svg"]})
# settings['running_mode']=('running_mode',{})


def test_basic_meansquare():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1, 5)
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    msd = IJob.create("MeanSquareDisplacement")
    msd.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    result_file = os.path.join(result_dir, "basic_meansquare.mda")

    with h5py.File(temp_name + ".mda") as actual,  h5py.File(result_file) as desired:
        np.testing.assert_array_almost_equal(actual["/msd_Cu"], desired["/msd_Cu"])
        np.testing.assert_array_almost_equal(actual["/msd_S"], desired["/msd_S"])
        np.testing.assert_array_almost_equal(actual["/msd_Sb"], desired["/msd_Sb"])
        np.testing.assert_array_almost_equal(actual["/msd_total"], desired["/msd_total"])

    os.remove(temp_name + ".mda")
    assert path.exists(temp_name + ".log")
    assert path.isfile(temp_name + ".log")
    os.remove(temp_name + ".log")


def test_parallel_meansquare():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1, 5)
    parameters["output_files"] = (temp_name, ("MDAFormat",), "INFO")
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    msd = IJob.create("MeanSquareDisplacement")
    msd.run(parameters, status=True)
    temp_name2 = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1, 5)
    parameters["output_files"] = (temp_name2, ("MDAFormat",), "INFO")
    parameters["running_mode"] = ("multicore", -4)
    parameters["trajectory"] = short_traj
    msd_par = IJob.create("MeanSquareDisplacement")
    msd_par.run(parameters, status=True)
    with (
        h5py.File(temp_name + ".mda") as single,
        h5py.File(temp_name2 + ".mda") as parallel,
    ):
        for kk in single.keys():
            if not "metadata" in kk:
                np.testing.assert_array_almost_equal(
                    np.array(single[kk]), np.array(parallel[kk])
                )
    os.remove(temp_name + ".mda")
    os.remove(temp_name2 + ".mda")

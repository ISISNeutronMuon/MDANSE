import sys
import tempfile
import os
from os import path
from icecream import ic
import numpy as np
import h5py
from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)
ic.disable()
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "short_trajectory_after_changes.mdt",
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
    parameters["frames"] = (0, 10, 1)
    parameters["output_files"] = (temp_name, ("MDAFormat",))
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    msd = IJob.create("MeanSquareDisplacement")
    msd.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")


def test_parallel_meansquare():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["output_files"] = (temp_name, ("MDAFormat",))
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    msd = IJob.create("MeanSquareDisplacement")
    msd.run(parameters, status=True)
    temp_name2 = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["output_files"] = (temp_name2, ("MDAFormat",))
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
                assert np.allclose(np.array(single[kk]), np.array(parallel[kk]), 1e-5, 1e-4)
    os.remove(temp_name + ".mda")
    os.remove(temp_name2 + ".mda")


def test_atom_selection():
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["frames"] = (0, 10, 1)
    parameters["output_files"] = (temp_name, ("MDAFormat",))
    parameters["running_mode"] = ("single-core",)
    parameters["trajectory"] = short_traj
    msd = IJob.create("MeanSquareDisplacement")
    msd.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")

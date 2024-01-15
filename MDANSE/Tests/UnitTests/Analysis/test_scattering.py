import sys
import tempfile
import os
from os import path
import pytest
from icecream import ic
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
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


@pytest.fixture(scope="module")
def qvector_spherical_lattice(trajectory):
    return (
        "SphericalLatticeQVectors",
        {"seed": 0, "shells": (5.0, 36, 10.0), "n_vectors": 10, "width": 9.0}
    )


def test_dcsf(trajectory, qvector_spherical_lattice):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("HDFFormat",))
    parameters["q_vectors"] = qvector_spherical_lattice
    parameters["running_mode"] = ("monoprocessor",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_coherent"
    dcsf = IJob.create("DynamicCoherentStructureFactor")
    dcsf.run(parameters, status=True)
    assert path.exists(temp_name + ".h5")
    assert path.isfile(temp_name + ".h5")
    os.remove(temp_name + ".h5")


def test_disf(trajectory, qvector_spherical_lattice):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("HDFFormat",))
    parameters["q_vectors"] = qvector_spherical_lattice
    parameters["running_mode"] = ("monoprocessor",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent2"
    disf = IJob.create("DynamicIncoherentStructureFactor")
    disf.run(parameters, status=True)
    assert path.exists(temp_name + ".h5")
    assert path.isfile(temp_name + ".h5")
    os.remove(temp_name + ".h5")


def test_eisf(trajectory, qvector_spherical_lattice):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1)
    parameters["output_files"] = (temp_name, ("HDFFormat",))
    parameters["q_vectors"] = qvector_spherical_lattice
    parameters["running_mode"] = ("monoprocessor",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent"
    eisf = IJob.create("ElasticIncoherentStructureFactor")
    eisf.run(parameters, status=True)
    assert path.exists(temp_name + ".h5")
    assert path.isfile(temp_name + ".h5")
    os.remove(temp_name + ".h5")


def test_gdisf(trajectory):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters["atom_selection"] = None
    parameters["atom_transmutation"] = None
    parameters["frames"] = (0, 10, 1)
    parameters["instrument_resolution"] = ("Ideal", {})
    parameters["output_files"] = (temp_name, ("HDFFormat",))
    parameters["q_shells"] = (2.0, 12.2, 2.0)
    parameters["running_mode"] = ("monoprocessor",)
    parameters["trajectory"] = short_traj
    parameters["weights"] = "b_incoherent2"
    gdisf = IJob.create("GaussianDynamicIncoherentStructureFactor")
    gdisf.run(parameters, status=True)
    assert path.exists(temp_name + ".h5")
    assert path.isfile(temp_name + ".h5")
    os.remove(temp_name + ".h5")


# def test_ndtsf(trajectory, qvector_spherical_lattice):
#     temp_name = tempfile.mktemp()
#     parameters = {}
#     parameters['atom_selection'] = None
#     parameters['atom_transmutation'] = None
#     parameters['frames'] = (0, 10, 1)
#     parameters['instrument_resolution'] = ('IdealResolution', {})
#     parameters['output_files'] = (temp_name, ('HDFFormat',))
#     parameters['q_vectors'] = qvector_spherical_lattice
#     parameters['running_mode'] = ('monoprocessor',)
#     parameters['trajectory'] = short_traj
#     parameters['weights'] = 'b_incoherent2'
#     ndtsf = REGISTRY['job']['ndtsf']()
#     ndtsf.run(parameters,status=True)
#     assert path.exists(temp_name + '.h5')
#     assert path.isfile(temp_name + '.h5')
#     os.remove(temp_name + '.h5')


import sys
import tempfile
import os
from os import path

import pytest
from icecream import ic
import numpy as np
import h5py

from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE

from ..Data.data import short_traj

sys.setrecursionlimit(100000)
ic.disable()

_, just_filename = path.split(short_traj)

# now we have the following variables related to the trajectory:
# 1. short_traj (str) - full path to the trajectory
# 2. just_filename (str) - filename of the trajectory
# 3. trajectory (pytest.fixture) - returns an instance of HDFTrajectoryInputData

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

@pytest.fixture(scope="module")
def trajectory():
    trajectory = REGISTRY["input_data"]["hdf_trajectory"](short_traj)
    yield trajectory

def test_basic_meansquare(trajectory):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters['frames'] = (0, 10, 1)
    parameters['output_files'] = (temp_name, ('hdf',))
    parameters['running_mode'] = ('monoprocessor',)
    parameters['trajectory'] = short_traj
    msd = REGISTRY['job']['msd']()
    msd.run(parameters,status=True)
    assert path.exists(temp_name + '.h5')
    assert path.isfile(temp_name + '.h5')
    os.remove(temp_name + '.h5')

def test_parallel_meansquare(trajectory):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters['frames'] = (0, 10, 1)
    parameters['output_files'] = (temp_name, ('hdf',))
    parameters['running_mode'] = ('monoprocessor',)
    parameters['trajectory'] = short_traj
    msd = REGISTRY['job']['msd']()
    msd.run(parameters,status=True)
    temp_name2 = tempfile.mktemp()
    parameters = {}
    parameters['frames'] = (0, 10, 1)
    parameters['output_files'] = (temp_name2, ('hdf',))
    parameters['running_mode'] = ('threadpool',4)
    parameters['trajectory'] = short_traj
    msd_par = REGISTRY['job']['msd']()
    msd_par.run(parameters,status=True)
    single = h5py.File(temp_name + '.h5')
    parallel = h5py.File(temp_name2 + '.h5')
    for kk in single.keys():
        assert np.allclose(np.array(single[kk]), np.array(parallel[kk]), 1e-5, 1e-4)
    os.remove(temp_name + '.h5')
    os.remove(temp_name2 + '.h5')

def test_atom_selection(trajectory):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters['frames'] = (0, 10, 1)
    parameters['output_files'] = (temp_name, ('hdf',))
    parameters['running_mode'] = ('monoprocessor',)
    parameters['trajectory'] = short_traj
    msd = REGISTRY['job']['msd']()
    msd.run(parameters,status=True)
    assert path.exists(temp_name + '.h5')
    assert path.isfile(temp_name + '.h5')
    os.remove(temp_name + '.h5')

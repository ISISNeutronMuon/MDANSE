
import sys
import tempfile
import os
from os import path

import pytest
from icecream import ic
import numpy as np
import h5py

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.UserDefinitionStore import UD_STORE

from ..Data.data import short_traj

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

@pytest.mark.parametrize('interp_order',[1,2,3])
def test_temperature(trajectory, interp_order):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters['frames'] = (0, 10, 1)
    parameters['interpolation_order'] = interp_order
    parameters['output_files'] = (temp_name, ('HDFFormat',))
    parameters['running_mode'] = ('monoprocessor',)
    parameters['trajectory'] = short_traj
    temp = IJob.create('Temperature')
    temp.run(parameters,status=True)
    assert path.exists(temp_name + '.h5')
    assert path.isfile(temp_name + '.h5')
    os.remove(temp_name + '.h5')

@pytest.mark.parametrize('interp_order',[1,2,3])
def test_temperature_nonzero(trajectory, interp_order):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters['frames'] = (0, 10, 1)
    parameters['interpolation_order'] = interp_order
    parameters['output_files'] = (temp_name, ('HDFFormat',))
    parameters['running_mode'] = ('monoprocessor',)
    parameters['trajectory'] = short_traj
    temp = IJob.create('Temperature')
    temp.run(parameters,status=True)
    results = h5py.File(temp_name + '.h5')
    print(results.keys())
    temperature = np.array(results['/temperature'])
    os.remove(temp_name + '.h5')
    assert np.all(temperature > 0.0)

def test_density(trajectory):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters['frames'] = (0, 10, 1)
    parameters['output_files'] = (temp_name, ('HDFFormat',))
    parameters['running_mode'] = ('monoprocessor',)
    parameters['trajectory'] = short_traj
    den = IJob.create('Density')
    den.run(parameters,status=True)
    assert path.exists(temp_name + '.h5')
    assert path.isfile(temp_name + '.h5')
    os.remove(temp_name + '.h5')

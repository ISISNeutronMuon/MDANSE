import sys
import tempfile
import os
from os import path

import pytest
from icecream import ic
import numpy as np

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

@pytest.fixture(scope="module")
def trajectory():
    trajectory = REGISTRY["input_data"]["hdf_trajectory"](short_traj)
    yield trajectory

@pytest.mark.parametrize('interp_order, normalise',[("1st order", True),
                                                    ("2nd order", True),
                                                    ("3rd order", True),
                                                    ("1st order", False),
                                                    ("2nd order", False),
                                                    ("3rd order", False),])
def test_vacf(trajectory, interp_order, normalise):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters['frames'] = (0, 10, 1)
    parameters['interpolation_order'] = interp_order
    parameters['output_files'] = (temp_name, ('hdf',))
    parameters['running_mode'] = ('monoprocessor',)
    parameters['normalize'] = normalise
    parameters['trajectory'] = short_traj
    vacf = REGISTRY['job']['vacf']()
    vacf.run(parameters,status=True)
    assert path.exists(temp_name + '.h5')
    assert path.isfile(temp_name + '.h5')
    os.remove(temp_name + '.h5')
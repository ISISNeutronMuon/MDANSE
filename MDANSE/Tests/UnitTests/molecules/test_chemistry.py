import sys
import tempfile
import os
from os import path

import pytest
from icecream import ic
import numpy as np
from rdkit.Chem import Mol

from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData

short_traj = 'co2gas_md3.h5'

@pytest.fixture(scope="module")
def trajectory():
    trajectory = REGISTRY["input_data"]["hdf_trajectory"](short_traj)
    yield trajectory

def test_molecule_finder(trajectory: HDFTrajectoryInputData):
    chem_system = trajectory.chemical_system
    configuration = chem_system.configuration
    coordinates = configuration._variables['coordinates']
    print(coordinates.shape)
    assert False

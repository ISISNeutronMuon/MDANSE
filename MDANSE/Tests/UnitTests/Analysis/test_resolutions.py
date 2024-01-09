
import sys
import tempfile
import os
from os import path

import pytest
from icecream import ic
import numpy as np

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.QVectors.IQVectors import IQVectors
from MDANSE.Framework.InstrumentResolutions.IInstrumentResolution import IInstrumentResolution
from MDANSE.Framework.Jobs.IJob import IJob
from MDANSE.Framework.UserDefinitionStore import UD_STORE

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
    out_name = "test_qvec"
    generator = IQVectors.create("SphericalLatticeQVectors", trajectory.chemical_system)
    q_parameters = {'seed' : 0,
                'shells' : (5.0, 36, 10.0),
                'n_vectors' : 10,
                'width' : 9.0}
    generator.setup(q_parameters)
    generator.generate()
    UD_STORE.load()
    if not UD_STORE.has_definition(just_filename, "q_vectors", out_name):
        ud = {}
        ud['parameters'] = (generator._type,generator._configuration)
        ud['generator'] = generator._type
        ud['q_vectors'] = generator._configuration['q_vectors']
        ud['is_lattice'] = generator.is_lattice
        UD_STORE.set_definition(just_filename, "q_vectors", out_name, ud)
        UD_STORE.save()
    return out_name

def test_disf(trajectory, qvector_spherical_lattice):
    parameters = {}
    parameters['atom_selection'] = None
    parameters['atom_transmutation'] = None
    parameters['frames'] = (0, 10, 1)
    parameters['instrument_resolution'] = ('Ideal', {})
    parameters['q_vectors'] = qvector_spherical_lattice
    parameters['running_mode'] = ('monoprocessor',)
    parameters['trajectory'] = short_traj
    parameters['weights'] = 'b_incoherent2'
    for resolution_generator in IInstrumentResolution.subclasses():
        temp_name = tempfile.mktemp()
        parameters['output_files'] = (temp_name, ('HDFFormat',))
        instance = IInstrumentResolution.create(resolution_generator)
        resolution_defaults = {name: value[1]['default'] for name, value in instance.settings.items()}
        print(resolution_generator)
        print(resolution_defaults)
        parameters['instrument_resolution'] = (resolution_generator, resolution_defaults)
        disf = IJob.create("DynamicIncoherentStructureFactor")
        disf.run(parameters,status=True)
        assert path.exists(temp_name + '.h5')
        assert path.isfile(temp_name + '.h5')
        os.remove(temp_name + '.h5')

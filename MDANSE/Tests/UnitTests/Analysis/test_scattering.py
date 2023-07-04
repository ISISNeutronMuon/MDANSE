
import sys
import tempfile
from os import path

import pytest
from icecream import ic

from MDANSE import REGISTRY
from MDANSE.Framework.UserDefinitionStore import UD_STORE

from ..Data.data import short_traj

sys.setrecursionlimit(100000)
ic.disable()

_, just_filename = path.split(short_traj)

@pytest.fixture(scope="module")
def trajectory():
    trajectory = REGISTRY["input_data"]["hdf_trajectory"](short_traj)
    yield trajectory

@pytest.fixture(scope="module")
def qvector_spherical_lattice(trajectory):
    out_name = "test_qvec"
    generator = REGISTRY["q_vectors"]["spherical_lattice"](trajectory.chemical_system)
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

def test_dcsf(trajectory, qvector_spherical_lattice):
    temp_name = tempfile.mktemp()
    parameters = {}
    parameters['atom_selection'] = None
    parameters['atom_transmutation'] = None
    parameters['frames'] = (0, 10, 1)
    parameters['instrument_resolution'] = ('ideal', {})
    parameters['output_files'] = (temp_name, ('hdf',))
    parameters['q_vectors'] = qvector_spherical_lattice
    parameters['running_mode'] = ('monoprocessor',)
    parameters['trajectory'] = short_traj
    parameters['weights'] = 'b_coherent'
    dcsf = REGISTRY['job']['dcsf']()
    dcsf.run(parameters,status=True)
    assert path.exists(temp_name + '.h5')
    assert path.isfile(temp_name + '.h5')


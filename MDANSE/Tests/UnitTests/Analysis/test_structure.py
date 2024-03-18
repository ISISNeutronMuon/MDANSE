import sys
import tempfile
import os
from os import path
import pytest
from icecream import ic
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Framework.Jobs.IJob import IJob


sys.setrecursionlimit(100000)
ic.disable()
short_traj = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "..",
    "Data",
    "short_trajectory_after_changes.mdt",
)

################################################################
# Job parameters                                               #
################################################################
@pytest.fixture(scope="function")
def parameters():
    parameters = {}
    # parameters['atom_selection'] = None
    # parameters['atom_transmutation'] = None
    # parameters['frames'] = (0, 1000, 1)
    parameters["trajectory"] = short_traj
    parameters['running_mode'] = ('threadpool', 4)
    parameters['q_vectors'] = ('SphericalLatticeQVectors',{
            "seed":  0,
            "shells":  (0, 5.0, 0.5),
            "n_vectors": 100,
            "width": 0.5,
            })
    parameters['q_values'] = (0.0, 10.0, 0.1)
    parameters['r_values'] = (0.0, 10.0, 0.1)
    parameters['per_axis'] = False
    parameters['reference_direction'] = (0, 0, 1)
    parameters['instrument_resolution'] = ('Gaussian', {'sigma' : 1.0, 'mu': 0.0})
    parameters['interpolation_order'] = '3rd order'
    parameters['projection'] = None
    parameters['normalize'] = True
    parameters['grouping_level'] = 'atom'
    parameters['weights'] = 'equal'
    return parameters

@pytest.mark.parametrize(
    "job_type",
    [
        "RadiusOfGyration",
        # "AreaPerMolecule",
        "SolventAccessibleSurface",
        "RootMeanSquareDeviation",
        "RootMeanSquareFluctuation",
        "DensityProfile",
        "MolecularTrace",
        "Voronoi",
        "Eccentricity",
    ],
)
def test_structure_analysis(parameters, job_type):
    temp_name = tempfile.mktemp()
    parameters["output_files"] = (temp_name, ("MDAFormat",))
    job = IJob.create(job_type)
    job.run(parameters, status=True)
    assert path.exists(temp_name + ".mda")
    assert path.isfile(temp_name + ".mda")
    os.remove(temp_name + ".mda")

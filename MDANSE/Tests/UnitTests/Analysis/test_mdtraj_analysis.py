from collections.abc import Iterable
import numpy as np
import pytest
from numpy.testing import assert_allclose
from MDANSE.Framework.Jobs.IJob import IJob
from test_helpers.compare_hdf5 import compare_hdf5
from test_helpers.paths import CONV_DIR, RESULTS_DIR

from MDANSE.mdtraj.trajectory import build_mdtraj_topology, build_mdtraj_trajectory
from MDANSE.mdtraj.analysis import mdtraj_initial_params
from MDANSE.MolecularDynamics.Trajectory import Trajectory

short_traj = CONV_DIR / "named_molecules.mdt"


@pytest.fixture(scope="module")
def mdanse_traj() -> Iterable[Trajectory]:
    mdanse_traj = Trajectory(short_traj)
    yield mdanse_traj
    mdanse_traj.close()


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
    parameters["running_mode"] = ("multicore", -4)
    parameters["q_vectors"] = (
        "SphericalLatticeQVectors",
        {
            "seed": 0,
            "shells": (0, 5.0, 0.5),
            "n_vectors": 100,
            "width": 0.5,
        },
    )
    parameters["q_values"] = (0.0, 10.0, 0.1)
    parameters["r_values"] = (0.0, 10.0, 0.1)
    parameters["per_axis"] = False
    parameters["polynomial_order"] = 1
    parameters["molecule_name"] = "C1_O2"
    parameters["molecule_and_axis"] = ("C1_O2", 0)
    parameters["axis"] = "ab"
    parameters["reference_direction"] = (0, 0, 1)
    parameters["instrument_resolution"] = ("Gaussian", {"sigma": 1.0, "mu": 0.0})
    parameters["interpolation_order"] = "3rd order"
    parameters["projection"] = None
    parameters["grouping_level"] = "atom"
    parameters["weights"] = "equal"
    return parameters


def test_mdtraj_topology(mdanse_traj):
    new_topology = build_mdtraj_topology(mdanse_traj)
    assert len(list(new_topology.atoms)) == len(mdanse_traj.atom_names)


def test_mdtraj_trajectory(mdanse_traj):
    new_trajectory = build_mdtraj_trajectory(mdanse_traj)
    assert new_trajectory.n_atoms == mdanse_traj.get_total_natoms()
    

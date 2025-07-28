#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import os

import pytest
import numpy as np

from MDANSE.MolecularDynamics.MockTrajectory import MockTrajectory


file_wd = os.path.dirname(os.path.realpath(__file__))

mock_json = os.path.join(file_wd, "Data", "mock.json")


@pytest.fixture(scope="module")
def static_trajectory():
    """Returns a trajectory containing a single atom,
    which does not move.
    """
    traj = MockTrajectory(
        number_of_frames=10,
        box_repetitions=(1, 1, 1),
    )
    traj.set_coordinates(np.array([[1.0, 0.0, 0.0]]))
    return traj


@pytest.fixture
def full_trajectory():
    """Returns a trajectory containing muiltiple atoms,
    in a supercell, which move periodically.
    """
    traj = MockTrajectory(
        number_of_frames=100,
        atoms_in_box=("Si", "O", "H"),
        box_repetitions=(3, 3, 3),
        box_size=4.0 * np.eye(3),
        pbc=True,
    )
    traj.set_coordinates(np.array([[1.0, 1.0, 1.0], [1.0, 2.0, 1.0], [1.0, 2.0, 1.9]]))
    return traj


def test_trajectory_parameters(static_trajectory):
    assert len(static_trajectory) == 10
    assert len(static_trajectory.chemical_system.atom_list) == 1


def test_static_coordinates(static_trajectory):
    conf2 = static_trajectory[2]
    conf3 = static_trajectory[3]
    assert conf2["time"] != conf3["time"]
    assert np.all(conf2["coordinates"] == conf3["coordinates"])


def test_com_trajectory(static_trajectory):
    """Centre of Mass (COM) trajectory should be identical
    to the static trajectory, since the atoms never moved"""
    com_trajectory = static_trajectory.read_com_trajectory(
        list(range(static_trajectory._num_atoms_in_box)), 0, 10, 1
    )
    conf_static = static_trajectory[3]
    conf_com = com_trajectory[3]
    assert np.all(conf_static["coordinates"] == conf_com)


def test_modulation_single_atom(static_trajectory):
    static_trajectory.modulate_structure(
        np.array([[1.0, 1.0, 0.0]]), np.array([0.0, 0.0, 0.0]), 5, 0.2
    )
    conf2 = static_trajectory[2]
    conf3 = static_trajectory[3]
    assert conf2["time"] != conf3["time"]
    assert not np.all(conf2["coordinates"] == conf3["coordinates"])


def test_modulation_full(full_trajectory):
    full_trajectory.modulate_structure(
        np.array([[1.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]),
        np.array([0.0, 0.0, 0.0]),
        20,
        0.2,
    )
    conf_init = full_trajectory[0]
    conf_between = full_trajectory[2]
    conf_half = full_trajectory[10]
    conf_end = full_trajectory[20]
    assert np.allclose(conf_init["coordinates"], conf_half["coordinates"])
    assert np.allclose(conf_init["coordinates"], conf_end["coordinates"])
    assert not np.allclose(conf_init["coordinates"], conf_between["coordinates"])


def test_modulation_multiple(full_trajectory):
    full_trajectory.modulate_structure(
        np.array([[1.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]),
        np.array([0.0, 0.0, 0.0]),
        20,
        0.2,
    )
    full_trajectory.modulate_structure(
        np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]]),
        np.array([1.0, 0.0, 0.0]),
        10,
        0.1,
    )
    conf_init = full_trajectory[0]
    conf_between = full_trajectory[2]
    conf_half = full_trajectory[10]
    conf_end = full_trajectory[20]
    assert np.allclose(conf_init["coordinates"], conf_half["coordinates"])
    assert np.allclose(conf_init["coordinates"], conf_end["coordinates"])
    assert not np.allclose(conf_init["coordinates"], conf_between["coordinates"])


def test_from_json(full_trajectory):
    full_trajectory.modulate_structure(
        np.array([[1.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]),
        np.array([0.0, 0.0, 0.0]),
        20,
        0.2,
    )
    full_trajectory.modulate_structure(
        np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]]),
        np.array([1.0, 0.0, 0.0]),
        10,
        0.1,
    )
    instance = MockTrajectory.from_json(mock_json)
    assert full_trajectory._atom_types == instance.atom_types
    print(full_trajectory.coordinates(25) - instance.coordinates(25))
    assert np.allclose(full_trajectory.coordinates(25), instance.coordinates(25))
    assert not np.allclose(full_trajectory.coordinates(25), instance.coordinates(22))

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/UnitTests/TestElementsDatabase.py
# @brief     Implements module/class/test TestElementsDatabase
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

# MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
# ------------------------------------------------------------------------------------------
# Copyright (C)
# 2015- Eric C. Pellegrini Institut Laue-Langevin
# BP 156
# 6, rue Jules Horowitz
# 38042 Grenoble Cedex 9
# France
# pellegrini[at]ill.fr
# goret[at]ill.fr
# aoun[at]ill.fr
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

""" 
Created on 25.01.2024

@author: M. Bartkowiak
"""

import tempfile

import pytest
import numpy as np

from MDANSE.MolecularDynamics.MockTrajectory import MockTrajectory


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


@pytest.fixture(scope="module")
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
        static_trajectory._chemicalSystem.atoms, 0, 10, 1
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
        np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]]),
        np.array([1.0, 0.0, 0.0]),
        10,
        0.1,
    )
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

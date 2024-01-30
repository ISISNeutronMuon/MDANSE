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
Created on Feb 17, 2023

@author: Maciej Bartkowiak
"""

import pytest
import tempfile
import os

import numpy as np

from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.MolecularDynamics.Trajectory import Trajectory, TrajectoryWriter
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData

from MDANSE_GUI.PyQtGUI.MolecularViewer.readers.hdf5wrapper import HDF5Wrapper

N_ATOMS = 4
N_TIMESTEPS = 150


@pytest.fixture(scope="module")
def chemical_system():
    temp = ChemicalSystem("Dummy test system")
    nAtoms = N_ATOMS
    for i in range(nAtoms):
        temp.add_chemical_entity(Atom(symbol="H"))
    return temp


@pytest.fixture(scope="module")
def sample_configuration(chemical_system):
    unit_cell = 15.0 * np.eye(3)
    coords = np.empty((N_ATOMS, 3), dtype=float)
    coords[0] = [1.0, 1.0, 1.0]
    coords[1] = [1.0, 2.0, 1.0]
    coords[2] = [10.0, 1.0, 5.11]
    coords[3] = [10.0, 2.0, 5.09]
    temp = RealConfiguration(
        chemical_system,
        coords,
        # unit_cell
    )
    return temp


@pytest.fixture(scope="module")
def sample_trajectory(chemical_system, sample_configuration):
    # here we write to a file
    fdesc, fname = tempfile.mkstemp()
    os.close(fdesc)
    writer = TrajectoryWriter(fname, chemical_system, n_steps=N_TIMESTEPS)
    for n, ts in enumerate(np.arange(N_TIMESTEPS)):
        writer.chemical_system.configuration = sample_configuration
        writer.dump_configuration(ts)
    return fname


@pytest.fixture(scope="module")
def wrapper(sample_trajectory):
    traj_object = HDFTrajectoryInputData(sample_trajectory)
    wrapper = HDF5Wrapper(
        sample_trajectory, traj_object.trajectory, traj_object.chemical_system
    )
    return wrapper


def test_frame_read(wrapper: HDF5Wrapper):
    coords = wrapper.read_frame(0)
    assert len(coords.shape) == 2

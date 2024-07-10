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
import pytest
import tempfile
import os

import numpy as np

from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import RealConfiguration
from MDANSE.MolecularDynamics.Trajectory import Trajectory, TrajectoryWriter

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
def gzipped_trajectory(chemical_system, sample_configuration):
    # here we write to a file
    fdesc, fname = tempfile.mkstemp()
    os.close(fdesc)
    writer = TrajectoryWriter(
        fname, chemical_system, n_steps=N_TIMESTEPS, compression="gzip"
    )
    for n, ts in enumerate(np.arange(N_TIMESTEPS)):
        writer.chemical_system.configuration = sample_configuration
        writer.dump_configuration(ts)
    return fname


@pytest.fixture(scope="module")
def lzffed_trajectory(chemical_system, sample_configuration):
    # here we write to a file
    fdesc, fname = tempfile.mkstemp()
    os.close(fdesc)
    writer = TrajectoryWriter(
        fname, chemical_system, n_steps=N_TIMESTEPS, compression="lzf"
    )
    for n, ts in enumerate(np.arange(N_TIMESTEPS)):
        writer.chemical_system.configuration = sample_configuration
        writer.dump_configuration(ts)
    return fname


def test_identity(chemical_system):
    temp = ChemicalSystem("Dummy test system")
    nAtoms = N_ATOMS
    for i in range(nAtoms):
        temp.add_chemical_entity(Atom(symbol="H"))
    # assert(temp == chemical_system)
    assert chemical_system == chemical_system


def test_copy(chemical_system):
    original = chemical_system
    copied = chemical_system.copy()
    print(original.atom_list)
    print(original.number_of_atoms)
    print(copied.atom_list)
    print(copied.number_of_atoms)
    assert repr(original) == repr(copied)


def test_compression(sample_trajectory, gzipped_trajectory, lzffed_trajectory):
    size_uncompressed = os.stat(sample_trajectory).st_size
    size_gzipped = os.stat(gzipped_trajectory).st_size
    size_lzffed = os.stat(lzffed_trajectory).st_size
    assert size_gzipped < size_uncompressed
    assert size_lzffed < size_uncompressed


def test_losslessness(sample_trajectory, gzipped_trajectory, lzffed_trajectory):
    traj = Trajectory(sample_trajectory)
    traj_gz = Trajectory(gzipped_trajectory)
    traj_lzf = Trajectory(lzffed_trajectory)
    assert len(traj) == len(traj_gz)
    assert len(traj) == len(traj_lzf)
    for step_number in range(len(traj)):
        assert np.allclose(
            traj.coordinates(step_number), traj_gz.coordinates(step_number)
        )
        assert np.allclose(
            traj.coordinates(step_number), traj_lzf.coordinates(step_number)
        )

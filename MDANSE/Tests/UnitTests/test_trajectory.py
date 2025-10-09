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
import tempfile
import unittest
import numpy as np
from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import Trajectory, TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class TestTrajectory(unittest.TestCase):
    """ """

    def setUp(self):
        self._chemical_system = ChemicalSystem()
        self._nAtoms = 4
        self._chemical_system.initialise_atoms(self._nAtoms * ["H"])

    def test_write_trajectory(self):
        tf = tempfile.NamedTemporaryFile().name
        tw = TrajectoryWriter(tf, self._chemical_system, 10)

        allCoordinates = []
        allUnitCells = []
        allTimes = []
        for i in range(10):
            allTimes.append(i)
            allUnitCells.append(np.random.uniform(0, 10, (3, 3)))
            allCoordinates.append(np.random.uniform(0, 10, (self._nAtoms, 3)))
            conf = PeriodicRealConfiguration(
                self._chemical_system, allCoordinates[-1], UnitCell(allUnitCells[-1])
            )
            tw.dump_configuration(conf, i)

        tw.close()

        t = Trajectory(tf)

        for i in range(len(t)):
            self.assertTrue(
                np.allclose(t[i]["unit_cell"][:], allUnitCells[i], rtol=1.0e-6)
            )
            self.assertTrue(np.allclose(t[i]["time"], allTimes[i], rtol=1.0e-6))
            self.assertTrue(
                np.allclose(t[i]["coordinates"][:], allCoordinates[i], rtol=1.0e-6)
            )

        t.close()

    def test_write_trajectory_with_velocities(self):
        tf = tempfile.NamedTemporaryFile().name
        tw = TrajectoryWriter(tf, self._chemical_system, 10)

        allCoordinates = []
        allUnitCells = []
        allTimes = []
        allVelocities = []
        for i in range(10):
            allTimes.append(i)
            allUnitCells.append(np.random.uniform(0, 10, (3, 3)))
            allCoordinates.append(np.random.uniform(0, 10, (self._nAtoms, 3)))
            allVelocities.append(np.random.uniform(0, 10, (self._nAtoms, 3)))
            conf = PeriodicRealConfiguration(
                self._chemical_system, allCoordinates[-1], UnitCell(allUnitCells[-1])
            )
            conf.variables["velocities"] = allVelocities[-1]
            tw.dump_configuration(conf, i)

        tw.close()

        t = Trajectory(tf)

        for i in range(len(t)):
            self.assertTrue(
                np.allclose(t[i]["unit_cell"][:], allUnitCells[i], rtol=1.0e-6)
            )
            self.assertTrue(np.allclose(t[i]["time"], allTimes[i], rtol=1.0e-6))
            self.assertTrue(
                np.allclose(t[i]["coordinates"][:], allCoordinates[i], rtol=1.0e-6)
            )
            self.assertTrue(
                np.allclose(t[i]["velocities"][:], allVelocities[i], rtol=1.0e-6)
            )

        t.close()

    def test_write_trajectory_with_gradients(self):
        tf = tempfile.NamedTemporaryFile().name
        tw = TrajectoryWriter(tf, self._chemical_system, 10)

        allCoordinates = []
        allUnitCells = []
        allTimes = []
        allVelocities = []
        allGradients = []
        for i in range(10):
            allTimes.append(i)
            allUnitCells.append(np.random.uniform(0, 10, (3, 3)))
            allCoordinates.append(np.random.uniform(0, 10, (self._nAtoms, 3)))
            allVelocities.append(np.random.uniform(0, 10, (self._nAtoms, 3)))
            allGradients.append(np.random.uniform(0, 10, (self._nAtoms, 3)))
            conf = PeriodicRealConfiguration(
                self._chemical_system, allCoordinates[-1], UnitCell(allUnitCells[-1])
            )
            conf.variables["velocities"] = allVelocities[-1]
            conf.variables["gradients"] = allGradients[-1]
            tw.dump_configuration(conf, i)

        tw.close()

        t = Trajectory(tf)

        for i in range(len(t)):
            self.assertTrue(
                np.allclose(t[i]["unit_cell"][:], allUnitCells[i], rtol=1.0e-6)
            )
            self.assertTrue(np.allclose(t[i]["time"], allTimes[i], rtol=1.0e-6))
            self.assertTrue(
                np.allclose(t[i]["coordinates"][:], allCoordinates[i], rtol=1.0e-6)
            )
            self.assertTrue(
                np.allclose(t[i]["velocities"][:], allVelocities[i], rtol=1.0e-6)
            )
            self.assertTrue(
                np.allclose(t[i]["gradients"][:], allGradients[i], rtol=1.0e-6)
            )

        t.close()


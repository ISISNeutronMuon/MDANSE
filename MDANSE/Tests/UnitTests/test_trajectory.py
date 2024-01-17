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
Created on May 29, 2015

@author: Eric C. Pellegrini
"""
import tempfile
import unittest
import numpy as np
from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import PeriodicRealConfiguration
from MDANSE.MolecularDynamics.Trajectory import Trajectory, TrajectoryWriter
from MDANSE.MolecularDynamics.UnitCell import UnitCell


class TestTrajectory(unittest.TestCase):
    """ """

    def setUp(self):
        self._chemicalSystem = ChemicalSystem()
        self._nAtoms = 4

        for i in range(self._nAtoms):
            self._chemicalSystem.add_chemical_entity(Atom(symbol="H"))

    def test_write_trajectory(self):
        tf = tempfile.NamedTemporaryFile().name
        tw = TrajectoryWriter(tf, self._chemicalSystem, 10)

        allCoordinates = []
        allUnitCells = []
        allTimes = []
        for i in range(10):
            allTimes.append(i)
            allUnitCells.append(np.random.uniform(0, 10, (3, 3)))
            allCoordinates.append(np.random.uniform(0, 10, (self._nAtoms, 3)))
            conf = PeriodicRealConfiguration(
                self._chemicalSystem, allCoordinates[-1], UnitCell(allUnitCells[-1])
            )
            tw.chemical_system.configuration = conf
            tw.dump_configuration(i)

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
        tw = TrajectoryWriter(tf, self._chemicalSystem, 10)

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
                self._chemicalSystem, allCoordinates[-1], UnitCell(allUnitCells[-1])
            )
            conf.variables["velocities"] = allVelocities[-1]
            self._chemicalSystem.configuration = conf
            tw.dump_configuration(i)

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
        tw = TrajectoryWriter(tf, self._chemicalSystem, 10)

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
                self._chemicalSystem, allCoordinates[-1], UnitCell(allUnitCells[-1])
            )
            conf.variables["velocities"] = allVelocities[-1]
            conf.variables["gradients"] = allGradients[-1]
            self._chemicalSystem.configuration = conf
            tw.dump_configuration(i)

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

    def test_read_com_trajectory(self):
        tf = tempfile.NamedTemporaryFile().name
        tw = TrajectoryWriter(tf, self._chemicalSystem, 1)

        allCoordinates = []
        allUnitCells = []
        allTimes = []
        for i in range(1):
            allTimes.append(i)
            allUnitCells.append([[10.0, 0.0, 0.0], [0.0, 10.0, 0.0], [0.0, 0.0, 10.0]])
            allCoordinates.append(
                [[0.0, 0.0, 0.0], [8.0, 8.0, 8.0], [4.0, 4.0, 4.0], [2.0, 2.0, 2.0]]
            )
            conf = PeriodicRealConfiguration(
                self._chemicalSystem, allCoordinates[-1], UnitCell(allUnitCells[-1])
            )
            self._chemicalSystem.configuration = conf
            tw.dump_configuration(i)

        tw.close()

        t = Trajectory(tf)
        com_trajectory = t.read_com_trajectory(
            self._chemicalSystem.atoms, 0, 1, 1
        )
        self.assertTrue(np.allclose(com_trajectory, [[3.5, 3.5, 3.5]], rtol=1.0e-6))
        t.close()

# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/UnitTests/TestConfigurator.py
# @brief     Implements module/class/test TestConfigurator
#
# @homepage https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
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

import os
import unittest

import numpy

from MMTK.Trajectory import Trajectory

from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Projectors.IProjector import ProjectorError
from MDANSE.Framework.AtomSelectionParser import AtomSelectionParserError

TRAJECTORIES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "UserData",
    "Trajectories",
)


class TestConfigurator(unittest.TestCase):
    """Unittest for the configurators used to setup an analysis in MDANSE"""

    def setUp(self):
        self._configurable = Configurable()
        self._validTrajectory = Trajectory(
            None,
            os.path.join(
                "..",
                "..",
                "Data",
                "Trajectories",
                "MMTK",
                "waterbox_in_periodic_universe.nc",
            ),
            "r",
        )
        self._parameters = {}

    def tearDown(self):
        self._configurable.settings.clear()
        self._parameters.clear()

    def test_integer(self):
        """Test the integer configurator"""

        self._configurable.set_settings({"test_integer": ("integer", {})})

        # Case of a valid integer
        self._parameters["test_integer"] = 20
        self._configurable.setup(self._parameters)

        # Case of a float that will casted to an integer
        self._parameters["test_integer"] = 20.2
        self._configurable.setup(self._parameters)
        self.assertEqual(self._configurable["test_integer"]["value"], 20)

        # Case of a string that can be casted to an integer
        self._parameters["test_integer"] = "30"
        self._configurable.setup(self._parameters)
        self.assertEqual(self._configurable["test_integer"]["value"], 30)

        # Case of a string that cannot be casted to an integer
        self._parameters["test_integer"] = "xxxx"
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # Case of an object that cannot be casted to an integer
        self._parameters["test_integer"] = [1, 2]
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

    def test_float(self):
        """Test the float configurator"""

        self._configurable.set_settings({"test_float": ("float", {})})

        # Case of an integer that will be casted to a float
        self._parameters["test_float"] = 20
        self._configurable.setup(self._parameters)
        self.assertEqual(self._configurable["test_float"]["value"], 20.0)

        # Case of a float
        self._parameters["test_float"] = 20.2
        self._configurable.setup(self._parameters)
        self.assertEqual(self._configurable["test_float"]["value"], 20.2)

        # Case of a string that can be casted to a float
        self._parameters["test_float"] = "30.2"
        self._configurable.setup(self._parameters)
        self.assertEqual(self._configurable["test_float"]["value"], 30.2)

        # Case of a string that cannot be casted to a float
        self._parameters["test_float"] = "xxxx"
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # Case of an object that cannot be casted to a float
        self._parameters["test_float"] = [1, 2]
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

    def test_mmtk_trajectory(self):
        """Test the mmtk_trajectory configurator"""

        self._configurable.set_settings({"trajectory": ("mmtk_trajectory", {})})

        # Case of a valid trajectory
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._configurable.setup(self._parameters)

        # Case of an unknown trajectory
        self._parameters["trajectory"] = "fsfsdjkfjkfjs"
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # Case of an invalid type for input trajectory
        self._parameters["trajectory"] = 1
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # Case of an invalid type for input trajectory
        self._parameters["trajectory"] = [1, 2, 3]
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

    def test_projection(self):
        self._configurable.set_settings({"projection": ("projection", {})})

        data = numpy.random.uniform(0, 1, (10, 3))

        # Wrong parameters
        self._parameters["projection"] = 10
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        self._parameters["projection"] = [1, 2, 3, 4]
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # No projection - wrong projection type
        self._parameters["projection"] = (30, None)
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # No projection
        self._parameters["projection"] = None
        self._configurable.setup(self._parameters)
        proj = self._configurable["projection"]["projector"](data)
        self.assertTrue(numpy.array_equal(data, proj))

        self._parameters["projection"] = ("null", None)
        self._configurable.setup(self._parameters)
        proj = self._configurable["projection"]["projector"](data)
        self.assertTrue(numpy.array_equal(data, proj))

        # Axial projection - wrong parameters
        self._parameters["projection"] = ("tutu", (1, 0, 0))
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)
        self._parameters["projection"] = ("axial", (1, 0, 0, 2, 12, 25))
        self.assertRaises(ProjectorError, self._configurable.setup, self._parameters)
        self._parameters["projection"] = ("axial", 30)
        self.assertRaises(ProjectorError, self._configurable.setup, self._parameters)

        # Axial projection - null vector
        self._parameters["projection"] = ("axial", (0, 0, 0))
        self.assertRaises(ProjectorError, self._configurable.setup, self._parameters)

        # Axial projection
        self._parameters["projection"] = ("axial", (1, 0, 0))
        self._configurable.setup(self._parameters)
        proj = self._configurable["projection"]["projector"](data)
        self.assertTrue(numpy.array_equal(data[:, 0], proj[:, 0]))

        # Axial projection - wrong data
        self._parameters["projection"] = ("axial", (1, 0, 0))
        self._configurable.setup(self._parameters)
        self.assertRaises(
            ProjectorError, self._configurable["projection"]["projector"].__call__, None
        )
        self.assertRaises(
            ProjectorError, self._configurable["projection"]["projector"].__call__, [1]
        )

        # Planar projection - wrong parameters
        self._parameters["projection"] = ("tutu", (1, 0, 0))
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)
        self._parameters["projection"] = ("planar", (1, 0, 0, 2, 99, 123))
        self.assertRaises(ProjectorError, self._configurable.setup, self._parameters)
        self._parameters["projection"] = ("planar", 30)
        self.assertRaises(ProjectorError, self._configurable.setup, self._parameters)

        # Planar projection - null vector
        self._parameters["projection"] = ("planar", (0, 0, 0))
        self.assertRaises(ProjectorError, self._configurable.setup, self._parameters)

        # Planar projection
        self._parameters["projection"] = ("planar", (1, 0, 0))
        self._configurable.setup(self._parameters)
        proj = self._configurable["projection"]["projector"](data)
        self.assertTrue(
            numpy.array_equal(
                numpy.zeros((data.shape[0],), dtype=numpy.float64), proj[:, 0]
            )
        )
        self.assertTrue(numpy.array_equal(data[:, 1], proj[:, 1]))
        self.assertTrue(numpy.array_equal(data[:, 2], proj[:, 2]))

        # Planar projection - wrong data
        self._parameters["projection"] = ("planar", (1, 0, 0))
        self._configurable.setup(self._parameters)
        self.assertRaises(
            ProjectorError, self._configurable["projection"]["projector"].__call__, None
        )
        self.assertRaises(
            ProjectorError, self._configurable["projection"]["projector"].__call__, [1]
        )

    def test_atom_selection(self):
        self._configurable.set_settings(
            {
                "trajectory": ("mmtk_trajectory", {}),
                "atom_selection": (
                    "atom_selection",
                    {"dependencies": {"trajectory": "trajectory"}},
                ),
            }
        )

        # Test wrong parameter for atom selection
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_selection"] = 10
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # Test wrong parameter for atom selection
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_selection"] = "dadsada"
        self.assertRaises(
            AtomSelectionParserError, self._configurable.setup, self._parameters
        )

        # Test that an empty selection selection raises a SelectionParserError
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_selection"] = "atomelement fsfsd)"
        self.assertRaises(
            AtomSelectionParserError, self._configurable.setup, self._parameters
        )

        # Test that None parameters selects everything
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_selection"] = None
        self._configurable.setup(self._parameters)
        self.assertEqual(
            self._configurable["atom_selection"]["selection_length"],
            self._configurable["trajectory"]["instance"].universe.numberOfAtoms(),
        )

        # Test that 'all' parameters selects everything
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_selection"] = "all"
        self._configurable.setup(self._parameters)
        self.assertEqual(
            self._configurable["atom_selection"]["selection_length"],
            self._configurable["trajectory"]["instance"].universe.numberOfAtoms(),
        )

        # Test a valid atom selection string
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_selection"] = "atom_type oxygen"
        self._configurable.setup(self._parameters)
        self.assertEqual(
            self._configurable["atom_selection"]["selection_length"],
            sum(
                [
                    True
                    for at in self._configurable["trajectory"][
                        "instance"
                    ].universe.atomList()
                    if at.symbol == "O"
                ]
            ),
        )

    def test_atom_transmutation(self):
        self._configurable.set_settings(
            {
                "trajectory": ("mmtk_trajectory", {}),
                "atom_selection": (
                    "atom_selection",
                    {"dependencies": {"trajectory": "trajectory"}},
                ),
                "atom_transmutation": (
                    "atom_transmutation",
                    {
                        "dependencies": {
                            "trajectory": "trajectory",
                            "atom_selection": "atom_selection",
                        }
                    },
                ),
            }
        )

        # Test wrong parameter for atom selection
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_selection"] = None
        self._parameters["atom_transmutation"] = 10
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # Test wrong parameter for atom selection
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_transmutation"] = "dadsada"
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # Test that an empty selection selection raises a SelectionParserError
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_transmutation"] = 'atom_type(["fsfsd"])'
        self.assertRaises(ConfiguratorError, self._configurable.setup, self._parameters)

        # Test that None parameters selects everything
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_transmutation"] = None
        self._configurable.setup(self._parameters)
        self.assertEqual(
            self._configurable["atom_selection"]["selection_length"],
            self._configurable["trajectory"]["instance"].universe.numberOfAtoms(),
        )

        # Test a valid atom selection string
        self._parameters["trajectory"] = self._validTrajectory.filename
        self._parameters["atom_transmutation"] = None
        self._configurable.setup(self._parameters)


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestConfigurator))
    return s


if __name__ == "__main__":
    unittest.main(verbosity=2)

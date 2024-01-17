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
import unittest

import numpy


from MDANSE.Framework.Configurable import Configurable
from MDANSE.Framework.Configurators.IConfigurator import ConfiguratorError
from MDANSE.Framework.Projectors.IProjector import ProjectorError


class TestConfigurator(unittest.TestCase):
    """Unittest for the configurators used to setup an analysis in MDANSE"""

    def setUp(self):
        self._configurable = Configurable()
        self._parameters = {}

    def tearDown(self):
        self._configurable.settings.clear()
        self._parameters.clear()

    def test_integer(self):
        """Test the integer configurator"""

        self._configurable.set_settings({"test_integer": ("IntegerConfigurator", {})})

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

        self._configurable.set_settings({"test_float": ("FloatConfigurator", {})})

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

    def test_projection(self):
        self._configurable.set_settings({"projection": ("ProjectionConfigurator", {})})

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

        self._parameters["projection"] = ("NullProjector", None)
        self._configurable.setup(self._parameters)
        proj = self._configurable["projection"]["projector"](data)
        self.assertTrue(numpy.array_equal(data, proj))

        # Axial projection - null vector
        self._parameters["projection"] = ("AxialProjector", (0, 0, 0))
        self.assertRaises(ProjectorError, self._configurable.setup, self._parameters)

        # Axial projection
        self._parameters["projection"] = ("AxialProjector", (1, 0, 0))
        self._configurable.setup(self._parameters)
        proj = self._configurable["projection"]["projector"](data)
        self.assertTrue(numpy.array_equal(data[:, 0], proj[:, 0]))

        # Axial projection - wrong data
        self._parameters["projection"] = ("AxialProjector", (1, 0, 0))
        self._configurable.setup(self._parameters)
        self.assertRaises(
            ProjectorError, self._configurable["projection"]["projector"].__call__, None
        )
        self.assertRaises(
            ProjectorError, self._configurable["projection"]["projector"].__call__, [1]
        )

        # Planar projection - null vector
        self._parameters["projection"] = ("PlanarProjector", (0, 0, 0))
        self.assertRaises(ProjectorError, self._configurable.setup, self._parameters)

        # Planar projection
        self._parameters["projection"] = ("PlanarProjector", (1, 0, 0))
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
        self._parameters["projection"] = ("PlanarProjector", (1, 0, 0))
        self._configurable.setup(self._parameters)
        self.assertRaises(
            ProjectorError, self._configurable["projection"]["projector"].__call__, None
        )
        self.assertRaises(
            ProjectorError, self._configurable["projection"]["projector"].__call__, [1]
        )

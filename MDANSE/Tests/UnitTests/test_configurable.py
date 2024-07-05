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
import unittest

import numpy


from MDANSE.Framework.Configurable import Configurable


class TestConfigurable(unittest.TestCase):
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
        self._configurable.setup(self._parameters)
        self.assertFalse(self._configurable._configured)

        # Case of an object that cannot be casted to an integer
        self._parameters["test_integer"] = [1, 2]
        self._configurable.setup(self._parameters)
        self.assertFalse(self._configurable._configured)

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
        self._configurable.setup(self._parameters)
        self.assertFalse(self._configurable._configured)

        # Case of an object that cannot be casted to a float
        self._parameters["test_float"] = [1, 2]
        self._configurable.setup(self._parameters)
        self.assertFalse(self._configurable._configured)

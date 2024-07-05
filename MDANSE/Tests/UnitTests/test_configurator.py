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
import unittest
import numpy

from MDANSE.Framework.Configurators.IConfigurator import IConfigurator


file_wd = os.path.dirname(os.path.realpath(__file__))
cp2k_pos = os.path.join(file_wd, "Data", "CO2GAS-pos-1.xyz")


class TestConfigurator(unittest.TestCase):
    """Unittest for the configurators used to setup an analysis in MDANSE"""

    def test_integer_configurator(self):
        configurator = IConfigurator.create("IntegerConfigurator", "dummy_input")
        configurator.configure(10)
        self.assertEqual(configurator["value"], 10)
        configurator.configure(10.1)
        self.assertEqual(configurator["value"], 10)
        configurator.configure("xxxx")
        self.assertFalse(configurator.valid)

    def test_float_configurator(self):
        """Test the float configurator"""
        configurator = IConfigurator.create("FloatConfigurator", "dummy_input")
        configurator.configure(20.0)
        self.assertEqual(configurator["value"], 20.0)
        configurator.configure(20.2)
        self.assertEqual(configurator["value"], 20.2)
        configurator.configure("30.2")
        self.assertEqual(configurator["value"], 30.2)
        configurator.configure("xxxx")
        self.assertFalse(configurator.valid)
        configurator.configure("")
        self.assertFalse(configurator.valid)
        configurator.configure([1, 2])
        self.assertFalse(configurator.valid)

    def test_projection_configurator(self):
        configurator = IConfigurator.create("ProjectionConfigurator", "dummy_input")
        data = numpy.random.uniform(0, 1, (10, 3))
        # Wrong parameters
        configurator.configure(10)
        self.assertFalse(configurator.valid)
        configurator.configure([1, 2, 3, 4])
        self.assertFalse(configurator.valid)
        # No projection - wrong projection type
        configurator.configure((30, None))
        self.assertFalse(configurator.valid)

    def test_projection_null(self):
        configurator = IConfigurator.create("ProjectionConfigurator", "dummy_input")
        data = numpy.random.uniform(0, 1, (10, 3))
        # No projection
        configurator.configure(None)
        proj = configurator["projector"](data)
        self.assertTrue(numpy.array_equal(data, proj))
        configurator.configure(("NullProjector", None))
        proj = configurator["projector"](data)
        self.assertTrue(numpy.array_equal(data, proj))

    def test_projection_axial(self):
        configurator = IConfigurator.create("ProjectionConfigurator", "dummy_input")
        data = numpy.random.uniform(0, 1, (10, 3))
        # Axial projection - null vector
        configurator.configure(("AxialProjector", (0, 0, 0)))
        self.assertFalse(configurator.valid)
        # Axial projection
        configurator.configure(("AxialProjector", (1, 0, 0)))
        proj = configurator["projector"](data)
        self.assertTrue(numpy.array_equal(data[:, 0], proj[:, 0]))

    def test_projection_planar(self):
        configurator = IConfigurator.create("ProjectionConfigurator", "dummy_input")
        data = numpy.random.uniform(0, 1, (10, 3))
        # Planar projection - null vector
        configurator.configure(("PlanarProjector", (0, 0, 0)))
        self.assertFalse(configurator.valid)
        # Planar projection
        configurator.configure(("PlanarProjector", (1, 0, 0)))
        proj = configurator["projector"](data)
        self.assertTrue(
            numpy.array_equal(
                numpy.zeros((data.shape[0],), dtype=numpy.float64), proj[:, 0]
            )
        )
        self.assertTrue(numpy.array_equal(data[:, 1], proj[:, 1]))
        self.assertTrue(numpy.array_equal(data[:, 2], proj[:, 2]))


def test_XYZFileConfigurator_with_cp2k_pos():
    from MDANSE.Framework.Configurators.XYZFileConfigurator import XYZFileConfigurator

    xyz_file = XYZFileConfigurator("test")
    xyz_file["filename"] = cp2k_pos
    xyz_file.parse()
    assert len(xyz_file["atoms"]) == 60
    assert xyz_file["n_frames"] == 100
    coords = xyz_file.read_step(0)
    assert len(coords) == 60

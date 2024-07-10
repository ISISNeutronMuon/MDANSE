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

from MDANSE.Mathematics.Geometry import center_of_mass


class TestGeometry(unittest.TestCase):
    """
    Unittest for the geometry-related functions
    """

    def test_center_of_mass(self):
        coords = numpy.array(
            [
                [0, 0, 0],
                [1, 0, 0],
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
                [1, 0, 1],
                [1, 1, 1],
                [0, 1, 1],
            ],
            dtype=numpy.float64,
        )

        self.assertTrue(
            numpy.array_equal(
                center_of_mass(coords),
                numpy.array([0.5, 0.5, 0.5], dtype=numpy.float64),
            )
        )

        masses = numpy.array(
            [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0], dtype=numpy.float64
        )
        self.assertTrue(
            numpy.array_equal(
                center_of_mass(coords, masses=masses),
                numpy.array([0.5, 0.5, 0.0], dtype=numpy.float64),
            )
        )

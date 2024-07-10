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
from MDANSE.IO.PDBReader import PDBReader


pbd_2vb1 = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Data", "2vb1.pdb")


class TestPDBReader(unittest.TestCase):
    """
    Unittest for the geometry-related functions
    """

    def test_reader(self):
        with self.assertRaises((IOError, AttributeError)):
            reader = PDBReader("xxxxx.pdb")

        reader = PDBReader(pbd_2vb1)

        chemicalSystem = reader.build_chemical_system()

        atomList = chemicalSystem.atom_list

        self.assertEqual(atomList[4].symbol, "C")
        self.assertEqual(atomList[7].name, "HB2")
        self.assertEqual(atomList[10].full_name, "...LYS1.HG2")
        self.assertEqual(atomList[28].parent.name, "VAL2")

        conf = chemicalSystem.configuration

        self.assertAlmostEqual(conf.variables["coordinates"][0, 0], 4.6382)
        self.assertAlmostEqual(conf.variables["coordinates"][0, 1], 3.0423)
        self.assertAlmostEqual(conf.variables["coordinates"][0, 2], 2.6918)

        self.assertAlmostEqual(conf.variables["coordinates"][-1, 0], 2.4937)
        self.assertAlmostEqual(conf.variables["coordinates"][-1, 1], 3.9669)
        self.assertAlmostEqual(conf.variables["coordinates"][-1, 2], -0.5209)

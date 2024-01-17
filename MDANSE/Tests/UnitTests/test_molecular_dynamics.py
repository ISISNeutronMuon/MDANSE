# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/UnitTests/TestMolecularDynamics.py
# @brief     Implements module/class/test TestMolecularDynamics
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

from MDANSE.MolecularDynamics.Analysis import (
    radius_of_gyration,
    mean_square_deviation,
    mean_square_fluctuation,
)


class TestMolecularDynamics(unittest.TestCase):
    """
    Unittest for the geometry-related functions
    """

    def test_radius_of_gyration(self):
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
        self.assertEqual(radius_of_gyration(coords, root=True), numpy.sqrt(0.75))

        masses = numpy.array(
            [1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0], dtype=numpy.float64
        )
        self.assertEqual(
            radius_of_gyration(coords, masses=masses, root=True), numpy.sqrt(0.5)
        )

    def test_mean_square_deviation(self):
        coords1 = numpy.array(
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

        coords2 = numpy.array(
            [
                [1, 1, 1],
                [2, 1, 1],
                [2, 2, 1],
                [1, 2, 1],
                [1, 1, 2],
                [2, 1, 2],
                [2, 2, 2],
                [1, 2, 2],
            ],
            dtype=numpy.float64,
        )

        self.assertEqual(
            mean_square_deviation(coords1, coords2, root=True), numpy.sqrt(3)
        )

        self.assertEqual(mean_square_deviation(coords1, coords2, root=False), 3)

    def test_mean_square_fluctuation(self):
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

        self.assertEqual(mean_square_fluctuation(coords, root=False), 0.75)

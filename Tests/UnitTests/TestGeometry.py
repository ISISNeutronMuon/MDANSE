# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/UnitTests/TestGeometry.py
# @brief     Implements module/class/test TestGeometry
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

#MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
#------------------------------------------------------------------------------------------
#Copyright (C)
#2015- Eric C. Pellegrini Institut Laue-Langevin
#BP 156
#6, rue Jules Horowitz
#38042 Grenoble Cedex 9
#France
#pellegrini[at]ill.fr
#goret[at]ill.fr
#aoun[at]ill.fr
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Lesser General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Lesser General Public License for more details.
#
#You should have received a copy of the GNU Lesser General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

''' 
Created on May 29, 2015

@author: Eric C. Pellegrini
'''

import unittest

import numpy

from MDANSE.Mathematics.Geometry import center_of_mass

class TestGeometry(unittest.TestCase):
    '''
    Unittest for the geometry-related functions
    '''
        
    def test_center_of_mass(self):
        
        coords = numpy.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],dtype=numpy.float64)

        self.assertTrue(numpy.array_equal(center_of_mass(coords),numpy.array([0.5,0.5,0.5],dtype=numpy.float64)))

        masses = numpy.array([1.0,1.0,1.0,1.0,0.0,0.0,0.0,0.0],dtype=numpy.float64)
        self.assertTrue(numpy.array_equal(center_of_mass(coords,masses=masses),numpy.array([0.5,0.5,0.0],dtype=numpy.float64)))
        
            
def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestGeometry))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
            
        

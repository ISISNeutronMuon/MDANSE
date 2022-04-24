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

import numpy as np

from MDANSE.Chemistry.ChemicalEntity import Atom, ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import BoxConfiguration, RealConfiguration

class TestConfiguration(unittest.TestCase):
    '''
    Unittest for the geometry-related functions
    '''

    def setUp(self):
                
        self._chemicalSystem = ChemicalSystem()
        self._nAtoms = 4

        for i in range(self._nAtoms):
            self._chemicalSystem.add_chemical_entity(Atom(symbol="H"))

    def test_real_configuration(self):

        coordinates = np.random.uniform(0,1,(2,3))
        with self.assertRaises(ValueError):
            _ = RealConfiguration(self._chemicalSystem,coordinates)

        coordinates = np.random.uniform(0,1,(self._nAtoms,3))
        conf = RealConfiguration(self._chemicalSystem,coordinates)
        self.assertTrue(np.allclose(conf.to_real_coordinates(),coordinates,rtol=1.0e-6))

        coordinates = np.random.uniform(0,1,(self._nAtoms,3))
        conf = RealConfiguration(self._chemicalSystem,coordinates)
        self.assertTrue(np.allclose(conf.to_box_coordinates(),coordinates,rtol=1.0e-6))

        unitCell = np.array([[1.0,2.0,1.0],[2.0,-1.0,1.0],[3.0,1.0,1.0]],dtype=np.float)
        coordinates = np.array(([1,2,3],[4,5,6],[7,8,9],[10,11,12]),dtype=np.float)
        conf = RealConfiguration(self._chemicalSystem,coordinates,unitCell)

        boxCoordinates = conf.to_box_coordinates()
        self.assertTrue(np.allclose(boxCoordinates[0,:],[3.0,2.0,-2.0],rtol=1.0e-6))
        self.assertTrue(np.allclose(boxCoordinates[1,:],[5.4,3.2,-2.6],rtol=1.0e-6))
        self.assertTrue(np.allclose(boxCoordinates[2,:],[7.8,4.4,-3.2],rtol=1.0e-6))
        self.assertTrue(np.allclose(boxCoordinates[3,:],[10.2,5.6,-3.8],rtol=1.0e-6))

    def test_box_configuration(self):

        coordinates = np.random.uniform(0,1,(2,3))
        with self.assertRaises(ValueError):
            _ = BoxConfiguration(self._chemicalSystem,coordinates)

        coordinates = np.random.uniform(0,1,(self._nAtoms,3))
        conf = BoxConfiguration(self._chemicalSystem,coordinates)
        self.assertTrue(np.allclose(conf.to_box_coordinates(),coordinates,rtol=1.0e-6))

        coordinates = np.random.uniform(0,1,(self._nAtoms,3))
        conf = BoxConfiguration(self._chemicalSystem,coordinates)
        self.assertTrue(np.allclose(conf.to_box_coordinates(),coordinates,rtol=1.0e-6))

        unitCell = np.array([[1.0,2.0,1.0],[2.0,-1.0,1.0],[3.0,1.0,1.0]],dtype=np.float)
        coordinates = np.array(([1,2,3],[4,5,6],[7,8,9],[10,11,12]),dtype=np.float)
        conf = BoxConfiguration(self._chemicalSystem,coordinates,unitCell)

        realCoordinates = conf.to_real_coordinates()
        self.assertTrue(np.allclose(realCoordinates[0,:],[14.0,3.0,6.0],rtol=1.0e-6))
        self.assertTrue(np.allclose(realCoordinates[1,:],[32.0,9.0,15.0],rtol=1.0e-6))
        self.assertTrue(np.allclose(realCoordinates[2,:],[50.0,15.0,24.0],rtol=1.0e-6))
        self.assertTrue(np.allclose(realCoordinates[3,:],[68.0,21.0,33.0],rtol=1.0e-6))









            
def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestConfiguration))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
            
        

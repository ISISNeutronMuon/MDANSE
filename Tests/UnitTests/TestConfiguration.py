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

from MDANSE.Chemistry.ChemicalEntity import Atom, AtomCluster, ChemicalSystem
from MDANSE.MolecularDynamics.Configuration import BoxConfiguration, RealConfiguration

class TestConfiguration(unittest.TestCase):
    '''
    Unittest for the geometry-related functions
    '''

    def setUp(self):
                
        self._chemicalSystem = ChemicalSystem()
        self._nAtoms = 4

        atoms = []
        for i in range(self._nAtoms):
            atoms.append(Atom(symbol='H'))
        ac = AtomCluster('',atoms)

        self._chemicalSystem.add_chemical_entity(ac)

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
        self.assertTrue(np.allclose(boxCoordinates,[[3.0,2.0,-2.0],
                                                    [5.4,3.2,-2.6],
                                                    [7.8,4.4,-3.2],
                                                    [10.2,5.6,-3.8]],rtol=1.0e-6))

        conf.fold_coordinates()

        self.assertTrue(np.allclose(conf.variables['coordinates'],[[0.0,0.0,0.0],
                                                                   [2.0,1.0,1.0],
                                                                   [0.0,-1.0,0.0],
                                                                   [0.0,1.0,0.0]],rtol=1.0e-6))

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
        self.assertTrue(np.allclose(realCoordinates,[[14.0,3.0,6.0],
                                                     [32.0,9.0,15.0],
                                                     [50.0,15.0,24.0],
                                                     [68.0,21.0,33.0]],rtol=1.0e-6))









            
    def test_fold_coordinates_real_pbc(self):

        unit_cell = np.array([[2,1,0],[-3,2,0],[2,1,-4]],dtype=np.float)
        coords = np.array([
            [-1.65955991,  4.40648987, -9.9977125 ],
            [-3.95334855, -7.06488218, -8.1532281 ],
            [-6.27479577, -3.08878546, -2.06465052],
            [ 0.77633468, -1.61610971,  3.70439001]])

        conf = RealConfiguration(self._chemicalSystem,coords,unit_cell)
        conf.fold_coordinates()

        real_coordinates = conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates,[[-0.65955991,  1.40648987, -1.9977125 ],
                                                      [ 1.04665145, -1.06488218, -0.1532281 ],
                                                      [-0.27479577, -0.08878546,  1.93534948],
                                                      [-0.22366532,  1.38389029, -0.29560999]],rtol=1.0e-6))

    def test_fold_coordinates_real_nopbc(self):

        coords = np.array([
            [-1.65955991,  4.40648987, -9.9977125 ],
            [-3.95334855, -7.06488218, -8.1532281 ],
            [-6.27479577, -3.08878546, -2.06465052],
            [ 0.77633468, -1.61610971,  3.70439001]])

        conf = RealConfiguration(self._chemicalSystem,coords)
        conf.fold_coordinates()

        real_coordinates = conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates,coords,rtol=1.0e-6))

    def test_fold_coordinates_box_pbc(self):

        unit_cell = np.array([[2,1,0],[-3,2,0],[2,1,-4]],dtype=np.float)
        coords = np.array([
            [ 0.6, 0.8, -0.7],
            [ 0.3, -0.1, 1.2],
            [ 0.4, 0.2, -0.9],
            [-0.2, 0.4, 0.6]])

        conf = BoxConfiguration(self._chemicalSystem,coords,unit_cell)
        conf.fold_coordinates()

        real_coordinates = conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates,[[-0.4,-0.2, 0.3],
                                                      [ 0.3,-0.1, 0.2],
                                                      [ 0.4, 0.2, 0.1],
                                                      [-0.2, 0.4,-0.4]],rtol=1.0e-6))

    def test_fold_coordinates_box_nopbc(self):

        coords = np.array([
            [ 0.6, 0.8, -0.7],
            [ 0.3, -0.1, 1.2],
            [ 0.4, 0.2, -0.9],
            [-0.2, 0.4, 0.6]])

        conf = BoxConfiguration(self._chemicalSystem,coords)
        conf.fold_coordinates()

        real_coordinates = conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates,coords,rtol=1.0e-6))

    def test_contiguous_configuration_real_pbc(self):

        unit_cell = np.array([[2,1,0],[-3,2,0],[2,1,-4]],dtype=np.float)

        box_coords = [[0.1,0.1,0.1],[0.3,0.2,0.4],[-1.3,-1.1,-1.3],[1.9,1.5,1.9]]
        box_conf = BoxConfiguration(self._chemicalSystem,box_coords,unit_cell)
        real_coords = box_conf.to_real_coordinates()
        real_conf = RealConfiguration(self._chemicalSystem,real_coords,unit_cell)

        contiguous_conf = real_conf.contiguous_configuration()
        real_coordinates = contiguous_conf['coordinates']

        self.assertTrue(np.allclose(real_coordinates,[[ 0.1,  0.4,-0.4],
                                                      [ 0.8,  1.1,-1.6],
                                                      [-0.9, -0.8, 1.2],
                                                      [-1.9,  0.8, 0.4]],rtol=1.0e-6))

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestConfiguration))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
            
        

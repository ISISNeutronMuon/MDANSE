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

from MDANSE.IO.PDBReader import PDBReader

class TestPDBReader(unittest.TestCase):
    '''
    Unittest for the geometry-related functions
    '''
        
    def test_reader(self):
        
        with self.assertRaises((IOError,AttributeError)):
            reader = PDBReader('xxxxx.pdb')

        reader = PDBReader('../../Data/Trajectories/CHARMM/2vb1.pdb')

        chemicalSystem = reader.build_chemical_system()

        atomList = chemicalSystem.atom_list()

        self.assertEqual(atomList[4].symbol,'C')
        self.assertEqual(atomList[7].name,'HB2')
        self.assertEqual(atomList[10].full_name(),'.LYS1.HG2')
        self.assertEqual(atomList[28].parent.name,'VAL2')

        conf = chemicalSystem.configuration

        self.assertAlmostEqual(conf.variables['coordinates'][0,0],4.6382)
        self.assertAlmostEqual(conf.variables['coordinates'][0,1],3.0423)
        self.assertAlmostEqual(conf.variables['coordinates'][0,2],2.6918)

        self.assertAlmostEqual(conf.variables['coordinates'][-1,0],2.4937)
        self.assertAlmostEqual(conf.variables['coordinates'][-1,1],3.9669)
        self.assertAlmostEqual(conf.variables['coordinates'][-1,2],-0.5209)


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestPDBReader))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
            
        

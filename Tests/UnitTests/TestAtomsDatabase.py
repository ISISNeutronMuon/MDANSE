# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/UnitTests/TestElementsDatabase.py
# @brief     Implements module/class/test TestElementsDatabase
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

from MDANSE.Chemistry import ATOMS_DATABASE
from MDANSE.Chemistry.Databases import AtomsDatabaseError

class TestAtomsDatabase(unittest.TestCase):
    '''
    '''
    
    def test___contains__(self):
        
        self.assertFalse("fhsdjfsd" in ATOMS_DATABASE)
        self.assertTrue("H" in ATOMS_DATABASE)

    def test___getitem__(self):
                
        for at in ATOMS_DATABASE.atoms:
            _ = ATOMS_DATABASE[at]

    def test_get_property(self):
                
        for p in ATOMS_DATABASE.properties:
            _ = ATOMS_DATABASE.get_property(p)

    def test___setitem__(self):
        
        ATOMS_DATABASE['C']['atomic_weight'] = 20.0
                                
    def test_add_atom(self):

        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.add_atom("H")

        ATOMS_DATABASE.add_atom("new_atom")
        
    def test_add_property(self):

        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.add_property("atomic_weight")

        ATOMS_DATABASE.add_property("new_prop")
        
    def test_has_property(self):
        
        for p in ATOMS_DATABASE.properties:
            self.assertTrue(ATOMS_DATABASE.has_property(p))
            
        self.assertFalse(ATOMS_DATABASE.has_property("gfkljfklsj"))
            
    def test_has_element(self):
        
        for at in ATOMS_DATABASE.atoms:
            self.assertTrue(ATOMS_DATABASE.has_atom(at))
            
        self.assertFalse(ATOMS_DATABASE.has_atom("gfkljfklsj"))
            
def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestAtomsDatabase))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
            
        

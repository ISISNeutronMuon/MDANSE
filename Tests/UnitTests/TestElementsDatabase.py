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

from MDANSE import ELEMENTS
from MDANSE.Data.ElementsDatabase import ElementsDatabaseError

class TestElementsDatabase(unittest.TestCase):
    '''
    Unittest for the configurators used to setup an analysis in MDANSE
    '''
    
    def setUp(self):
        
        self._types = {float:1.0,int:1,str:"toto"}
    

    def test___contains__(self):
        
        self.assertFalse("fhsdjfsd" in ELEMENTS)
        self.assertTrue("h" in ELEMENTS)
        self.assertTrue("H" in ELEMENTS)

    def test___getitem__(self):
                
        for e in ELEMENTS.elements:
            for p in ELEMENTS.properties:
                _ = ELEMENTS[e,p]

    def test_getelement(self):
        
        for e in ELEMENTS.elements:
            _ = ELEMENTS.get_element(e)

    def test_get_property(self):
                
        for p in ELEMENTS.properties:
            _ = ELEMENTS.get_property(p)

    def test___setitem__(self):
        
        ELEMENTS['C','atomic_weight'] = 20.0
                                
    def test_add_element(self):
        
        # Otherwise, everything should be OK
        ELEMENTS.add_element("element1")
        
    def test_add_property(self):
        
        # Adding an already existing property must trigger an error
        self.assertRaises(ElementsDatabaseError, ELEMENTS.add_property, "atomic_weight",0.0)
                
        # Otherwise, everything should be OK
        ELEMENTS.add_property("prop1",'float')
        ELEMENTS.add_property("prop2",'int')
        ELEMENTS.add_property("prop3",'str')
        
    def test_has_property(self):
        
        for p in ELEMENTS.properties:
            self.assertTrue(ELEMENTS.has_property(p))
            
        self.assertFalse(ELEMENTS.has_property("gfkljfklsj"))
            
    def test_has_element(self):
        
        for e in ELEMENTS.elements:
            self.assertTrue(ELEMENTS.has_element(e))
            
        self.assertFalse(ELEMENTS.has_element("gfkljfklsj"))
            
def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestElementsDatabase))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
            
        

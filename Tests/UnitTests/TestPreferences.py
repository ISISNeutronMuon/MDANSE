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

import os
import shutil
import unittest

from MDANSE.Core.Preferences import Preferences
from MDANSE.Core.Preferences import PreferencesError
from UnitTest import UnitTest

class UnStringable:
    
    def __str__(self):        
        raise TypeError("Object not castable to a string.")

class TestPreferences(UnitTest):

    def setUp(self):
                
        PREFERENCES = Preferences()
    
    def test_get_item(self):
        
        self.assertRaises(PreferencesError,PREFERENCES.__getitem__,'xxxxx')

    def test_set_item(self):
        
        val = PREFERENCES["working_directory"].get_value()
        PREFERENCES["working_directory"].set_value("test")
        self.assertEqual(PREFERENCES["working_directory"].value,os.path.join(os.getcwd(),"test"))
        PREFERENCES["working_directory"].set_value(val)
        
        shutil.rmtree("test")
                
    def test_load_preferences(self):
        '''
        Test the method that loads the preferences
        '''
        
        # Test that loading a preferences file whose type is not a basestring throw a PreferencesError
        self.assertRaises(PreferencesError,PREFERENCES.load,10)

    def test_save_preferences(self):
        '''
        Test the method that saves the preferences
        '''
        
        # Test that saving a preferences file whose type is not a basestring throw a PreferencesError
        self.assertRaises(PreferencesError,PREFERENCES.save,10)
        # Test that saving a preferences whose path does not exists throw a PreferencesError
        self.assertRaises(PreferencesError,PREFERENCES.save,os.path.join('xxxx','yyyy'))

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestPreferences))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)

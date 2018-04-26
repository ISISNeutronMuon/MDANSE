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
import os
import sys
import glob

def suite():
    files = glob.glob("Test*.py")
    #os.chdir("Jobs")
    modules = [__import__(os.path.splitext(f)[0],globals(),locals(),[],-1) for f in files]
    test_suite = unittest.TestSuite()
    for m in modules:
        print m.__file__
        test_suite.addTests(m.suite())
    return test_suite

def run_test():
    if not unittest.TextTestRunner(verbosity=2).run(suite()).wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    #os.chdir("Jobs")
    run_test()

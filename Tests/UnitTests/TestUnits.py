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

from MDANSE.Framework.Units import UnitError, measure

class TestUnits(unittest.TestCase):
    '''
    Unittest for the geometry-related functions
    '''
        
    def test_basic_units(self):

        m = measure(1.0,'kg')
        self.assertAlmostEqual(m.toval('g'),1.0e+03,10)
        self.assertAlmostEqual(m.toval('mg'),1.0e+06,10)

        m = measure(1.0,'m')
        self.assertAlmostEqual(m.toval('dm'),10.0,10)
        self.assertAlmostEqual(m.toval('km'),0.001,10)

        m = measure(1.0,'s')
        self.assertAlmostEqual(m.toval('us'),1.0e+06,10)
        self.assertAlmostEqual(m.toval('das'),1.0e-01,10)

        m = measure(1.0,'K')
        self.assertAlmostEqual(m.toval('mK'),1.0e+03,10)
        self.assertAlmostEqual(m.toval('cK'),1.0e+02,10)
        self.assertAlmostEqual(m.toval('hK'),1.0e-02,10)

        m = measure(1.0,'mol')
        self.assertAlmostEqual(m.toval('mmol'),1.0e+03,10)

        m = measure(1.0,'A')
        self.assertAlmostEqual(m.toval('uA'),1.0e+06,10)

        m = measure(1.0,'cd')
        self.assertAlmostEqual(m.toval('dacd'),1.0e-01,10)

        m = measure(1.0,'rad')
        self.assertAlmostEqual(m.toval('nrad'),1.0e+09,6)

        m = measure(1.0,'sr')
        self.assertAlmostEqual(m.toval('Msr'),1.0e-06,6)

    def test_composite_units(self):

        m = measure(1.0,'m/s')
        self.assertAlmostEqual(m.toval('km/h'),3.6,10)

    def test_add_units(self):

        m1 = measure(1.0,'s')
        m2 = measure(1.0,'ms')

        m = m1 + m2
        self.assertAlmostEqual(m.toval('s'),1.001,10)

        m += m2
        self.assertAlmostEqual(m.toval('s'),1.002,10)

    def test_substract_units(self):

        m1 = measure(1.0,'s')
        m2 = measure(1.0,'ms')

        m = m1 - m2
        self.assertAlmostEqual(m.toval('s'),0.999,10)

        m -= m2
        self.assertAlmostEqual(m.toval('s'),0.998,10)

    def test_product_units(self):

        m1 = measure(1.0,'m')
        m2 = measure(5.0,'hm')

        m = m1 * m2
        self.assertAlmostEqual(m.toval('m2'),500,10)

        m *= measure(10,'cm')
        self.assertAlmostEqual(m.toval('m3'),50,10)

        m *= 20
        self.assertAlmostEqual(m.toval('m3'),1000,10)

    def test_divide_units(self):

        m1 = measure(1.0,'m')
        m2 = measure(5.0,'hm')

        m = m1 / m2
        self.assertAlmostEqual(m.toval('au'),0.002,10)

        m /= 0.0001
        self.assertAlmostEqual(m.toval('au'),20.0,10)

        m /= m2
        self.assertRaises(UnitError,m.toval,'au')
        self.assertAlmostEqual(m.toval('1/m'),4.0e-02,10)

    def test_equivalent_units(self):

        m = measure(1.0,'eV',equivalent=True)
        self.assertAlmostEqual(m.toval('THz'),241.799050402293,3)
        self.assertAlmostEqual(m.toval('K'),11604.5250061598,1)

        m = measure(1.0,'eV',equivalent=False)
        self.assertRaises(UnitError,m.toval,'THz')

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestUnits))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
            
        

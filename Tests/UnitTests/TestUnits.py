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

from MDANSE.Framework.Units import _PREFIXES, UnitError, measure

class TestUnits(unittest.TestCase):
    '''
    Unittest for the geometry-related functions
    '''
        
    def test_basic_units(self):

        m = measure(1.0,'kg')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

        m = measure(1.0,'m')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

        m = measure(1.0,'s')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

        m = measure(1.0,'K')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

        m = measure(1.0,'mol')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

        m = measure(1.0,'A')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

        m = measure(1.0,'cd')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

        m = measure(1.0,'rad')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

        m = measure(1.0,'sr')
        self.assertAlmostEqual(m.toval(),1.0,delta=1.0e-09)

    def test_prefix(self):

        m = measure(1.0,'s')
        self.assertAlmostEqual(m.toval('ys'),1.0/_PREFIXES['y'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('zs'),1.0/_PREFIXES['z'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('as'),1.0/_PREFIXES['a'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('fs'),1.0/_PREFIXES['f'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('ps'),1.0/_PREFIXES['p'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('ns'),1.0/_PREFIXES['n'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('us'),1.0/_PREFIXES['u'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('ms'),1.0/_PREFIXES['m'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('cs'),1.0/_PREFIXES['c'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('ds'),1.0/_PREFIXES['d'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('das'),1.0/_PREFIXES['da'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('hs'),1.0/_PREFIXES['h'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('ks'),1.0/_PREFIXES['k'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('Ms'),1.0/_PREFIXES['M'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('Gs'),1.0/_PREFIXES['G'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('Ts'),1.0/_PREFIXES['T'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('Ps'),1.0/_PREFIXES['P'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('Es'),1.0/_PREFIXES['E'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('Zs'),1.0/_PREFIXES['Z'],delta=1.0e-09)
        self.assertAlmostEqual(m.toval('Ys'),1.0/_PREFIXES['Y'],delta=1.0e-09)

    def test_composite_units(self):

        m = measure(1.0,'m/s')
        self.assertAlmostEqual(m.toval('km/h'),3.6,delta=1.0e-09)

    def test_add_units(self):

        m1 = measure(1.0,'s')
        m2 = measure(1.0,'ms')

        m = m1 + m2
        self.assertAlmostEqual(m.toval('s'),1.001,delta=1.0e-09)

        m += m2
        self.assertAlmostEqual(m.toval('s'),1.002,delta=1.0e-09)

    def test_substract_units(self):

        m1 = measure(1.0,'s')
        m2 = measure(1.0,'ms')

        m = m1 - m2
        self.assertAlmostEqual(m.toval('s'),0.999,delta=1.0e-09)

        m -= m2
        self.assertAlmostEqual(m.toval('s'),0.998,delta=1.0e-09)

    def test_product_units(self):

        m1 = measure(1.0,'m')
        m2 = measure(5.0,'hm')

        m = m1 * m2
        self.assertAlmostEqual(m.toval('m2'),500,delta=1.0e-09)

        m *= measure(10,'cm')
        self.assertAlmostEqual(m.toval('m3'),50,delta=1.0e-09)

        m *= 20
        self.assertAlmostEqual(m.toval('m3'),1000,delta=1.0e-09)

    def test_divide_units(self):

        m1 = measure(1.0,'m')
        m2 = measure(5.0,'hm')

        m = m1 / m2
        self.assertAlmostEqual(m.toval('au'),0.002,delta=1.0e-09)

        m /= 0.0001
        self.assertAlmostEqual(m.toval('au'),20.0,delta=1.0e-09)

        m /= m2
        self.assertRaises(UnitError,m.toval,'au')
        self.assertAlmostEqual(m.toval('1/m'),4.0e-02,delta=1.0e-09)

    def test_floor_unit(self):

        self.assertAlmostEqual(measure(10.2, 'm/s').floor().toval(),10.0,delta=1.0e-09)
        self.assertAlmostEqual(measure(3.6, 'm/s').ounit('km/h').floor().toval(),12.0,delta=1.0e-09)
        self.assertAlmostEqual(measure(50.3, 'km/h').floor().toval(),50.0,delta=1.0e-09)

    def test_ceil_unit(self):

        self.assertAlmostEqual(measure(10.2, 'm/s').ceil().toval(),11.0,delta=1.0e-09)
        self.assertAlmostEqual(measure(3.6, 'm/s').ounit('km/h').ceil().toval(),13.0,delta=1.0e-09)
        self.assertAlmostEqual(measure(50.3, 'km/h').ceil().toval(),51.0,delta=1.0e-09)

    def test_round_unit(self):

        self.assertAlmostEqual(measure(10.2, 'm/s').round().toval(),10.0,delta=1.0e-09)
        self.assertAlmostEqual(measure(3.6, 'm/s').ounit('km/h').round().toval(),13.0,delta=1.0e-09)
        self.assertAlmostEqual(measure(50.3, 'km/h').round().toval(),50.0,delta=1.0e-09)

    def test_int_unit(self):

        self.assertEqual(int(measure(10.2, 'km/h')),10)

    def test_sqrt_unit(self):

        m = measure(4.0,'m2/s2')

        m = m.sqrt()

        self.assertAlmostEqual(m.toval(),2.0,delta=1.0e-09)
        self.assertEqual(m.dimension,[0,1,-1,0,0,0,0,0,0])

    def test_power_unit(self):

        m = measure(4.0,'m')
        m **=3
        self.assertAlmostEqual(m.toval(),64.0,delta=1.0e-09)
        self.assertEqual(m.dimension,[0,3,0,0,0,0,0,0,0])

    def test_equivalent_units(self):

        m = measure(1.0,'eV',equivalent=True)
        self.assertAlmostEqual(m.toval('THz'),241.799,delta=1.0e-03)
        self.assertAlmostEqual(m.toval('K'),11604.52, delta=1.0e-02)

        m = measure(1.0,'eV',equivalent=False)
        self.assertRaises(UnitError,m.toval,'THz')

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestUnits))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
            
        

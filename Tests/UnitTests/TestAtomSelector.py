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

from MDANSE.Framework.Selectors import *
from MDANSE.IO.PDBReader import PDBReader

class TestAtomsSelector(unittest.TestCase):
    '''
    '''

    @classmethod
    def setUpClass(cls):
        """ get_some_resource() is slow, to avoid calling it for each test use setUpClass()
            and store the result as class variable
        """
        super(TestAtomsSelector, cls).setUpClass()

        reader = PDBReader('./Data/Trajectories/CHARMM/2vb1.pdb')

        cls._chemicalSystem = reader.build_chemical_system()
    
    def test_all(self):

        selector = All.All(self._chemicalSystem)
        selection = selector.select()

        self.assertEqual(len(selection),30714)

    def test_amine(self):

        selector = Amine.Amine(self._chemicalSystem)
        selection = selector.select(['*'])
        self.assertEqual(len(selection),117)

    def test_ammonium(self):

        selector = Ammonium.Ammonium(self._chemicalSystem)
        selection = selector.select(['*'])
        self.assertEqual(len(selection),28)

    def test_atom_element(self):

        selector = AtomElement.AtomElement(self._chemicalSystem)
        selection = list(selector.select(['sulphur']))
        self.assertEqual(len(selection),10)

        selection = list(selector.select(['*']))
        self.assertEqual(len(selection),30714)

    def test_atom_full_name(self):

        selector = AtomFullName.AtomFullName(self._chemicalSystem)
        selection = selector.select(['.LYS1.N','.VAL2.O'])
        self.assertEqual(len(selection),2)

        selection = list(selector.select(['*']))
        self.assertEqual(len(selection),30714)

    def test_atom_index(self):

        selector = AtomIndex.AtomIndex(self._chemicalSystem)
        selection = list(selector.select([0,1,2,3]))
        self.assertEqual(len(selection),4)
        self.assertTrue(selection[0].name in ['N','HT1','HT2','HT3'])
        self.assertTrue(selection[1].name in ['N','HT1','HT2','HT3'])
        self.assertTrue(selection[2].name in ['N','HT1','HT2','HT3'])
        self.assertTrue(selection[3].name in ['N','HT1','HT2','HT3'])

        selection = list(selector.select(['*']))
        self.assertEqual(len(selection),30714)

    def test_atom_name(self):

        selector = AtomName.AtomName(self._chemicalSystem)
        selection = selector.select(['N','O'])
        self.assertEqual(len(selection),258)

        selection = list(selector.select(['*']))
        self.assertEqual(len(selection),30714)

    def test_atom_picked(self):

        selector = AtomPicked.AtomPicked(self._chemicalSystem)
        selection = list(selector.select([0,1,2,3]))
        self.assertEqual(len(selection),4)
        self.assertTrue(selection[0].name in ['N','HT1','HT2','HT3'])
        self.assertTrue(selection[1].name in ['N','HT1','HT2','HT3'])
        self.assertTrue(selection[2].name in ['N','HT1','HT2','HT3'])
        self.assertTrue(selection[3].name in ['N','HT1','HT2','HT3'])

        selection = list(selector.select(['*']))
        self.assertEqual(len(selection),30714)

    def test_atom_symbol(self):

        selector = AtomSymbol.AtomSymbol(self._chemicalSystem)
        selection = list(selector.select(['S']))
        self.assertEqual(len(selection),10)

        selection = list(selector.select(['*']))
        self.assertEqual(len(selection),30714)

    def test_backbone(self):

        selector = Backbone.Backbone(self._chemicalSystem)
        selection = selector.select()
        self.assertEqual(len(selection),775)

    def test_carbo_hydrogens(self):

        selector = CarboHydrogen.CarboHydrogen(self._chemicalSystem)
        selection = selector.select(['.LYS1.HB2','.LYS1.HB3'])
        self.assertEqual(len(selection),2)

        selection = list(selector.select(['*']))
        self.assertEqual(len(selection),696)

    def test_carbon_alpha(self):

        selector = CarbonAlpha.CarbonAlpha(self._chemicalSystem)

        selection = selector.select()
        self.assertEqual(len(selection),129)

    def test_chain_name(self):

        selector = ChainName.ChainName(self._chemicalSystem)

        selection = selector.select([''])
        self.assertEqual(len(selection),1960)

        selection = selector.select(['*'])
        self.assertEqual(len(selection),1960)

    def test_hetero_hydrogen(self):

        selector = HeteroHydrogen.HeteroHydrogen(self._chemicalSystem)

        selection = selector.select(['.SER24.HG'])
        self.assertEqual(len(selection),1)

        selection = selector.select(['*'])
        self.assertEqual(len(selection),19427)

    def test_hydroxyl(self):

        selector = Hydroxyl.Hydroxyl(self._chemicalSystem)

        selection = selector.select(['.SER24.HG'])
        self.assertEqual(len(selection),1)

        selection = selector.select(['*'])
        self.assertEqual(len(selection),28786)

    def test_macromolecule(self):

        selector = Macromolecule.Macromolecule(self._chemicalSystem)

        selection = selector.select(['peptide_chain'])
        self.assertEqual(len(selection),1960)

        selection = selector.select(['*'])
        self.assertEqual(len(selection),1960)

    def test_methyl(self):

        selector = Methyl.Methyl(self._chemicalSystem)

        selection = selector.select(['.VAL29.1HG1','.VAL29.1HG2'])
        self.assertEqual(len(selection),2)

        selection = selector.select(['*'])
        self.assertEqual(len(selection),183)

    def test_molecule_index(self):

        selector = MoleculeIndex.MoleculeIndex(self._chemicalSystem)

        selection = selector.select([0])
        self.assertEqual(len(selection),1960)

        selection = selector.select([15])
        self.assertEqual(len(selection),3)

        selection = selector.select(['*'])
        self.assertEqual(len(selection),30714)

    def test_molecule_name(self):

        selector = MoleculeName.MoleculeName(self._chemicalSystem)

        selection = selector.select([''])
        self.assertEqual(len(selection),1960)

        selection = selector.select(['WAT9709'])
        self.assertEqual(len(selection),3)

        selection = selector.select(['*'])
        self.assertEqual(len(selection),30714)

def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestAtomsSelector))
    return s

if __name__ == '__main__':
    unittest.main(verbosity=2)
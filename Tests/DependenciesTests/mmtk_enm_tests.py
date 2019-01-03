# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/DependenciesTests/mmtk_enm_tests.py
# @brief     Implements module/class/test mmtk_enm_tests
#
# @homepage  https://mdanse.org
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

# Elastic network model tests
#
# Written by Konrad Hinsen
#

import unittest
from MMTK import *
from MMTK.ForceFields import CalphaForceField, DeformationForceField, \
                             AnisotropicNetworkForceField
from MMTK.Proteins import Protein
from mmtk_subsets import SubsetTest

class CalphaFFSubsetTest(unittest.TestCase,
                         SubsetTest):

    def setUp(self):
        self.universe = InfiniteUniverse(CalphaForceField())
        protein = Protein('insulin_calpha')
        self.universe.addObject(protein)        
        self.subset1 = protein[0]
        self.subset2 = protein[1]


class DeformationFFSubsetTest(unittest.TestCase,
                              SubsetTest):

    def setUp(self):
        self.universe = InfiniteUniverse(DeformationForceField(cutoff=5.))
        protein = Protein('insulin_calpha')
        self.universe.addObject(protein)        
        self.subset1 = protein[0]
        self.subset2 = protein[1]


class ANMFFSubsetTest(unittest.TestCase,
                      SubsetTest):

    def setUp(self):
        self.universe = InfiniteUniverse(AnisotropicNetworkForceField(cutoff=5.))
        protein = Protein('insulin_calpha')
        self.universe.addObject(protein)        
        self.subset1 = protein[0]
        self.subset2 = protein[1]


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(CalphaFFSubsetTest))
    s.addTest(loader.loadTestsFromTestCase(DeformationFFSubsetTest))
    s.addTest(loader.loadTestsFromTestCase(ANMFFSubsetTest))
    return s


if __name__ == '__main__':
    unittest.main()

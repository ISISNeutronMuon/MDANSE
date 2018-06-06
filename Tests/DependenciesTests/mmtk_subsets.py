# Subset energy tests
#
# Written by Konrad Hinsen
#

import numpy

class SubsetTest(object):

    def test_singleSubset(self):
        outside = set(self.universe.atomList())-set(self.subset1.atomList())
        e, fc = self.universe.energyAndForceConstants(self.subset1)
        for a1 in outside:
            for a2 in outside:
                self.assert_((numpy.fabs(fc[a1,a2].array) < 1.e-11).all())
        for a1 in self.subset1.atomList():
            for a2 in self.subset1.atomList():
                self.assert_((numpy.fabs(fc[a1,a2].array) > 1.e-11).any())

    def test_twoSubsets(self):
        inside = set(self.subset1.atomList()) | set(self.subset2.atomList())
        outside = set(self.universe.atomList())-inside
        e, fc = self.universe.energyAndForceConstants(self.subset1, self.subset2)
        for a1 in self.subset1.atomList():
            for a2 in self.subset1.atomList():
                if a1 != a2:
                    self.assert_((numpy.fabs(fc[a1,a2].array) < 1.e-11).all())
        for a1 in self.subset2.atomList():
            for a2 in self.subset2.atomList():
                if a1 != a2:
                    self.assert_((numpy.fabs(fc[a1,a2].array) < 1.e-11).all())
        for a1 in self.subset1.atomList():
            for a2 in self.subset2.atomList():
                self.assert_((numpy.fabs(fc[a1,a2].array) > 1.e-11).any())
        for a1 in outside:
            for a2 in outside:
                self.assert_((numpy.fabs(fc[a1,a2].array) < 1.e-11).all())


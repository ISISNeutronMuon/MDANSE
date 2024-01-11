# **************************************************************************
#
# MDANSE: Molecular Dynamics Analysis for Neutron Scattering Experiments
#
# @file      Tests/DependenciesTests/mmtk_internal_coordinate_tests.py
# @brief     Implements module/class/test mmtk_internal_coordinate_tests
#
# @homepage https://www.isis.stfc.ac.uk/Pages/MDANSEproject.aspx
# @license   GNU General Public License v3 or higher (see LICENSE)
# @copyright Institut Laue Langevin 2013-now
# @copyright ISIS Neutron and Muon Source, STFC, UKRI 2021-now
# @authors   Scientific Computing Group at ILL (see AUTHORS)
#
# **************************************************************************

# Internal coordinate tests
#
# Written by Konrad Hinsen
#

import unittest

import numpy
from MMTK.Proteins import Protein
from MMTK.InternalCoordinates import BondLength, BondAngle, DihedralAngle


class ICTest(unittest.TestCase):
    def setUp(self):
        # Pick a proline residue because of its cycle
        self.protein = Protein("insulin.pdb")
        self.chain = self.protein[1]
        self.res = self.chain[27]

    def test_phipsi(self):
        phi, psi = self.res.phiPsi()
        phi_o = self.res.phiAngle()
        psi_o = self.res.psiAngle()
        self.assertAlmostEqual(phi, phi_o.getValue(), 10)
        self.assertAlmostEqual(psi, psi_o.getValue(), 10)

    def test_changephi(self):
        phi = self.res.phiAngle()
        current_phi = phi.getValue()
        for dphi in [-0.2, -0.1, 0.1, 0.2]:
            phi.setValue(current_phi + dphi)
            self.assertAlmostEqual(
                phi.getValue() % (2.0 * numpy.pi),
                (current_phi + dphi) % (2.0 * numpy.pi),
                10,
            )

    def test_changebond(self):
        b = BondLength(self.res.peptide.C_alpha, self.res.peptide.C)
        current_b = b.getValue()
        for db in [-0.02, -0.01, 0.01, 0.02]:
            b.setValue(current_b + db)
            self.assertAlmostEqual(b.getValue(), current_b + db)

    def test_changeangle(self):
        a = BondAngle(self.res.peptide.N, self.res.peptide.C_alpha, self.res.peptide.C)
        current_a = a.getValue()
        for da in [-0.2, -0.1, 0.1, 0.2]:
            a.setValue(current_a + da)
            self.assertAlmostEqual(
                a.getValue() % (2.0 * numpy.pi), (current_a + da) % (2.0 * numpy.pi), 10
            )

    def test_cyclic(self):
        self.assertRaises(
            ValueError, BondLength, self.res.peptide.N, self.res.peptide.C_alpha
        )
        self.assertRaises(
            ValueError,
            BondAngle,
            self.res.peptide.N,
            self.res.peptide.C_alpha,
            self.res.sidechain.C_beta,
        )
        self.assertRaises(
            ValueError,
            DihedralAngle,
            self.res.peptide.N,
            self.res.peptide.C_alpha,
            self.res.sidechain.C_beta,
            self.res.sidechain.C_gamma,
        )


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(ICTest)


if __name__ == "__main__":
    unittest.main()

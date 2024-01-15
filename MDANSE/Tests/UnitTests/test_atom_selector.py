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

# MDANSE : Molecular Dynamics Analysis for Neutron Scattering Experiments
# ------------------------------------------------------------------------------------------
# Copyright (C)
# 2015- Eric C. Pellegrini Institut Laue-Langevin
# BP 156
# 6, rue Jules Horowitz
# 38042 Grenoble Cedex 9
# France
# pellegrini[at]ill.fr
# goret[at]ill.fr
# aoun[at]ill.fr
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

""" 
Created on May 29, 2015

@author: Eric C. Pellegrini
"""
import os
import unittest
from MDANSE.Framework.Selectors import All
from MDANSE.Framework.Selectors import Amine
from MDANSE.Framework.Selectors import Ammonium
from MDANSE.Framework.Selectors import AtomElement
from MDANSE.Framework.Selectors import AtomFullName
from MDANSE.Framework.Selectors import AtomIndex
from MDANSE.Framework.Selectors import AtomName
from MDANSE.Framework.Selectors import AtomPicked
from MDANSE.Framework.Selectors import AtomSymbol
from MDANSE.Framework.Selectors import Backbone
from MDANSE.Framework.Selectors import CarboHydrogen
from MDANSE.Framework.Selectors import CarbonAlpha
from MDANSE.Framework.Selectors import ChainName
from MDANSE.Framework.Selectors import HeteroHydrogen
from MDANSE.Framework.Selectors import Hydroxyl
from MDANSE.Framework.Selectors import Macromolecule
from MDANSE.Framework.Selectors import Methyl
from MDANSE.Framework.Selectors import MoleculeIndex
from MDANSE.Framework.Selectors import MoleculeName
from MDANSE.Framework.Selectors import NitroHydrogen
from MDANSE.Framework.Selectors import NucleotideBase
from MDANSE.Framework.Selectors import NucleotideSugar
from MDANSE.Framework.Selectors import NucleotideType
from MDANSE.Framework.Selectors import OxyHydrogen
from MDANSE.Framework.Selectors import Peptide
from MDANSE.Framework.Selectors import Phosphate
from MDANSE.Framework.Selectors import PythonScript
from MDANSE.Framework.Selectors import ResidueClass
from MDANSE.Framework.Selectors import ResidueName
from MDANSE.Framework.Selectors import ResidueType
from MDANSE.Framework.Selectors import SideChain
from MDANSE.Framework.Selectors import Sulphate
from MDANSE.Framework.Selectors import SulphurHydrogen
from MDANSE.Framework.Selectors import Thiol
from MDANSE.Framework.Selectors import WithinShell
from MDANSE.IO.PDBReader import PDBReader


pbd_2vb1 = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "Data", "2vb1.pdb")
pbd_1gip = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "Data", "1gip.pdb")
select_atoms_script = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "select_atoms.py")


class TestAtomsSelector(unittest.TestCase):
    """ """

    @classmethod
    def setUpClass(cls):
        """get_some_resource() is slow, to avoid calling it for each test use setUpClass()
        and store the result as class variable
        """
        super(TestAtomsSelector, cls).setUpClass()

        reader = PDBReader(pbd_2vb1)
        cls._proteinChemicalSystem = reader.build_chemical_system()

        reader = PDBReader(pbd_1gip)
        cls._nucleicAcidChemicalSystem = reader.build_chemical_system()

    def test_all(self):
        selector = All.All(self._proteinChemicalSystem)
        selection = selector.select()

        self.assertEqual(len(selection), 30714)

    def test_amine(self):
        selector = Amine.Amine(self._proteinChemicalSystem)
        selection = selector.select(["*"])
        self.assertEqual(len(selection), 117)

    def test_ammonium(self):
        selector = Ammonium.Ammonium(self._proteinChemicalSystem)
        selection = selector.select(["*"])
        self.assertEqual(len(selection), 28)

    def test_atom_element(self):
        selector = AtomElement.AtomElement(self._proteinChemicalSystem)
        selection = list(selector.select(["sulphur"]))
        self.assertEqual(len(selection), 10)

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 30714)

    def test_atom_full_name(self):
        selector = AtomFullName.AtomFullName(self._proteinChemicalSystem)
        selection = selector.select(["...LYS1.N", "...VAL2.O"])
        self.assertEqual(len(selection), 2)

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 30714)

    def test_atom_index(self):
        selector = AtomIndex.AtomIndex(self._proteinChemicalSystem)
        selection = list(selector.select([0, 1, 2, 3]))
        self.assertEqual(len(selection), 4)
        self.assertTrue(selection[0].name in ["N", "HT1", "HT2", "HT3"])
        self.assertTrue(selection[1].name in ["N", "HT1", "HT2", "HT3"])
        self.assertTrue(selection[2].name in ["N", "HT1", "HT2", "HT3"])
        self.assertTrue(selection[3].name in ["N", "HT1", "HT2", "HT3"])

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 30714)

    def test_atom_name(self):
        selector = AtomName.AtomName(self._proteinChemicalSystem)
        selection = selector.select(["N", "O"])
        self.assertEqual(len(selection), 258)

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 30714)

    def test_atom_picked(self):
        selector = AtomPicked.AtomPicked(self._proteinChemicalSystem)
        selection = list(selector.select([0, 1, 2, 3]))
        self.assertEqual(len(selection), 4)
        self.assertTrue(selection[0].name in ["N", "HT1", "HT2", "HT3"])
        self.assertTrue(selection[1].name in ["N", "HT1", "HT2", "HT3"])
        self.assertTrue(selection[2].name in ["N", "HT1", "HT2", "HT3"])
        self.assertTrue(selection[3].name in ["N", "HT1", "HT2", "HT3"])

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 30714)

    def test_atom_symbol(self):
        selector = AtomSymbol.AtomSymbol(self._proteinChemicalSystem)
        selection = list(selector.select(["S"]))
        self.assertEqual(len(selection), 10)

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 30714)

    def test_backbone(self):
        selector = Backbone.Backbone(self._proteinChemicalSystem)
        selection = selector.select(["*"])
        self.assertEqual(len(selection), 775)

    def test_carbo_hydrogens(self):
        selector = CarboHydrogen.CarboHydrogen(self._proteinChemicalSystem)
        selection = selector.select(["...LYS1.HB2", "...LYS1.HB3"])
        self.assertEqual(len(selection), 2)

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 696)

    def test_carbon_alpha(self):
        selector = CarbonAlpha.CarbonAlpha(self._proteinChemicalSystem)

        selection = selector.select()
        self.assertEqual(len(selection), 129)

    def test_chain_name(self):
        selector = ChainName.ChainName(self._proteinChemicalSystem)

        selection = selector.select([""])
        self.assertEqual(len(selection), 1960)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 1960)

    def test_hetero_hydrogen(self):
        selector = HeteroHydrogen.HeteroHydrogen(self._proteinChemicalSystem)

        selection = selector.select(["...SER24.HG"])
        self.assertEqual(len(selection), 1)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 19427)

    def test_hydroxyl(self):
        selector = Hydroxyl.Hydroxyl(self._proteinChemicalSystem)

        selection = selector.select(["...SER24.HG"])
        self.assertEqual(len(selection), 1)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 28786)

    def test_macromolecule(self):
        selector = Macromolecule.Macromolecule(self._proteinChemicalSystem)

        selection = selector.select(["peptide_chain"])
        self.assertEqual(len(selection), 1960)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 1960)

    def test_methyl(self):
        selector = Methyl.Methyl(self._proteinChemicalSystem)

        selection = selector.select(["...VAL29.1HG1", "...VAL29.1HG2"])
        self.assertEqual(len(selection), 2)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 183)

    def test_molecule_index(self):
        selector = MoleculeIndex.MoleculeIndex(self._proteinChemicalSystem)

        selection = selector.select([0])
        self.assertEqual(len(selection), 1960)

        selection = selector.select([15])
        self.assertEqual(len(selection), 3)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 30714)

    def test_molecule_name(self):
        selector = MoleculeName.MoleculeName(self._proteinChemicalSystem)

        selection = selector.select([""])
        self.assertEqual(len(selection), 1960)

        selection = selector.select(["WAT_9709"])
        self.assertEqual(len(selection), 3)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 30714)

    def test_nitro_hydrogens(self):
        selector = NitroHydrogen.NitroHydrogen(self._proteinChemicalSystem)
        selection = selector.select(["...LYS1.HT1", "...LYS1.HT2", "...LYS1.HT3"])
        self.assertEqual(len(selection), 3)

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 243)

    def test_nucleotide_base(self):
        selector = NucleotideBase.NucleotideBase(self._nucleicAcidChemicalSystem)
        selection = selector.select(["A"])
        self.assertEqual(len(selection), 164)

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 328)

    def test_nucleotide_sugar(self):
        selector = NucleotideSugar.NucleotideSugar(self._nucleicAcidChemicalSystem)
        selection = selector.select(["A"])
        self.assertEqual(len(selection), 156)

        selection = list(selector.select(["*"]))
        self.assertEqual(len(selection), 312)

    def test_nucleotide_type(self):
        selector = NucleotideType.NucleotideType(self._nucleicAcidChemicalSystem)
        selection = selector.select(["DA"])
        self.assertEqual(len(selection), 128)

        selector = NucleotideType.NucleotideType(self._nucleicAcidChemicalSystem)
        selection = selector.select(["DT"])
        self.assertEqual(len(selection), 128)

        selector = NucleotideType.NucleotideType(self._nucleicAcidChemicalSystem)
        selection = selector.select(["DG"])
        self.assertEqual(len(selection), 266)

        selector = NucleotideType.NucleotideType(self._nucleicAcidChemicalSystem)
        selection = selector.select(["DC"])
        self.assertEqual(len(selection), 236)

        selector = NucleotideType.NucleotideType(self._nucleicAcidChemicalSystem)
        selection = selector.select(["*"])
        self.assertEqual(len(selection), 758)

    def test_oxy_hydrogen(self):
        selector = OxyHydrogen.OxyHydrogen(self._proteinChemicalSystem)

        selection = selector.select(["...THR118.HG1"])
        self.assertEqual(len(selection), 1)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 19184)

    def test_peptides(self):
        selector = Peptide.Peptide(self._proteinChemicalSystem)

        selection = selector.select([""])
        self.assertEqual(len(selection), 508)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 508)

    def test_phosphate(self):
        selector = Phosphate.Phosphate(self._nucleicAcidChemicalSystem)
        selection = selector.select(["*"])
        self.assertEqual(len(selection), 88)

    def test_python_script(self):
        selector = PythonScript.PythonScript(self._nucleicAcidChemicalSystem)
        selection = selector.select([select_atoms_script])
        self.assertEqual(len(selection), 22)

    def test_residue_class(self):
        selector = ResidueClass.ResidueClass(self._proteinChemicalSystem)

        selection = selector.select(["acidic"])
        self.assertEqual(len(selection), 114)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 1960)

    def test_residue_name(self):
        selector = ResidueName.ResidueName(self._proteinChemicalSystem)

        selection = selector.select(["...LYS1"])
        self.assertEqual(len(selection), 24)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 1960)

    def test_residue_name(self):
        selector = ResidueType.ResidueType(self._proteinChemicalSystem)

        selection = selector.select(["CYX"])
        self.assertEqual(len(selection), 80)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 1960)

    def test_sidechains(self):
        selector = SideChain.SideChain(self._proteinChemicalSystem)

        selection = selector.select([""])
        self.assertEqual(len(selection), 1185)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 1185)

    def test_sulphate(self):
        selector = Sulphate.Sulphate(self._proteinChemicalSystem)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 0)

    def test_sulphur_hydrogen(self):
        selector = SulphurHydrogen.SulphurHydrogen(self._proteinChemicalSystem)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 0)

    def test_thiol(self):
        selector = Thiol.Thiol(self._proteinChemicalSystem)

        selection = selector.select(["*"])
        self.assertEqual(len(selection), 0)

    def test_within_shell(self):
        selector = WithinShell.WithinShell(self._proteinChemicalSystem)

        selection = selector.select(0, 0, 0.3)
        self.assertEqual(len(selection), 16)


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestAtomsSelector))
    return s


if __name__ == "__main__":
    unittest.main(verbosity=2)

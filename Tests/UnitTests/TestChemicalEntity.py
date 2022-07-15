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
import collections
import pickle
from typing import Union
import unittest

from MDANSE.Chemistry import RESIDUES_DATABASE, NUCLEOTIDES_DATABASE
import MDANSE.Chemistry.ChemicalEntity as ce


class TestAtom(unittest.TestCase):

    def test_empty_instantiation(self):
        atom = ce.Atom()

        self.assertEqual(atom.symbol, 'H')
        self.assertEqual(atom.name, 'H')
        self.assertEqual(atom.bonds, [])
        self.assertEqual(atom._groups, [])
        self.assertEqual(atom.ghost, False)
        self.assertEqual(atom.index, None)
        self.assertEqual(atom.parent, None)

    def test_correct_instantiation(self):
        # user getitem
        atom = ce.Atom(symbol='C', name='carbon12')

    def test_undefined_element(self):
        with self.assertRaises(ce.UnknownAtomError):
            ce.Atom(symbol='CC')

    def test_copy(self):
        atom = ce.Atom()
        copy = atom.copy()

        self.assertEqual(atom.symbol, copy.symbol)
        self.assertEqual(atom.name, copy.name)
        self.assertEqual(atom.bonds, copy.bonds)
        self.assertEqual(atom._groups, copy._groups)
        self.assertEqual(atom.ghost, copy.ghost)
        self.assertEqual(atom.index, copy.index)
        self.assertEqual(atom.parent, copy.parent)

    def test_pickling(self):
        atom = ce.Atom()
        pickled = pickle.dumps(atom)
        unpickled = pickle.loads(pickled)

        self.assertEqual(atom.symbol, unpickled.symbol)
        self.assertEqual(atom.name, unpickled.name)
        self.assertEqual(atom.bonds, unpickled.bonds)
        self.assertEqual(atom._groups, unpickled._groups)
        self.assertEqual(atom.ghost, unpickled.ghost)
        self.assertEqual(atom.index, unpickled.index)
        self.assertEqual(atom.parent, unpickled.parent)

    def test_dunder_str(self):
        atom = ce.Atom(name='Hydrogen')
        self.assertEqual(str(atom), 'Hydrogen')

    def test_dunder_repr(self):
        atom = ce.Atom(name='Hydrogen', bonds=[ce.Atom(name='H5')])
        self.assertEqual(repr(atom), "MDANSE.Chemistry.ChemicalEntity.Atom(parent=None, name='Hydrogen', "
                                     "symbol='H', bonds=[Atom(H5)], groups=[], ghost=False, index=None)")

    def test_atom_list_ghost_true(self):
        atom = ce.Atom(ghost=True)
        atom_list = atom.atom_list()
        self.assertEqual(atom_list, [])

    def test_atom_list_ghost_false(self):
        atom = ce.Atom(ghost=False)
        atom_list = atom.atom_list()
        self.assertEqual(atom_list, [atom])

    def test_total_number_of_atoms(self):
        atom = ce.Atom()
        n = atom.total_number_of_atoms()
        self.assertEqual(n, 1)

    def test_number_of_atoms(self):
        atom = ce.Atom(ghost=False)
        ghost = ce.Atom(ghost=True)

        self.assertEqual(atom.number_of_atoms(), 0)
        self.assertEqual(ghost.number_of_atoms(), 1)

    def test_bonds_setter(self):
        atom = ce.Atom()
        atom.bonds = [ce.Atom(symbol='C')]
        self.assertEqual(len(atom.bonds), 1)
        self.assertEqual(atom.bonds[0].symbol, 'C')
        self.assertEqual(atom.bonds[0].name, 'C')
        self.assertEqual(atom.bonds[0].bonds, [])
        self.assertEqual(atom.bonds[0]._groups, [])
        self.assertEqual(atom.bonds[0].ghost, False)
        self.assertEqual(atom.bonds[0].index, None)
        self.assertEqual(atom.bonds[0].parent, None)

    def test_ghost_setter(self):
        atom = ce.Atom(ghost=False)
        atom.ghost = True
        self.assertTrue(atom.ghost)

    def test_index_setter_index_not_set(self):
        atom = ce.Atom()
        atom.index = 0
        self.assertEqual(atom.index, 0)

    def test_index_setter_index_set(self):
        atom = ce.Atom(index=0)
        atom.index = 1
        self.assertEqual(atom.index, 0)

    def test_name_setter(self):
        atom = ce.Atom()
        atom.name = 'Hydrogen'
        self.assertEqual(atom.name, 'Hydrogen')

    def test_symbol_setter(self):
        atom = ce.Atom()
        atom.symbol = 'C'

        self.assertEqual(atom.symbol, 'C')
        with self.assertRaises(ce.UnknownAtomError):
            atom.symbol = 'CC'

    def test_serialize(self):
        atom = ce.Atom()
        dictionary = {}
        result = atom.serialize(dictionary)

        self.assertEqual(result, ('atoms', 0))
        self.assertEqual(dictionary, {'atoms': ['H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)']})


@unittest.skip
class TestAtomCluster(unittest.TestCase):
    def test_valid_instantiation_parentful(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()])

        self.assertEqual(None, cluster.parent)
        self.assertEqual('Cluster1', cluster.name)
        self.assertEqual(False, cluster._parentless)
        self.assertEqual('H', cluster)
        for atom in cluster._atoms.values():
            self.assertEqual('H', atom.symbol)
            self.assertEqual('H', atom.name)
            self.assertEqual([], atom.bonds)
            self.assertEqual([], atom._groups)
            self.assertEqual(False, atom.ghost)
            self.assertEqual(None, atom.index)
            self.assertEqual(cluster, atom.parent)

    def test_valid_instantiation_parentless(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)

        self.assertEqual(cluster.parent, None)
        self.assertEqual(cluster.name, 'Cluster1')
        self.assertEqual(cluster._parentless, True)
        for atom in cluster._atoms:
            self.assertEqual(atom.symbol, 'H')
            self.assertEqual(atom.name, 'H')
            self.assertEqual(atom.bonds, [])
            self.assertEqual(atom._groups, [])
            self.assertEqual(atom.ghost, False)
            self.assertEqual(atom.index, None)
            self.assertEqual(atom.parent, None)

    def test_pickling(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)

        pickled = pickle.dumps(cluster)
        unpickled = pickle.loads(pickled)

        self.assertEqual(cluster.parent, unpickled.parent)
        self.assertEqual(cluster.name, unpickled.name)
        self.assertEqual(cluster._parentless, unpickled._parentless)
        for atom, unpickled_atom in zip(cluster._atoms, unpickled._atoms):
            self.assertEqual(atom.symbol, unpickled_atom.symbol)
            self.assertEqual(atom.name, unpickled_atom.name)
            self.assertEqual(atom.bonds, unpickled_atom.bonds)
            self.assertEqual(atom._groups, unpickled_atom._groups)
            self.assertEqual(atom.ghost, unpickled_atom.ghost)
            self.assertEqual(atom.index, unpickled_atom.index)
            self.assertEqual(atom.parent, unpickled_atom.parent)

    def test_atom_list(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom(ghost=True)], parentless=True)

        self.assertEqual(1, len(cluster.atom_list()))
        for atom in cluster.atom_list():
            self.assertEqual(atom.symbol, 'H')
            self.assertEqual(atom.name, 'H')
            self.assertEqual(atom.bonds, [])
            self.assertEqual(atom._groups, [])
            self.assertEqual(atom.ghost, False)
            self.assertEqual(atom.index, None)
            self.assertEqual(atom.parent, None)

    def test_copy(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)
        copy = cluster.copy()

        self.assertEqual(cluster.parent, copy.parent)
        self.assertEqual(cluster.name, copy.name)
        self.assertEqual(cluster._parentless, copy._parentless)
        for atom, copied_atom in zip(cluster._atoms, copy._atoms):
            self.assertEqual(atom.symbol, copied_atom.symbol)
            self.assertEqual(atom.name, copied_atom.name)
            self.assertEqual(atom.bonds, copied_atom.bonds)
            self.assertEqual(atom._groups, copied_atom._groups)
            self.assertEqual(atom.ghost, copied_atom.ghost)
            self.assertEqual(atom.index, copied_atom.index)
            # self.assertEqual(atom.parent, copied_atom.parent)

    def test_number_of_atoms(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)
        ghost_cluster = ce.AtomCluster('Cluster1', [ce.Atom(ghost=True), ce.Atom(ghost=True)], parentless=True)

        self.assertEqual(2, cluster.number_of_atoms())
        self.assertEqual(0, ghost_cluster.number_of_atoms())

    def test_total_number_of_atoms(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)
        ghost_cluster = ce.AtomCluster('Cluster1', [ce.Atom(ghost=True), ce.Atom(ghost=True)], parentless=True)

        self.assertEqual(2, cluster.total_number_of_atoms())
        self.assertEqual(2, ghost_cluster.total_number_of_atoms())

    def test_reorder_atoms_exception(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(symbol='H'), ce.Atom(symbol='C')], parentless=True)
        with self.assertRaises(ce.InconsistentAtomNamesError):
            cluster.reorder_atoms(['H', 'H'])

    def test_reorder_atoms_valid(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(symbol='H'), ce.Atom(symbol='C')], parentless=True)
        cluster.reorder_atoms(['C', 'H'])


class TestMolecule(unittest.TestCase):
    def setUp(self):
        self.molecule = ce.Molecule('WAT', 'water')

    def compare_two_molecules(self, molecule: ce.Molecule):
        self.assertEqual(None, molecule.parent)
        self.assertEqual('water', molecule.name)
        self.assertEqual('WAT', molecule.code)

        for name, reference_name in zip(molecule._atoms.keys(), ['OW', 'HW2', 'HW1']):
            self.assertEqual(reference_name, name)

        self.compare_atoms(molecule._atoms, molecule)

    def compare_atoms(self, atom_list, parent: ce.Molecule):
        try:
            atom = atom_list['OW']
        except TypeError:
            atom = atom_list[0]
        self.assertEqual('O', atom.symbol)
        self.assertEqual('OW', atom.name)
        self.assertEqual(2, len(atom.bonds))
        self.assertEqual(parent._atoms['HW1'], atom.bonds[0])
        self.assertEqual(parent._atoms['HW2'], atom.bonds[1])
        self.assertEqual([], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

        try:
            atom = atom_list['HW1']
        except TypeError:
            atom = atom_list[2]
        self.assertEqual('H', atom.symbol)
        self.assertEqual('HW1', atom.name)
        self.assertEqual(1, len(atom.bonds))
        self.assertEqual(parent._atoms['OW'], atom.bonds[0])
        self.assertEqual([], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

        try:
            atom = atom_list['HW2']
        except TypeError:
            atom = atom_list[1]
        self.assertEqual('H', atom.symbol)
        self.assertEqual('HW2', atom.name)
        self.assertEqual(1, len(atom.bonds))
        self.assertEqual(parent._atoms['OW'], atom.bonds[0])
        self.assertEqual([], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

    def test_valid_molecule_instantiation(self):
        self.compare_two_molecules(self.molecule)

    def test_unregistered_molecule_instantiation(self):
        with self.assertRaises(ce.UnknownMoleculeError):
            ce.Molecule('000000', '000000')

    def test_dunder_getitem(self):
        self.assertEqual(self.molecule._atoms['OW'], self.molecule['OW'])

    def test_pickling(self):
        pickled = pickle.dumps(self.molecule)
        unpickled = pickle.loads(pickled)

        self.compare_two_molecules(unpickled)

    def test_dunder_repr(self):
        self.assertEqual("MDANSE.MolecularDynamics.ChemicalEntity.Molecule(parent=None, name='water', "
                         "atoms=OrderedDict([('OW', MDANSE.Chemistry.ChemicalEntity.Atom(parent=MDANSE.Chemistry."
                         "ChemicalEntity.Molecule(water), name='OW', symbol='O', bonds=[Atom(HW1), Atom(HW2)], "
                         "groups=[], ghost=False, index=None, alternatives=['O', 'OH2'])), ('HW2', MDANSE.Chemistry."
                         "ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity.Molecule(water), name='HW2', "
                         "symbol='H', bonds=[Atom(OW)], groups=[], ghost=False, index=None, alternatives=['H2'])), "
                         "('HW1', MDANSE.Chemistry.ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity."
                         "Molecule(water), name='HW1', symbol='H', bonds=[Atom(OW)], groups=[], ghost=False, index=None"
                         ", alternatives=['H1']))]), code='WAT')", repr(self.molecule))

    def test_atom_list(self):
        self.assertEqual(3, len(self.molecule.atom_list()))
        self.compare_atoms(self.molecule.atom_list(), self.molecule)

    def test_copy(self):
        copy = self.molecule.copy()
        self.compare_two_molecules(copy)

    def test_number_of_atoms(self):
        self.assertEqual(3, self.molecule.number_of_atoms())

    def test_total_number_of_atoms(self):
        self.assertEqual(3, self.molecule.total_number_of_atoms())

    def test_reorder_atoms_invalid_input(self):
        with self.assertRaises(ce.InconsistentAtomNamesError):
            self.molecule.reorder_atoms(['O', 'H', 'H'])

    def test_reorder_atoms_valid_input(self):
        self.molecule.reorder_atoms(['HW1', 'HW2', 'OW'])
        self.assertEqual('HW1', self.molecule.atom_list()[0].name)
        self.assertEqual('HW2', self.molecule.atom_list()[1].name)
        self.assertEqual('OW', self.molecule.atom_list()[2].name)

    def test_serialize_from_empty_dict(self):
        dictionary = {}
        result = self.molecule.serialize(dictionary)

        self.assertEqual(('molecules', 0), result)
        self.assertDictEqual({'molecules': ['H5Molecule(self._h5_file,h5_contents,[0, 1, 2],code="WAT",name="water")'],
                              'atoms': ['H5Atom(self._h5_file,h5_contents,symbol="O", name="OW", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HW2", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HW1", ghost=False)']},
                             dictionary)

    def test_serialize_from_nonempty_dict(self):
        dictionary = {'atoms': ['', '']}
        result = self.molecule.serialize(dictionary)

        self.assertEqual(('molecules', 0), result)
        self.assertDictEqual({'atoms': ['', '',
                                        'H5Atom(self._h5_file,h5_contents,symbol="O", name="OW", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HW2", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HW1", ghost=False)'],
                             'molecules': ['H5Molecule(self._h5_file,h5_contents,[2, 3, 4],code="WAT",name="water")']},
                             dictionary)


class TestResidue(unittest.TestCase):
    def test_valid_residue_initialisation_without_variant(self):
        residue = ce.Residue('GLY', 'glycine', None)

        self.compare_base_residues(residue, True)

    def compare_base_residues(self, residue: ce.Residue, compare_atoms: bool):
        self.assertEqual('glycine', residue.name)
        self.assertEqual(None, residue.parent)
        self.assertEqual('GLY', residue.code)
        self.assertEqual(None, residue._variant)
        self.assertEqual(None, residue._selected_variant)
        if compare_atoms:
            self.assertEqual(collections.OrderedDict(), residue._atoms)

    def test_valid_residue_initialisation_with_valid_variant(self):
        residue = ce.Residue('GLY', 'glycine', 'CT1')

        self.assertEqual('glycine', residue.name)
        self.assertEqual(None, residue.parent)
        self.assertEqual('GLY', residue.code)
        self.assertEqual('CT1', residue._variant)
        self.assertDictEqual(RESIDUES_DATABASE['CT1'], residue._selected_variant)
        self.assertEqual(collections.OrderedDict(), residue._atoms)

    def test_invalid_residue_initialisation(self):
        with self.assertRaises(ce.UnknownResidueError):
            ce.Residue('00000', '00000')

    def test_valid_residue_initialisation_with_nonexistent_variant(self):
        with self.assertRaises(ce.InvalidVariantError):
            ce.Residue('GLY', 'glycine', '00000')

    def test_valid_residue_initialisation_with_invalid_variant(self):
        with self.assertRaises(ce.InvalidVariantError):
            ce.Residue('GLY', 'glycine', 'GLY')

    def test_set_atoms_valid(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])

        self.assertEqual(7, len(residue._atoms))
        self.compare_atoms(residue._atoms, residue)

    def compare_atoms(self, atom_list: Union[list, dict, ce.Residue], parent: ce.Residue):
        try:
            atom = atom_list['H']
        except TypeError:
            atom = atom_list[0]
        self.assertEqual('H', atom.symbol)
        self.assertEqual('H', atom.name)
        self.assertEqual(1, len(atom.bonds))
        self.assertEqual(parent._atoms['N'], atom.bonds[0])
        self.assertEqual(['backbone', 'peptide'], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

        try:
            atom = atom_list['HA3']
        except TypeError:
            atom = atom_list[1]
        self.assertEqual('H', atom.symbol)
        self.assertEqual('HA3', atom.name)
        self.assertEqual(1, len(atom.bonds))
        self.assertEqual(parent._atoms['CA'], atom.bonds[0])
        self.assertEqual(['sidechain'], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

        try:
            atom = atom_list['O']
        except TypeError:
            atom = atom_list[2]
        self.assertEqual('O', atom.symbol)
        self.assertEqual('O', atom.name)
        self.assertEqual(1, len(atom.bonds))
        self.assertEqual(parent._atoms['C'], atom.bonds[0])
        self.assertEqual(['backbone', 'peptide'], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

        try:
            atom = atom_list['N']
        except TypeError:
            atom = atom_list[3]
        self.assertEqual('N', atom.symbol)
        self.assertEqual('N', atom.name)
        self.assertEqual(3, len(atom.bonds))
        self.assertEqual(parent._atoms['CA'], atom.bonds[0])
        self.assertEqual(parent._atoms['H'], atom.bonds[1])
        self.assertEqual('-R', atom.bonds[2])
        self.assertEqual(['backbone', 'peptide'], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

        try:
            atom = atom_list['CA']
        except TypeError:
            atom = atom_list[4]
        self.assertEqual('C', atom.symbol)
        self.assertEqual('CA', atom.name)
        self.assertEqual(4, len(atom.bonds))
        self.assertEqual(parent._atoms['C'], atom.bonds[0])
        self.assertEqual(parent._atoms['HA2'], atom.bonds[1])
        self.assertEqual(parent._atoms['HA3'], atom.bonds[2])
        self.assertEqual(parent._atoms['N'], atom.bonds[3])
        self.assertEqual(['backbone'], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

        try:
            atom = atom_list['HA2']
        except TypeError:
            atom = atom_list[5]
        self.assertEqual('H', atom.symbol)
        self.assertEqual('HA2', atom.name)
        self.assertEqual(1, len(atom.bonds))
        self.assertEqual(parent._atoms['CA'], atom.bonds[0])
        self.assertEqual(['backbone'], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

        try:
            atom = atom_list['C']
        except TypeError:
            atom = atom_list[6]
        self.assertEqual('C', atom.symbol)
        self.assertEqual('C', atom.name)
        self.assertEqual(3, len(atom.bonds))
        self.assertEqual(parent._atoms['CA'], atom.bonds[0])
        self.assertEqual(parent._atoms['O'], atom.bonds[1])
        self.assertEqual('+R', atom.bonds[2])
        self.assertEqual(['backbone', 'peptide'], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(parent, atom.parent)

    def test_set_atoms_invalid(self):
        residue = ce.Residue('GLY', 'glycine', None)
        with self.assertRaises(ce.InconsistentAtomNamesError):
            residue.set_atoms([])

    def test_pickling(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])

        pickled = pickle.dumps(residue)
        unpickled = pickle.loads(pickled)

        self.compare_base_residues(unpickled, False)
        self.compare_atoms(unpickled._atoms, unpickled)

    def test_dunder_getitem(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        self.compare_atoms(residue, residue)

    def test_atom_list(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        self.compare_atoms(residue.atom_list(), residue)

    def test_number_of_atoms(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        self.assertEqual(7, residue.number_of_atoms())
        self.assertEqual(7, residue.total_number_of_atoms())

    def test_copy(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        copy = residue.copy()

        self.compare_atoms(copy, copy)

    def test_serialize_empty_dict(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        dictionary = {}
        result = residue.serialize(dictionary)

        self.maxDiff = None
        self.assertEqual(('residues', 0), result)
        self.assertDictEqual({'residues': ['H5Residue(self._h5_file,h5_contents,[0, 1, 2, 3, 4, 5, 6],code="GLY",'
                                           'name="glycine",variant=None)'],
                              'atoms': ['H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HA3", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="O", name="O", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="N", name="N", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="C", name="CA", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HA2", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="C", name="C", ghost=False)']},
                             dictionary)

    def test_serialize_nonempty_dict(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        dictionary = {'atoms': ['', '', '']}
        result = residue.serialize(dictionary)

        self.maxDiff = None
        self.assertEqual(('residues', 0), result)
        self.assertDictEqual({'residues': ['H5Residue(self._h5_file,h5_contents,[3, 4, 5, 6, 7, 8, 9],code="GLY",'
                                           'name="glycine",variant=None)'],
                              'atoms': ['', '', '',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HA3", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="O", name="O", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="N", name="N", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="C", name="CA", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HA2", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="C", name="C", ghost=False)']},
                             dictionary)


class TestNucleotide(unittest.TestCase):
    def test_valid_residue_initialisation_without_variant(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)

        self.compare_base_residues(nucleotide, True)

    def compare_base_residues(self, nucleotide: ce.Nucleotide, compare_atoms: bool):
        self.assertEqual('5T1', nucleotide.name)
        self.assertEqual(None, nucleotide.parent)
        self.assertEqual('5T1', nucleotide.code)
        self.assertEqual(None, nucleotide._variant)
        self.assertEqual(None, nucleotide._selected_variant)
        if compare_atoms:
            self.assertEqual(collections.OrderedDict(), nucleotide._atoms)

    def test_valid_residue_initialisation_with_valid_variant(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', '3T1')

        self.assertEqual('5T1', nucleotide.name)
        self.assertEqual(None, nucleotide.parent)
        self.assertEqual('5T1', nucleotide.code)
        self.assertEqual('3T1', nucleotide._variant)
        self.assertDictEqual(NUCLEOTIDES_DATABASE['3T1'], nucleotide._selected_variant)
        self.assertEqual(collections.OrderedDict(), nucleotide._atoms)

    def test_invalid_residue_initialisation(self):
        with self.assertRaises(ce.UnknownResidueError):
            ce.Nucleotide('00000', '00000')

    def test_valid_residue_initialisation_with_nonexistent_variant(self):
        with self.assertRaises(ce.InvalidVariantError):
            ce.Nucleotide('5T1', '5T1', '00000')

    def test_valid_residue_initialisation_with_invalid_variant(self):
        with self.assertRaises(ce.InvalidVariantError):
            ce.Nucleotide('5T1', '5T1', 'A')

    def test_set_atoms_none(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])

        self.compare_atoms_in_5t1(nucleotide._atoms, nucleotide)

    def compare_atoms_in_5t1(self, atom_list: Union[dict, ce.Nucleotide, list], nucleotide: ce.Nucleotide):
        try:
            atom = atom_list['HO5\'']
        except TypeError:
            atom = atom_list[0]
        self.assertEqual('H', atom.symbol)
        self.assertEqual('HO5\'', atom.name)
        self.assertEqual(1, len(atom.bonds))
        self.assertEqual('O5\'', atom.bonds[0])
        self.assertEqual([], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(nucleotide, atom.parent)

    def test_set_atoms_variant(self):
        nucleotide = ce.Nucleotide('A', 'adenine', '5T1')
        names = ['C3\'', 'C1\'', 'C5\'', 'H2\'', 'H5\'', 'H3\'', 'O4\'', 'C8', 'C2', 'H1\'', 'C6', 'C5', 'C4', 'H5\'\'',
                 'HO2\'', 'N9', 'C4\'', 'C2\'', 'O2\'', 'N1', 'N3', 'N6', 'N7','H4\'', 'H8', 'H2', 'O5\'', 'H61', 'H62',
                 'O3\'', 'HO5\'']
        nucleotide.set_atoms(names)

        symbols = ['C', 'C', 'C', 'H', 'H', 'H', 'O', 'C', 'C', 'H', 'C', 'C', 'C', 'H', 'H', 'N', 'C', 'C', 'O', 'N',
                   'N', 'N', 'N', 'H', 'H', 'H', 'O', 'H', 'H', 'O', 'H']
        bond_atoms = [['C2\'', 'C4\'', 'H3\'', 'O3\''], ['C2\'', 'H1\'', 'N9', 'O4\''], ['C4\'', 'H5\'', 'H5\'\'', 'O5\''],
                      ['C2\''], ['C5\''], ['C3\''], ['C1\'', 'C3\''], ['H8', 'N7', 'N9'], ['N1', 'N3', 'H2'], ['C1\''],
                      ['C5', 'N1', 'N6'], ['C4', 'C6', 'N7'], ['C5', 'N3', 'N9'], ['C5\''], ['O2\''],
                      ['C1\'', 'C4', 'C8'], ['C3\'', 'C5\'', 'H4\'', 'O4\''], ['C1\'', 'C3\'', 'H2\'', 'O2\''],
                      ['C2\'', 'HO2\''], ['C2', 'C6'], ['C2', 'C4'], ['C6', 'H61', 'H62'], ['C5', 'C8'], ['C4\''],
                      ['C8'], ['C2'], ['C5\''], ['N6'], ['N6'], ['C3\'', '+R'], ['O5\'']]
        groups = [['sugar']] * 7 + [['base'], ['base'], ['sugar']] + [['base']] * 3 + [['sugar'], ['sugar'], ['base']] \
                 + [['sugar']] * 3 + [['base']] * 4 + [['sugar'], ['base'], ['base'], ['phosphate'], ['base'], ['base'],
                                                       ['phosphate']]

        for atom, symbol, name, bonds, group in zip(nucleotide._atoms.values(), symbols, names, bond_atoms, groups):
            self.assertEqual(symbol, atom.symbol)
            self.assertEqual(name, atom.name)
            self.assertEqual(len(bonds), len(atom.bonds))
            for i, bond in enumerate(bonds):
                if bond[0] != '+':
                    self.assertEqual(nucleotide._atoms[bond], atom.bonds[i])
                else:
                    self.assertEqual(bond, atom.bonds[i])
            self.assertEqual(group, atom._groups)
            self.assertEqual(False, atom.ghost)
            self.assertEqual(None, atom.index)
            self.assertEqual(nucleotide, atom.parent)

    def test_set_atoms_invalid_input(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        with self.assertRaises(ce.InconsistentAtomNamesError):
            nucleotide.set_atoms(['HO5'])

    def test_dunder_getitem(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        self.compare_atoms_in_5t1(nucleotide, nucleotide)

    def test_pickling(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])

        pickled = pickle.dumps(nucleotide)
        unpickled = pickle.loads(pickled)

        self.compare_base_residues(unpickled, False)
        self.compare_atoms_in_5t1(unpickled._atoms, unpickled)

    def test_copy(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        copy = nucleotide.copy()

        self.compare_base_residues(copy, False)
        self.compare_atoms_in_5t1(copy._atoms, copy)

    def test_atom_list(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        self.compare_atoms_in_5t1(nucleotide.atom_list(), nucleotide)

    def test_number_of_atoms(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        self.assertEqual(1, nucleotide.number_of_atoms())
        self.assertEqual(1, nucleotide.total_number_of_atoms())

    def test_serialize_empty_dict(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        dictionary = {}
        result = nucleotide.serialize(dictionary)

        self.assertEqual(('nucleotides', 0), result)
        self.assertDictEqual({'nucleotides': ['H5Nucleotide(self._h5_file,h5_contents,[0],code="5T1",name="5T1",'
                                              'variant=None)'],
                              'atoms': ['H5Atom(self._h5_file,h5_contents,symbol="H", name="HO5\'", ghost=False)']},
                             dictionary)

    def test_serialize_nonempty_dict(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        dictionary = {'atoms': ['', '', '']}
        result = nucleotide.serialize(dictionary)

        self.assertEqual(('nucleotides', 0), result)
        self.assertDictEqual({'nucleotides': ['H5Nucleotide(self._h5_file,h5_contents,[3],code="5T1",name="5T1",'
                                              'variant=None)'],
                              'atoms': ['', '', '',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HO5\'", ghost=False)']},
                             dictionary)


# class TestAtomGroup(unittest.TestCase):
#     def test_valid_instantiation(self):
#         group = ce.AtomGroup()

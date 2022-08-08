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

from MDANSE.Chemistry import MOLECULES_DATABASE, RESIDUES_DATABASE, NUCLEOTIDES_DATABASE
import MDANSE.Chemistry.ChemicalEntity as ce


class TestAtom(unittest.TestCase):

    def test_empty_instantiation(self):
        atom = ce.Atom()

        self.assertEqual('H', atom.symbol)
        self.assertEqual('H', atom.name)
        self.assertEqual([], atom.bonds)
        self.assertEqual([], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(None, atom.parent)

    def test_instantiation_overwriting_default_values(self):
        bond = ce.Atom()
        atom = ce.Atom(symbol='C', name='carbon12', bonds=[bond], groups=['backbone'], ghost=True,
                       index=0, parent=bond, atomic_mass=12, random='12345')

        self.assertEqual('C', atom.symbol)
        self.assertEqual('carbon12', atom.name)
        self.assertEqual([bond], atom.bonds)
        self.assertEqual(['backbone'], atom._groups)
        self.assertEqual(True, atom.ghost)
        self.assertEqual(0, atom.index)
        self.assertEqual(bond, atom.parent)
        self.assertEqual(12, atom.atomic_mass)
        self.assertEqual('12345', atom.random)

    def test_instantiation_undefined_element(self):
        with self.assertRaises(ce.UnknownAtomError):
            ce.Atom(symbol='CC')

    def test_copy(self):
        atom = ce.Atom()
        copy = atom.copy()
        self.assertEqual(repr(atom), repr(copy))

    def test_pickling(self):
        atom = ce.Atom()
        pickled = pickle.dumps(atom)
        unpickled = pickle.loads(pickled)
        self.assertEqual(repr(atom), repr(unpickled))

    def test_dunder_str(self):
        atom = ce.Atom(name='Hydrogen')
        self.assertEqual('Hydrogen', str(atom))

    def test_dunder_repr(self):
        atom = ce.Atom(name='Hydrogen', bonds=[ce.Atom(name='H5')])
        self.assertEqual("MDANSE.Chemistry.ChemicalEntity.Atom(parent=None, name='Hydrogen', symbol='H', "
                         "bonds=[Atom(H5)], groups=[], ghost=False, index=None)", repr(atom))

    def test_atom_list_ghost_true(self):
        atom = ce.Atom(ghost=True)
        atom_list = atom.atom_list
        self.assertEqual([], atom_list)

    def test_atom_list_ghost_false(self):
        atom = ce.Atom(ghost=False)
        atom_list = atom.atom_list
        self.assertEqual([atom], atom_list)

    def test_total_number_of_atoms(self):
        atom = ce.Atom(ghost=False)
        ghost = ce.Atom(ghost=True)
        self.assertEqual(1, atom.total_number_of_atoms)
        self.assertEqual(1, ghost.total_number_of_atoms)

    def test_number_of_atoms(self):
        atom = ce.Atom(ghost=False)
        ghost = ce.Atom(ghost=True)

        self.assertEqual(0, atom.number_of_atoms)
        self.assertEqual(1, ghost.number_of_atoms)

    def test_bonds_setter(self):
        atom = ce.Atom()
        bond = ce.Atom(symbol='C')
        atom.bonds = [bond]
        self.assertEqual([bond], atom.bonds)

    def test_ghost_setter(self):
        atom = ce.Atom(ghost=False)
        atom.ghost = True
        self.assertTrue(atom.ghost)

    def test_index_setter_index_not_set(self):
        atom = ce.Atom()
        atom.index = 0
        self.assertEqual(0, atom.index)

    def test_index_setter_index_set(self):
        atom = ce.Atom(index=0)
        atom.index = 1
        self.assertEqual(0, atom.index)

    def test_name_setter(self):
        atom = ce.Atom(name='name')
        atom.name = 'Hydrogen'
        self.assertEqual('Hydrogen', atom.name)

    def test_symbol_setter(self):
        atom = ce.Atom(symbol='H')
        atom.symbol = 'C'

        self.assertEqual('C', atom.symbol)
        with self.assertRaises(ce.UnknownAtomError):
            atom.symbol = 'CC'

    def test_serialize(self):
        atom = ce.Atom()
        dictionary = {}
        result = atom.serialize(dictionary)

        self.assertEqual(('atoms', 0), result)
        self.assertEqual({'atoms': ['H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)']}, dictionary)


class TestAtomGroup(unittest.TestCase):
    def setUp(self):
        self.atom1 = ce.Atom(name='H1')
        self.atom2 = ce.Atom(name='H2')

        self.system = ce.ChemicalSystem('name')
        self.system.add_chemical_entity(self.atom1)
        self.system.add_chemical_entity(self.atom2)

        self.group = ce.AtomGroup([self.atom1, self.atom2])

    def test_instantiation_valid(self):
        self.assertEqual('', self.group.name)
        self.assertEqual(None, self.group.parent)
        self.assertEqual([self.atom1, self.atom2], self.group._atoms)
        self.assertEqual(self.system, self.group._chemical_system)

    def test_instantiation_invalid(self):
        system2 = ce.ChemicalSystem('name')
        system2.add_chemical_entity(self.atom2)

        with self.assertRaises(ce.ChemicalEntityError):
            ce.AtomGroup([self.atom1, self.atom2])

    def test_pickling(self):
        pickled = pickle.dumps(self.group)
        unpickled = pickle.loads(pickled)

        self.assertEqual('', unpickled.name)
        self.assertEqual(None, unpickled.parent)
        self.assertEqual(2, len(unpickled._atoms))
        self.assertEqual(repr(self.atom1), repr(unpickled._atoms[0]))
        self.assertEqual(repr(self.atom2), repr(unpickled._atoms[1]))
        self.assertEqual(repr(self.system), repr(unpickled._chemical_system))

    def test_duner_repr(self):
        self.assertEqual("MDANSE.MolecularDynamics.ChemicalEntity.AtomGroup(parent=None, name='', atoms=[MDANSE."
                         "Chemistry.ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity.ChemicalSystem(name), "
                         "name='H1', symbol='H', bonds=[], groups=[], ghost=False, index=0), MDANSE.Chemistry."
                         "ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity.ChemicalSystem(name), name='H2', "
                         "symbol='H', bonds=[], groups=[], ghost=False, index=1)], chemical_system=MDANSE.Chemistry."
                         "ChemicalEntity.ChemicalSystem(name))", repr(self.group))

    def test_dunder_str(self):
        self.assertEqual('AtomGroup consisting of 2 atoms', str(self.group))

    def test_atom_list(self):
        self.atom2._ghost = True
        self.assertEqual([self.atom1], self.group.atom_list)

    def test_copy(self):
        self.assertEqual(None, self.group.copy())

    def test_number_of_atoms(self):
        self.atom2._ghost = True
        self.assertEqual(1, self.group.number_of_atoms)
        self.assertEqual(2, self.group.total_number_of_atoms)

    def test_root_chemical_system(self):
        self.assertEqual(repr(self.system), repr(self.group.root_chemical_system))

    def test_serialize(self):
        dictionary = {}
        result = self.group.serialize(dictionary)

        self.assertEqual(None, result)
        self.assertDictEqual({}, dictionary)


class TestAtomCluster(unittest.TestCase):
    def test_valid_instantiation_parentful(self):
        atom1 = ce.Atom()
        atom2 = ce.Atom()
        cluster = ce.AtomCluster('Cluster1', [atom1, atom2])

        self.assertEqual(None, cluster.parent)
        self.assertEqual('Cluster1', cluster.name)
        self.assertEqual(False, cluster._parentless)
        self.assertEqual([atom1, atom2], cluster._atoms)
        self.assertEqual(cluster, cluster._atoms[0].parent)

    def test_valid_instantiation_parentless(self):
        atom1 = ce.Atom()
        atom2 = ce.Atom()
        cluster = ce.AtomCluster('Cluster1', [atom1, atom2], parentless=True)

        self.assertEqual(None, cluster.parent)
        self.assertEqual('Cluster1', cluster.name)
        self.assertEqual(True, cluster._parentless)
        self.assertEqual([atom1, atom2], cluster._atoms)
        self.assertEqual(None, cluster._atoms[0].parent)

    def test_pickling(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)

        pickled = pickle.dumps(cluster)
        unpickled = pickle.loads(pickled)

        self.assertEqual(cluster.parent, unpickled.parent)
        self.assertEqual(cluster.name, unpickled.name)
        self.assertEqual(cluster._parentless, unpickled._parentless)
        self.assertEqual(repr(cluster._atoms), repr(unpickled._atoms))

    def test_dunder_getitem(self):
        atom = ce.Atom()
        cluster = ce.AtomCluster('Cluster1', [atom, ce.Atom()], parentless=True)
        self.assertEqual(atom, cluster[0])

    def test_dunder_repr(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)
        self.assertEqual("MDANSE.MolecularDynamics.ChemicalEntity.AtomCluster(parent=None, name='Cluster1', "
                         "parentless=True, atoms=[MDANSE.Chemistry.ChemicalEntity.Atom(parent=None, name='H', "
                         "symbol='H', bonds=[], groups=[], ghost=False, index=None), MDANSE.Chemistry.ChemicalEntity."
                         "Atom(parent=None, name='H', symbol='H', bonds=[], groups=[], ghost=False, index=None)])",
                         repr(cluster))

    def test_dunder_str(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)
        self.assertEqual('AtomCluster consisting of 2 atoms', str(cluster))

    def test_atom_list(self):
        atom = ce.Atom()
        ghost = ce.Atom(ghost=True)
        cluster = ce.AtomCluster('Cluster1', [atom, ghost], parentless=True)
        self.assertEqual([atom], cluster.atom_list)

    def test_copy_parentful(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=False)
        copy = cluster.copy()
        self.assertEqual(repr(cluster), repr(copy))

    def test_copy_parentless(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)
        copy = cluster.copy()
        self.assertEqual(repr(cluster), repr(copy))

    def test_number_of_atoms(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom(ghost=True)], parentless=True)
        self.assertEqual(1, cluster.number_of_atoms)
        self.assertEqual(2, cluster.total_number_of_atoms)

    def test_reorder_atoms_exception(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(symbol='H'), ce.Atom(symbol='C')], parentless=True)
        with self.assertRaises(ce.InconsistentAtomNamesError):
            cluster.reorder_atoms(['H', 'H'])
        with self.assertRaises(ce.InconsistentAtomNamesError):
            cluster.reorder_atoms(['C', 'H', 'H'])

    def test_reorder_atoms_valid(self):
        h = ce.Atom(symbol='H')
        c = ce.Atom(symbol='C')
        cluster = ce.AtomCluster('Cluster1', [h, c], parentless=True)
        cluster.reorder_atoms(['C', 'H'])

        self.assertEqual([c, h], cluster._atoms)

    def test_serialize_empty_dict(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)
        dictionary = {}
        result = cluster.serialize(dictionary)

        self.assertEqual(('atom_clusters', 0), result)
        self.assertDictEqual({'atom_clusters': ['H5AtomCluster(self._h5_file,h5_contents,[0, 1],name="Cluster1")'],
                              'atoms': ['H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)']},
                             dictionary)

    def test_serialize_nonempty_dict(self):
        cluster = ce.AtomCluster('Cluster1', [ce.Atom(), ce.Atom()], parentless=True)
        dictionary = {'atom_clusters': ['', '', ''], 'atoms': ['', '', '']}
        result = cluster.serialize(dictionary)

        self.assertEqual(('atom_clusters', 3), result)
        self.assertDictEqual({'atom_clusters': ['', '', '',
                                                'H5AtomCluster(self._h5_file,h5_contents,[3, 4],name="Cluster1")'],
                              'atoms': ['', '', '',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)']},
                             dictionary)


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

    def test_dunder_str(self):
        self.assertEqual('Molecule of water (database code "WAT")', str(self.molecule))

    def test_atom_list(self):
        self.assertEqual(3, len(self.molecule.atom_list))
        self.compare_atoms(self.molecule.atom_list, self.molecule)

    def test_copy(self):
        copy = self.molecule.copy()
        self.compare_two_molecules(copy)

    def test_number_of_atoms(self):
        self.assertEqual(3, self.molecule.number_of_atoms)

    def test_total_number_of_atoms(self):
        self.assertEqual(3, self.molecule.total_number_of_atoms)

    def test_reorder_atoms_invalid_input(self):
        with self.assertRaises(ce.InconsistentAtomNamesError):
            self.molecule.reorder_atoms(['O', 'H', 'H'])

    def test_reorder_atoms_valid_input(self):
        self.molecule.reorder_atoms(['HW1', 'HW2', 'OW'])
        self.assertEqual('HW1', self.molecule.atom_list[0].name)
        self.assertEqual('HW2', self.molecule.atom_list[1].name)
        self.assertEqual('OW', self.molecule.atom_list[2].name)

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

    def test_set_atoms_variant(self):
        residue = ce.Residue('GLY', 'glycine', 'CT1')
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C', 'OXT'])
        selected_variant = RESIDUES_DATABASE['CT1']
        selected_variant['atoms']['OXT']['bonds'] = [residue._atoms['C']]

        self.maxDiff = None
        self.assertEqual('glycine', residue.name)
        self.assertEqual(None, residue.parent)
        self.assertEqual('GLY', residue.code)
        self.assertEqual('CT1', residue._variant)
        self.assertDictEqual(selected_variant, residue._selected_variant)

        self.compare_atoms(residue._atoms, residue)

        atom = residue._atoms['OXT']
        self.assertEqual('O', atom.symbol)
        self.assertEqual('OXT', atom.name)
        self.assertEqual(1, len(atom.bonds))
        self.assertEqual(residue._atoms['C'], atom.bonds[0])
        self.assertEqual(['backbone'], atom._groups)
        self.assertEqual(False, atom.ghost)
        self.assertEqual(None, atom.index)
        self.assertEqual(residue, atom.parent)

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

    def test_dunder_repr(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        self.assertEqual("MDANSE.MolecularDynamics.ChemicalEntity.Residue(parent=None, name='glycine', code='GLY', "
                         "variant=None, selected_variant=None, atoms=OrderedDict([('H', MDANSE.Chemistry.ChemicalEntity"
                         ".Atom(parent=MDANSE.Chemistry.ChemicalEntity.Residue(glycine), name='H', symbol='H', bonds="
                         "[Atom(N)], groups=['backbone', 'peptide'], ghost=False, index=None, alternatives=['HN'])), "
                         "('HA3', MDANSE.Chemistry.ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity.Residue"
                         "(glycine), name='HA3', symbol='H', bonds=[Atom(CA)], groups=['sidechain'], ghost=False, "
                         "index=None, alternatives=['HA1'])), ('O', MDANSE.Chemistry.ChemicalEntity.Atom(parent=MDANSE"
                         ".Chemistry.ChemicalEntity.Residue(glycine), name='O', symbol='O', bonds=[Atom(C)], groups="
                         "['backbone', 'peptide'], ghost=False, index=None, alternatives=['OT1'])), ('N', MDANSE."
                         "Chemistry.ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity.Residue(glycine), name="
                         "'N', symbol='N', bonds=[Atom(CA), Atom(H), Atom(-R)], groups=['backbone', 'peptide'], ghost="
                         "False, index=None, alternatives=[])), ('CA', MDANSE.Chemistry.ChemicalEntity.Atom(parent="
                         "MDANSE.Chemistry.ChemicalEntity.Residue(glycine), name='CA', symbol='C', bonds=[Atom(C), "
                         "Atom(HA2), Atom(HA3), Atom(N)], groups=['backbone'], ghost=False, index=None, alternatives="
                         "[])), ('HA2', MDANSE.Chemistry.ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity."
                         "Residue(glycine), name='HA2', symbol='H', bonds=[Atom(CA)], groups=['backbone'], ghost=False,"
                         " index=None, alternatives=['HA'])), ('C', MDANSE.Chemistry.ChemicalEntity.Atom(parent=MDANSE"
                         ".Chemistry.ChemicalEntity.Residue(glycine), name='C', symbol='C', bonds=[Atom(CA), Atom(O), "
                         "Atom(+R)], groups=['backbone', 'peptide'], ghost=False, index=None, alternatives=[]))]))",
                         repr(residue))

    def test_dunder_str(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        self.assertEqual('Amino acid Residue glycine (database code "GLY")', str(residue))

    def test_atom_list(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        self.compare_atoms(residue.atom_list, residue)

    def test_number_of_atoms(self):
        residue = ce.Residue('GLY', 'glycine', None)
        residue.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C'])
        self.assertEqual(7, residue.number_of_atoms)
        self.assertEqual(7, residue.total_number_of_atoms)

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

    def test_dunder_repr(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])

        self.assertEqual('MDANSE.MolecularDynamics.ChemicalEntity.Nucleotide(parent=None, name=\'5T1\', resname=\'5T1\''
                         ', code=\'5T1\', variant=None, selected_variant=None, atoms=OrderedDict([("HO5\'", MDANSE.'
                         'Chemistry.ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity.Nucleotide(5T1), name='
                         '"HO5\'", symbol=\'H\', bonds=[Atom(O5\')], groups=[], ghost=False, index=None, replaces='
                         '[\'OP1\', \'OP2\', \'P\'], o5prime_connected=True, alternatives=[]))]))',
                         repr(nucleotide))

    def test_dunder_str(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        self.assertEqual('Nucleotide 5T1 (database code "5T1")', str(nucleotide))

    def test_copy(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        copy = nucleotide.copy()

        self.compare_base_residues(copy, False)
        self.compare_atoms_in_5t1(copy._atoms, copy)

    def test_atom_list(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        self.compare_atoms_in_5t1(nucleotide.atom_list, nucleotide)

    def test_number_of_atoms(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])
        self.assertEqual(1, nucleotide.number_of_atoms)
        self.assertEqual(1, nucleotide.total_number_of_atoms)

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


class TestNucleotideChain(unittest.TestCase):
    def setUp(self):
        self.chain = ce.NucleotideChain('name')

    def test_instantiation(self):
        self.assertEqual('name', self.chain.name)
        self.assertEqual(None, self.chain.parent)
        self.assertEqual([], self.chain._nucleotides)

    def test_set_nucleotides(self):
        n1, n2 = self.prepare_nucleotides()

        self.chain.set_nucleotides([n1, n2])

        self.assertEqual(2, len(self.chain._nucleotides))
        self.assertEqual(self.chain, self.chain._nucleotides[0].parent)
        self.assertEqual(self.chain, self.chain._nucleotides[1].parent)

        self.assertEqual([n1, n2], self.chain._nucleotides)
        self.assertEqual(n2['P'], n1['O3\''].bonds[1])
        self.assertEqual(n1['O3\''], n2['P'].bonds[3])

    @staticmethod
    def prepare_nucleotides():
        names5 = ['C3\'', 'C1\'', 'C5\'', 'H2\'', 'H5\'', 'H3\'', 'O4\'', 'C8', 'C2', 'H1\'', 'C6', 'C5', 'C4',
                  'H5\'\'', 'HO2\'', 'N9', 'C4\'', 'C2\'', 'O2\'', 'N1', 'N3', 'N6', 'N7', 'H4\'', 'H8', 'H2', 'O5\'',
                  'H61', 'H62', 'O3\'', 'HO5\'']
        n1 = ce.Nucleotide('A', 'adenine', '5T1')
        n1.set_atoms(names5)

        names3 = ['C3\'', 'C1\'', 'C5\'', 'H2\'', 'H5\'', 'H3\'', 'O4\'', 'C8', 'C2', 'H1\'', 'C6', 'C5', 'C4',
                  'H5\'\'', 'HO2\'', 'N9', 'C4\'', 'C2\'', 'O2\'', 'N1', 'N3', 'N6', 'N7', 'H4\'', 'H8', 'H2', 'O5\'',
                  'H61', 'H62', 'O3\'', 'HO3\'', 'OP1', 'OP2', 'P']
        n2 = ce.Nucleotide('A', 'adenine', '3T1')
        n2.set_atoms(names3)

        return n1, n2

    def test_set_nucleotides_no_atoms_on_5prime_oxygen(self):
        n1, n2 = self.prepare_nucleotides()

        with self.assertRaises(ce.InvalidNucleotideChainError) as e:
            self.chain.set_nucleotides([n2, n1])
        self.assertEqual('The first nucleotide in the chain must contain an atom that is connected to the 5\' terminal'
                         ' oxygen (O5\').', str(e.exception)[:105])

    def test_set_nucleotides_first_no_5prime_oxygen(self):
        nucleotide = ce.Nucleotide('5T1', '5T1', None)
        nucleotide.set_atoms(['HO5\''])

        with self.assertRaises(ce.InvalidNucleotideChainError) as e:
            self.chain.set_nucleotides([nucleotide, nucleotide])
        self.assertEqual('The first nucleotide in the chain must contain 5\' terminal oxygen atom (O5\').',
                         str(e.exception)[:77])

    def test_set_nucleotides_last_no_ho3prime(self):
        names5 = ['C3\'', 'C1\'', 'C5\'', 'H2\'', 'H5\'', 'H3\'', 'O4\'', 'C8', 'C2', 'H1\'', 'C6', 'C5', 'C4',
                  'H5\'\'', 'HO2\'', 'N9', 'C4\'', 'C2\'', 'O2\'', 'N1', 'N3', 'N6', 'N7', 'H4\'', 'H8', 'H2', 'O5\'',
                  'H61', 'H62', 'O3\'', 'HO5\'']
        n1 = ce.Nucleotide('A', 'adenine', '5T1')
        n1.set_atoms(names5)
        n2 = ce.Nucleotide('5T1', '5T1', None)

        with self.assertRaises(ce.InvalidNucleotideChainError) as e:
            self.chain.set_nucleotides([n1, n2])
        self.assertEqual('The last nucleotide in the chain must contain an atom that is connected to the 3\' terminal'
                         ' oxygen (O3\').', str(e.exception)[:104])

    def test_set_nucleotides_last_no_o3prime(self):
        names5 = ['C3\'', 'C1\'', 'C5\'', 'H2\'', 'H5\'', 'H3\'', 'O4\'', 'C8', 'C2', 'H1\'', 'C6', 'C5', 'C4',
                  'H5\'\'', 'HO2\'', 'N9', 'C4\'', 'C2\'', 'O2\'', 'N1', 'N3', 'N6', 'N7', 'H4\'', 'H8', 'H2', 'O5\'',
                  'H61', 'H62', 'O3\'', 'HO5\'']
        n1 = ce.Nucleotide('A', 'adenine', '5T1')
        n1.set_atoms(names5)
        n2 = ce.Nucleotide('3T1', '3T1', None)
        n2.set_atoms(['HO3\''])

        with self.assertRaises(ce.InvalidNucleotideChainError) as e:
            self.chain.set_nucleotides([n1, n2])
        self.assertEqual('The last nucleotide in the chain must contain 3\' terminal oxygen atom (O3\').',
                         str(e.exception)[:76])

    def test_dunder_getitem(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])

        self.assertEqual(n1, self.chain[0])
        self.assertEqual(n2, self.chain[1])

    def test_pickling(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])

        pickled = pickle.dumps(self.chain)
        unpickled = pickle.loads(pickled)

        self.assertEqual('name', unpickled.name)
        self.assertEqual(None, unpickled.parent)

        self.assertEqual(2, len(unpickled._nucleotides))
        self.assertEqual(unpickled[1]['P'], unpickled[0]['O3\''].bonds[1])
        self.assertEqual(unpickled[0]['O3\''], unpickled[1]['P'].bonds[3])

    def test_dunder_str(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])

        self.assertEqual('NucleotideChain of 2 nucleotides', str(self.chain))

    def test_dunder_repr(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])

        self.maxDiff = None
        self.assertEqual("MDANSE.MolecularDynamics.ChemicalEntity.NucleotideChain(parent=None, name='name', "
                         "nucleotides=[MDANSE.MolecularDynamics.ChemicalEntity.Nucleotide(parent=MDANSE.Chemistry."
                         "ChemicalEntity.NucleotideChain(name=name), name='adenine', resname='A', code='A', "
                         "variant='5T1', selected_variant={'is_3ter_terminus': False, 'atoms':",
                         repr(self.chain)[:320])

    def test_bases(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])

        self.assertEqual([n1['C8'], n1['C2'], n1['C6'], n1['C5'], n1['C4'], n1['N9'], n1['N1'], n1['N3'], n1['N6'],
                          n1['N7'], n1['H8'], n1['H2'], n1['H61'], n1['H62'], n2['C8'], n2['C2'], n2['C6'], n2['C5'],
                          n2['C4'], n2['N9'], n2['N1'], n2['N3'], n2['N6'], n2['N7'], n2['H8'], n2['H2'], n2['H61'],
                          n2['H62']], self.chain.bases)

    def test_copy(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])
        copy = self.chain.copy()

        self.assertEqual(repr(self.chain), repr(copy))

    def test_residues(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])

        self.assertEqual([n1, n2], self.chain.residues)

    def test_number_of_atoms(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])

        self.assertEqual(65, self.chain.number_of_atoms)
        self.assertEqual(65, self.chain.total_number_of_atoms)

    def test_serialize_empty_dict(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])
        dictionary = {}
        result = self.chain.serialize(dictionary)

        self.maxDiff = None
        self.assertEqual(('nucleotide_chains', 0), result)
        self.assertDictEqual({'nucleotides': ['H5Nucleotide(self._h5_file,h5_contents,[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, '
                                              '10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, '
                                              '28, 29, 30],code="A",name="adenine",variant=\'5T1\')',
                                              'H5Nucleotide(self._h5_file,h5_contents,[31, 32, 33, 34, 35, 36, 37, 38, '
                                              '39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, '
                                              '57, 58, 59, 60, 61, 62, 63, 64],code="A",name="adenine",'
                                              'variant=\'3T1\')'],
                              'atoms': [f'H5Atom(self._h5_file,h5_contents,symbol="{i}", name="{j}", ghost=False)'
                                        for i, j in zip(['C', 'C', 'C', 'H', 'H', 'H', 'O', 'C', 'C', 'H', 'C', 'C',
                                                         'C', 'H', 'H', 'N', 'C', 'C', 'O', 'N', 'N', 'N', 'N', 'H',
                                                         'H', 'H', 'O', 'H', 'H', 'O', 'H', 'C', 'C', 'C', 'H', 'H',
                                                         'H', 'O', 'C', 'C', 'H', 'C', 'C', 'C', 'H', 'H', 'N', 'C',
                                                         'C', 'O', 'N', 'N', 'N', 'N', 'H', 'H', 'H', 'O', 'H', 'H',
                                                         'O', 'H', 'O', 'O', 'P'],
                                                        ['C3\'', 'C1\'', 'C5\'', 'H2\'', 'H5\'', 'H3\'', 'O4\'', 'C8',
                                                         'C2', 'H1\'', 'C6', 'C5', 'C4', 'H5\'\'', 'HO2\'', 'N9',
                                                         'C4\'', 'C2\'', 'O2\'', 'N1', 'N3', 'N6', 'N7', 'H4\'', 'H8',
                                                         'H2', 'O5\'', 'H61', 'H62', 'O3\'', 'HO5\'', 'C3\'', 'C1\'',
                                                         'C5\'', 'H2\'', 'H5\'', 'H3\'', 'O4\'', 'C8', 'C2', 'H1\'',
                                                         'C6', 'C5', 'C4', 'H5\'\'', 'HO2\'', 'N9', 'C4\'', 'C2\'',
                                                         'O2\'', 'N1', 'N3', 'N6', 'N7', 'H4\'', 'H8', 'H2', 'O5\'',
                                                         'H61', 'H62', 'O3\'', 'HO3\'', 'OP1', 'OP2', 'P'])],
                              'nucleotide_chains': ['H5NucleotideChain(self._h5_file,h5_contents,"name",[0, 1])']},
                             dictionary)

    def test_serialize_nonempty_dict(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])
        dictionary = {'nucleotides': ['', '', ''], 'nucleotide_chains': ['']}
        result = self.chain.serialize(dictionary)

        self.assertEqual(('nucleotide_chains', 1), result)
        self.assertEqual(['', 'H5NucleotideChain(self._h5_file,h5_contents,"name",[3, 4])'],
                         dictionary['nucleotide_chains'])

    def test_sugars(self):
        n1, n2 = self.prepare_nucleotides()
        self.chain.set_nucleotides([n1, n2])

        self.assertEqual([n1["C3'"], n1["C1'"], n1["C5'"], n1["H2'"], n1["H5'"], n1["H3'"], n1["O4'"], n1["H1'"],
                          n1["H5''"], n1["HO2'"], n1["C4'"], n1["C2'"], n1["O2'"], n1["H4'"], n2["C3'"], n2["C1'"],
                          n2["C5'"], n2["H2'"], n2["H5'"], n2["H3'"], n2["O4'"], n2["H1'"], n2["H5''"], n2["HO2'"],
                          n2["C4'"], n2["C2'"], n2["O2'"], n2["H4'"]],
                         self.chain.sugars)


class TestPeptideChain(unittest.TestCase):
    def setUp(self):
        self.chain = ce.PeptideChain('name')

    def test_instantiation(self):
        self.assertEqual('name', self.chain.name)
        self.assertEqual(None, self.chain.parent)
        self.assertEqual([], self.chain._residues)

    def test_set_residues_valid(self):
        self.populate_chain()

        self.assertEqual(2, len(self.chain._residues))
        self.assertEqual(self.chain, self.chain._residues[0].parent)
        self.assertEqual(self.chain, self.chain._residues[1].parent)

        self.assertEqual(self.chain._residues[1]['N'], self.chain._residues[0]['C'].bonds[2])
        self.assertEqual(self.chain._residues[0]['C'], self.chain._residues[1]['N'].bonds[2])

    def populate_chain(self):
        r1 = ce.Residue('GLY', 'glycine1', 'NT1')
        r1.set_atoms(['HA3', 'O', 'N', 'CA', 'HA2', 'C', 'HT1', 'HT2', 'HT3'])

        r2 = ce.Residue('GLY', 'glycine2', 'CT1')
        r2.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C', 'OXT'])
        self.chain.set_residues([r1, r2])

        return r1, r2

    def test_set_residues_no_atoms_connected_to_terminal_nitrogen(self):
        r1 = ce.Residue('GLY', 'glycine1', None)
        r1.set_atoms(['HA3', 'O', 'N', 'CA', 'HA2', 'C', 'H'])

        r2 = ce.Residue('GLY', 'glycine2', 'CT1')
        r2.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C', 'OXT'])

        with self.assertRaises(ce.InvalidPeptideChainError) as e:
            self.chain.set_residues([r1, r2])

        self.assertEqual('The first residue in the chain must contain an atom that is connected to the terminal '
                         'nitrogen.', str(e.exception)[:95])

    def test_set_residues_no_terminal_nitrogen(self):
        r = ce.Residue('NT1', 'NT1', None)
        r.set_atoms(['HT1', 'HT2', 'HT3'])

        with self.assertRaises(ce.InvalidPeptideChainError) as e:
            self.chain.set_residues([r, r])

        self.assertEqual('The first residue in the chain must contain the terminal nitrogen atom. ',
                         str(e.exception)[:72])

    def test_set_residues_no_atoms_connected_to_terminal_carbon(self):
        r1 = ce.Residue('GLY', 'glycine1', 'NT1')
        r1.set_atoms(['HA3', 'O', 'N', 'CA', 'HA2', 'C', 'HT1', 'HT2', 'HT3'])

        with self.assertRaises(ce.InvalidPeptideChainError) as e:
            self.chain.set_residues([r1, r1])

        self.assertEqual('The last residue in the chain must contain an atom that is connected to the terminal carbon.',
                         str(e.exception)[:92])

    def test_set_residues_no_terminal_carbon(self):
        r1 = ce.Residue('GLY', 'glycine1', 'NT1')
        r1.set_atoms(['HA3', 'O', 'N', 'CA', 'HA2', 'C', 'HT1', 'HT2', 'HT3'])

        r2 = ce.Residue('CT1', 'CT1', 'CT1')
        r2.set_atoms(['OXT'])

        with self.assertRaises(ce.InvalidPeptideChainError) as e:
            self.chain.set_residues([r1, r2])

        self.assertEqual('The last residue in the chain must contain the terminal carbon atom. ',
                         str(e.exception)[:69])

    def test_dunder_getitem(self):
        r1, r2 = self.populate_chain()

        self.assertEqual(r1, self.chain[0])
        self.assertEqual(r2, self.chain[1])

    def test_pickling(self):
        self.populate_chain()

        pickled = pickle.dumps(self.chain)
        unpickled = pickle.loads(pickled)

        self.assertEqual('name', unpickled.name)
        self.assertEqual(None, unpickled.parent)
        self.assertEqual(2, len(unpickled._residues))

    def test_dunder_str(self):
        self.populate_chain()
        self.assertEqual('PeptideChain of 2 residues', str(self.chain))

    def test_dunder_repr(self):
        self.populate_chain()

        self.maxDiff = None
        self.assertEqual("MDANSE.MolecularDynamics.ChemicalEntity.PeptideChain(parent=None, name='name', "
                         "residues=[MDANSE.MolecularDynamics.ChemicalEntity.Residue(parent=MDANSE.Chemistry."
                         "ChemicalEntity.PeptideChain(name), name='glycine1', code='GLY', variant='NT1', "
                         "selected_variant={'is_n_terminus': True, ", repr(self.chain)[:281])

    def test_atom_list(self):
        r1, r2 = self.populate_chain()

        self.assertEqual([r1['HA3'], r1['O'], r1['N'], r1['CA'], r1['HA2'], r1['C'], r1['HT1'], r1['HT2'], r1['HT3'],
                          r2['H'], r2['HA3'], r2['O'], r2['N'], r2['CA'], r2['HA2'], r2['C'], r2['OXT']],
                         self.chain.atom_list)

    def test_backbone(self):
        r1, r2 = self.populate_chain()

        self.assertEqual([r1['O'], r1['N'], r1['CA'], r1['HA2'], r1['C'], r1['HT1'], r1['HT2'], r1['HT3'],
                          r2['H'], r2['O'], r2['N'], r2['CA'], r2['HA2'], r2['C'], r2['OXT']],
                         self.chain.backbone)

    def test_copy(self):
        self.populate_chain()
        copy = self.chain.copy()

        self.maxDiff = None
        self.assertEqual(repr(self.chain), repr(copy))

    def test_number_of_atoms(self):
        self.populate_chain()
        self.assertEqual(17, self.chain.number_of_atoms)
        self.assertEqual(17, self.chain.total_number_of_atoms)

    def test_peptide_chains(self):
        self.populate_chain()
        self.assertEqual([self.chain], self.chain.peptide_chains)

    def test_peptides(self):
        r1, r2 = self.populate_chain()
        self.assertEqual([r1['O'], r1['N'], r1['C'], r2['H'], r2['O'], r2['N'], r2['C']],
                         self.chain.peptides)

    def test_residues(self):
        r1, r2 = self.populate_chain()
        self.assertEqual([r1, r2], self.chain.residues)

    def test_serialize_empty_dict(self):
        self.populate_chain()
        dictionary = {}
        result = self.chain.serialize(dictionary)

        self.maxDiff = None
        self.assertEqual(('peptide_chains', 0), result)
        self.assertDictEqual({'residues': ['H5Residue(self._h5_file,h5_contents,[0, 1, 2, 3, 4, 5, 6, 7, 8],code="GLY",'
                                           'name="glycine1",variant=\'NT1\')',
                                           'H5Residue(self._h5_file,h5_contents,[9, 10, 11, 12, 13, 14, 15, 16],'
                                           'code="GLY",name="glycine2",variant=\'CT1\')'],
                              'atoms': ['H5Atom(self._h5_file,h5_contents,symbol="H", name="HA3", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="O", name="O", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="N", name="N", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="C", name="CA", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HA2", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="C", name="C", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HT1", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HT2", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HT3", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="H", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HA3", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="O", name="O", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="N", name="N", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="C", name="CA", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="H", name="HA2", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="C", name="C", ghost=False)',
                                        'H5Atom(self._h5_file,h5_contents,symbol="O", name="OXT", ghost=False)'],
                              'peptide_chains': ['H5PeptideChain(self._h5_file,h5_contents,"name",[0, 1])']},
                             dictionary)

    def test_serialize_nonempty_dict(self):
        self.populate_chain()
        dictionary = {'residues': ['', '', ''], 'peptide_chains': ['', '', '']}
        result = self.chain.serialize(dictionary)

        self.assertEqual(('peptide_chains', 3), result)
        self.assertEqual(['', '', '', 'H5PeptideChain(self._h5_file,h5_contents,"name",[3, 4])'],
                         dictionary['peptide_chains'])

    def test_sidechains(self):
        r1, r2 = self.populate_chain()
        self.assertEqual([r1['HA3'], r2['HA3']], self.chain.sidechains)


class TestProtein(unittest.TestCase):
    def setUp(self):
        self.protein = ce.Protein('name')

    def test_instantiation(self):
        self.assertEqual('name', self.protein.name)
        self.assertEqual(None, self.protein.parent)
        self.assertEqual([], self.protein._peptide_chains)

    def test_set_peptide_chains(self):
        chain = self.populate_protein()

        self.assertEqual([chain], self.protein._peptide_chains)
        self.assertEqual(self.protein, self.protein._peptide_chains[0].parent)

    def populate_protein(self):
        r1 = ce.Residue('GLY', 'glycine1', 'NT1')
        r1.set_atoms(['HA3', 'O', 'N', 'CA', 'HA2', 'C', 'HT1', 'HT2', 'HT3'])

        r2 = ce.Residue('GLY', 'glycine2', 'CT1')
        r2.set_atoms(['H', 'HA3', 'O', 'N', 'CA', 'HA2', 'C', 'OXT'])

        chain = ce.PeptideChain('name')
        chain.set_residues([r1, r2])
        self.protein.set_peptide_chains([chain])

        return chain

    def test_pickling(self):
        chain = self.populate_protein()

        pickled = pickle.dumps(self.protein)
        unpickled = pickle.loads(pickled)

        self.maxDiff = None
        self.assertEqual('name', unpickled.name)
        self.assertEqual(None, unpickled.parent)
        self.assertEqual(1, len(unpickled._peptide_chains))
        self.assertEqual(repr(chain), repr(unpickled._peptide_chains[0]))

    def test_dunder_getitem(self):
        chain = self.populate_protein()
        self.assertEqual(chain, self.protein[0])

    def test_dunder_repr(self):
        self.populate_protein()
        self.assertEqual("MDANSE.MolecularDynamics.ChemicalEntity.Protein(parent=None, name='name', peptide_chains="
                         "[MDANSE.MolecularDynamics.ChemicalEntity.PeptideChain(parent=MDANSE.Chemistry.ChemicalEntity."
                         "Protein(name=name), name='name'", repr(self.protein)[:213])

    def test_dunder_str(self):
        self.populate_protein()
        self.assertEqual('Protein name consisting of 1 peptide chains', str(self.protein))

    def test_atom_list(self):
        chain = self.populate_protein()

        self.assertEqual([chain[0]['HA3'], chain[0]['O'], chain[0]['N'], chain[0]['CA'], chain[0]['HA2'], chain[0]['C'],
                          chain[0]['HT1'], chain[0]['HT2'], chain[0]['HT3'], chain[1]['H'], chain[1]['HA3'],
                          chain[1]['O'], chain[1]['N'], chain[1]['CA'], chain[1]['HA2'], chain[1]['C'],
                          chain[1]['OXT']], self.protein.atom_list)

    def test_backbone(self):
        chain = self.populate_protein()
        self.assertEqual([chain[0]['O'], chain[0]['N'], chain[0]['CA'], chain[0]['HA2'], chain[0]['C'], chain[0]['HT1'],
                          chain[0]['HT2'], chain[0]['HT3'], chain[1]['H'], chain[1]['O'], chain[1]['N'], chain[1]['CA'],
                          chain[1]['HA2'], chain[1]['C'], chain[1]['OXT']], self.protein.backbone)

    def test_copy(self):
        chain = self.populate_protein()
        copy = self.protein.copy()

        self.maxDiff = None
        self.assertEqual('name', copy.name)
        self.assertEqual(None, copy.parent)
        self.assertEqual(1, len(copy._peptide_chains))
        self.assertEqual(repr(chain), repr(copy._peptide_chains[0]))

    def test_number_of_atoms(self):
        self.populate_protein()

        self.assertEqual(17, self.protein.number_of_atoms)
        self.assertEqual(17, self.protein.total_number_of_atoms)

    def test_peptide_chains(self):
        chain = self.populate_protein()
        self.assertEqual([chain], self.protein.peptide_chains)

    def test_peptides(self):
        chain = self.populate_protein()
        self.assertEqual([chain[0]['O'], chain[0]['N'], chain[0]['C'], chain[1]['H'], chain[1]['O'], chain[1]['N'],
                          chain[1]['C']], self.protein.peptides)

    def test_residues(self):
        chain = self.populate_protein()
        self.assertEqual(chain.residues, self.protein.residues)

    def test_serialize_empty_dict(self):
        self.populate_protein()
        dictionary = {}

        result = self.protein.serialize(dictionary)

        self.assertEqual(('proteins', 0), result)
        self.assertEqual(['H5Protein(self._h5_file,h5_contents,"name",[0])'], dictionary['proteins'])
        self.assertEqual(['H5PeptideChain(self._h5_file,h5_contents,"name",[0, 1])'], dictionary['peptide_chains'])

    def test_serialize_nonempty_dict(self):
        self.populate_protein()
        dictionary = {'proteins': ['', '', ''], 'peptide_chains': ['', '', '']}
        result = self.protein.serialize(dictionary)

        self.assertEqual(('proteins', 3), result)
        self.assertEqual(['', '', '', 'H5Protein(self._h5_file,h5_contents,"name",[3])'], dictionary['proteins'])

    def test_sidechains(self):
        chain = self.populate_protein()
        self.assertEqual([chain[0]['HA3'], chain[1]['HA3']], self.protein.sidechains)


class TestTranslateAtomNames(unittest.TestCase):
    def test_valid(self):
        result = ce.translate_atom_names(MOLECULES_DATABASE, 'WAT', ['O', 'HW2', 'H1'])
        self.assertEqual(['OW', 'HW2', 'HW1'], result)

    def test_subset_of_all_atoms(self):
        result = ce.translate_atom_names(MOLECULES_DATABASE, 'WAT', ['O', 'HW2'])
        self.assertEqual(['OW', 'HW2'], result)

    def test_multiple_of_one_atom(self):
        result = ce.translate_atom_names(MOLECULES_DATABASE, 'WAT', ['O', 'HW2', 'HW2', 'HW2', 'HW2'])
        self.assertEqual(['OW', 'HW2', 'HW2', 'HW2', 'HW2'], result)

    def test_invalid_molname(self):
        with self.assertRaises(ce.UnknownMoleculeError):
            ce.translate_atom_names(MOLECULES_DATABASE, '00000', ['OW', 'HW1', 'HW2'])

    def test_invalid_atom(self):
        with self.assertRaises(ce.UnknownAtomError):
            ce.translate_atom_names(MOLECULES_DATABASE, 'WAT', [''])


class TestChemicalSystem(unittest.TestCase):
    def setUp(self):
        self.system = ce.ChemicalSystem('name')

    def test_instantiation(self):
        self.assertEqual('name', self.system.name)
        self.assertEqual(None, self.system.parent)
        self.assertEqual([], self.system.chemical_entities)
        self.assertEqual(None, self.system._configuration)
        self.assertEqual(0, self.system._number_of_atoms)
        self.assertEqual(0, self.system._total_number_of_atoms)
        self.assertEqual(None, self.system._atoms)

    def test_add_chemical_entity_valid(self):
        cluster = ce.AtomCluster('name', [ce.Atom(ghost=False), ce.Atom(ghost=True)])
        self.system.add_chemical_entity(cluster)

        self.assertEqual(1, self.system._number_of_atoms)
        self.assertEqual(2, self.system._total_number_of_atoms)
        self.assertEqual(self.system, cluster.parent)
        self.assertEqual([cluster], self.system.chemical_entities)
        self.assertEqual(None, self.system._configuration)
        self.assertEqual(None, self.system._atoms)

    def test_add_chemical_entity_invalid_input(self):
        with self.assertRaises(ce.InvalidChemicalEntityError):
            self.system.add_chemical_entity([])

    def test_pickling(self):
        molecule = ce.Molecule('WAT', 'name')
        self.system.add_chemical_entity(molecule)

        pickled = pickle.dumps(self.system)
        unpickled = pickle.loads(pickled)

        self.assertEqual('name', unpickled.name)
        self.assertEqual(None, unpickled.parent)
        self.assertEqual(3, unpickled._number_of_atoms)
        self.assertEqual(3, unpickled._total_number_of_atoms)
        self.assertEqual(repr(molecule), repr(unpickled.chemical_entities[0]))
        self.assertEqual(None, unpickled._configuration)
        self.assertEqual(None, unpickled._atoms)

    def test_dunder_repr(self):
        molecule = ce.Molecule('WAT', 'name')
        self.system.add_chemical_entity(molecule)

        self.maxDiff = None
        self.assertEqual("MDANSE.MolecularDynamics.ChemicalEntity.ChemicalSystem(parent=None, name='name', "
                         "chemical_entities=[MDANSE.MolecularDynamics.ChemicalEntity.Molecule(parent=MDANSE.Chemistry."
                         "ChemicalEntity.ChemicalSystem(name), name='name', atoms=OrderedDict([('OW', MDANSE.Chemistry."
                         "ChemicalEntity.Atom(parent=MDANSE.Chemistry.ChemicalEntity.Molecule(name), name='OW', "
                         "symbol='O', bonds=[Atom(HW1), Atom(HW2)], groups=[], ghost=False, index=0, alternatives="
                         "['O', 'OH2'])), ('HW2', MDANSE.Chemistry.ChemicalEntity.Atom(parent=MDANSE.Chemistry."
                         "ChemicalEntity.Molecule(name), name='HW2', symbol='H', bonds=[Atom(OW)], groups=[], "
                         "ghost=False, index=1, alternatives=['H2'])), ('HW1', MDANSE.Chemistry.ChemicalEntity."
                         "Atom(parent=MDANSE.Chemistry.ChemicalEntity.Molecule(name), name='HW1', symbol='H', bonds="
                         "[Atom(OW)], groups=[], ghost=False, index=2, alternatives=['H1']))]), code='WAT')], "
                         "configuration=None, number_of_atoms=3, total_number_of_atoms=3, atoms=None)",
                         repr(self.system))

    def test_dunder_str(self):
        atom1 = ce.Atom(ghost=False)
        atom2 = ce.Atom(ghost=False)
        cluster = ce.AtomCluster('name', [atom1, atom2])
        self.system.add_chemical_entity(cluster)
        self.assertEqual('ChemicalSystem name consisting of 1 chemical entities', str(self.system))

    def test_atom_list(self):
        atom1 = ce.Atom(ghost=False)
        atom2 = ce.Atom(ghost=False)
        cluster = ce.AtomCluster('name', [atom1, atom2])
        self.system.add_chemical_entity(cluster)

        self.assertEqual([atom1, atom2], self.system.atom_list)

    def test_atoms(self):
        atom1 = ce.Atom(ghost=False)
        atom2 = ce.Atom(ghost=False)
        cluster = ce.AtomCluster('name', [atom1, atom2])
        self.system.add_chemical_entity(cluster)

        atom1._index = 1
        atom2._index = 0

        self.maxDiff = None
        self.assertEqual([atom2, atom1], self.system.atoms)

    def test_configuration_setter_valid(self):
        config = DummyConfiguration(self.system)
        self.system.configuration = config

        self.assertEqual(config, self.system.configuration)

    def test_configuration_setter_invalid(self):
        other_system = ce.ChemicalSystem('name')
        config = DummyConfiguration(self.system)

        with self.assertRaises(ce.InconsistentChemicalSystemError):
            other_system.configuration = config

    def test_copy(self):
        molecule = ce.Molecule('WAT', 'name')
        self.system.add_chemical_entity(molecule)
        copy = self.system.copy()

        self.assertEqual('name', copy.name)
        self.assertEqual(None, copy.parent)
        self.assertEqual(repr(molecule), repr(copy.chemical_entities[0]))
        self.assertEqual(None, copy._configuration)
        self.assertEqual(3, copy._number_of_atoms)
        self.assertEqual(3, copy._total_number_of_atoms)
        self.assertEqual(None, copy._atoms)

    def test_load_valid(self):
        file = StubHDFFile()
        file['/chemical_system'] = StubHDFFile()
        file['/chemical_system'].attrs['name'] = 'new'

        file['/chemical_system/contents'] = [('atoms'.encode(encoding = 'UTF-8',errors = 'strict'), 0)]
        file['/chemical_system']['atoms'] = ['H5Atom(self._h5_file,h5_contents,symbol="H", name="H1", ghost=False)']
        self.system.load(file)

        self.assertEqual(None, self.system._h5_file)
        self.assertEqual('new', self.system.name)
        self.assertEqual(None, self.system.parent)
        self.assertEqual(repr(ce.Atom(name="H1", parent=self.system, index=0)), repr(self.system.chemical_entities[0]))
        self.assertEqual(None, self.system._configuration)
        self.assertEqual(1, self.system._number_of_atoms)
        self.assertEqual(1, self.system._total_number_of_atoms)
        self.assertEqual(None, self.system._atoms)

    def test_load_corrupt_file_unexpected_eval_input(self):
        file = StubHDFFile()
        file['/chemical_system'] = StubHDFFile()
        file['/chemical_system'].attrs['name'] = 'new'

        file['/chemical_system/contents'] = [('atoms'.encode(encoding='UTF-8', errors='strict'), 0)]
        file['/chemical_system']['atoms'] = ['Atom(symbol="H", name="H1", ghost=False)']

        with self.assertRaises(ce.CorruptedFileError):
            self.system.load(file)

    def test_serialize(self):
        molecule = ce.Molecule('WAT', 'water')
        self.system.add_chemical_entity(molecule)
        file = StubHDFFile()
        self.system.serialize(file)

        self.assertEqual('name', file['/chemical_system'].attrs['name'])
        self.assertEqual(['H5Molecule(self._h5_file,h5_contents,[0, 1, 2],code="WAT",name="water")'],
                         file['/chemical_system']['molecules'])
        self.assertEqual(['H5Atom(self._h5_file,h5_contents,symbol="O", name="OW", ghost=False)',
                          'H5Atom(self._h5_file,h5_contents,symbol="H", name="HW2", ghost=False)',
                          'H5Atom(self._h5_file,h5_contents,symbol="H", name="HW1", ghost=False)'],
                         file['/chemical_system']['atoms'])
        self.assertEqual([('molecules', '0')], file['/chemical_system']['contents'])


class DummyConfiguration:
    def __init__(self, system: ce.ChemicalSystem):
        self.chemical_system = system


class StubHDFFile(dict):
    attrs = {}

    def close(self):
        pass

    def create_group(self, value: str):
        self[value] = StubHDFFile()
        return self[value]

    def create_dataset(self, name: str, data, dtype):
        self[name] = data
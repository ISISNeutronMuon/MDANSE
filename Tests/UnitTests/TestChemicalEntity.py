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

import pickle
import unittest

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


# class TestAtomGroup(unittest.TestCase):
#     def test_valid_instantiation(self):
#         group = ce.AtomGroup()

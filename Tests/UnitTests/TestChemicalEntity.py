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
        #user getitem
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
        atom = ce.Atom(name='Hydrogen')
        self.assertEqual(repr(atom), "MDANSE.Chemistry.ChemicalEntity.Atom(parent=None, name='Hydrogen', "
                                     "symbol='H', bonds=[], groups=[], ghost=False, index=None)")

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


class TestAtomGroup(unittest.TestCase):
    def test_empty_instantiation(self):



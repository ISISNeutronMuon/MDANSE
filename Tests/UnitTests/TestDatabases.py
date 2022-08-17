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

"""
Created on May 29, 2015

@author: Eric C. Pellegrini
"""

import json
import os
import unittest
from unittest.mock import patch, mock_open, ANY

from MDANSE.Chemistry import ATOMS_DATABASE, MOLECULES_DATABASE, RESIDUES_DATABASE, NUCLEOTIDES_DATABASE
import MDANSE.Chemistry.Databases as Databases
from MDANSE.Chemistry.Databases import AtomsDatabaseError, MoleculesDatabaseError, ResiduesDatabaseError, \
    NucleotidesDatabaseError


class TestAtomsDatabase(unittest.TestCase):
    def setUp(self):
        self.data = {'H': {"family": "non metal", "nucleon": 0, "alternatives": [],
                           "electronegativity": 2.2, "symbol": "H"},
                     'H2': {"family": "non metal", "nucleon": 2, "alternatives": [],
                            "electronegativity": 2.2, "symbol": "H", },
                     'O': {"family": "non metal", "nucleon": 0, "alternatives": [],
                           "electronegativity": 3.44, "symbol": "O"},
                     'Fe': {"family": "transition metal", "nucleon": 0, "alternatives": [],
                            "electronegativity": 1.83, "symbol": "Fe"}}
        self.properties = {"family": "str", "nucleon": "int", "alternatives": "list",
                           "electronegativity": "float", "symbol": "str"}
        self.overwrite_database()

    @classmethod
    def tearDownClass(cls):
        ATOMS_DATABASE._load()

    def overwrite_database(self):
        ATOMS_DATABASE._data = self.data
        ATOMS_DATABASE._properties = self.properties

    def test__load_default_database(self):
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps({'properties': {'family': 'str'},
                                                                                  'atoms': {'H': {
                                                                                      'family': 'non-metal'}}})) as m:
            ATOMS_DATABASE._load()
            m.assert_called_with(os.path.join(os.path.dirname(Databases.__file__), 'atoms.json'), 'r')
            self.assertDictEqual({'family': 'str'}, ATOMS_DATABASE._properties)
            self.assertDictEqual({'H': {'family': 'non-metal'}}, ATOMS_DATABASE._data)

    def test__load_user_database(self):
        with patch('builtins.open', new_callable=mock_open,
                   read_data=json.dumps({'properties': {'family': 'str'},
                                         'atoms': {'H': {'family': 'non-metal'}}})) as m:
            with patch('os.path.exists', spec=True):
                ATOMS_DATABASE._load('user.json')
                m.assert_called_with('user.json', 'r')
                self.assertDictEqual({'family': 'str'}, ATOMS_DATABASE._properties)
                self.assertDictEqual({'H': {'family': 'non-metal'}}, ATOMS_DATABASE._data)

    def test___contains__(self):
        self.assertFalse("fhsdjfsd" in ATOMS_DATABASE)
        self.assertTrue("H" in ATOMS_DATABASE)

    def test___getitem__(self):
        self.assertDictEqual({"family": "non metal", "nucleon": 0, "alternatives": [],
                              "electronegativity": 2.2, "symbol": "H"},
                             ATOMS_DATABASE['H'])
        with self.assertRaises(AtomsDatabaseError):
            a = ATOMS_DATABASE['INVALID']

    def test___iter__(self):
        generator = iter(ATOMS_DATABASE)
        self.assertDictEqual({"family": "non metal", "nucleon": 0, "alternatives": [],
                              "electronegativity": 2.2, "symbol": "H"}, next(generator))

    def test_add_atom_existing_atom(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.add_atom("H")

    def test_add_atom_valid(self):
        with patch('json.dump') as m, patch('MDANSE.Chemistry.Databases.AtomsDatabase.save') as n:
            ATOMS_DATABASE.add_atom("new_atom")
            self.assertDictEqual({}, ATOMS_DATABASE['new_atom'])
            assert not m.called
            assert not n.called

    def test_add_property_already_registered(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.add_property('symbol', 'str')

    def test_add_property_invalid_type(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.add_property('new_property', 'xxxx')

    def test_add_property_valid(self):
        ATOMS_DATABASE.add_property('new_property', 'str')
        self.assertEqual('str', ATOMS_DATABASE._properties['new_property'])
        for at in ATOMS_DATABASE._data.values():
            self.assertEqual('', at['new_property'])

    def test_atoms(self):
        self.assertEqual(['Fe', 'H', 'H2', 'O'], ATOMS_DATABASE.atoms)

    def test_get_isotopes_valid(self):
        self.assertEqual(['H', 'H2'], ATOMS_DATABASE.get_isotopes('H'))

    def test_get_isotopes_unknown_atom(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.get_isotopes('INVALID')

    def test_properties(self):
        self.assertEqual(sorted(list(self.properties.keys())), ATOMS_DATABASE.properties)

    def test_get_property_valid(self):
        self.assertEqual({'Fe': 'Fe', 'H': 'H', 'H2': 'H', 'O': 'O'}, ATOMS_DATABASE.get_property('symbol'))

    def test_get_property_invalid_property(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.get_property('INVALID')

    def test_get_value_valid(self):
        self.assertEqual('H', ATOMS_DATABASE.get_value('H', 'symbol'))

    def test_get_value_unknown_atom(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.get_value('INVALID', 'symbol')

    def test_get_value_unknown_property(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.get_value('H', 'INVALID')

    def test_get_value_for_multiple_atoms_valid(self):
        self.assertEqual([0, 0, 2, 0, 0, 0, 0],
                         ATOMS_DATABASE.get_values_for_multiple_atoms(['H', 'H', 'H2', 'O', 'O', 'O', 'H'], 'nucleon'))

    def test_get_value_for_multiple_atoms_unknown_atom(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.get_values_for_multiple_atoms(['H', 'O', 'O', 'INVALID'], 'nucleon')

    def test_get_value_for_multiple_atoms_unknown_property(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.get_values_for_multiple_atoms(['H', 'H', 'H'], 'INVALID')

    def test_set_value_valid(self):
        ATOMS_DATABASE.set_value('H', 'symbol', 'C')
        self.assertEqual('C', ATOMS_DATABASE['H']['symbol'])

    def test_set_value_unknown_atom(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.set_value('INVALID', 'symbol', 'H')

    def test_set_value_unknown_property(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.set_value('H', 'INVALID', 'H')

    def test_set_value_invalid_value_type(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.set_value('H', 'nucleon', 'H')

    def test_has_atom(self):
        self.assertTrue(ATOMS_DATABASE.has_atom('H'))
        self.assertFalse(ATOMS_DATABASE.has_atom('INVALID'))

    def test_has_property(self):
        self.assertTrue(ATOMS_DATABASE.has_property('symbol'))
        self.assertFalse(ATOMS_DATABASE.has_property('INVALID'))

    def test_info(self):
        self.assertEqual('----------------------------------------------------------------------\n'
                         '                                  H                                   \n'
                         ' property                                                         value\n'
                         '----------------------------------------------------------------------\n'
                         ' alternatives                                                        []\n'
                         ' electronegativity                                                  2.2\n'
                         ' family                                                       non metal\n'
                         ' nucleon                                                              0\n'
                         ' symbol                                                               H\n'
                         '----------------------------------------------------------------------',
                         ATOMS_DATABASE.info('H'))

    def test_items(self):

        for (expected_atom, expected_data), (atom, data) in zip(self.data.items(), ATOMS_DATABASE.items()):
            self.assertEqual(expected_atom, atom)
            self.assertDictEqual(expected_data, data)

    def test_match_numeric_property_valid(self):
        self.assertEqual(['H', 'H2'], ATOMS_DATABASE.match_numeric_property('electronegativity', 2.2))
        self.assertEqual(['H', 'H2', 'Fe'], ATOMS_DATABASE.match_numeric_property('electronegativity', 2, 0.3))

    def test_match_numeric_property_non_numeric_property(self):
        with self.assertRaises(AtomsDatabaseError) as e:
            ATOMS_DATABASE.match_numeric_property('symbol', 0)
        self.assertEqual('The provided property must be numeric, but "symbol" has type str.', str(e.exception)[1:-1])

    def test_match_numeric_property_unknown_property(self):
        with self.assertRaises(AtomsDatabaseError) as e:
            ATOMS_DATABASE.match_numeric_property('INVALID', 0)
        self.assertEqual('The property INVALID is not registered in the database', str(e.exception)[1:-1])

    def test_match_numeric_property_non_numeric_value(self):
        with self.assertRaises(AtomsDatabaseError) as e:
            ATOMS_DATABASE.match_numeric_property('electronegativity', [])
        self.assertEqual('The provided value must be a numeric type, but [] was provided, which is of type '
                         '<class \'list\'>. If you are sure that [] is numeric, then your database might be corrupt.',
                         str(e.exception)[1:-1])

    def test_n_atoms(self):
        self.assertEqual(4, ATOMS_DATABASE.n_atoms)

    def test_n_properties(self):
        self.assertEqual(5, ATOMS_DATABASE.n_properties)

    def test_numeric_properties(self):
        self.assertEqual(['nucleon', 'electronegativity'], ATOMS_DATABASE.numeric_properties)

    def test__reset(self):
        ATOMS_DATABASE._reset()
        self.assertDictEqual({}, ATOMS_DATABASE._data)
        self.assertDictEqual({}, ATOMS_DATABASE._properties)

    def test_save(self):
        with patch('builtins.open', new_callable=mock_open) as op, patch('json.dump') as dump:
            ATOMS_DATABASE.save()
            op.assert_called_with(ATOMS_DATABASE._USER_DATABASE, 'w')
            dump.assert_called_with({'properties': self.properties, 'atoms': self.data}, ANY)


class TestMoleculesDatabase(unittest.TestCase):
    def setUp(self):
        self.data = {"WAT": {"alternatives": ["H2O", "water", "TIP3"],
                             "atoms": {"OW": {"symbol": "O", "alternatives": ["O", "OH2"], "groups": [],
                                              "bonds": ["HW1", "HW2"]},
                                       "HW2": {"symbol": "H", "alternatives": ["H2"], "groups": [], "bonds": ["OW"]}}}}
        self.overwrite_database()

    @classmethod
    def tearDownClass(cls):
        MOLECULES_DATABASE._load()

    def overwrite_database(self):
        MOLECULES_DATABASE._data = self.data

    def test__load_default_database(self):
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(self.data)) as m:
            MOLECULES_DATABASE._load('INVALID.json', 'molecules.json')
            m.assert_called_with('molecules.json', 'r')
            self.assertDictEqual(self.data, MOLECULES_DATABASE._data)

    def test__load_user_database(self):
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(self.data)) as m, \
                patch('os.path.exists', spec=True):
            MOLECULES_DATABASE._load('user.json', 'default.json')
            m.assert_called_with('user.json', 'r')
            self.assertDictEqual(self.data, MOLECULES_DATABASE._data)

    def test___contains__(self):
        self.assertFalse("fhsdjfsd" in MOLECULES_DATABASE)
        self.assertTrue("WAT" in MOLECULES_DATABASE)
        self.assertTrue('H2O' in MOLECULES_DATABASE)

    def test___getitem__(self):
        self.assertDictEqual(self.data['WAT'], MOLECULES_DATABASE['WAT'])
        with self.assertRaises(MoleculesDatabaseError):
            a = MOLECULES_DATABASE['INVALID']
        # TODO: Look into the not implemented description of __getitem__

    def test___iter__(self):
        generator = iter(MOLECULES_DATABASE)
        self.assertDictEqual(self.data['WAT'], next(generator))

    def test_add_molecule_existing_molecule(self):
        with self.assertRaises(MoleculesDatabaseError):
            MOLECULES_DATABASE.add_molecule("WAT")

    def test_add_molecule_valid(self):
        with patch('json.dump') as m, patch('MDANSE.Chemistry.Databases.MoleculesDatabase.save') as n:
            MOLECULES_DATABASE.add_molecule("new_molecule")
            self.assertDictEqual({'alternatives': [], 'atoms': {}}, MOLECULES_DATABASE['new_molecule'])
            assert not m.called
            assert not n.called

    def test_items(self):
        for (expected_atom, expected_data), (atom, data) in zip(self.data.items(), MOLECULES_DATABASE.items()):
            self.assertEqual(expected_atom, atom)
            self.assertDictEqual(expected_data, data)

    def test_molecules(self):
        self.assertEqual(['WAT'], MOLECULES_DATABASE.molecules)

    def test_n_molecules(self):
        self.assertEqual(1, MOLECULES_DATABASE.n_molecules)

    def test__reset(self):
        MOLECULES_DATABASE._reset()
        self.assertDictEqual({}, MOLECULES_DATABASE._data)

    def test_save(self):
        with patch('builtins.open', new_callable=mock_open) as op, patch('json.dump') as dump:
            MOLECULES_DATABASE.save()
            op.assert_called_with(MOLECULES_DATABASE._USER_DATABASE, 'w')
            dump.assert_called_with(self.data, ANY)


class TestNucleotidesDatabase(unittest.TestCase):
    def setUp(self):
        self.data = {"5T1": {"is_3ter_terminus": False,
                             "atoms": {"HO5'": {"replaces": ["OP1", "OP2", "P"], "o5prime_connected": True,
                                                "groups": [], "bonds": ["O5'"], "symbol": "H", "alternatives": []}},
                             "alternatives": ["5-terminus", "5T"], "is_5ter_terminus": True}}
        NUCLEOTIDES_DATABASE._data = self.data
        NUCLEOTIDES_DATABASE._residue_map = {'5T1': '5T1', '5-terminus': '5T1', '5T': '5T1'}

    @classmethod
    def tearDownClass(cls):
        NUCLEOTIDES_DATABASE._load()

    def test__load_default_database(self):
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(self.data)) as m:
            NUCLEOTIDES_DATABASE._load('INVALID.json', 'molecules.json')
            m.assert_called_with('molecules.json', 'r')
            self.assertDictEqual(self.data, NUCLEOTIDES_DATABASE._data)
            self.assertDictEqual({'5T1': '5T1', '5-terminus': '5T1', '5T': '5T1'}, NUCLEOTIDES_DATABASE._residue_map)

    def test__load_user_database(self):
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(self.data)) as m, \
                patch('os.path.exists', spec=True):
            NUCLEOTIDES_DATABASE._load('user.json', 'default.json')
            m.assert_called_with('user.json', 'r')
            self.assertDictEqual(self.data, NUCLEOTIDES_DATABASE._data)
            self.assertDictEqual({'5T1': '5T1', '5-terminus': '5T1', '5T': '5T1'}, NUCLEOTIDES_DATABASE._residue_map)

    def test___contains__(self):
        self.assertFalse("fhsdjfsd" in NUCLEOTIDES_DATABASE)
        self.assertTrue("5T1" in NUCLEOTIDES_DATABASE)
        self.assertTrue('5T' in NUCLEOTIDES_DATABASE)

    def test___getitem__(self):
        self.assertDictEqual(self.data['5T1'], NUCLEOTIDES_DATABASE['5T1'])
        self.assertDictEqual(self.data['5T1'], NUCLEOTIDES_DATABASE['5T'])
        with self.assertRaises(NucleotidesDatabaseError):
            a = NUCLEOTIDES_DATABASE['INVALID']
        # TODO: Look into the not implemented description of __getitem__

    def test___iter__(self):
        generator = iter(NUCLEOTIDES_DATABASE)
        self.assertDictEqual(self.data['5T1'], next(generator))

    def test_add_nucleotide_existing_nucleotide(self):
        with self.assertRaises(NucleotidesDatabaseError):
            NUCLEOTIDES_DATABASE.add_nucleotide("5T")

    def test_add_nucleotide_valid(self):
        with patch('json.dump') as m, patch('MDANSE.Chemistry.Databases.NucleotidesDatabase.save') as n:
            NUCLEOTIDES_DATABASE.add_nucleotide("new_nucleotide", True, True)
            self.assertDictEqual({'alternatives': [], 'atoms': {}, 'is_5ter_terminus': True, 'is_3ter_terminus': True},
                                 NUCLEOTIDES_DATABASE['new_nucleotide'])
            assert not m.called
            assert not n.called

    def test_items(self):
        for (expected_atom, expected_data), (atom, data) in zip(self.data.items(), NUCLEOTIDES_DATABASE.items()):
            self.assertEqual(expected_atom, atom)
            self.assertDictEqual(expected_data, data)

    def test_nucleotides(self):
        self.assertEqual(['5T1'], NUCLEOTIDES_DATABASE.nucleotides)

    def test_n_nucleotides(self):
        self.assertEqual(1, NUCLEOTIDES_DATABASE.n_nucleotides)

    def test__reset(self):
        NUCLEOTIDES_DATABASE._reset()
        self.assertDictEqual({}, NUCLEOTIDES_DATABASE._data)

    def test_save(self):
        with patch('builtins.open', new_callable=mock_open) as op, patch('json.dump') as dump:
            NUCLEOTIDES_DATABASE.save()
            op.assert_called_with(NUCLEOTIDES_DATABASE._USER_DATABASE, 'w')
            dump.assert_called_with(self.data, ANY)


class TestResiduesDatabase(unittest.TestCase):
    def setUp(self):
        self.data = {"GLY": {"is_n_terminus": False,
                             "atoms": {"C": {"symbol": "C", "alternatives": [], "groups": ["backbone", "peptide"],
                                             "bonds": ["CA", "O", "+R"]},
                                       "H": {"symbol": "H", "alternatives": ["HN"], "groups": ["backbone", "peptide"],
                                             "bonds": ["N"]},
                                       "CA": {"symbol": "C", "alternatives": [], "groups": ["backbone"],
                                              "bonds": ["C", "HA2", "HA3", "N"]}},
                     "alternatives": ['glycine', 'G'], "is_c_terminus": False}}
        RESIDUES_DATABASE._data = self.data
        RESIDUES_DATABASE._residue_map = {'GLY': 'GLY', 'glycine': 'GLY', 'G': 'GLY'}

    @classmethod
    def tearDownClass(cls):
        RESIDUES_DATABASE._load()

    def test__load_default_database(self):
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(self.data)) as m:
            RESIDUES_DATABASE._load('INVALID.json', 'residues.json')
            m.assert_called_with('residues.json', 'r')
            self.assertDictEqual(self.data, RESIDUES_DATABASE._data)
            self.assertDictEqual({'GLY': 'GLY', 'glycine': 'GLY', 'G': 'GLY'}, RESIDUES_DATABASE._residue_map)

    def test__load_user_database(self):
        with patch('builtins.open', new_callable=mock_open, read_data=json.dumps(self.data)) as m, \
                patch('os.path.exists', spec=True):
            RESIDUES_DATABASE._load('user.json', 'default.json')
            m.assert_called_with('user.json', 'r')
            self.assertDictEqual(self.data, RESIDUES_DATABASE._data)
            self.assertDictEqual({'GLY': 'GLY', 'glycine': 'GLY', 'G': 'GLY'}, RESIDUES_DATABASE._residue_map)

    def test___contains__(self):
        self.assertFalse("fhsdjfsd" in RESIDUES_DATABASE)
        self.assertTrue("GLY" in RESIDUES_DATABASE)
        self.assertTrue('G' in RESIDUES_DATABASE)

    def test___getitem__(self):
        self.assertDictEqual(self.data['GLY'], RESIDUES_DATABASE['GLY'])
        self.assertDictEqual(self.data['GLY'], RESIDUES_DATABASE['G'])
        with self.assertRaises(ResiduesDatabaseError):
            a = RESIDUES_DATABASE['INVALID']
        # TODO: Look into the not implemented description of __getitem__

    def test___iter__(self):
        generator = iter(RESIDUES_DATABASE)
        self.assertDictEqual(self.data['GLY'], next(generator))

    def test_add_residue_existing_nucleotide(self):
        with self.assertRaises(ResiduesDatabaseError):
            RESIDUES_DATABASE.add_residue("G")

    def test_add_residue_valid(self):
        with patch('json.dump') as m, patch('MDANSE.Chemistry.Databases.ResiduesDatabase.save') as n:
            RESIDUES_DATABASE.add_residue("new_residues", True, True)
            self.assertDictEqual({'alternatives': [], 'atoms': {}, 'is_c_terminus': True, 'is_n_terminus': True},
                                 RESIDUES_DATABASE['new_residues'])
            assert not m.called
            assert not n.called

    def test_items(self):
        for (expected_atom, expected_data), (atom, data) in zip(self.data.items(), RESIDUES_DATABASE.items()):
            self.assertEqual(expected_atom, atom)
            self.assertDictEqual(expected_data, data)

    def test_residues(self):
        self.assertEqual(['GLY'], RESIDUES_DATABASE.residues)

    def test_n_residues(self):
        self.assertEqual(1, RESIDUES_DATABASE.n_residues)

    def test__reset(self):
        RESIDUES_DATABASE._reset()
        self.assertDictEqual({}, RESIDUES_DATABASE._data)

    def test_save(self):
        with patch('builtins.open', new_callable=mock_open) as op, patch('json.dump') as dump:
            RESIDUES_DATABASE.save()
            op.assert_called_with(RESIDUES_DATABASE._USER_DATABASE, 'w')
            dump.assert_called_with(self.data, ANY)


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestAtomsDatabase))
    s.addTest(loader.loadTestsFromTestCase(TestMoleculesDatabase))
    s.addTest(loader.loadTestsFromTestCase(TestNucleotidesDatabase))
    s.addTest(loader.loadTestsFromTestCase(TestResiduesDatabase))
    return s


if __name__ == '__main__':
    unittest.main(verbosity=2)

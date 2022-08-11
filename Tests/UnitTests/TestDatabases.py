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

''' 
Created on May 29, 2015

@author: Eric C. Pellegrini
'''

import json
import os
import unittest
from unittest.mock import patch, mock_open, ANY

from MDANSE.Chemistry import ATOMS_DATABASE
import MDANSE.Chemistry.Databases as Databases
from MDANSE.Chemistry.Databases import AtomsDatabaseError


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


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTest(loader.loadTestsFromTestCase(TestAtomsDatabase))
    return s


if __name__ == '__main__':
    unittest.main(verbosity=2)

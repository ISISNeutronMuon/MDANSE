#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
import unittest
from unittest.mock import patch, mock_open

from MDANSE.Chemistry import (
    ATOMS_DATABASE,
)
from MDANSE.Chemistry.Databases import (
    AtomsDatabaseError
)
from MDANSE.IO.IOUtils import MDANSEEncoder
from MDANSE.IO.AtomInfo import atom_info


class TestAtomsDatabase(unittest.TestCase):
    def setUp(self):
        self.data = {
            "H": {
                "family": "non metal",
                "nucleon": 0,
                "electronegativity": 2.2,
                "symbol": "H",
            },
            "H2": {
                "family": "non metal",
                "nucleon": 2,
                "electronegativity": 2.2,
                "symbol": "H",
            },
            "O": {
                "family": "non metal",
                "nucleon": 0,
                "electronegativity": 3.44,
                "symbol": "O",
            },
            "Fe": {
                "family": "transition metal",
                "nucleon": 0,
                "electronegativity": 1.83,
                "symbol": "Fe",
            },
        }
        self.properties = {
            "family": "str",
            "nucleon": "int",
            "electronegativity": "float",
            "symbol": "str",
        }
        self.units = {
            "family": "none",
            "nucleon": "none",
            "electronegativity": "none",
            "symbol": "none",
        }
        self.overwrite_database()

    @classmethod
    def tearDownClass(cls):
        ATOMS_DATABASE._load()

    def overwrite_database(self):
        ATOMS_DATABASE._data = self.data
        ATOMS_DATABASE._properties = self.properties
        ATOMS_DATABASE._units = self.units

    def test___contains__(self):
        self.assertFalse("fhsdjfsd" in ATOMS_DATABASE)
        self.assertTrue("H" in ATOMS_DATABASE)

    def test___getitem__(self):
        self.assertDictEqual(
            {
                "family": "non metal",
                "nucleon": 0,
                "electronegativity": 2.2,
                "symbol": "H",
            },
            ATOMS_DATABASE["H"],
        )
        with self.assertRaises(KeyError):
            _a = ATOMS_DATABASE["INVALID"]

    def test___iter__(self):
        generator = iter(ATOMS_DATABASE)
        self.assertDictEqual(
            {
                "family": "non metal",
                "nucleon": 0,
                "electronegativity": 2.2,
                "symbol": "H",
            },
            next(generator),
        )

    def test_add_atom_existing_atom(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.add_atom("H")

    def test_add_atom_valid(self):
        with (
            patch("json.dump") as m,
            patch("MDANSE.Chemistry.Databases.AtomsDatabase.save") as n,
        ):
            ATOMS_DATABASE.add_atom("new_atom")
            self.assertDictEqual({
                "family": "",
                "nucleon": 0,
                "electronegativity": 0.0,
                "symbol": ""
            }, ATOMS_DATABASE["new_atom"])
            assert not m.called
            assert not n.called

    def test_add_property_already_registered(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.add_property("symbol", "str")

    def test_add_property_invalid_type(self):
        with self.assertRaises(TypeError):
            ATOMS_DATABASE.add_property("new_property", "xxxx")

    def test_add_property_valid(self):
        ATOMS_DATABASE.add_property("new_property", "str")
        self.assertEqual("str", ATOMS_DATABASE._properties["new_property"])
        for at in ATOMS_DATABASE._data.values():
            self.assertEqual("", at["new_property"])

    def test_atoms(self):
        self.assertEqual(["Fe", "H", "H2", "O"], ATOMS_DATABASE.atoms)

    def test_get_isotopes_valid(self):
        self.assertEqual(["H2"], ATOMS_DATABASE.get_isotopes("H"))

    def test_get_isotopes_unknown_atom(self):
        with self.assertRaises(KeyError):
            ATOMS_DATABASE.get_isotopes("INVALID")

    def test_properties(self):
        self.assertEqual(
            sorted(list(self.properties.keys())), ATOMS_DATABASE.properties
        )

    def test_get_property_valid(self):
        self.assertEqual(
            {"Fe": "Fe", "H": "H", "H2": "H", "O": "O"},
            ATOMS_DATABASE.get_property("symbol"),
        )

    def test_get_property_invalid_property(self):
        with self.assertRaises(KeyError):
            ATOMS_DATABASE.get_property("INVALID")

    def test_get_value_valid(self):
        self.assertEqual("H", ATOMS_DATABASE.get_value("H", "symbol"))

    def test_get_value_unknown_atom(self):
        with self.assertRaises(KeyError):
            ATOMS_DATABASE.get_value("INVALID", "symbol")

    def test_get_value_unknown_property(self):
        with self.assertRaises(KeyError):
            ATOMS_DATABASE.get_value("H", "INVALID")

    def test_set_value_valid(self):
        ATOMS_DATABASE.set_value("H", "symbol", "C")
        self.assertEqual("C", ATOMS_DATABASE["H"]["symbol"])

    def test_set_value_unknown_atom(self):
        with self.assertRaises(KeyError):
            ATOMS_DATABASE.set_value("INVALID", "symbol", "H")

    def test_set_value_unknown_property(self):
        with self.assertRaises(KeyError):
            ATOMS_DATABASE.set_value("H", "INVALID", "H")

    def test_set_value_invalid_value_type(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.set_value("H", "nucleon", "H")

    def test_has_atom(self):
        self.assertTrue(ATOMS_DATABASE.has_atom("H"))
        self.assertFalse(ATOMS_DATABASE.has_atom("INVALID"))

    def test_has_property(self):
        self.assertTrue(ATOMS_DATABASE.has_property("symbol"))
        self.assertFalse(ATOMS_DATABASE.has_property("INVALID"))

    def test_info(self):
        info_text = atom_info("H", database=ATOMS_DATABASE)
        lines = iter(info_text.splitlines())
        next(lines)
        self.assertEqual(next(lines).strip(), "H")
        self.assertTrue({"property", "value", "unit"}.issubset(next(lines).split()))
        
        properties = {
            tokens[0] for line in lines if len(tokens := line.split()) > 2
        }
        self.assertTrue(set(self.properties) <= properties)

    def test_items(self):
        for (expected_atom, expected_data), (atom, data) in zip(
            self.data.items(), ATOMS_DATABASE.items()
        ):
            self.assertEqual(expected_atom, atom)
            self.assertDictEqual(expected_data, data)

    def test_match_numeric_property_valid(self):
        self.assertEqual(
            ["H", "H2"], ATOMS_DATABASE.match_numeric_property("electronegativity", 2.2)
        )
        self.assertEqual(
            ["H", "H2", "Fe"],
            ATOMS_DATABASE.match_numeric_property("electronegativity", 2, 0.3),
        )

    def test_match_numeric_property_non_numeric_property(self):
        with self.assertRaises(AtomsDatabaseError) as e:
            ATOMS_DATABASE.match_numeric_property("symbol", 0)
        self.assertEqual(
            'The provided property must be numeric, but "symbol" has type str.',
            str(e.exception)[1:-1],
        )

    def test_match_numeric_property_unknown_property(self):
        with self.assertRaises(KeyError):
            ATOMS_DATABASE.match_numeric_property("INVALID", 0)

    def test_match_numeric_property_non_numeric_value(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.match_numeric_property("electronegativity", [])

    def test_n_atoms(self):
        self.assertEqual(4, ATOMS_DATABASE.n_atoms)

    def test_n_properties(self):
        self.assertEqual(4, ATOMS_DATABASE.n_properties)

    def test_numeric_properties(self):
        self.assertEqual(
            ["nucleon", "electronegativity"], ATOMS_DATABASE.numeric_properties
        )

    def test__reset(self):
        ATOMS_DATABASE._reset()
        self.assertDictEqual({}, ATOMS_DATABASE._data)
        self.assertDictEqual({}, ATOMS_DATABASE._properties)

    def test_save(self):
        with (
            patch("builtins.open", new_callable=mock_open) as op,
            patch("json.dumps") as dump,
        ):
            ATOMS_DATABASE.save()
            op.assert_called_with(ATOMS_DATABASE._USER_DATABASE, "w")
            dump.assert_called_with(
                {"properties": self.properties, "units": self.units, "atoms": self.data}, indent=4, cls=MDANSEEncoder
            )

    def test_remove_atom(self):
        ATOMS_DATABASE.remove_atom("Fe")
        self.assertEqual(["H", "H2", "O"], ATOMS_DATABASE.atoms)

    def test_remove_atom_for_atom_that_does_not_exist_raise_database_error(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.remove_atom("Test")

    def test_remove_property(self):
        ATOMS_DATABASE.remove_property("electronegativity")
        self.assertDictEqual({
                "family": "transition metal",
                "nucleon": 0,
                "symbol": "Fe",
            },
            ATOMS_DATABASE["Fe"]
        )

    def test_remove_property_for_property_that_does_not_exist_raise_database_error(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.remove_property("Test")

    def test_rename_atom_type(self):
        ATOMS_DATABASE.rename_atom_type("Fe", "FeNew")
        self.assertEqual(["FeNew", "H", "H2", "O"], ATOMS_DATABASE.atoms)

    def test_rename_atom_type_raise_database_error_when_new_atom_type_already_exists(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.rename_atom_type("Fe", "H")

    def test_rename_atom_type_raise_database_error_when_old_atom_type_does_not_exists(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.rename_atom_type("Fee", "H")

    def test_rename_atom_property(self):
        ATOMS_DATABASE.rename_atom_property("electronegativity", "electronegativitynew")
        self.assertDictEqual({
                "family": "transition metal",
                "nucleon": 0,
                "electronegativitynew": 1.83,
                "symbol": "Fe",
            },
            ATOMS_DATABASE["Fe"]
        )

    def test_rename_atom_property_raise_database_error_when_new_atom_property_already_exists(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.rename_atom_property("symbol", "electronegativity")

    def test_rename_atom_property_raise_database_error_when_old_atom_type_does_not_exists(self):
        with self.assertRaises(AtomsDatabaseError):
            ATOMS_DATABASE.rename_atom_property("electronegativitytest", "symbol")

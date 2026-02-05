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

import numpy as np
import pytest

from MDANSE.Chemistry import ATOMS_DATABASE


element_list = [atom_symbol for atom_symbol in ATOMS_DATABASE.atoms if atom_symbol.isalpha()]
monoisotopic = [atom_symbol for atom_symbol in element_list if len(ATOMS_DATABASE.get_isotopes(atom_symbol)) == 1]

@pytest.mark.parametrize('element', monoisotopic)
def test_single_isotope(element):
    avg_dict = ATOMS_DATABASE.get_property_dict(element)
    isotope = ATOMS_DATABASE.get_isotopes(element)[0]
    isotope_dict = ATOMS_DATABASE.get_property_dict(isotope)
    for key in avg_dict:
        if (
            isinstance(avg_dict[key], (list, dict)) 
            or avg_dict[key] == isotope_dict[key]
            or key == "nuclear_spin"
        ):
            continue
        assert np.isclose(avg_dict[key], isotope_dict[key], equal_nan=True)


@pytest.mark.parametrize('element', element_list)
def test_b_coherent(element):
    isotopes = ATOMS_DATABASE.get_isotopes(element)
    avg_b_coh = ATOMS_DATABASE.get_atom_property(element, 'b_coherent')
    if (
        np.isnan(avg_b_coh)
        or element in {'Hg', 'Ru', 'Kr', 'Xe', 'Cm', 'Pu'}
    ):
        return
    b_coh_values = [ATOMS_DATABASE.get_atom_property(isotope, 'b_coherent') for isotope in isotopes]
    abundance_values = [ATOMS_DATABASE.get_atom_property(isotope, 'abundance') for isotope in isotopes]
    mask = [np.isnan(b_coh) for b_coh in b_coh_values]
    b_coh_array = np.array([b_coh_values[it] for it in range(len(b_coh_values)) if not mask[it]])
    abundance_array = np.array([abundance_values[it] for it in range(len(abundance_values)) if not mask[it]])/100.0
    calculated_b_coh = (b_coh_array*abundance_array).sum()
    print(f"{element} {avg_b_coh} {calculated_b_coh}")
    assert np.isclose(avg_b_coh, calculated_b_coh, rtol= 5e-3, atol= 5e-7, equal_nan=True)


def test_database_units():
    for key in ATOMS_DATABASE._properties:
        assert key in ATOMS_DATABASE._units

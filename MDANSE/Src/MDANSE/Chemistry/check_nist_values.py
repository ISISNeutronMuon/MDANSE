#    This file is part of MDANSE.
#
#    MDANSE is free software: you can redistribute it and/or modify
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
from __future__ import annotations

import re


def parse_number(number_string: str) -> complex | float | None:
    if number_string == "---":
        return None
    substring = re.search(r"\((\w+)\)", number_string)
    clean_string = number_string.replace(substring, "")
    try:
        val = complex(clean_string.replace("i", "j"))
    except (TypeError, ValueError):
        return None
    else:
        if abs(val.imag) < 1e-10:
            return val.real
        return val


def load_csv(fname: str) -> dict[str, list[complex | float | str]]:
    """Load neutron scattering properties for the NIST database.

    Parameters
    ----------
    fname : str
        path to the CSV file containing the NIST neutron scattering values.

    Returns
    -------
    dict[str,list[complex | float | str]]
        For each atom type, a list of neutron scattering properties

    """
    database = {}
    with open(fname) as source:
        for line in source:
            toks = line.split(",")
            if "#" in toks[0]:
                continue
            database[toks[0]] = [parse_number(number_str) for number_str in toks[1:]]
    return database

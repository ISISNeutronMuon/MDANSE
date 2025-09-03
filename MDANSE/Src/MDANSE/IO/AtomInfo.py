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

from collections import defaultdict

from MDANSE.Chemistry import ATOMS_DATABASE, AtomsDatabase
from MDANSE.MolecularDynamics.Trajectory import Trajectory


def atom_info(atom: str, database: AtomsDatabase | Trajectory | None = None) -> str:
    """Return as string all the information about the input atom.

    Parameters
    ----------
    atom : str
        Atom type.
    database: AtomsDatabase | Trajectory | None
        Object providing atom information. If None, ATOMS_DATABASE will be used.

    Returns
    -------
    str
        Multi-line list of all the atom properties.

    """
    if database is None:
        database = ATOMS_DATABASE
    if isinstance(database, AtomsDatabase):
        units = database.units
    else:
        units = defaultdict(lambda: "none")

    properties = database.properties
    atoms = database.atoms

    if atom not in atoms:
        raise KeyError(f"Atom {atom} is not in the atom database {database}.")

    if isinstance(database, AtomsDatabase):
        property_dict = {
            prop_name: database.get_value(atom, prop_name, raw_value=True)
            for prop_name in properties
        }
    else:
        property_dict = {
            prop_name: database.get_atom_property(atom, prop_name)
            for prop_name in properties
        }
    # A delimiter line.
    delimiter = "-" * 70
    tab_fmt = "{:<20}{!s:>40}{!s:>10}"

    info = [
        delimiter,
        f"{atom:^70}",
        tab_fmt.format("property", "value", "unit"),
        delimiter,
    ]

    # The values for all element's properties
    for pname in sorted(properties):
        if pname.strip():
            info.append(
                tab_fmt.format(pname, property_dict.get(pname), units.get(pname))
            )

    info.append(delimiter)
    info = "\n".join(info)

    return info

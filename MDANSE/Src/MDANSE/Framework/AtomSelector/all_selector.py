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
from typing import Union
from MDANSE.Chemistry.ChemicalEntity import ChemicalSystem


def select_all(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects all atoms in the chemical system except for the dummy
    atoms.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    check_exists : bool, optional
        Check if a match exists.

    Returns
    -------
    Union[set[int], bool]
        All atom indices except for dummy atoms or a bool if checking
        match.
    """
    if check_exists:
        return True
    else:
        return set([at.index for at in system.atom_list if at.element != "dummy"])

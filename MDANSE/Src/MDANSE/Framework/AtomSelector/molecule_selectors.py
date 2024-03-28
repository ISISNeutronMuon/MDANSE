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


__all__ = [
    "select_water",
]


def select_water(
    system: ChemicalSystem, check_exists: bool = False
) -> Union[set[int], bool]:
    """Selects the O and H atoms of all water molecules.

    Parameters
    ----------
    system : ChemicalSystem
        The MDANSE chemical system.
    check_exists : bool, optional
        Check if a match exists.

    Returns
    -------
    Union[set[int], bool]
        The atom indices of the matched atoms or a bool if checking match.
    """
    pattern = "[#8X2;H2](~[H])~[H]"
    if check_exists:
        return system.has_substructure_match(pattern)
    else:
        return system.get_substructure_matches(pattern)

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

from collections.abc import Sequence

from MDANSE.MolecularDynamics.Trajectory import Trajectory


def select_atoms(
    trajectory: Trajectory,
    *,
    index_list: Sequence[int] | None = None,
    index_range: Sequence[int] | None = None,
    index_slice: Sequence[int] | None = None,
    atom_types: Sequence[str] = (),
    atom_names: Sequence[str] = (),
    **_kwargs: str,
) -> set[int]:
    """Select specific atoms in the trajectory.

    Atoms can be selected based
    on indices, atom type or trajectory-specific atom name.
    The atom type is normally the chemical element, while
    the atom name can be more specific and depend on the
    force field used.

    Parameters
    ----------
    trajectory : Trajectory
        A trajectory instance to which the selection is applied
    index_list : Sequence[int]
        a list of indices to be selected
    index_range : Sequence[int]
        a pair of (first, last+1) indices defining a range
    index_slice : Sequence[int]
        a sequence of (first, last+1, step) indices defining a slice
    atom_types : Sequence[str]
        a list of atom types (i.e. chemical elements) to be selected, given as string
    atom_names : Sequence[str]
        a list of atom names (as used by the MD engine, force field, etc.) to be selected

    Returns
    -------
    set[int]
        A set of indices which have been selected

    """
    selection = set()
    system = trajectory.chemical_system
    element_list = system.atom_list
    name_list = system.name_list
    indices = system.all_indices
    if index_list is not None:
        selection |= indices & set(index_list)
    if index_range is not None:
        selection |= indices & set(range(*index_range))
    if index_slice is not None:
        selection |= indices & set(range(*index_slice))
    if atom_types:
        new_indices = {index for index in indices if element_list[index] in atom_types}
        selection |= new_indices
    if atom_names:
        new_indices = {index for index in indices if name_list[index] in atom_names}
        selection |= new_indices
    return selection


def select_dummy(
    trajectory: Trajectory,
    **_kwargs: str,
) -> set[int]:
    """Select all atoms with the dummy property.

    Parameters
    ----------
    trajectory : Trajectory
        A trajectory instance to which the selection is applied

    Returns
    -------
    set[int]
        A set of indices which have been selected

    """
    system = trajectory.chemical_system
    element_list = system.atom_list
    dummy_types = {
        type
        for type in set(element_list)
        if trajectory.get_atom_property(type, "dummy")
    }
    return {index for index in system.all_indices if element_list[index] in dummy_types}

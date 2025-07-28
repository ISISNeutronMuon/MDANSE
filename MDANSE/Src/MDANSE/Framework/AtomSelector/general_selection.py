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

from collections import Counter

from MDANSE.MolecularDynamics.Trajectory import Trajectory


def select_all(trajectory: Trajectory, **_kwargs: str) -> set[int]:
    """Select all the atoms in the trajectory.

    Parameters
    ----------
    trajectory : Trajectory
        A trajectory instance to which the selection is applied

    Returns
    -------
    Set[int]
        Set of all the atom indices

    """
    return trajectory.chemical_system.all_indices


def select_none(_trajectory: Trajectory, **_kwargs: str) -> set[int]:
    """Return an empty selection.

    Parameters
    ----------
    _trajectory : Trajectory
        A trajectory instance, ignored in this selection

    Returns
    -------
    Set[int]
        An empty set.

    """
    return set()


def invert_selection(
    trajectory: Trajectory,
    selection: set[int],
    **_kwargs: str,
) -> set[int]:
    """Invert the current selection for the input trajectory.

    Return a set of all the indices that are present in the trajectory
    and were not included in the input selection.

    Parameters
    ----------
    trajectory : Trajectory
        a trajectory containing atoms to be selected
    selection : Set[int]
        set of indices to be excluded from the set of all indices

    Returns
    -------
    Set[int]
        set of all the indices in the trajectory which were not in the input selection

    """
    all_indices = select_all(trajectory)
    return all_indices - selection


def toggle_selection(
    trajectory: Trajectory,
    current_selection: set[int],
    clicked_atoms: list[int],
    **_kwargs: str,
) -> set[int]:
    """Invert the selection state of atoms clicked in the GUI.

    Return the updated selection.

    Parameters
    ----------
    trajectory : Trajectory
        A trajectory containing atoms to be selected.
    current_selection : set[int]
        Set of indices that had been selected before manual selection.
    clicked_atoms : list[int]
        List of atom indices that have been clicked so far.

    Returns
    -------
    set[int]
        New selection after manual selection.

    """
    click_counter = Counter(clicked_atoms)
    # Add current selection count as True
    click_counter.update(current_selection)
    return {index for index, state in click_counter.items() if state % 2}

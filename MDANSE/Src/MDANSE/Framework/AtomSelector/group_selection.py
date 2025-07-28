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

from more_itertools import value_chain

from MDANSE.MolecularDynamics.Trajectory import Trajectory


def select_labels(
    trajectory: Trajectory,
    atom_labels: Sequence[str] = (),
    **_kwargs: str,
) -> set[int]:
    """Select atoms with a specific label in the trajectory.

    A residue name can be used as a label by MDANSE.

    Parameters
    ----------
    trajectory : Trajectory
        A trajectory instance to which the selection is applied
    atom_labels : Sequence[str]
        a list of string labels (e.g. residue names) by which to select atoms

    Returns
    -------
    Set[int]
        Set of atom indices corresponding to the selected labels

    """
    system = trajectory.chemical_system
    return {struc for label in atom_labels for struc in system._labels.get(label, [])}


def select_pattern(
    trajectory: Trajectory,
    *,
    rdkit_pattern: str,
    **_kwargs: str,
) -> set[int]:
    """Select atoms according to the SMARTS string given as input.

    This will only work if molecules and bonds have been detected in the system.
    If the bond information was not read from the input trajectory on conversion,
    it can still be determined in a TrajectoryEditor run.

    Parameters
    ----------
    trajectory : Trajectory
        A trajectory instance to which the selection is applied
    rdkit_pattern : str
        a SMARTS string to be matched

    Returns
    -------
    Set[int]
        Set of atom indices matched by rdkit

    """
    selection = set()
    system = trajectory.chemical_system
    selection = system.get_substructure_matches(rdkit_pattern)
    return selection

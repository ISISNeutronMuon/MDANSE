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


def select_molecules(
    trajectory: Trajectory, molecule_names: Sequence[str] = (), **_kwargs: str
) -> set[int]:
    """Selects all the atoms belonging to the specified molecule types.

    Parameters
    ----------
    trajectory : Trajectory
        A trajectory instance to which the selection is applied
    molecule_names : Sequence[str]
        a list of molecule names (str) which are keys of ChemicalSystem._clusters

    Returns
    -------
    Set[int]
        Set of indices of atoms belonging to molecules from molecule_names
    """
    selection = set()
    system = trajectory.chemical_system
    selection = {
        index
        for molecule in molecule_names
        for cluster in system._clusters.get(molecule, ())
        for index in cluster
    }
    return selection

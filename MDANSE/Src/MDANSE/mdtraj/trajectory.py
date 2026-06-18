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

from typing import TYPE_CHECKING

from mdtraj import Topology as mdtraj_topology
from mdtraj import Trajectory as mdtraj_trajectory
from mdtraj.core.element import Element

from MDANSE.MolecularDynamics.Connectivity import Connectivity

if TYPE_CHECKING:
    from MDANSE.MolecularDynamics.Trajectory import Trajectory


def build_mdtraj_topology(mdanse_traj: Trajectory) -> mdtraj_topology:
    """Construct an MDTraj Topology object from an MDANSE trajectory.

    Parameters
    ----------
    mdanse_traj : Trajectory
        An MDANSE trajectory instance.

    Returns
    -------
    mdtraj_topology
        mdtraj.Topology instance.
    """
    new_topology = mdtraj_topology()
    chain = new_topology.add_chain("ALL")
    default_residue = new_topology.add_residue("NONE", chain)
    selected_indices = mdanse_traj.atom_indices
    mdtraj_elements = {
        str_symbol: Element.getBySymbol(str_symbol)
        for str_symbol in mdanse_traj.unique_elements
    }
    elements = [mdanse_traj.atom_types[index] for index in selected_indices]
    names = [mdanse_traj.atom_names[index] for index in selected_indices]
    residues = [default_residue] * len(elements)
    for label, mol_indices in mdanse_traj.chemical_system._labels.items():
        res = new_topology.add_residue(label, chain)
        for index in mol_indices:
            if index in selected_indices:
                residues[index] = res
    mdtraj_atoms = {}
    for index, name, element, residue in zip(
        selected_indices, names, elements, residues, strict=True
    ):
        mdtraj_atoms[index] = new_topology.add_atom(
            name, mdtraj_elements[element], residue
        )
    if mdanse_traj.chemical_system._bonds:
        bond_list = mdanse_traj.chemical_system._bonds
    else:
        conn = Connectivity(mdanse_traj, selection=mdanse_traj.atom_indices)
        conn.find_bonds([0])
        bond_list = conn._unique_bonds
    for ind1, ind2 in bond_list:
        if ind1 in selected_indices and ind2 in selected_indices:
            new_topology.add_bond(mdtraj_atoms[ind1], mdtraj_atoms[ind2])
    return new_topology


def build_mdtraj_trajectory(
    mdanse_traj: Trajectory, frame_slice: tuple[int, int, int] | None = None
) -> mdtraj_trajectory:
    """Build an MDTraj Trajectory from an MDANSE trajectory.

    The output trajectory can be used as input in MDTraj analysis runs.

    Parameters
    ----------
    mdanse_traj : Trajectory
        An MDANSE Trajectory instance.
    frame_slice : tuple[int, int, int] | None, optional
        Frame selection as a (start, stop, step) index tuple, by default None

    Returns
    -------
    mdtraj_trajectory
        An mdtraj.Trajectory instance.
    """
    new_topology = build_mdtraj_topology(mdanse_traj)
    unit_cell_abc = []
    unit_cell_angles = []
    the_slice = (
        slice(None, None, None)
        if frame_slice is None
        else slice(frame_slice[0], frame_slice[1], frame_slice[2])
    )
    the_range = (
        range(len(mdanse_traj))
        if frame_slice is None
        else range(frame_slice[0], frame_slice[1], frame_slice[2])
    )
    for frame in the_range:
        a, b, c, alpha, beta, gamma = mdanse_traj.unit_cell(frame).abc_and_angles
        unit_cell_abc.append((a, b, c))
        unit_cell_angles.append((alpha, beta, gamma))
    new_instance = mdtraj_trajectory(
        mdanse_traj.coordinates(the_slice, mdanse_traj.atom_indices),
        new_topology,
        time=mdanse_traj.time()[the_slice],
        unitcell_angles=unit_cell_angles,
        unitcell_lengths=unit_cell_abc,
    )
    return new_instance

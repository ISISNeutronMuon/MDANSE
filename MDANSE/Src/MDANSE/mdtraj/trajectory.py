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

if TYPE_CHECKING:
    from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
    from MDANSE.MolecularDynamics.Trajectory import Trajectory


def build_mdtraj_topology(mdanse_traj: Trajectory) -> mdtraj_topology:
    new_topology = mdtraj_topology()
    elements = mdanse_traj.atom_types
    names = mdanse_traj.atom_names
    residues = [""] * len(elements)
    for label, indices in mdanse_traj.chemical_system._labels.items():
        for index in indices:
            residues[index] = label
    for name, element, residue in zip(names, elements, residues, strict=True):
        new_topology.add_atom(name, element, residue)
    return new_topology


def build_mdtraj_trajectory(
    mdanse_traj: Trajectory, frame_slice: tuple[int, int, int] | None = None
) -> mdtraj_trajectory:
    new_topology = build_mdtraj_topology(mdanse_traj)
    unit_cell_abc = []
    unit_cell_angles = []
    the_slice = (
        slice()
        if frame_slice is None
        else slice(frame_slice[0], frame_slice[1], frame_slice[2])
    )
    the_range = (
        range(len(mdanse_traj))
        if frame_slice is None
        else range(frame_slice[0], frame_slice[1], frame_slice[2])
    )
    for frame in the_range:
        abc, angles = mdanse_traj.unit_cell(frame).abc_and_angles()
        unit_cell_abc.append(abc)
        unit_cell_angles.append(angles)
    new_instance = mdtraj_trajectory(
        mdanse_traj.coordinates(the_slice),
        new_topology,
        time=mdanse_traj.time()[the_slice],
        unitcell_angles=unit_cell_angles,
        unitcell_lengths=unit_cell_abc,
    )
    return new_instance

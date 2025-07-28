#    This file is part of MDANSE_GUI.
#
#    MDANSE_GUI is free software: you can redistribute it and/or modify
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

import typing

import numpy as np

from MDANSE.MolecularDynamics.UnitCell import UnitCell

if typing.TYPE_CHECKING:
    from MDANSE.Chemistry.ChemicalSystem import ChemicalSystem
    from MDANSE.MolecularDynamics.Trajectory import Trajectory

from MDANSE_GUI.MolecularViewer.readers.i_reader import IReader


class HDF5Wrapper(IReader):
    def __init__(self, fname, trajectory: Trajectory, chemical: ChemicalSystem):
        super().__init__(fname)
        self._n_atoms = chemical.number_of_atoms
        self._n_frames = len(trajectory)
        self._trajectory = trajectory
        self._chemical_system = chemical
        self._filename = fname
        self._atom_ids = chemical._atom_indices
        self._atom_types = chemical.atom_list
        self._atom_names = [
            f"{element}_{index}"
            for element, index in zip(chemical.atom_list, chemical._atom_indices)
        ]

    def read_frame(self, frame: int) -> np.ndarray:
        coords = self._trajectory.coordinates(frame)
        return np.array(coords)

    def read_pbc(self, frame: int) -> UnitCell:
        try:
            unit_cell = self._trajectory.unit_cell(frame)
        except AttributeError:
            unit_cell = None
        return unit_cell

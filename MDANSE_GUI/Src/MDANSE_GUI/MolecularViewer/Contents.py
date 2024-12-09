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

import time

import numpy as np

from MDANSE.Chemistry import ATOMS_DATABASE as CHEMICAL_ELEMENTS
from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE_GUI.MolecularViewer.AtomProperties import (
    AtomProperties,
    ndarray_to_vtkarray,
)


class TrajectoryState:
    """This object will store the information about the atoms
    present in the trajectory, allowing the user to customise
    the way the trajectory is visualised.
    It is a subclass of QStandardItemModel, allowing the information
    to be used with a QTableView widget.
    """

    def __init__(self, *args, filename=None, **kwargs):
        temp = HDFTrajectoryInputData(filename)
        now = time.time_ns()
        self._identifier = str(filename) + str(now)
        self._trajectory = temp.trajectory
        self._min_frame = 0
        self._max_frame = len(self._trajectory)
        self._current_frame = 0
        self._num_atoms = self._trajectory.chemical_system.total_number_of_atoms
        self._number_array = np.arange(self._num_atoms, dtype=int)
        self._atoms = [
            atom.symbol for atom in self._trajectory.chemical_system.atom_list
        ]
        self._camera_focus = [0.0, 0.0, 0.0]
        self._camera_position = [20.0, 0.0, 0.0]
        self._bkg_colour = (0, 0, 0)
        self._projection = 0
        self._unique_atoms = np.unique(self._atoms)
        self._atom_properties = AtomProperties()
        self.create_atom_details()

    def create_atom_details(self):
        self._atom_colours = self._atom_properties.reinitialise_from_database(
            self._atoms, CHEMICAL_ELEMENTS, 0.0
        )
        # this returns a list of indices, mapping colours to atoms

        self._atom_scales = np.array(
            [
                CHEMICAL_ELEMENTS.get_atom_property(at, "vdw_radius")
                for at in self._atoms
            ]
        ).astype(np.float32)
        self.du_log = np.array(
            [
                CHEMICAL_ELEMENTS.get_atom_property(at, "element") != "dummy"
                for at in self._atoms
            ]
        )
        self.not_du = np.array(
            [
                i
                for i, at in enumerate(self._atoms)
                if CHEMICAL_ELEMENTS.get_atom_property(at, "element") != "dummy"
            ]
        )
        self.covs = np.array(
            [
                CHEMICAL_ELEMENTS.get_atom_property(at, "covalent_radius")
                for at in self._atoms
            ]
        )

    def take_atom_properties(self, data):
        colours, radii, numbers = data
        self._atom_colours = colours
        self._atom_scales = radii
        self._number_array = numbers

    def get_unit_cell(self, frame_number: int):
        self._current_frame = frame_number
        return self._trajectory.unit_cell(self._current_frame)

    def get_coordinates(self, frame_number: int) -> np.ndarray:
        self._current_frame = frame_number
        return self._trajectory.coordinates(frame_number)

    def scalars_for_vtk(self):
        return ndarray_to_vtkarray(
            self._atom_colours, self._atom_scales, self._number_array
        )

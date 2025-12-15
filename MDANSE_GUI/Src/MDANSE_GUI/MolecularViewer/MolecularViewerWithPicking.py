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

import numpy as np
import vtk
from qtpy.QtCore import Signal
from scipy.spatial import cKDTree as KDTree
from vtk.util import numpy_support

from MDANSE_GUI.MolecularViewer.AtomProperties import ndarray_to_vtkarray

from .MolecularViewer import MolecularViewer


class MolecularViewerWithPicking(MolecularViewer):
    """This class implements a molecular viewer with picking."""

    clicked_atom_index = Signal(int)
    picked_atoms_changed = Signal(object)

    def __init__(self):
        super().__init__()
        # we set dummy size to something non-zero since we need to be
        # able to see it for picking purposes
        self.dummy_size = 0.1
        self._picked_polydata = vtk.vtkPolyData()
        self.picked_atoms = set()
        self._iren.AddObserver("LeftButtonPressEvent", self.on_pick)

        self.picked_atom_actor = None
        self.picked_bond_actor = None

    def clear_atoms(self):
        super().clear_atoms()
        self.clear_picked_atoms()

    def create_atoms(self, atm_opacity: float = 0.15, picked_opacity: float = 1.0):
        super().create_atoms(atm_opacity)
        self.create_picked_atoms()

    def clear_bonds(self):
        super().clear_bonds()
        self.clear_picked_bonds()

    def create_bonds(self, bond_opacity: float = 0.15, picked_opacity: float = 1.0):
        super().create_bonds(bond_opacity)
        self.create_picked_bonds()

    def update_atm_polydata(self):
        super().update_atm_polydata()
        self.update_picked_polydata()

    def clear_picked_atoms(self):
        if not self.picked_atom_actor:
            return

        self._renderer.RemoveActor(self.picked_atom_actor)
        self.picked_atom_actor = None

    def create_picked_atoms(self, ball_opacity: float = 1.0):
        self.clear_picked_atoms()

        if not self._atoms_visible or len(self.picked_atoms) == 0:
            return

        actor = self.create_atom_actor(self._picked_polydata, ball_opacity)
        self._renderer.AddActor(actor)
        self.picked_atom_actor = actor

    def clear_picked_bonds(self):
        if not self.picked_bond_actor:
            return

        self._renderer.RemoveActor(self.picked_bond_actor)
        self.picked_bond_actor = None

    def create_picked_bonds(self, line_opacity: float = 1.0):
        self.clear_picked_bonds()

        if not self._bonds_visible or len(self.picked_atoms) == 0:
            return

        actor = self.create_bond_actor(self._picked_polydata, line_opacity)
        self._renderer.AddActor(actor)
        self.picked_bond_actor = actor

    def update_picked_polydata(self):
        atoms = vtk.vtkPoints()

        if len(self.picked_atoms) == 0:
            self._picked_polydata.SetPoints(atoms)
            return

        picked = np.array(sorted(self.picked_atoms))
        coords = self._current_coords
        atoms.SetData(numpy_support.numpy_to_vtk(coords[picked]))
        self._picked_polydata.SetPoints(atoms)

        self.set_atm_polydata_scalars(
            (
                self._colour_manager.colours[picked],
                self._colour_manager.radii[picked],
                np.arange(len(self.picked_atoms)),
            )
        )

        not_du = np.arange(len(self.picked_atoms))[self.du_log[picked]]
        if self._bonds_visible and len(not_du) >= 1:
            # do not bond atoms to dummy atoms
            rs = coords[picked][not_du]
            covs = self.covs[picked][not_du]

            bonds, bonds_exist = self.create_bond_cell_array(rs, covs, not_du)
            if bonds_exist:
                self._picked_polydata.SetLines(bonds)
                return

    def on_pick(self, obj, event=None):
        """Event handler when an atom is mouse-picked with the left mouse button"""

        if not self._reader or self.atom_actor is None:
            return

        picker = vtk.vtkCellPicker()

        picker.AddPickList(self.atom_actor)
        picker.PickFromListOn()

        pos = obj.GetEventPosition()
        picker.Pick(pos[0], pos[1], 0, self._renderer)

        picked_actor = picker.GetActor()
        if picked_actor is None:
            return

        picked_pos = np.array(picker.GetPickPosition())
        coords = self._reader.read_frame(self._current_frame)
        _, idx = KDTree(coords).query(picked_pos)

        if idx < 0 or idx >= self._n_atoms:
            return

        self.clicked_atom_index.emit(idx)
        self.pick_atom(idx)
        self.picked_atoms_changed.emit(self.picked_atoms)

    def pick_atom(self, picked_atom):
        if picked_atom in self.picked_atoms:
            self.picked_atoms.remove(picked_atom)
        else:
            self.picked_atoms.add(picked_atom)
        self._picked_polydata.Initialize()
        self.update_picked_polydata()
        self.create_picked_atoms()
        self.create_picked_bonds()
        self.update_renderer()

    def change_picked(self, picked: set[int]):
        self.picked_atoms = picked
        self._picked_polydata.Initialize()
        self.update_picked_polydata()
        self.create_picked_atoms()
        self.create_picked_bonds()
        self.update_renderer()

    def set_atm_polydata_scalars(self, data):
        super().set_atm_polydata_scalars(data)
        self.set_picked_polydata_scalars(data)

    def set_picked_polydata_scalars(self, data):
        colours, radii, numbers = data

        picked = np.array(sorted(self.picked_atoms))
        if len(picked) == 0:
            return

        colours = np.array(colours)[picked]
        radii = np.array(radii)[picked]

        scalars = ndarray_to_vtkarray(
            colours,
            radii,
            np.arange(len(self.picked_atoms)),
        )
        self._picked_polydata.GetPointData().SetScalars(scalars)

        radii_vtk = numpy_support.numpy_to_vtk(radii)
        radii_vtk.SetName("radii")
        colours_vtk = numpy_support.numpy_to_vtk(colours)
        colours_vtk.SetName("colours")
        self._picked_polydata.GetPointData().AddArray(radii_vtk)
        self._picked_polydata.GetPointData().AddArray(colours_vtk)

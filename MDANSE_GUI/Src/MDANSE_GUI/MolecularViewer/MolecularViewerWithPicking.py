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
from vtk.util import numpy_support

from MDANSE.util_types import ByteArray, FloatArray
from MDANSE_GUI.MolecularViewer.AtomProperties import ndarray_to_vtkarray

from .MolecularViewer import BondCalc, MolecularViewer


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

    @property
    def n_picked_atoms(self) -> int:
        """
        Returns
        -------
        int
            The number of picked atoms.
        """
        return len(self.picked_atoms)

    def clear_atoms(self):
        """Clears atom and picked atoms."""
        super().clear_atoms()
        self.clear_picked_atoms()

    def create_atoms(self, *, opacity: float = 0.4, picked_opacity: float = 1.0):
        """Creates atom and picked atoms actors with different opacities.

        Parameters
        ----------
        opacity : float
            opacity (alpha) of the atom sphere, by default 0.2
        picked_opacity : float
            opacity (alpha) of the picked atom sphere, by default 1.0
        """
        super().create_atoms(opacity=opacity)
        self.create_picked_atoms(opacity=picked_opacity)

    def clear_bonds(self):
        """Clears bonds and picked bonds."""
        super().clear_bonds()
        self.clear_picked_bonds()

    def create_bonds(self, *, opacity: float = 0.4, picked_opacity: float = 1.0):
        """Creates bonds and picked bonds with different opacities.

        Parameters
        ----------
        opacity : float
            opacity (alpha) of the bond lines, by default 0.2
        picked_opacity : float
            opacity (alpha) of the picked bond lines, by default 1.0
        """
        super().create_bonds(opacity=opacity)
        self.create_picked_bonds(opacity=picked_opacity)

    def update_atm_polydata(self):
        """Updates the atom and picked atom polydata coordinates."""
        super().update_atm_polydata()
        self.update_picked_polydata()

    def change_atm_polydata_lines(self):
        """Updates the atom and picked atom polydata lines."""
        super().change_atm_polydata_lines()
        self.change_picked_polydata_lines()

    def clear_picked_atoms(self):
        """Clears the picked atom actor and removes it from the renderer."""
        if not self.picked_atom_actor:
            return

        self._renderer.RemoveActor(self.picked_atom_actor)
        self.picked_atom_actor = None

    def create_picked_atoms(self, *, opacity: float = 1.0):
        """Clear and create the picked atom actor and add it to renderer.

        Parameters
        ----------
        opacity : float, optional
            opacity (alpha) of picked atom spheres, by default 1.0
        """
        self.clear_picked_atoms()

        if not self._atoms_visible or self.n_picked_atoms == 0:
            return

        actor = self.create_atom_actor(self._picked_polydata, opacity=opacity)
        self._renderer.AddActor(actor)
        self.picked_atom_actor = actor

    def clear_picked_bonds(self):
        """Clears the picked bond actor and removes it from the renderer."""
        if not self.picked_bond_actor:
            return

        self._renderer.RemoveActor(self.picked_bond_actor)
        self.picked_bond_actor = None

    def create_picked_bonds(self, *, opacity: float = 1.0):
        """Clear and create the picked bond actor and add it to renderer.

        Parameters
        ----------
        opacity : float, optional
            opacity (alpha) of picked bond lines, by default 1.0
        """
        self.clear_picked_bonds()

        if self.bond_calc is BondCalc.NONE or self.n_picked_atoms == 0:
            return

        actor = self.create_bond_actor(self._picked_polydata, opacity=opacity)
        self._renderer.AddActor(actor)
        self.picked_bond_actor = actor

    def update_picked_polydata(self):
        """Updates the picked polydata coordinates."""
        atoms = vtk.vtkPoints()

        if self.n_picked_atoms == 0:
            self._picked_polydata.SetPoints(atoms)
            return

        picked = np.array(sorted(self.picked_atoms))
        coords = self._current_coords
        atoms.SetData(numpy_support.numpy_to_vtk(coords[picked]))
        self._picked_polydata.SetPoints(atoms)

        self.set_atm_polydata_scalars(
            (
                self._colour_manager.colours,
                self._colour_manager.radii,
            )
        )

    def change_picked_polydata_lines(self):
        """Calculate and/or updates the picked polydata bonds."""
        if self.n_picked_atoms <= 1:
            self._picked_polydata.SetLines(vtk.vtkCellArray())
            return

        picked = np.array(sorted(self.picked_atoms))
        not_du = np.arange(self.n_picked_atoms)[self.du_log[picked]]

        match self.bond_calc:
            case BondCalc.EVERY:
                rs = self._current_coords
            case BondCalc.FIRST:
                rs = self._reader.read_frame(0)
            case BondCalc.LAST:
                rs = self._reader.read_frame(self._n_frames - 1)
            case BondCalc.FILE:
                bonds = np.array(self._reader._trajectory.chemical_system._bonds)
                if len(bonds) == 0:
                    self._picked_polydata.SetLines(vtk.vtkCellArray())
                    return

                # unlike the other bond calc methods if the MDANSE trajectory bonds
                # atoms to dummy atoms we will also do that here
                mask = np.isin(bonds[:, 0], picked) & np.isin(bonds[:, 1], picked)
                picked_bonds = bonds[mask]
                picked_bonds = np.column_stack(
                    (
                        np.searchsorted(picked, picked_bonds[:, 0]),
                        np.searchsorted(picked, picked_bonds[:, 1]),
                    )
                )

                n_bonds = len(picked_bonds)
                if n_bonds == 0:
                    self._picked_polydata.SetLines(vtk.vtkCellArray())
                else:
                    cell_array = vtk.vtkCellArray()
                    idxs = np.column_stack((np.full(n_bonds, 2), picked_bonds))
                    cell_array.SetCells(
                        n_bonds, numpy_support.numpy_to_vtkIdTypeArray(idxs.flatten())
                    )
                    self._picked_polydata.SetLines(cell_array)
                return
            case BondCalc.NONE:
                self._picked_polydata.SetLines(vtk.vtkCellArray())
                return

        bonds = self.create_bond_cell_array(
            rs=rs[picked][not_du], covs=self.covs[picked][not_du], not_du=not_du
        )
        self._picked_polydata.SetLines(bonds)

    def on_pick(self, obj, event=None):
        """Event handler when an atom is mouse-picked with the left mouse button"""

        if not self._reader or self.atom_actor is None or self._current_coords is None:
            return

        coords = self._current_coords
        scaled_radii = self._colour_manager.radii * self._atom_scale_factor**2
        idxs = np.arange(len(scaled_radii))

        x, y = obj.GetEventPosition()

        self._renderer.SetDisplayPoint(x, y, 0.0)
        self._renderer.DisplayToWorld()
        x_1 = np.array(self._renderer.GetWorldPoint()[:3])

        self._renderer.SetDisplayPoint(x, y, 1.0)
        self._renderer.DisplayToWorld()
        x_2 = np.array(self._renderer.GetWorldPoint()[:3])

        x_21 = x_2 - x_1
        dist_to_line = np.linalg.norm(
            np.cross(coords - x_1, coords - x_2), axis=1
        ) / np.linalg.norm(x_21)
        selected = dist_to_line < scaled_radii
        dist_x_21 = np.dot(coords - x_1, x_21)

        if not np.any(selected):
            return

        picked_index = idxs[selected][np.argsort(dist_x_21[selected])][0]
        self.clicked_atom_index.emit(picked_index)
        self.pick_atom(picked_index)
        self.picked_atoms_changed.emit(self.picked_atoms)

    def pick_atom(self, picked_atom):
        """Updates the 3D view on atom picked from mouse clicks."""
        self.picked_atoms = self.picked_atoms.symmetric_difference({picked_atom})
        self._picked_polydata.Initialize()
        self.update_picked_polydata()
        self.change_picked_polydata_lines()
        self.create_picked_atoms()
        self.create_picked_bonds()
        self.update_renderer()

    def change_picked(self, picked: set[int]):
        """Changes the picked atoms based on the input atom indices.

        Parameters
        ----------
        picked : set[int]
            The set of picked atom indices.
        """
        self.picked_atoms = picked
        self._picked_polydata.Initialize()
        self.update_picked_polydata()
        self.change_picked_polydata_lines()
        self.create_picked_atoms()
        self.create_picked_bonds()
        self.update_renderer()

    def set_atm_polydata_scalars(self, data: tuple[ByteArray, FloatArray]):
        """Sets the atom and picked atom polydata scalar and array data.

        Parameters
        ----------
        data : tuple[ByteArray, FloatArray]
            A tuple of arrays of atom colours, and radii.
        """
        super().set_atm_polydata_scalars(data)
        self.set_picked_polydata_scalars(data)

    def set_picked_polydata_scalars(self, data: tuple[ByteArray, FloatArray]):
        """Sets the picked polydata scalar and array data.

        Parameters
        ----------
        data : tuple[ByteArray, FloatArray]
            A tuple of arrays of atom colours and radii.
        """
        colours, radii = data

        picked = np.array(sorted(self.picked_atoms))
        if len(picked) == 0:
            return

        colours = np.array(colours)[picked]
        radii = np.array(radii)[picked]

        scalars = ndarray_to_vtkarray(
            colours,
            radii,
            np.arange(self.n_picked_atoms),
        )
        self._picked_polydata.GetPointData().SetScalars(scalars)

        radii_vtk = numpy_support.numpy_to_vtk(radii)
        radii_vtk.SetName("radii")
        colours_vtk = numpy_support.numpy_to_vtk(colours)
        colours_vtk.SetName("colours")
        self._picked_polydata.GetPointData().AddArray(radii_vtk)
        self._picked_polydata.GetPointData().AddArray(colours_vtk)

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

import copy
from collections import ChainMap
from typing import Any

import more_itertools
import numpy as np
import vtk
from qtpy import QtWidgets
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QSizePolicy
from scipy.interpolate import CubicSpline
from scipy.spatial import cKDTree as KDTree
from scipy.spatial.transform import Rotation as R
from vtk.util import numpy_support
from vtkmodules.vtkCommonCore import vtkStringArray
from vtkmodules.vtkRenderingLabel import vtkLabeledDataMapper
from vtkmodules.vtkRenderingCore import vtkActor2D
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Connectivity import distance_calculation
from MDANSE_GUI.MolecularViewer.AtomProperties import (
    AtomProperties,
    ndarray_to_vtkarray,
)
from MDANSE_GUI.MolecularViewer.readers import hdf5wrapper
from MDANSE_GUI.MolecularViewer.TraceWidget import TRACE_PARAMETERS


def array_to_3d_imagedata(data: np.ndarray, spacing: tuple[float, float, float]):
    nx, ny, nz = data.shape
    image = vtk.vtkImageData()
    image.SetDimensions(nx, ny, nz)
    dx, dy, dz = spacing
    image.SetSpacing(dx, dy, dz)
    image.SetExtent(0, nx - 1, 0, ny - 1, 0, nz - 1)
    image.AllocateScalars(vtk.VTK_DOUBLE, 1)
    image.GetPointData().SetScalars(numpy_support.numpy_to_vtk(data.ravel("F")))
    return image


class MolecularViewer(QtWidgets.QWidget):
    """MolecularViewer is a Qt widget containing a 3D viewer
    of molecular structures, currently implemented in VTK."""

    new_max_frames = Signal(int)
    frame_changed = Signal()
    changed_trace = Signal()

    def __init__(self):
        super().__init__()

        self._scale_factor = 0.4

        self._element_database = None

        self._iren = QVTKRenderWindowInteractor(self)
        self._iren.keyPressEvent = lambda *args, **kwargs: None

        # the main render which includes the trajectory
        self._renderer = vtk.vtkRenderer()
        self._renderer.SetLayer(0)
        # create another renderer for the atoms labels, we want the
        # labels to be ontop of the atoms so they can be read more
        # easily
        self._label_renderer = vtk.vtkRenderer()
        self._label_renderer.SetLayer(1)
        self._label_renderer.SetBackgroundAlpha(0)
        self._label_renderer.SetInteractive(False)
        # create another renderer for the axes, we want the axes to
        # be ontop of everything else and fixed to the corner of
        # the screen
        self._axes_renderer = vtk.vtkRenderer()
        self._axes_renderer.SetLayer(2)
        self._axes_renderer.SetBackgroundAlpha(0)
        self._axes_renderer.SetInteractive(False)
        self._axes_renderer.SetViewport(0.0, 0.0, 0.25, 0.25)

        self._iren.GetRenderWindow().SetNumberOfLayers(3)
        self._iren.GetRenderWindow().AddRenderer(self._renderer)
        self._iren.GetRenderWindow().AddRenderer(self._label_renderer)
        self._iren.GetRenderWindow().AddRenderer(self._axes_renderer)

        self._iren.GetRenderWindow().SetPosition((0, 0))

        self._iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self._iren.Enable()

        self._iren.GetRenderWindow()

        layout = QtWidgets.QStackedLayout(self)
        layout.addWidget(self._iren)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # create camera
        self._camera = vtk.vtkCamera()
        # associate camera to renderer
        self._renderer.SetActiveCamera(self._camera)
        self._label_renderer.SetActiveCamera(self._camera)
        self._camera.SetFocalPoint(0, 0, 0)
        self._camera.SetPosition(20, 0, 0)
        self._camera.SetViewUp(0, 0, 1)

        # camera for the axes
        self._axes_camera = vtk.vtkCamera()
        self._axes_renderer.SetActiveCamera(self._axes_camera)
        self._axes_camera.SetFocalPoint(0, 0, 0)
        self._axes_camera.SetPosition(0, 0, 8)

        def update_axes_orientation(caller, event):
            """The axes camera needs to rotate with the main camera."""
            m = self._camera.GetViewTransformMatrix()
            rot = np.array([[m.GetElement(i, j) for j in range(3)] for i in range(3)])
            pos = np.array([0, 0, 8]) @ rot
            up = np.array([0, 1, 0]) @ rot
            self._axes_camera.SetPosition(pos[0], pos[1], pos[2])
            self._axes_camera.SetViewUp(up[0], up[1], up[2])

        self._renderer.GetActiveCamera().AddObserver(
            "ModifiedEvent", update_axes_orientation
        )

        self._n_atoms = 0
        self._n_frames = 0
        self._resolution = 0

        self._atoms_visible = True
        self._bonds_visible = True
        self._cell_visible = True
        self.current_axes_type = "cartesian"
        self.atom_label_type = "none"

        self._iren.Initialize()

        self._atoms = []
        self._surfaces = []
        self._isocontours = []

        self._reader = None

        self._current_frame = 0
        self._current_coords = None

        self.axes_actors = []
        self.atom_label_actor = None
        self.uc_actor = None
        self.atom_actor = None
        self.bond_actor = None

        self._atm_polydata = vtk.vtkPolyData()
        self._uc_polydata = vtk.vtkPolyData()

        self.create_axes()
        self.create_unit_cell()

        self._colour_manager = AtomProperties()
        self.dummy_size = 0.0

    def clear_axes(self):
        if not self.axes_actors:
            return

        for actor in self.axes_actors:
            self._axes_renderer.RemoveActor(actor)

        self.axes_actors = []

    def create_axes(self):
        def add_arrow(color, direction):
            rot = R.align_vectors(direction, [1, 0, 0])[0].as_matrix()

            vtk_matrix = vtk.vtkMatrix4x4()
            for j in range(3):
                for k in range(3):
                    vtk_matrix.SetElement(j, k, rot[j, k])
            vtk_matrix.SetElement(3, 3, 1.0)
            transform = vtk.vtkTransform()
            transform.SetMatrix(vtk_matrix)

            arrow_source = vtk.vtkArrowSource()
            arrow_mapper = vtk.vtkPolyDataMapper()
            arrow_mapper.SetInputConnection(arrow_source.GetOutputPort())
            arrow_actor = vtk.vtkActor()
            arrow_actor.SetMapper(arrow_mapper)
            arrow_actor.GetProperty().SetColor(color)
            arrow_actor.SetUserTransform(transform)
            self.axes_actors.append(arrow_actor)
            self._axes_renderer.AddActor(arrow_actor)

        def add_text(text, coord):
            vec_text = vtk.vtkVectorText()
            vec_text.SetText(text)

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(vec_text.GetOutputPort())

            follower = vtk.vtkFollower()
            follower.SetMapper(mapper)
            follower.SetScale(0.25)
            follower.SetCamera(self._axes_renderer.GetActiveCamera())
            follower.SetPosition(*coord)
            self.axes_actors.append(follower)
            self._axes_renderer.AddActor(follower)

        self.clear_axes()

        if self.current_axes_type == "none":
            return

        if self.current_axes_type == "cartesian":
            add_arrow([1, 0, 0], [1, 0, 0])
            add_arrow([0, 1, 0], [0, 1, 0])
            add_arrow([0, 0, 1], [0, 0, 1])
            add_text("X", [1, 0, 0])
            add_text("Y", [0, 1, 0])
            add_text("Z", [0, 0, 1])
            return

        if self._reader is None:
            return
        uc = self._reader.read_pbc(self._current_frame)
        if uc is None:
            return

        if self.current_axes_type == "direct":
            matrix = uc.direct.copy()
            labels = ["a", "b", "c"]
        elif self.current_axes_type == "reciprocal":
            matrix = uc.inverse.copy().T
            labels = ["a*", "b*", "c*"]

        matrix /= np.linalg.norm(matrix, axis=1)[:, np.newaxis]
        for i, label in enumerate(labels):
            add_arrow(np.eye(3)[i], matrix[i])
            add_text(label, matrix[i])

    def change_axes(self, axes_option: str):
        """Changes the axes type in the 3D viewer.

        Parameters
        ----------
        axes_option : str
            The axes type that will be used.
        """
        self.current_axes_type = axes_option
        self.create_axes()
        self.update_renderer()

    def clear_atom_labels(self):
        """Clears the atoms labels."""
        if not self.atom_label_actor:
            return

        self._label_renderer.RemoveActor(self.atom_label_actor)
        self.atom_label_actor = None

    def create_atom_labels(self):
        """Creates atom label actors, setting the text to the chosen
        atom_label_type.
        """
        self.clear_atom_labels()

        if self._reader is None:
            return

        if self.atom_label_type == "index":
            labels = list(range(self._n_atoms))
        elif self.atom_label_type == "label":
            label_dict = self._reader._trajectory.chemical_system._labels
            if not label_dict:
                return
            keys = more_itertools.run_length.decode(
                ((k, len(v)) for k, v in label_dict.items())
            )
            labels = sorted(keys, key=label_dict.__getitem__)
        elif self.atom_label_type == "atom":
            labels = self._atoms
        elif self.atom_label_type == "molecule":
            label_dict = self._reader._trajectory.chemical_system._clusters
            if not label_dict:
                return
            label_dict = {
                k: list(more_itertools.collapse(v)) for k, v in label_dict.items()
            }
            keys = more_itertools.run_length.decode(
                ((k, len(v)) for k, v in label_dict.items())
            )
            labels = sorted(keys, key=label_dict.__getitem__)
        else:
            return

        if len(labels) != self._n_atoms:
            return

        labels_vtk = vtkStringArray()
        labels_vtk.SetName("labels")
        labels_vtk.SetNumberOfValues(self._n_atoms)
        for i, label in enumerate(labels):
            labels_vtk.SetValue(i, str(label))
        self._atm_polydata.GetPointData().AddArray(labels_vtk)

        label_mapper = vtkLabeledDataMapper()
        label_mapper.SetInputData(self._atm_polydata)
        label_mapper.SetLabelModeToLabelFieldData()
        label_mapper.SetFieldDataName("labels")
        text_prop = label_mapper.GetLabelTextProperty()
        text_prop.SetFontSize(12)

        actor = vtkActor2D()
        actor.SetMapper(label_mapper)
        self.atom_label_actor = actor
        self._label_renderer.AddActor(actor)

    def update_atom_labels(self):
        """Updates the atom label follwer positions."""
        if (
            self._reader is None
            or self._current_coords is None
            or not self.atom_label_actors
            or self.atom_label_type == "none"
        ):
            return

        for follower, coord in zip(
            self.atom_label_actors,
            self._current_coords,
            strict=True,
        ):
            follower.SetPosition(*coord)

    def change_atom_labels(self, label_option: str) -> None:
        """Changes the atoms label text.

        Parameters
        ----------
        label_option : str
            The atom label option.
        """
        self.atom_label_type = label_option
        self.create_atom_labels()
        self.update_renderer()

    def clear_unit_cell(self):
        if not self.uc_actor:
            return

        self._renderer.RemoveActor(self.uc_actor)
        self.uc_actor = None

    def create_unit_cell(self):
        self.clear_unit_cell()

        if not self._cell_visible:
            return

        uc_mapper = vtk.vtkPolyDataMapper()
        uc_mapper.SetInputData(self._uc_polydata)
        uc_mapper.ScalarVisibilityOn()
        uc_actor = vtk.vtkLODActor()
        uc_actor.GetProperty().SetLineWidth(3 * self._scale_factor)
        uc_actor.SetMapper(uc_mapper)
        self._renderer.AddActor(uc_actor)
        self.uc_actor = uc_actor

    def update_uc_polydata(self):
        """Updates the unit cell actor using the unit cell parameters
        from the current trajectory frame.
        """
        if self._reader is None:
            return

        uc = self._reader.read_pbc(self._current_frame)
        if self._cell_visible and uc is not None:
            # update the unit cell
            a = uc.a_vector
            b = uc.b_vector
            c = uc.c_vector
            uc_points = vtk.vtkPoints()
            uc_points.SetNumberOfPoints(8)
            for i, v in enumerate([[0, 0, 0], a, b, c, a + b, a + c, b + c, a + b + c]):
                uc_points.SetPoint(i, *v)
            self._uc_polydata.SetPoints(uc_points)

            uc_lines = vtk.vtkCellArray()
            for i, j in [
                (0, 1),
                (0, 2),
                (0, 3),
                (1, 4),
                (1, 5),
                (4, 7),
                (2, 4),
                (2, 6),
                (5, 7),
                (3, 5),
                (3, 6),
                (6, 7),
            ]:
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, i)
                line.GetPointIds().SetId(1, j)
                uc_lines.InsertNextCell(line)
            self._uc_polydata.SetLines(uc_lines)

    def clear_atoms(self):
        if not self.atom_actor:
            return

        self._renderer.RemoveActor(self.atom_actor)
        self.atom_actor = None

    def create_atoms(self, ball_opacity: float = 1.0):
        self.clear_atoms()

        if not self._atoms_visible:
            return

        actor = self.create_atom_actor(self._atm_polydata, ball_opacity)
        self._renderer.AddActor(actor)
        self.atom_actor = actor

    def clear_bonds(self):
        if not self.bond_actor:
            return

        self._renderer.RemoveActor(self.bond_actor)
        self.bond_actor = None

    def create_bonds(self, line_opacity: float = 1.0):
        self.clear_bonds()

        if not self._bonds_visible:
            return

        actor = self.create_bond_actor(self._atm_polydata, line_opacity)
        self._renderer.AddActor(actor)
        self.bond_actor = actor

    def create_atom_actor(
        self,
        polydata: vtk.vtkPolyData,
        ball_opacity: float = 1.0,
    ) -> vtk.vtkLODActor:
        """Creates VTK actors which visualise atoms.

        Parameters
        ----------
        polydata : vtk.vtkPolyData
            VTK object storing the atom properties used in 3D view (colour, radius)
        ball_opacity : float, optional
            opacity (alpha) of atom spheres, by default 1.0

        Returns
        -------
            Two vtk.vtkLODActor instances, for atoms

        """
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(0, 0, 0)
        sphere.SetRadius(self._scale_factor)
        sphere.SetThetaResolution(self._resolution)
        sphere.SetPhiResolution(self._resolution)

        glyph_mapper = vtk.vtkGlyph3DMapper()
        glyph_mapper.SetInputData(polydata)
        glyph_mapper.SetSourceConnection(sphere.GetOutputPort())

        glyph_mapper.ScalingOn()
        glyph_mapper.SetScaleModeToScaleByMagnitude()
        glyph_mapper.SetScaleArray("radii")
        glyph_mapper.SetScaleFactor(self._scale_factor)

        glyph_mapper.ScalarVisibilityOn()
        glyph_mapper.SelectColorArray("colours")
        glyph_mapper.ColorByArrayComponent("colours", 1)
        glyph_mapper.SetLookupTable(self._colour_manager._lut)
        glyph_mapper.SetScalarRange(
            polydata.GetPointData().GetArray("colours").GetRange()
        )

        ball_actor = vtk.vtkLODActor()
        ball_actor.SetMapper(glyph_mapper)
        ball_actor.GetProperty().SetAmbient(0.2)
        ball_actor.GetProperty().SetDiffuse(0.5)
        ball_actor.GetProperty().SetSpecular(0.3)
        ball_actor.GetProperty().SetOpacity(ball_opacity)
        ball_actor.SetNumberOfCloudPoints(30000)
        return ball_actor

    def create_bond_actor(
        self,
        polydata: vtk.vtkPolyData,
        line_opacity: float = 1.0,
    ) -> vtk.vtkLODActor:
        """Creates VTK actors which visualise bonds.

        Parameters
        ----------
        polydata : vtk.vtkPolyData
            VTK object storing the atom properties used in 3D view (colour, radius)
        line_opacity : float, optional
            opacity (alpha) of bond lines, by default 1.0

        Returns
        -------
            Two vtk.vtkLODActor instances, for bonds
        """
        line_mapper = vtk.vtkPolyDataMapper()
        line_mapper.SetInputData(polydata)
        line_mapper.SetLookupTable(self._colour_manager._lut)
        line_mapper.ScalarVisibilityOn()
        line_mapper.ColorByArrayComponent("scalars", 1)
        line_actor = vtk.vtkLODActor()
        line_actor.GetProperty().SetLineWidth(3 * self._scale_factor)
        line_actor.SetMapper(line_mapper)
        line_actor.GetProperty().SetAmbient(0.2)
        line_actor.GetProperty().SetDiffuse(0.5)
        line_actor.GetProperty().SetSpecular(0.3)
        line_actor.GetProperty().SetOpacity(line_opacity)
        return line_actor

    def update_atm_polydata(self):
        """Triggers an update of the VTK actors, making them use the
        latest parameters from the input widgets.
        """
        if self._current_coords is None:
            return

        if self._atoms_visible or self._bonds_visible:
            atoms = vtk.vtkPoints()
            atoms.SetData(numpy_support.numpy_to_vtk(self._current_coords))
            self._atm_polydata.SetPoints(atoms)

        if self._bonds_visible:
            # do not bond atoms to dummy atoms
            rs = self._current_coords[self.not_du]
            bonds, bonds_exist = self.create_bond_cell_array(
                rs, self.covs[self.not_du], self.not_du
            )
            if bonds_exist:
                self._atm_polydata.SetLines(bonds)
                return

    def create_bond_cell_array(
        self,
        rs: np.ndarray,
        covs: np.typing.NDArray[float],
        not_du: np.typing.NDArray[bool],
        tolerance: float = 0.04,
    ):
        """Finds the pairs of atoms which should be connected by bonds,
        based on their positions, covalent radii and tolerance of distances.
        Dummy atoms can be excluded from forming bonds.

        This does NOT consider periodic boundary conditions.

        Parameters
        ----------
        rs : np.ndarray
            an (N,3) array of atom coordinates
        covs : Iterable[float]
            an (N,) array of covalent radii
        not_du : Iterable[bool]
            an (N,) list of boolean flags. A dummy atom is marked with False
        tolerance : float, optional
            bond is formed if |pos_1 - pos_2| < radius_1 + radius_2 + tolerance.
            By default 0.04 nm

        Returns
        -------
        vtk.vtkCellArray, bool
            a VTK array of pairs of atom indices, and a flag True if some bonds were found
        """
        # determine and set bonds without PBC applied
        bonds = vtk.vtkCellArray()

        dist, js, ks, _ = distance_calculation(rs, 2 * np.max(covs) + tolerance)
        sum_radii = (covs[js] + covs[ks] + tolerance) ** 2
        js = js[(dist > 0) & (dist < sum_radii)]
        ks = ks[(dist > 0) & (dist < sum_radii)]
        ls = not_du[js]
        ms = not_du[ks]

        n_points = len(ls)
        idxs = np.zeros((n_points, 3), dtype=np.int64)
        idxs[:, 0] = 2
        idxs[:, 1] = ls
        idxs[:, 2] = ms
        bonds.SetCells(n_points, numpy_support.numpy_to_vtkIdTypeArray(idxs.flatten()))

        return bonds, n_points > 0

    def _new_trajectory_object(self, fname: str, trajectory: Trajectory):
        """Creates and sets a new trajectory reader for the input trajectory.

        Parameters
        ----------
        fname : str
            trajectory file name
        data : Trajectory
            instance of the MDANSE input trajectory handler
        """
        reader = hdf5wrapper.HDF5Wrapper(fname, trajectory, trajectory.chemical_system)
        if (self._reader is not None) and (reader.filename == self._reader.filename):
            return
        self.set_reader(reader)

    @Slot(float)
    def _new_scaling(self, scale_factor: float):
        """Update the scale factor by which all the atom radii are multiplied.

        Scale factor 1.0 means that the covalent radii of atoms are used as
        radii of the spheres in the 3D view. By default the atom size is scaled
        down to allow the user to see atoms behind the first layer and the
        bonds between atoms.

        Parameters
        ----------
        scale_factor : float
            Sphere radii in 3D view will be multiplied by this factor
        """
        self._scale_factor = scale_factor
        if self._reader is not None:
            self.create_atoms()
            self.update_renderer()

    def _new_visibility(self, flags: list[bool]):
        """Takes the new values of boolean flags which make
        different actors in the 3D scene (in)visible.

        Parameters
        ----------
        flags : List[bool]
            Each actor will be visible if its flag is True.
        """
        self._atoms_visible = flags[0]
        self._bonds_visible = flags[1]
        self._cell_visible = flags[2]
        self.create_unit_cell()
        self.update_atm_polydata()
        self.create_atoms()
        self.create_bonds()
        self.update_renderer()

    def trace_from_dialog(self, params: dict[str, Any]):
        """Passes the input parameter dictionary to the method
        which draws an isosurface in the 3D view.

        Parameters
        ----------
        params : dict[str, Any]
            dictionary of input parameters from TraceWidget.py
        """
        self._draw_isosurface(params["atom_number"], params)

    def delete_isosurface_from_dialog(self, trace_number: int):
        """Deletes from the 3D scene the isosurface with a specified
        index, if it exists.

        Parameters
        ----------
        trace_number : int
            index of the isosurface
        """
        try:
            surface = self._surfaces[trace_number]
        except IndexError:
            return
        surface.VisibilityOff()
        surface.ReleaseGraphicsResources(self._iren.GetRenderWindow())
        self._renderer.RemoveActor(surface)
        self._surfaces.pop(trace_number)
        self.update_renderer()
        self.changed_trace.emit()

    def _draw_isosurface(self, index: int, params: dict[str, Any] | None = None):
        """Calculates the total volume used by an atom in the trajectory
        and draws an isosurface around it.

        Parameters
        ----------
        index : int
            index of the atom in the system
        params : Dict[str, Any], optional
            A dictionary of isosurface parameters. If None, defaults from
            TraceWidget.py will be used instead.
        """

        if self._reader is None:
            return

        LOG.info(f"Computing isosurface of atom {index}")
        if params is None:
            params = copy.copy(TRACE_PARAMETERS)
        else:
            params = ChainMap(params, TRACE_PARAMETERS)

        traj_sampling = params["traj_samples"]
        smearing_factor = params["smearing_factor"]
        grid_step = params["grid_sampling"]
        rgb = params["surface_colour"]
        opacity = params["surface_opacity"]
        trace_isovalue = params["trace_isovalue"]

        # interpolate the trajectory and sample to reduce the number of
        # positions that will be evaluated or if there are only a few
        # positions then interpolate to ensure that the atom trace
        # is continuous
        coords = self._reader.read_atom_trajectory(index)
        idxs1 = np.linspace(0, 1, num=coords.shape[0])
        idxs2 = np.linspace(0, 1, num=traj_sampling)
        f_x = CubicSpline(idxs1, coords[:, 0])
        f_y = CubicSpline(idxs1, coords[:, 1])
        f_z = CubicSpline(idxs1, coords[:, 2])
        coords = np.stack((f_x(idxs2), f_y(idxs2), f_z(idxs2)), axis=-1)

        element = self._reader._atom_types[index]
        radius = smearing_factor * self._reader._trajectory.get_atom_property(
            element, "vdw_radius"
        )

        upper_limit = np.max(coords, axis=0) + radius
        lower_limit = np.min(coords, axis=0) - radius
        span = upper_limit - lower_limit
        grid_steps = list((span // grid_step).astype(int))

        xs = np.linspace(lower_limit[0], upper_limit[0], grid_steps[0])
        ys = np.linspace(lower_limit[1], upper_limit[1], grid_steps[1])
        zs = np.linspace(lower_limit[2], upper_limit[2], grid_steps[2])
        grid = np.stack(list(np.meshgrid(xs, ys, zs, indexing="ij")), axis=-1).reshape(
            -1, 3
        )

        tree = KDTree(grid)
        contacts = tree.query_ball_point(coords, radius, workers=-1)
        n_dists = sum([len(i) for i in contacts])

        js = np.zeros(n_dists, dtype=int)
        ks = np.zeros(n_dists, dtype=int)
        start = 0
        for i, idxs in enumerate(contacts):
            n_idxs = len(idxs)
            if n_idxs == 0:
                continue
            js[start : start + n_idxs] = i
            ks[start : start + n_idxs] = idxs
            start += n_idxs

        diff = coords[js] - grid[ks]
        sq_dist = np.sum(diff**2, axis=-1)
        exp_res = np.exp(-sq_dist / (2 * (radius / 3) ** 2))

        vals = np.zeros(grid.shape[0])
        np.add.at(vals, ks, exp_res)
        vals = vals / np.max(vals)
        vals = vals.reshape(grid_steps)

        self._image = array_to_3d_imagedata(vals, (grid_step, grid_step, grid_step))

        new_isocontour = vtk.vtkMarchingContourFilter()
        new_isocontour.UseScalarTreeOn()
        new_isocontour.ComputeNormalsOn()
        new_isocontour.SetInputData(self._image)
        new_isocontour.SetValue(0, trace_isovalue)

        self._depthSort = vtk.vtkDepthSortPolyData()
        self._depthSort.SetInputConnection(new_isocontour.GetOutputPort())
        self._depthSort.SetDirectionToBackToFront()
        self._depthSort.SetVector(1, 1, 1)
        self._depthSort.SetCamera(self._camera)
        self._depthSort.SortScalarsOn()
        self._depthSort.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self._depthSort.GetOutputPort())
        mapper.ScalarVisibilityOff()
        mapper.Update()

        new_surface = vtk.vtkActor()
        new_surface.SetMapper(mapper)
        new_surface.GetProperty().SetColor(rgb)
        new_surface.GetProperty().SetOpacity(opacity)
        new_surface.PickableOff()

        new_surface.GetProperty().SetRepresentationToSurface()

        new_surface.GetProperty().SetInterpolationToGouraud()
        new_surface.GetProperty().SetSpecular(0.4)
        new_surface.GetProperty().SetSpecularPower(10)

        self._renderer.AddActor(new_surface)

        new_surface.SetPosition(*lower_limit)
        self._surfaces.append(new_surface)
        self._isocontours.append(new_isocontour)

        self.update_renderer()

        LOG.info("Finished calculating the trace of atom %d", index)
        self.changed_trace.emit()

    def clear_panel(self):
        """Clears the Molecular Viewer panel"""
        self.on_clear_atomic_trace()

        self._atm_polydata.Initialize()
        self._uc_polydata.Initialize()

        self.clear_atom_labels()
        self.clear_atoms()
        self.clear_bonds()
        self.clear_unit_cell()
        self.create_axes()

        self.update_renderer()

        self._reader = None

        # set everything to some empty/zero value
        self._n_atoms = 0
        self._n_frames = 0
        self.new_max_frames.emit(0)
        self._atoms = []
        self._atom_colours = []
        self._current_frame = 0

        # clear the atom properties table
        self._colour_manager.removeRows(0, self._colour_manager.rowCount())

    def on_change_atomic_trace_opacity(self, surface_index: int, opacity: float):
        """This method should allow changing the opacity of an already existing
        isosurface. Currently not connected to any widgets.

        Parameters
        ----------
        surface_index : int
            index of the isosurface in self._surfaces
        opacity : float
            new opacity value for the isosurface
        """

        if surface_index >= len(self._surfaces):
            return

        self._surfaces[surface_index].GetProperty().SetOpacity(opacity)
        self.update_renderer()

    def on_change_atomic_trace_isocontour_level(self, surface_index: int, level: float):
        """This method should allow changing the isocontour level for an already existing
        isosurface. Currently not connected to any widgets.

        Parameters
        ----------
        surface_index : int
            index of the isosurface in self._surfaces
        level : float
            new value of isocontour level
        """

        if surface_index >= len(self._surfaces):
            return

        self._isocontours[surface_index].SetValue(0, level)
        self._isocontours[surface_index].Update()
        self.update_renderer()

    def on_change_atomic_trace_rendering_type(
        self, surface_index: int, rendering_type: str
    ):
        """Method for changing the rendering style of an existing isosurface.
        Currently not connected to any widgets.

        Parameters
        ----------
        surface_index : int
            index of the isosurface in self._surfaces
        rendering_type : str
            one of the following: wireframe, surface, points
        """

        if surface_index >= len(self._surfaces):
            return

        surface = self._surfaces[surface_index]

        if rendering_type == "wireframe":
            surface.GetProperty().SetRepresentationToWireframe()
        elif rendering_type == "surface":
            surface.GetProperty().SetRepresentationToSurface()
        elif rendering_type == "points":
            surface.GetProperty().SetRepresentationToPoints()
            surface.GetProperty().SetPointSize(3)
        else:
            return

        self.update_renderer()

    def on_clear_atomic_trace(self):
        """Event handler called when the user select the 'Atomic trace -> Clear' main menu item"""

        if not self._surfaces:
            return

        for surface in self._surfaces:
            surface.VisibilityOff()
            surface.ReleaseGraphicsResources(self._iren.GetRenderWindow())
            self._renderer.RemoveActor(surface)
        self.update_renderer()

        self._surfaces = []
        self.changed_trace.emit()

    def create_trace_dialog(self, viewer_controls):
        """Creates and connects an additional panel of the GUI which contains
        an instance of TraceWidget.

        Parameters
        ----------
        viewer_controls : ViewerControls
            instance of the ViewerControls widget from View3D
        """
        self._trace_dialog = viewer_controls.createTracePanel(self)
        self._trace_dialog.new_atom_trace.connect(self.trace_from_dialog)
        self._trace_dialog.remove_atom_trace.connect(self.delete_isosurface_from_dialog)
        self.changed_trace.connect(self._trace_dialog.update_limits)

    @Slot(int)
    def set_coordinates(self, frame: int):
        """Changes the atom positions in the 3D view to those from
        the selected frame of the trajectory.

        Parameters
        ----------
        frame : int
            index of the trajectory frame
        """
        if self._reader is None:
            return

        self._current_frame = frame % self._reader.n_frames
        self._current_coords = self._reader.read_frame(self._current_frame)

        # update the atoms
        self.update_atm_polydata()
        self.update_uc_polydata()
        self.create_axes()

        # Update the view.
        self.update_renderer()
        self.frame_changed.emit()

    def set_reader(self, reader):
        """Sets the input object to be the new source of atom data for
        the 3D viewer.

        Parameters
        ----------
        reader : IReader
            typically an instance of HDF5Wrapper from MolecularViewer
        """
        self._reader = reader

        self._element_database = self._reader._trajectory
        self._n_atoms = self._reader.n_atoms
        self._n_frames = self._reader.n_frames
        self._current_frame = min(self._current_frame, self._n_frames - 1)

        self._atoms = self._reader.atom_types

        # Hack for reducing objects resolution when the system is big
        self._resolution = int(np.sqrt(3000000.0 / self._n_atoms))
        self._resolution = min(self._resolution, 10)
        self._resolution = max(self._resolution, 4)

        self._colour_manager.reinitialise_from_database(
            self._atoms, self._element_database, self.dummy_size
        )
        self._colour_manager.rebuild_colours()
        # this returns a list of indices, mapping colours to atoms

        self.du_log = np.array(
            [
                self._element_database.get_atom_property(at, "dummy") == 0
                for at in self._reader.atom_types
            ]
        )
        self.not_du = np.array(
            [
                i
                for i, at in enumerate(self._reader.atom_types)
                if self._element_database.get_atom_property(at, "dummy") == 0
            ]
        )
        self.covs = np.array(
            [
                self._element_database.get_atom_property(at, "covalent_radius")
                for at in self._reader.atom_types
            ]
        )

        self._current_coords = self._reader.read_frame(self._current_frame)

        self._atm_polydata.Initialize()
        self._uc_polydata.Initialize()
        self.set_atm_polydata_scalars(
            (
                self._colour_manager.colours,
                self._colour_manager.radii,
                np.arange(self._colour_manager._total_length),
            )
        )

        self.update_atm_polydata()
        self.update_uc_polydata()

        self.create_unit_cell()
        self.create_atom_labels()
        self.create_atoms()
        self.create_bonds()
        self.create_axes()

        self._renderer.ResetCamera()
        self._camera.SetWindowCenter(0.0, 0.0)
        self.update_renderer()

        self.new_max_frames.emit(self._n_frames - 1)
        self._trace_dialog.update_limits()

    @Slot(object)
    def take_atom_properties(self, data):
        self.set_atm_polydata_scalars(data)
        self.create_atoms()
        self.create_bonds()
        self.update_renderer()

    def set_atm_polydata_scalars(self, data):
        colours, radii, numbers = data
        scalars = ndarray_to_vtkarray(colours, radii, numbers)
        self._atm_polydata.GetPointData().SetScalars(scalars)

        radii_vtk = numpy_support.numpy_to_vtk(radii)
        radii_vtk.SetName("radii")
        colours_vtk = numpy_support.numpy_to_vtk(colours)
        colours_vtk.SetName("colours")
        self._atm_polydata.GetPointData().AddArray(radii_vtk)
        self._atm_polydata.GetPointData().AddArray(colours_vtk)

    def update_renderer(self):
        self._iren.GetRenderWindow().Render()
        self._iren.Render()

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
import copy
from typing import Any, Optional

import numpy as np
import vtk
from qtpy import QtWidgets
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QSizePolicy
from scipy.spatial import cKDTree as KDTree
from vtk.util import numpy_support
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor

from MDANSE.MLogging import LOG
from MDANSE.MolecularDynamics.Trajectory import Trajectory
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
    if vtk.vtkVersion.GetVTKMajorVersion() < 6:
        image.SetScalarTypeToDouble()
        image.SetNumberOfScalarComponents(1)
    else:
        image.AllocateScalars(vtk.VTK_DOUBLE, 1)

    for (i, j, k), val in np.ndenumerate(data):
        image.SetScalarComponentFromDouble(i, j, k, 0, val)

    return image


def smear_grid(grid: np.ndarray, fine_sampling: int) -> np.ndarray:
    """Include atom radius effect in the array of atom counts on a grid.

    Parameters
    ----------
    grid : np.ndarray
        a 3D histogram of atom positions over time
    fine_sampling : int
        the fraction of the atom radius defining the binning grid

    Returns
    -------
    np.ndarray
        a 3D histogram of the volume taken by the atom
    """
    if fine_sampling < 2:
        return grid
    final_histogram = grid.copy()
    for _ in range(1, fine_sampling):
        n = 1
        new_histogram = np.zeros_like(grid)
        new_histogram[:, :, n:] += final_histogram[:, :, :-n]
        new_histogram[:, :, :-n] += final_histogram[:, :, n:]
        new_histogram[:, n:, :] += final_histogram[:, :-n, :]
        new_histogram[:, :-n, :] += final_histogram[:, n:, :]
        new_histogram[n:, :, :] += final_histogram[:-n, :, :]
        new_histogram[:-n, :, :] += final_histogram[n:, :, :]
        final_histogram += new_histogram
    return final_histogram


class MolecularViewer(QtWidgets.QWidget):
    """MolecularViewer is a Qt widget containing a 3D viewer
    of molecular structures, currently implemented in VTK."""

    new_max_frames = Signal(int)
    changed_trace = Signal()

    def __init__(self):
        super().__init__()

        self._scale_factor = 0.4

        self._element_database = None

        self._iren = QVTKRenderWindowInteractor(self)

        def dummy_method(self, ev=None):
            pass

        setattr(self._iren, "keyPressEvent", dummy_method)

        self._renderer = vtk.vtkRenderer()

        self._iren.GetRenderWindow().AddRenderer(self._renderer)

        self._iren.GetRenderWindow().SetPosition((0, 0))

        self._iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self._iren.Enable()

        self._iren.GetRenderWindow()

        self.axes_actor = vtkAxesActor()
        self.axes_actor.AxisLabelsOn()
        self.axes_actor.SetShaftTypeToCylinder()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self._iren.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.25, 0.25)
        self.axes_widget.SetEnabled(True)
        self.axes_widget.InteractiveOff()

        self.atom_actor = None
        self._last_coords = None

        layout = QtWidgets.QStackedLayout(self)
        layout.addWidget(self._iren)
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        # create camera
        self._camera = vtk.vtkCamera()
        # associate camera to renderer
        self._renderer.SetActiveCamera(self._camera)
        self._camera.SetFocalPoint(0, 0, 0)
        self._camera.SetPosition(0, 0, 20)

        self._n_atoms = 0
        self._n_frames = 0
        self._resolution = 0

        self._atoms_visible = True
        self._bonds_visible = True
        self._axes_visible = True
        self._cell_visible = True

        self._iren.Initialize()

        self._atoms = []

        self._polydata = None
        self._polydata_bonds_exist = False
        self._uc_polydata = None

        self._surfaces = []
        self._isocontours = []

        self._reader = None

        self._current_frame = 0

        self._colour_manager = AtomProperties()
        self.dummy_size = 0.0

        self.reset_camera = False

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
        self.set_reader(reader)

    @Slot(float)
    def _new_scaling(self, scale_factor: float):
        """Updates the scale factor by which all the atom radii are multiplied.
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
        self._axes_visible = flags[2]
        self._cell_visible = flags[3]
        self.axes_widget.SetEnabled(self._axes_visible)
        result = self.set_coordinates(self._current_frame)
        if result is False:
            self.update_renderer()

    def trace_from_dialog(self, params: dict[str, Any]):
        """Passes the input parameter dictionary to the method
        which draws an isosurface in the 3D view.

        Parameters
        ----------
        params : Dict[str, Any]
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
        else:
            surface.VisibilityOff()
            surface.ReleaseGraphicsResources(self._iren.GetRenderWindow())
            self._renderer.RemoveActor(surface)
            self._surfaces.pop(trace_number)
            self._iren.Render()
            self.changed_trace.emit()

    def _draw_isosurface(self, index: int, params: Optional[dict[str, Any]] = None):
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
        fine_sampling = params.get("fine_sampling", 5)
        rgb = params.get("surface_colour", (0, 0.5, 0.75))
        opacity = params.get("surface_opacity", 0.5)
        trace_cutoff = params.get("trace_cutoff", 90)

        coords = self._reader.read_atom_trajectory(index)
        element = self._reader._atom_types[index]
        radius = self._reader._trajectory.get_atom_property(element, "covalent_radius")
        upper_limit = np.max(coords, axis=0) + radius
        lower_limit = np.min(coords, axis=0) - radius
        grid_step = radius / fine_sampling

        span = upper_limit - lower_limit
        grid_steps = list((span // grid_step).astype(int))
        gdim = tuple(grid_steps[0:3])
        grid = np.zeros(gdim, dtype=np.int32)

        indices = ((coords - lower_limit.reshape((1, 3))) // grid_step).astype(int)
        unique_indices, counts = np.unique(indices, return_counts=True, axis=0)
        grid[tuple(unique_indices.T)] += counts
        self._atomic_trace_histogram = smear_grid(grid, fine_sampling)

        self._image = array_to_3d_imagedata(
            self._atomic_trace_histogram, (grid_step, grid_step, grid_step)
        )
        isovalue = np.percentile(self._atomic_trace_histogram, trace_cutoff)

        new_isocontour = vtk.vtkMarchingContourFilter()
        new_isocontour.UseScalarTreeOn()
        new_isocontour.ComputeNormalsOn()
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            new_isocontour.SetInput(self.image)
        else:
            new_isocontour.SetInputData(self._image)
        new_isocontour.SetValue(0, isovalue)

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

        new_surface.SetPosition(lower_limit[0], lower_limit[1], lower_limit[2])
        self._surfaces.append(new_surface)
        self._isocontours.append(new_isocontour)

        self._iren.Render()

        LOG.info(f"Finished calculating the trace of atom {index}")
        self.changed_trace.emit()

    def create_all_actors(self) -> list[vtk.vtkActor]:
        """Collects all the VTK actors that should be shown in 3D view.

        Returns
        -------
        List[vtk.vtkActor]
            typically actors for unit cell, bonds and atoms
        """
        actors = []
        if self._polydata is None:
            return actors

        line_actor, ball_actor = self.create_traj_actors(self._polydata)
        if self._cell_visible:
            uc_actor = self.create_uc_actor()
            actors.append(uc_actor)
        if self._bonds_visible and self._polydata_bonds_exist:
            actors.append(line_actor)
        if self._atoms_visible:
            actors.append(ball_actor)
            self.atom_actor = ball_actor
        else:
            self.atom_actor = None
        return actors

    def create_uc_actor(self):
        uc_mapper = vtk.vtkPolyDataMapper()
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            uc_mapper.SetInput(self._uc_polydata)
        else:
            uc_mapper.SetInputData(self._uc_polydata)
        uc_mapper.ScalarVisibilityOn()
        uc_actor = vtk.vtkLODActor()
        uc_actor.GetProperty().SetLineWidth(3 * self._scale_factor)
        uc_actor.SetMapper(uc_mapper)
        return uc_actor

    def create_traj_actors(
        self,
        polydata: vtk.vtkPolyData,
        line_opacity: float = 1.0,
        ball_opacity: float = 1.0,
    ) -> list[vtk.vtkActor]:
        """Creates VTK actors which visualise atoms and bonds.

        Parameters
        ----------
        polydata : vtk.vtkPolyData
            VTK object storing the atom properties used in 3D view (colour, radius)
        line_opacity : float, optional
            opacity (alpha) of bond lines, by default 1.0
        ball_opacity : float, optional
            opacity (alpha) of atom spheres, by default 1.0

        Returns
        -------
            Two vtk.vtkLODActor instances, for bonds and atoms

        """
        line_mapper = vtk.vtkPolyDataMapper()
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            line_mapper.SetInput(polydata)
        else:
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

        temp_radius = float(1.0 * self._scale_factor)
        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(0, 0, 0)
        sphere.SetRadius(temp_radius)
        sphere.SetThetaResolution(self._resolution)
        sphere.SetPhiResolution(self._resolution)
        glyph = vtk.vtkGlyph3D()
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            glyph.SetInput(polydata)
        else:
            glyph.SetInputData(polydata)

        temp_scale = float(1.0 * self._scale_factor)
        glyph.SetScaleModeToScaleByScalar()
        glyph.SetColorModeToColorByScalar()
        glyph.SetScaleFactor(temp_scale)
        glyph.SetSourceConnection(sphere.GetOutputPort())
        glyph.SetIndexModeToScalar()
        sphere_mapper = vtk.vtkPolyDataMapper()
        sphere_mapper.SetLookupTable(self._colour_manager._lut)
        sphere_mapper.SetScalarRange(polydata.GetScalarRange())
        sphere_mapper.SetInputConnection(glyph.GetOutputPort())
        sphere_mapper.ScalarVisibilityOn()
        sphere_mapper.ColorByArrayComponent("scalars", 1)
        ball_actor = vtk.vtkLODActor()
        ball_actor.SetMapper(sphere_mapper)
        ball_actor.GetProperty().SetAmbient(0.2)
        ball_actor.GetProperty().SetDiffuse(0.5)
        ball_actor.GetProperty().SetSpecular(0.3)
        ball_actor.GetProperty().SetOpacity(ball_opacity)
        ball_actor.SetNumberOfCloudPoints(30000)
        return [line_actor, ball_actor]

    def clear_trajectory(self, clear_isosurfaces=True):
        """Removes all the actors from the 3D view.

        When updating the animation frame, it usually makes sense to keep
        the isosurfaces in the view, which is allowed by the keyword argument.

        Parameters
        ----------
        clear_isosurfaces : bool, optional
            if True, isosurfaces are removed too, by default True
        """

        if not hasattr(self, "_actors"):
            return
        if self._actors is None:
            return

        if clear_isosurfaces:
            self.on_clear_atomic_trace()
        self._actors.VisibilityOff()
        self._actors.ReleaseGraphicsResources(self.get_render_window())
        self._renderer.RemoveActor(self._actors)
        self.atom_actor = None

        del self._actors

    def clear_panel(self) -> None:
        """Clears the Molecular Viewer panel"""
        self.clear_trajectory()

        self._reader = None

        # set everything to some empty/zero value
        self._n_atoms = 0
        self._n_frames = 0
        self.new_max_frames.emit(0)
        self._atoms = []
        self._atom_colours = []
        self._current_frame = 0
        self.reset_all_polydata()

        self.update_renderer()

        # clear the atom properties table
        self._colour_manager.removeRows(0, self._colour_manager.rowCount())

    def reset_all_polydata(self):
        self._polydata = vtk.vtkPolyData()
        self._uc_polydata = vtk.vtkPolyData()

    def update_all_polydata(self):
        self.update_polydata()
        self.update_uc_polydata()

    def update_polydata(self):
        """Triggers an update of the VTK actors, making them use the
        latest parameters from the input widgets.
        """
        coords = self._reader.read_frame(self._current_frame)
        self._last_coords = coords

        if self._atoms_visible or self._bonds_visible:
            atoms = vtk.vtkPoints()
            atoms.SetData(numpy_support.numpy_to_vtk(coords))
            self._polydata.SetPoints(atoms)

        if self._bonds_visible:
            # do not bond atoms to dummy atoms
            rs = coords[self.not_du]
            bonds, bonds_exist = self.create_bond_cell_array(
                rs, self.covs[self.not_du], self.not_du
            )
            if bonds_exist:
                self._polydata.SetLines(bonds)
                self._polydata_bonds_exist = True
                return

        self._polydata_bonds_exist = False

    def create_bond_cell_array(
        self,
        rs: np.ndarray,
        covs: np.typing.NDArray[float],
        not_du: list[bool],
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

        tree = KDTree(rs)
        contacts = tree.query_ball_point(rs, 2 * np.max(covs) + tolerance, workers=-1)
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

        mask = js < ks
        js = js[mask]
        ks = ks[mask]
        diff = rs[js] - rs[ks]
        dist = np.sum(diff * diff, axis=1)
        sum_radii = (covs[js] + covs[ks] + tolerance) ** 2
        js = js[(0 < dist) & (dist < sum_radii)]
        ks = ks[(0 < dist) & (dist < sum_radii)]
        ls = not_du[js]
        ms = not_du[ks]

        n_points = len(ls)
        idxs = np.zeros((len(ls), 3), dtype=np.int64)
        idxs[:, 0] = 2
        idxs[:, 1] = ls
        idxs[:, 2] = ms
        bonds.SetCells(n_points, numpy_support.numpy_to_vtkIdTypeArray(idxs.flatten()))

        return bonds, len(ls) > 0

    def update_uc_polydata(self):
        """Updates the unit cell actor using the unit cell parameters
        from the current trajectory frame.
        """
        uc = self._reader.read_pbc(self._current_frame)
        if self._cell_visible and uc is not None:
            # update the unit cell
            a = uc.a_vector
            b = uc.b_vector
            c = uc.c_vector
            uc_points = vtk.vtkPoints()
            uc_points.SetNumberOfPoints(8)
            for i, v in enumerate([[0, 0, 0], a, b, c, a + b, a + c, b + c, a + b + c]):
                x, y, z = v
                uc_points.SetPoint(i, x, y, z)
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

    def get_atom_index(self, pid):
        """Return the atom index from the vtk data point index.

        Args:
            pid (int): the data point index
        """

        _, _, idx = (
            self.glyph.GetOutput().GetPointData().GetArray("scalars").GetTuple3(pid)
        )

        return int(idx)

    def get_render_window(self):
        """Returns the render window."""
        return self._iren.GetRenderWindow()

    @property
    def iren(self):
        return self._iren

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
        self._iren.Render()

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
        self._iren.Render()

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

        self._iren.Render()

    def on_clear_atomic_trace(self):
        """Event handler called when the user select the 'Atomic trace -> Clear' main menu item"""

        if not self._surfaces:
            return

        for surface in self._surfaces:
            surface.VisibilityOff()
            surface.ReleaseGraphicsResources(self._iren.GetRenderWindow())
            self._renderer.RemoveActor(surface)
        self._iren.Render()

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

    @property
    def renderer(self):
        return self._renderer

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
            return False

        self._current_frame = frame % self._reader.n_frames

        # update the atoms
        self.update_all_polydata()

        # Update the view.
        self.update_renderer()

    def set_reader(self, reader):
        """Sets the input object to be the new source of atom data for
        the 3D viewer.

        Parameters
        ----------
        reader : IReader
            typically an instance of HDF5Wrapper from MolecularViewer
        """

        if (self._reader is not None) and (reader.filename == self._reader.filename):
            return

        self.reset_camera = True
        self.clear_trajectory()

        self._reader = reader

        self._element_database = self._reader._trajectory
        self._n_atoms = self._reader.n_atoms
        self._n_frames = self._reader.n_frames
        self._current_frame = min(self._current_frame, self._n_frames - 1)

        self._atoms = self._reader.atom_types

        # Hack for reducing objects resolution when the system is big
        self._resolution = int(np.sqrt(3000000.0 / self._n_atoms))
        self._resolution = 10 if self._resolution > 10 else self._resolution
        self._resolution = 4 if self._resolution < 4 else self._resolution

        self._atom_colours = self._colour_manager.reinitialise_from_database(
            self._atoms, self._element_database, self.dummy_size
        )
        # this returns a list of indices, mapping colours to atoms

        self._atom_scales = np.array(
            [
                self._element_database.get_atom_property(at, "vdw_radius")
                for at in self._atoms
            ]
        ).astype(np.float32)
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

        scalars = ndarray_to_vtkarray(
            self._atom_colours, self._atom_scales, self._n_atoms
        )

        self.reset_all_polydata()
        self._polydata.GetPointData().SetScalars(scalars)

        self._colour_manager.onNewValues()
        self.new_max_frames.emit(self._n_frames - 1)
        self._trace_dialog.update_limits()

    @Slot(object)
    def take_atom_properties(self, data):
        colours, radii, numbers = data
        scalars = ndarray_to_vtkarray(colours, radii, numbers)
        self._polydata = vtk.vtkPolyData()
        self._polydata.GetPointData().SetScalars(scalars)
        self.update_all_polydata()
        self.update_renderer()

    def update_renderer(self):
        """
        Update the renderer
        """
        # deleting old frame
        self.clear_trajectory(clear_isosurfaces=False)

        # creating new polydata
        self._actors = vtk.vtkAssembly()
        for actor in self.create_all_actors():
            self._actors.AddPart(actor)

        # adding polydata to renderer
        self._renderer.AddActor(self._actors)

        # rendering
        if self.reset_camera:
            self._renderer.ResetCamera()
            self.reset_camera = False

        self._iren.Render()


class MolecularViewerExtended(MolecularViewer):
    """MolecularViewer which emits atom index when clicked."""

    clicked_atom_index = Signal(int)

    def __init__(self):
        super().__init__()
        self._iren.AddObserver("LeftButtonPressEvent", self.handle_click_event)

    def handle_click_event(self, obj, event=None):
        """Event handler when an atom is mouse-picked with the left mouse button"""

        if not self._reader:
            return

        if self.atom_actor is None:
            return

        if self._last_coords is None:
            return

        picker = vtk.vtkPropPicker()

        picker.AddPickList(self.atom_actor)
        picker.PickFromListOn()

        pos = obj.GetEventPosition()
        picker.Pick(pos[0], pos[1], 0, self._renderer)

        picked_actor = picker.GetActor()
        if picked_actor is None:
            return

        picked_pos = np.array(picker.GetPickPosition())
        _, picked_index = KDTree(self._last_coords).query(picked_pos)

        if picked_index < 0 or picked_index >= self._n_atoms:
            return

        self.clicked_atom_index.emit(picked_index)
        LOG.debug(f"Click event picked up atom index {picked_index}")


class MolecularViewerWithPicking(MolecularViewer):
    """This class implements a molecular viewer with picking."""

    clicked_atom_index = Signal(int)
    picked_atoms_changed = Signal(object)

    def __init__(self):
        super().__init__()
        # we set dummy size to something non-zero since we need to be
        # able to see it for picking purposes
        self.dummy_size = 0.1
        self._picking_domain = None
        self._picked_polydata = None
        self._picked_polydata_bonds_exist = False
        self._polydata_opacity = 0.15
        self.picked_atoms = set()
        self.build_events()

    def build_events(self):
        """Build the events."""
        self._iren.AddObserver("LeftButtonPressEvent", self.on_pick)

    def on_pick(self, obj, event=None):
        """Event handler when an atom is mouse-picked with the left mouse button"""

        if not self._reader:
            return

        if self._picking_domain is None:
            return

        picker = vtk.vtkPropPicker()

        picker.AddPickList(self._picking_domain)
        picker.PickFromListOn()

        pos = obj.GetEventPosition()
        picker.Pick(pos[0], pos[1], 0, self._renderer)

        picked_actor = picker.GetActor()
        if picked_actor is None:
            return

        picked_pos = np.array(picker.GetPickPosition())
        coords = self._reader.read_frame(self._current_frame)
        _, idx = KDTree(coords).query(picked_pos)
        self.on_pick_atom(idx)

    def on_pick_atom(self, picked_atom):
        """Change the color of a selected atom"""
        if self._reader is None:
            return

        if picked_atom < 0 or picked_atom >= self._n_atoms:
            return

        self.clicked_atom_index.emit(picked_atom)
        if picked_atom in self.picked_atoms:
            self.picked_atoms.remove(picked_atom)
        else:
            self.picked_atoms.add(picked_atom)

        self.update_picked_polydata()
        self.update_renderer()
        self.picked_atoms_changed.emit(self.picked_atoms)

    def change_picked(self, picked: set[int]):
        self.picked_atoms = picked
        self.update_picked_polydata()
        self.update_renderer()

    def update_picked_polydata(self):
        atoms = vtk.vtkPoints()

        if len(self.picked_atoms) == 0:
            self._picked_polydata.SetPoints(atoms)
            return

        picked = np.array(sorted(list(self.picked_atoms)))
        coords = self._reader.read_frame(self._current_frame)
        atoms.SetData(numpy_support.numpy_to_vtk(coords[picked]))
        self._picked_polydata.SetPoints(atoms)

        scalars = ndarray_to_vtkarray(
            self._colour_manager.colours[picked],
            self._colour_manager.radii[picked],
            np.arange(len(self.picked_atoms)),
        )
        self._picked_polydata.GetPointData().SetScalars(scalars)

        not_du = np.arange(len(self.picked_atoms))[self.du_log[picked]]
        if self._bonds_visible and len(not_du) >= 1:
            # do not bond atoms to dummy atoms
            rs = coords[picked][not_du]
            covs = self.covs[picked][not_du]

            bonds, bonds_exist = self.create_bond_cell_array(rs, covs, not_du)
            if bonds_exist:
                self._picked_polydata.SetLines(bonds)
                self._picked_polydata_bonds_exist = True
                return

        self._picked_polydata_bonds_exist = False

    def reset_all_polydata(self):
        super().reset_all_polydata()
        self._picked_polydata = vtk.vtkPolyData()

    def update_all_polydata(self):
        super().update_all_polydata()
        self.update_picked_polydata()

    def create_all_actors(self):
        actors = []
        if self._polydata is None or self._picked_polydata is None:
            return actors

        line_actor, ball_actor = self.create_traj_actors(
            self._polydata,
            line_opacity=self._polydata_opacity,
            ball_opacity=self._polydata_opacity,
        )
        picked_line_actor, picked_ball_actor = self.create_traj_actors(
            self._picked_polydata
        )
        if self._cell_visible:
            uc_actor = self.create_uc_actor()
            actors.append(uc_actor)
        if self._bonds_visible and self._polydata_bonds_exist:
            actors.append(line_actor)
        if self._bonds_visible and self._picked_polydata_bonds_exist:
            actors.append(picked_line_actor)
        if self._atoms_visible:
            self._picking_domain = ball_actor
            actors.append(ball_actor)
            actors.append(picked_ball_actor)
        else:
            self._picking_domain = None
        return actors

    @Slot(object)
    def take_atom_properties(self, data):
        colours, radii, numbers = data
        scalars = ndarray_to_vtkarray(colours, radii, numbers)
        self._polydata = vtk.vtkPolyData()
        self._polydata.GetPointData().SetScalars(scalars)

        picked_colours = []
        picked_radii = []
        picked_numbers = []
        for i in sorted(list(self.picked_atoms)):
            picked_colours.append(colours[i])
            picked_radii.append(radii[i])
            picked_numbers.append(numbers[i])

        scalars = ndarray_to_vtkarray(
            np.array(picked_colours),
            np.array(picked_radii),
            np.arange(len(self.picked_atoms)),
        )
        self._picked_polydata = vtk.vtkPolyData()
        self._picked_polydata.GetPointData().SetScalars(scalars)

        self.set_coordinates(self._current_frame)

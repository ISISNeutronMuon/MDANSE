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
from typing import List

import numpy as np
from scipy.spatial import cKDTree as KDTree

from qtpy import QtWidgets
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QSizePolicy

import vtk
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingAnnotation import vtkAxesActor

from MDANSE.Framework.InputData.HDFTrajectoryInputData import HDFTrajectoryInputData
from MDANSE.Chemistry import ATOMS_DATABASE as CHEMICAL_ELEMENTS
from MDANSE.MLogging import LOG

from MDANSE_GUI.MolecularViewer.readers import hdf5wrapper
from MDANSE_GUI.MolecularViewer.Dummy import PyConnectivity
from MDANSE_GUI.MolecularViewer.Contents import TrajectoryAtomData
from MDANSE_GUI.MolecularViewer.AtomProperties import (
    AtomProperties,
    ndarray_to_vtkarray,
)


def array_to_3d_imagedata(data, spacing):
    nx = data.shape[0]
    ny = data.shape[1]
    nz = data.shape[2]
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

    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                image.SetScalarComponentFromDouble(i, j, k, 0, data[i, j, k])

    return image


class MolecularViewer(QtWidgets.QWidget):
    """This class implements a molecular viewer."""

    new_max_frames = Signal(int)

    def __init__(self):
        super(MolecularViewer, self).__init__()

        self._scale_factor = 0.8

        self._datamodel = None

        self._iren = QVTKRenderWindowInteractor(self)

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

        self._surface = None

        self._reader = None

        self._current_frame = 0

        self._colour_manager = AtomProperties()
        self.dummy_size = 0.0

        self.reset_camera = False

    def setDataModel(self, datamodel: TrajectoryAtomData):
        self._datamodel = datamodel

    def _new_trajectory_object(self, fname: str, data: HDFTrajectoryInputData):
        reader = hdf5wrapper.HDF5Wrapper(fname, data.trajectory, data.chemical_system)
        self.set_reader(reader)

    @Slot(str)
    def _new_trajectory(self, fname: str):
        data = HDFTrajectoryInputData(fname)
        reader = hdf5wrapper.HDF5Wrapper(fname, data.trajectory, data.chemical_system)
        self.set_reader(reader)

    @Slot(float)
    def _new_scaling(self, scale_factor: float):
        self._scale_factor = scale_factor
        self.update_renderer()

    def _new_visibility(self, flags: List[bool]):
        self._atoms_visible = flags[0]
        self._bonds_visible = flags[1]
        self._axes_visible = flags[2]
        self._cell_visible = flags[3]
        self.axes_widget.SetEnabled(self._axes_visible)
        result = self.set_coordinates(self._current_frame)
        if result is False:
            self.update_renderer()

    @Slot()
    def _new_atom_parameters(self):
        if self._polydata is None or self._datamodel is None:
            return

        # we need to add the new colours to LUT
        # then assign new colour NUMBERS to _atom_colours

        # we also need to assign new atom radii to _atom_scales

        scalars = ndarray_to_vtkarray(
            self._atom_colours, self._atom_scales, self._n_atoms
        )

        self._polydata.GetPointData().SetScalars(scalars)

        self.update_renderer()

    def _draw_isosurface(self, index):
        """Draw the isosurface of an atom with the given index"""

        return None  # we are not ready for this

        if self._surface is not None:
            self.on_clear_atomic_trace()

        LOG.info("Computing isosurface ...")

        initial_coords = self._reader.read_frame(0)
        coords, lower_bounds, upper_bounds = self._reader.read_atom_trajectory(index)
        spacing, self._atomic_trace_histogram = histogram_3d(
            coords, lower_bounds, upper_bounds, 100, 100, 100
        )

        self._image = array_to_3d_imagedata(self._atomic_trace_histogram, spacing)
        isovalue = self._atomic_trace_histogram.mean()

        self._isocontour = vtk.vtkMarchingContourFilter()
        self._isocontour.UseScalarTreeOn()
        self._isocontour.ComputeNormalsOn()
        if vtk.vtkVersion.GetVTKMajorVersion() < 6:
            self._isocontour.SetInput(self.image)
        else:
            self._isocontour.SetInputData(self._image)
        self._isocontour.SetValue(0, isovalue)

        self._depthSort = vtk.vtkDepthSortPolyData()
        self._depthSort.SetInputConnection(self._isocontour.GetOutputPort())
        self._depthSort.SetDirectionToBackToFront()
        self._depthSort.SetVector(1, 1, 1)
        self._depthSort.SetCamera(self._camera)
        self._depthSort.SortScalarsOn()
        self._depthSort.Update()

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self._depthSort.GetOutputPort())
        mapper.ScalarVisibilityOff()
        mapper.Update()

        self._surface = vtk.vtkActor()
        self._surface.SetMapper(mapper)
        self._surface.GetProperty().SetColor((0, 0.5, 0.75))
        self._surface.GetProperty().SetOpacity(0.5)
        self._surface.PickableOff()

        self._surface.GetProperty().SetRepresentationToSurface()

        self._surface.GetProperty().SetInterpolationToGouraud()
        self._surface.GetProperty().SetSpecular(0.4)
        self._surface.GetProperty().SetSpecularPower(10)

        self._renderer.AddActor(self._surface)

        self._surface.SetPosition(
            lower_bounds[0, 0], lower_bounds[0, 1], lower_bounds[0, 2]
        )

        self._iren.Render()

        LOG.info("... done")

    def create_all_actors(self):
        line_actor, ball_actor = self.create_traj_actors(self._polydata)
        actors = []
        if self._cell_visible:
            uc_actor = self.create_uc_actor()
            actors.append(uc_actor)
        if self._bonds_visible and self._polydata_bonds_exist:
            actors.append(line_actor)
        if self._atoms_visible:
            actors.append(ball_actor)
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

    def create_traj_actors(self, polydata, line_opacity=1.0, ball_opacity=1.0):
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

        temp_scale = float(0.2 * self._scale_factor)
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

    def clear_trajectory(self):
        """Clear the vtk scene from atoms and bonds actors."""

        if not hasattr(self, "_actors"):
            return
        if self._actors is None:
            return

        self._actors.VisibilityOff()
        self._actors.ReleaseGraphicsResources(self.get_render_window())
        self._renderer.RemoveActor(self._actors)

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
        coords = self._reader.read_frame(self._current_frame)

        if self._atoms_visible or self._bonds_visible:
            atoms = vtk.vtkPoints()
            atoms.SetNumberOfPoints(self._n_atoms)
            for i in range(self._n_atoms):
                x, y, z = coords[i, :]
                atoms.SetPoint(i, x, y, z)

            self._polydata.SetPoints(atoms)

        if self._bonds_visible:
            # do not bond atoms to dummy atoms
            not_du = np.array(
                [
                    i
                    for i, at in enumerate(self._reader.atom_types)
                    if CHEMICAL_ELEMENTS.get_atom_property(at, "element") != "dummy"
                ]
            )
            rs = coords[not_du]
            covs = np.array(
                [
                    CHEMICAL_ELEMENTS.get_atom_property(at, "covalent_radius")
                    for at in self._reader.atom_types
                ]
            )[not_du]

            bonds, bonds_exist = self.create_bond_cell_array(rs, covs, not_du)
            if bonds_exist:
                self._polydata.SetLines(bonds)
                self._polydata_bonds_exist = True
                return

        self._polydata_bonds_exist = False

    def create_bond_cell_array(self, rs, covs, not_du, tolerance=0.04):
        # determine and set bonds without PBC applied
        tree = KDTree(rs)
        bonds = vtk.vtkCellArray()
        contacts = tree.query_ball_tree(tree, 2 * np.max(covs) + tolerance)
        n_bonds = 0
        for i, idxs in enumerate(contacts):
            if len(idxs) == 0:
                continue
            diff = rs[i] - rs[idxs]
            dist = np.sum(diff * diff, axis=1)
            sum_radii = (covs[i] + covs[idxs] + tolerance) ** 2
            js = np.array(idxs)[(0 < dist) & (dist < sum_radii)]
            js = not_du[js[i < js]]
            n_bonds += len(js)
            for j in js:
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, not_du[i])
                line.GetPointIds().SetId(1, j)
                bonds.InsertNextCell(line)
        return bonds, n_bonds > 0

    def update_uc_polydata(self):
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

    def on_change_atomic_trace_opacity(self, opacity):
        """Event handler called when the opacity level is changed."""

        if self._surface is None:
            return

        self._surface.GetProperty().SetOpacity(opacity)
        self._iren.Render()

    def on_change_atomic_trace_isocontour_level(self, level):
        """Event handler called when the user change the isocontour level."""

        if self._surface is None:
            return

        self._isocontour.SetValue(0, level)
        self._isocontour.Update()
        self._iren.Render()

    def on_change_atomic_trace_rendering_type(self, rendering_type):
        """Event handler called when the user change the rendering type for the atomic trace."""

        if self._surface is None:
            return

        if rendering_type == "wireframe":
            self._surface.GetProperty().SetRepresentationToWireframe()
        elif rendering_type == "surface":
            self._surface.GetProperty().SetRepresentationToSurface()
        elif rendering_type == "points":
            self._surface.GetProperty().SetRepresentationToPoints()
            self._surface.GetProperty().SetPointSize(3)
        else:
            return

        self._iren.Render()

    def on_clear_atomic_trace(self):
        """Event handler called when the user select the 'Atomic trace -> Clear' main menu item"""

        if self._surface is None:
            return

        self._surface.VisibilityOff()
        self._surface.ReleaseGraphicsResources(self._iren.GetRenderWindow())
        self._renderer.RemoveActor(self._surface)
        self._iren.Render()

        self._surface = None

    def on_open_atomic_trace_settings_dialog(self):
        """Event handler which pops the atomic trace settings."""

        if self._surface is None:
            return

        hist_min = self._atomic_trace_histogram.min()
        hist_max = self._atomic_trace_histogram.max()
        hist_mean = self._atomic_trace_histogram.mean()

        dlg = AtomicTraceSettingsDialog(hist_min, hist_max, hist_mean, self)

        dlg.rendering_type_changed.connect(self.on_change_atomic_trace_rendering_type)
        dlg.opacity_changed.connect(self.on_change_atomic_trace_opacity)
        dlg.isocontour_level_changed.connect(
            self.on_change_atomic_trace_isocontour_level
        )

        dlg.show()

    def on_show_atomic_trace(self):
        if self._previously_picked_atom is None:
            LOG.warning("No atom selected for computing atomic trace")
            return

        self._draw_isosurface(self._previously_picked_atom[0])

    @property
    def renderer(self):
        return self._renderer

    def set_connectivity_builder(self, coords, covalent_radii):
        # Compute the bounding box of the system
        lower_bound = coords.min(axis=0)
        upper_bound = coords.max(axis=0)

        # Enlarge it a bit to not miss any atom
        lower_bound -= 1.0e-6
        upper_bound += 1.0e-6

        # Initializes the octree used to build the connectivity
        self._connectivity_builder = PyConnectivity(lower_bound, upper_bound, 0, 10, 18)

        # Add the points to the octree
        for index, xyz, radius in zip(range(self._n_atoms), coords, covalent_radii):
            self._connectivity_builder.add_point(index, xyz, radius)

    @Slot(int)
    def set_coordinates(self, frame: int):
        """Sets a new configuration.

        @param frame: the configuration number
        @type frame: integer
        """
        if self._reader is None:
            return False

        self._current_frame = frame % self._reader.n_frames

        # update the atoms
        self.update_all_polydata()

        # Update the view.
        self.update_renderer()

    def set_reader(self, reader, frame=0):
        """Set the trajectory at a given frame

        Args:
            reader (IReader): the trajectory object
            frame (int): the selected frame
        """

        if (self._reader is not None) and (reader.filename == self._reader.filename):
            return

        self.reset_camera = True
        self.clear_trajectory()

        self._reader = reader

        self._n_atoms = self._reader.n_atoms
        self._n_frames = self._reader.n_frames

        self.new_max_frames.emit(self._n_frames - 1)

        self._atoms = self._reader.atom_types

        # Hack for reducing objects resolution when the system is big
        self._resolution = int(np.sqrt(3000000.0 / self._n_atoms))
        self._resolution = 10 if self._resolution > 10 else self._resolution
        self._resolution = 4 if self._resolution < 4 else self._resolution

        self._atom_colours = self._colour_manager.reinitialise_from_database(
            self._atoms, CHEMICAL_ELEMENTS, self.dummy_size
        )
        # this returs a list of indices, mapping colours to atoms

        self._atom_scales = np.array(
            [
                CHEMICAL_ELEMENTS.get_atom_property(at, "vdw_radius")
                for at in self._atoms
            ]
        ).astype(np.float32)

        scalars = ndarray_to_vtkarray(
            self._atom_colours, self._atom_scales, self._n_atoms
        )

        self.reset_all_polydata()
        self._polydata.GetPointData().SetScalars(scalars)

        self._current_frame = frame
        self._colour_manager.onNewValues()

    @Slot(object)
    def take_atom_properties(self, data):
        colours, radii, numbers = data
        scalars = ndarray_to_vtkarray(colours, radii, numbers)
        self._polydata = vtk.vtkPolyData()
        self._polydata.GetPointData().SetScalars(scalars)
        self.set_coordinates(self._current_frame)

        # self._datamodel.setReader(reader)

    def update_renderer(self):
        """
        Update the renderer
        """
        # deleting old frame
        self.clear_trajectory()

        # creating new polydata
        self._actors = vtk.vtkAssembly()
        for actor in self.create_all_actors():
            self._actors.AddPart(actor)

        # adding polydata to renderer
        self._renderer.AddActor(self._actors)

        # rendering
        if self.reset_camera:
            self._renderer.ResetCamera()
            self._renderer.ResetCameraClippingRange()
            self.reset_camera = False

        self._iren.Render()


class MolecularViewerWithPicking(MolecularViewer):
    """This class implements a molecular viewer with picking."""

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
        picked = np.array(sorted(list(self.picked_atoms)))
        coords = self._reader.read_frame(self._current_frame)

        atoms = vtk.vtkPoints()
        atoms.SetNumberOfPoints(len(self.picked_atoms))
        for i, j in enumerate(picked):
            x, y, z = coords[j, :]
            atoms.SetPoint(i, x, y, z)
        self._picked_polydata.SetPoints(atoms)

        picked_colours = []
        picked_radii = []
        for i in sorted(list(self.picked_atoms)):
            picked_colours.append(self._colour_manager.colours[i])
            picked_radii.append(self._colour_manager.radii[i])
        scalars = ndarray_to_vtkarray(
            np.array(picked_colours),
            np.array(picked_radii),
            np.arange(len(self.picked_atoms)),
        )
        self._picked_polydata.GetPointData().SetScalars(scalars)

        not_du = np.array(
            [
                i
                for i, j in enumerate(picked)
                if CHEMICAL_ELEMENTS.get_atom_property(
                    self._reader.atom_types[j], "element"
                )
                != "dummy"
            ]
        )

        if self._bonds_visible and len(not_du) >= 1:
            # do not bond atoms to dummy atoms
            rs = coords[picked][not_du]
            covs = np.array(
                [
                    CHEMICAL_ELEMENTS.get_atom_property(
                        self._reader.atom_types[i], "covalent_radius"
                    )
                    for i in picked
                ]
            )[not_du]

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
        line_actor, ball_actor = self.create_traj_actors(
            self._polydata,
            line_opacity=self._polydata_opacity,
            ball_opacity=self._polydata_opacity,
        )
        picked_line_actor, picked_ball_actor = self.create_traj_actors(
            self._picked_polydata
        )
        actors = []
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

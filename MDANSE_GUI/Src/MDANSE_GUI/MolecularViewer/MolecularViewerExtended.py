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

from pathlib import Path

import numpy as np
import vtk
from qtpy.QtCore import QTimer, Signal
from vtk.util import numpy_support

from MDANSE.MLogging import LOG

from .MolecularViewer import MolecularViewer


class MolecularViewerExtended(MolecularViewer):
    """MolecularViewer which emits atom index when clicked."""

    clicked_atom_index = Signal(int)

    def __init__(self):
        super().__init__()
        self._iren.AddObserver("LeftButtonPressEvent", self.handle_click_event)

        # Initialize rotation parameters
        self.rotation_speed = 5
        self.secondary_speed = 0.23 * self.rotation_speed

        self.placeholder_actors = []

        # Animation timer for rotating the 3D model
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self.animate_rotation)
        self.create_placeholder()
        self.start_animation()
        # reset camera once more after the gui has been set up
        QTimer.singleShot(0, lambda: self._renderer.ResetCameraScreenSpace(0.4))

    def set_reader(self, reader):
        """Stops the animation, clears the placeholder, sets the camera
        position center back to the normal position, and finally set the
        reader which loads the trajectory."""
        self._animation_timer.stop()
        self.clear_placeholder()
        self._camera.SetWindowCenter(0.0, 0.0)
        super().set_reader(reader)

    def handle_click_event(self, obj, event=None):
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
        LOG.debug("Click event picked up atom index %d", picked_index)

    def clear_placeholder(self):
        """Clears the placeholder actors and removes them from the renderer."""
        if not self.placeholder_actors:
            return

        for actor in self.placeholder_actors:
            self._renderer.RemoveActor(actor)

        self.placeholder_actors = []

    def create_placeholder(self):
        """Loads a 3D blender model of mdanse into the viewer."""
        self.clear_placeholder()

        spheres = [
            ("center_sphere.stl", (0.6, 0.6, 0.6), 0.4, (0, 0, 0)),  # grey center
            ("yellow_sphere.stl", (0.2, 0.85, 0.25), 0.4, (0, 0, 0)),
            ("blue_sphere.stl", (0.2, 0.35, 0.85), 0.4, (0, 0, 0)),
            ("red_sphere.stl", (0.85, 0.24, 0.2), 0.4, (0, 0, 0)),
        ]

        for filename, colour, scale, position in spheres:
            reader = vtk.vtkSTLReader()
            filepath = Path(__file__).parents[1] / "Icons" / filename
            reader.SetFileName(filepath)
            reader.Update()

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(reader.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(colour)

            actor.SetPosition(position)
            actor.SetScale(scale)
            # make center sphere metallic and semi-transparent
            if filename == "center_sphere.stl":
                actor.GetProperty().SetOpacity(
                    0.5
                )  # Make the center sphere semi-transparent
                actor.GetProperty().SetSpecular(1)
                actor.GetProperty().SetSpecularPower(100)
                actor.GetProperty().SetMetallic(1.0)
                actor.GetProperty().SetRoughness(0.2)

            individual_transform = vtk.vtkTransform()
            individual_transform.Identity()
            individual_transform.Translate(0.0, 0.5, 0.5)
            individual_transform.Scale(0.5, 0.5, 0.5)
            actor.SetUserTransform(individual_transform)

            self._renderer.AddActor(actor)
            self.placeholder_actors.append(actor)

    def start_animation(self):
        """Set the camera and start the placeholder animation."""
        # side view of 3d model
        self._camera.SetPosition(20, 0, 0)
        self._camera.SetFocalPoint(0, 0, 0)
        self._camera.SetViewUp(0, 0, 1)
        self._camera.SetWindowCenter(-0.5, -0.5)
        self._renderer.ResetCameraScreenSpace(0.4)
        self._animation_timer.start(50)

    def animate_rotation(self):
        """Continuously rotate the 3D model."""
        if self._animation_timer.isActive() and self._viewer_is_visible:
            for i, actor in enumerate(self.placeholder_actors):
                if i == 0:  # center sphere
                    actor.RotateZ(self.rotation_speed)
                elif i == 1:  # green sphere
                    actor.RotateY(-self.rotation_speed)
                    actor.RotateZ(self.secondary_speed)
                elif i == 2:  # blue sphere
                    actor.RotateX(self.rotation_speed)
                    actor.RotateZ(-self.secondary_speed)
                elif i == 3:  # red sphere
                    actor.RotateY(-self.rotation_speed)
                    actor.RotateX(-self.secondary_speed)
            self.update_renderer()

    def clear_panel(self):
        """Clears the panel, and then create and animate the placeholder."""
        super().clear_panel()
        if not self._animation_timer.isActive():
            self.create_placeholder()
            self.start_animation()

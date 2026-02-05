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

from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import QVBoxLayout, QWidget

from MDANSE.MolecularDynamics.Trajectory import Trajectory
from MDANSE_GUI.MolecularViewer import MolecularViewer
from MDANSE_GUI.MolecularViewer.Controls import ViewerControls


class View3D(QWidget):
    error = Signal(str)

    def __init__(self, viewer: MolecularViewer, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QVBoxLayout(self)
        self.setLayout(layout)

        controls = ViewerControls(self)
        viewer.setParent(controls)
        controls.setViewer(viewer)
        controls.createSidePanel()
        controls.create_property_viewer()
        controls.create_trace_dialog()
        if hasattr(viewer, "clicked_atom_index"):
            viewer.clicked_atom_index.connect(controls._trace_widget.accept_atom_index)
        layout.addWidget(controls)
        self._viewer = viewer
        self._controls = controls
        self._controls.toggle_projection()

    @Slot(tuple)
    def update_panel(self, data: tuple[str, Trajectory] | None):
        if data is None or data[0] == "":
            self._viewer.clear_panel()
            self._controls._property_widget.clear_viewer()
            return
        fullpath, incoming = data
        try:
            self._viewer._new_trajectory_object(fullpath, incoming)
            self._controls._property_widget.extract_props(incoming)
        except AttributeError:
            self.error.emit(f"3D View could not visualise {fullpath}")
            self._viewer.clear_panel()
            self._controls._property_widget.clear_viewer()

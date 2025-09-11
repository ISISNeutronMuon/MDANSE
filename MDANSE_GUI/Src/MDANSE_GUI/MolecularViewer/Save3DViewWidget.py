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
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from qtpy.QtCore import Signal, Slot
from qtpy.QtGui import QValidator
from qtpy.QtWidgets import (
    QDoubleSpinBox,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from MDANSE_GUI.MolecularViewer.MolecularViewer import MolecularViewer


TRACE_PARAMETERS = {
    "atom_number": 0,
    "fine_sampling": 3,
    "surface_colour": (0, 0.5, 0.75),
    "surface_opacity": 0.5,
    "trace_cutoff": 5,
    "surface_number": -1,
}


class Save3DViewWidget(QWidget):
    new_atom_trace = Signal(dict)
    remove_atom_trace = Signal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self._molviewer = None

        self.setWindowTitle("Add atom trace to the view")
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self._n_atoms = 0
        initial_parameters = copy.copy(TRACE_PARAMETERS)
        self._opacity = initial_parameters["surface_opacity"]
        self._color = initial_parameters["surface_colour"]
        self._iso_percentile = initial_parameters["trace_cutoff"]
        self.populate_layout()

    def initialise_values(self, viewer: MolecularViewer):
        """An instance of MolecularViewer will be saved as
        an internal attribute to allow this widget to
        access attributes and call methods directly.

        Parameters
        ----------
        viewer : MolecularViewer
            One of the 3D viewer instances in the MDANSE GUI
        """
        self._molviewer = viewer
        self._n_atoms = viewer._n_atoms

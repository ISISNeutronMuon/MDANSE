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


class RGBValidator(QValidator):
    """A custom validator for a QLineEdit.
    It is intended to limit the input to a string
    of 3 integer numbers in the range of 0-255
    separated by commas.

    Additional checks are necessary later in the code,
    since the validator cannot exclude the cases of
    1 or 2 comma-separated values, since they are
    a preliminary step when typing in 3 numbers.
    """

    def validate(
        self, input_string: str, position: int
    ) -> tuple[QValidator.State, int, str]:
        """Implementation of the virtual method of QValidator.
        It takes in the string from a QLineEdit and the cursor position,
        and an enum value of the validator state. Widgets will reject
        inputs which change the state to Invalid.

        Parameters
        ----------
        input_string : str
            current contents of a text input field
        position : int
            position of the cursor in the text input field

        Returns
        -------
        Tuple[int,str]
            a tuple of (validator state, input string, cursor position)
        """
        state = QValidator.State.Intermediate
        comma_count = input_string.count(",")
        if len(input_string) > 0:
            try:
                rgb = [int(x) for x in input_string.split(",")]
            except (TypeError, ValueError):
                if input_string[-1] == "," and comma_count < 3:
                    state = QValidator.State.Intermediate
                else:
                    state = QValidator.State.Invalid
            else:
                if any([x > 255 for x in rgb]):
                    state = QValidator.State.Invalid
                elif len(rgb) > 3:
                    state = QValidator.State.Invalid
                elif len(rgb) == 3:
                    if all([(x >= 0) and (x < 256) for x in rgb]):
                        state = QValidator.State.Acceptable
                else:
                    state = QValidator.State.Intermediate
        return state, input_string, position


class TraceWidget(QWidget):
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

    def populate_layout(self):
        """Creates all the widgets, places them in the layout
        and connects their signals and slots.
        """
        layout = self.layout()
        self.add_trace_button = QPushButton("Calculate and add atom trace", self)
        self.remove_trace_button = QPushButton("Remove atom trace", self)
        self.add_trace_button.clicked.connect(self.new_trace_details)
        self.remove_trace_button.clicked.connect(self.remove_trace)
        self._atom_spinbox = QSpinBox(self)
        self._surface_spinbox = QSpinBox(self)
        self._fraction_spinbox = QSpinBox(self)
        self._grid_spinbox = QSpinBox(self)
        self._opacity_spinbox = QDoubleSpinBox(self)
        self._colour_lineedit = QLineEdit("0,128,192", self)
        self._colour_lineedit.setPlaceholderText("0,128,192 (red,green,blue)")
        self._colour_validator = RGBValidator(self._colour_lineedit)
        self._colour_lineedit.setValidator(self._colour_validator)
        self._colour_lineedit.textChanged.connect(self.check_rgb)
        for sbox in [
            self._atom_spinbox,
            self._surface_spinbox,
            self._fraction_spinbox,
            self._opacity_spinbox,
        ]:
            sbox.setMinimum(0)
            sbox.setValue(0)
        self.update_limits()
        self._fraction_spinbox.setMaximum(100)
        self._fraction_spinbox.setValue(5)
        self._grid_spinbox.setMaximum(10)
        self._grid_spinbox.setMinimum(1)
        self._grid_spinbox.setValue(3)
        self._opacity_spinbox.setMaximum(1.0)
        self._opacity_spinbox.setValue(0.5)
        self._opacity_spinbox.setSingleStep(0.01)
        for label, widget in [
            ("Selected atom index: ", self._atom_spinbox),
            ("Sampling step (1=coarse, 10=fine)", self._grid_spinbox),
            ("Trace percentile for isovalue", self._fraction_spinbox),
            ("Isosurface opacity", self._opacity_spinbox),
            ("Isosurface colour (R,G,B)", self._colour_lineedit),
        ]:
            temp_box = QGroupBox(label, self)
            temp_layout = QVBoxLayout(temp_box)
            temp_layout.addWidget(widget)
            layout.addWidget(temp_box)
        layout.addWidget(self.add_trace_button)
        for label, widget in [
            ("Remove the surface with index: ", self._surface_spinbox)
        ]:
            temp_box = QGroupBox(label, self)
            temp_layout = QVBoxLayout(temp_box)
            temp_layout.addWidget(widget)
            layout.addWidget(temp_box)
        layout.addWidget(self.remove_trace_button)

    @Slot(int)
    def accept_atom_index(self, new_index: int):
        """Set atom index from external source (typically 3D view)"""
        self._atom_spinbox.setValue(new_index)

    @Slot()
    def update_limits(self):
        """Changes the limits of the spinboxes when the current trajectory
        is changed or an isosurface is added/removed.
        """
        if self._molviewer is None:
            return
        self._atom_spinbox.setMaximum(max(self._molviewer._n_atoms - 1, 0))
        self._surface_spinbox.setMaximum(max(len(self._molviewer._surfaces) - 1, 0))
        self.enable_buttons()

    @Slot(str)
    def check_rgb(self, colour_string: str):
        """This method disables the button which creates an isosurface,
        if the coulor input field text contains less than three numbers,
        and re-enables it if it reaches three numbers.

        Parameters
        ----------
        colour_string : str
            The current contents of the colour input QLineEdit
        """
        tokens = colour_string.split(",")
        non_empty = all([len(token) > 0 for token in tokens])
        colour_count = len(tokens)
        self.add_trace_button.setEnabled(non_empty and colour_count == 3)

    def enable_buttons(self):
        """This method disables the button removing an isosurface
        if no isosurfaces are present. It also disables the isosurface
        creation button if the current view contains no atoms.
        """
        if self._molviewer is None:
            return
        self.remove_trace_button.setEnabled(len(self._molviewer._surfaces) != 0)
        self.add_trace_button.setEnabled(self._molviewer._n_atoms > 0)

    def get_values(self) -> dict[str, Any]:
        """Reads the values of the input widgets and returns
        a dictionary containing these values.

        Returns
        -------
        Dict[str, Any]
            A dictionary of all the input parameters from the widgets
        """
        params = copy.copy(TRACE_PARAMETERS)
        params["atom_number"] = self._atom_spinbox.value()
        params["surface_number"] = self._surface_spinbox.value()
        with suppress(ValueError, TypeError):
            params["surface_colour"] = [
                float(x) / 256 for x in self._colour_lineedit.text().split(",")
            ]
        params["trace_cutoff"] = self._fraction_spinbox.value()
        params["fine_sampling"] = self._grid_spinbox.value()
        params["surface_opacity"] = self._opacity_spinbox.value()
        return params

    def new_trace_details(self):
        """This method triggers the calculation of an isosurface
        by sending the parameter dictionary via a Qt signal.
        """
        params = self.get_values()
        self.new_atom_trace.emit(params)

    def remove_trace(self):
        """This method sends a Qt signal to instruct a 3D view
        to delete the currently selected isosurface."""
        params = self.get_values()
        self.remove_atom_trace.emit(params["surface_number"])
